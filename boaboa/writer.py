import json
import os
import re
import time

from groq import Groq

from boaboa.config import (
    ALLOWED_LABELS,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_MODEL_FALLBACKS,
    GROQ_API_KEY,
    GROQ_MODEL_OVERRIDE,
    GROQ_MODEL_PRIORITY,
    MAX_LABELS_PER_POST,
    META_DESC_IDEAL_MAX,
    META_DESC_IDEAL_MIN,
    MIN_SOURCE_CHARS,
    MIN_SOURCE_SENTENCES,
    SEO_TITLE_IDEAL_MAX,
    SEO_TITLE_IDEAL_MIN,
    SEO_TITLE_MAX_CHARS,
)
from boaboa.extractor import count_sentences
from boaboa.quality_guard import sanitize_article_data, validate_article_quality

NON_CHAT_KEYWORDS = ("whisper", "guard", "embed", "vision", "audio", "tts", "playai")
REASONING_MODEL_KEYWORDS = ("gpt-oss", "deepseek-r1", "qwq", "reasoning", "thinking")


def _is_reasoning_model(model_id: str) -> bool:
    lower = (model_id or "").lower()
    return any(k in lower for k in REASONING_MODEL_KEYWORDS)


def _model_size_score(model_id: str) -> tuple[int, int]:
    lower = model_id.lower()
    size_match = re.search(r"(\d+)b\b", lower)
    param_b = int(size_match.group(1)) if size_match else 0
    is_instant = 1 if ("instant" in lower or "mini" in lower) else 0
    return (param_b, -is_instant)


def get_groq_model_candidates(groq_client: Groq | None = None) -> list[str]:
    """Mengembalikan daftar model obrolan yang tersedia diurutkan sesuai prioritas."""
    if GROQ_MODEL_OVERRIDE:
        return [GROQ_MODEL_OVERRIDE]

    candidates: list[str] = []
    if groq_client:
        try:
            model_data = groq_client.models.list().data
            all_models = [m.id for m in model_data]
            chat_models = [
                m_id for m_id in all_models
                if not any(blocked in m_id.lower() for blocked in NON_CHAT_KEYWORDS)
            ]

            chat_map = {m.lower(): m for m in chat_models}
            for preferred in GROQ_MODEL_PRIORITY:
                if preferred.lower() in chat_map:
                    real_name = chat_map[preferred.lower()]
                    if real_name not in candidates:
                        candidates.append(real_name)

            if chat_models:
                chat_models.sort(key=_model_size_score, reverse=True)
                for m in chat_models:
                    if m not in candidates:
                        candidates.append(m)
        except Exception as e:
            print(f"Peringatan deteksi model Groq: {e}", flush=True)

    if not candidates:
        candidates = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    return candidates


def get_best_groq_model(groq_client: Groq | None = None) -> str:
    candidates = get_groq_model_candidates(groq_client)
    return candidates[0] if candidates else "llama-3.3-70b-versatile"


def _parse_json_response(raw_content: str) -> dict:
    clean = (raw_content or "").strip()
    clean = re.sub(r"<think>.*?</think>", "", clean, flags=re.S)
    clean = clean.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        clean = clean[start : end + 1]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        clean_fixed = re.sub(r",\s*([}\]])", r"\1", clean)
        return json.loads(clean_fixed)


def _call_gemini_structured(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model_name: str = "",
) -> dict:
    """Memanggil Gemini API via SDK google-genai dengan structured JSON output dan multi-model fallback."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    models_to_try = [model_name] if model_name else []
    for m in GEMINI_MODEL_FALLBACKS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for target_model in models_to_try:
        try:
            response = client.models.generate_content(
                model=target_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            raw = response.text or ""
            return _parse_json_response(raw)
        except Exception as e:
            last_error = e
            print(f"Percobaan Gemini API model [{target_model}] gagal ({e}). Mencoba fallback...", flush=True)

    raise RuntimeError(f"Semua kandidat model Gemini gagal dieksekusi: {last_error}")


def _call_groq_json(
    groq_client: Groq,
    model_name: str | list[str],
    messages: list[dict],
    temperature: float = 0.2,
    max_retries: int = 3,
) -> dict:
    if isinstance(model_name, list) and model_name:
        models_to_try = list(model_name)
    elif isinstance(model_name, str) and model_name:
        models_to_try = [model_name]
        for fallback in GROQ_MODEL_PRIORITY:
            if fallback.lower() != model_name.lower() and fallback not in models_to_try:
                models_to_try.append(fallback)
    else:
        models_to_try = list(GROQ_MODEL_PRIORITY)

    last_error = None
    for attempt in range(1, max_retries + 1):
        current_model = models_to_try[min(attempt - 1, len(models_to_try) - 1)]
        try:
            extra_body = {}
            if _is_reasoning_model(current_model):
                extra_body["reasoning_format"] = "hidden"

            call_kwargs = {
                "messages": messages,
                "model": current_model,
                "temperature": temperature,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"},
            }
            if extra_body:
                call_kwargs["extra_body"] = extra_body

            completion = groq_client.chat.completions.create(**call_kwargs)
            raw = completion.choices[0].message.content
            return _parse_json_response(raw)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_sec = 2 * attempt
                next_model = models_to_try[min(attempt, len(models_to_try) - 1)]
                switch_msg = f" (ganti ke model fallback: {next_model})" if next_model != current_model else ""
                print(
                    f"Percobaan AI {attempt}/{max_retries} [{current_model}] gagal ({e})."
                    f"{switch_msg} Mengulang dalam {wait_sec} dtk...",
                    flush=True,
                )
                time.sleep(wait_sec)
    raise RuntimeError(f"Gagal memanggil Groq API setelah {max_retries} percobaan: {last_error}")


def _build_system_instruction() -> str:
    labels_str = ", ".join(f'"{lbl}"' for lbl in ALLOWED_LABELS)
    return (
        "Kamu adalah redaktur senior dan jurnalis profesional portal berita BoaBoa (boaboa.bataktive.com, standar Dewan Pers Indonesia).\n"
        "Tugasmu adalah menyusun ulang berita berdasarkan Naskah Sumber menjadi artikel berita "
        "Bahasa Indonesia jurnalistik baku (PUEBI/EYD V) yang tajam, akurat, informatif, bebas clickbait, "
        "serta patuh penuh pada standar editorial Dewan Pers dan SEO boaboa.bataktive.com.\n\n"
        "ATURAN KETAT ETIKA JURNALISTIK & STANDAR DEWAN PERS:\n"
        "1. AKURASI FAKTA & TAHUN MUTLAK: Hanya gunakan fakta, nama tokoh, jabatan, lokasi, angka, tahun/tanggal, "
        "dan istilah teknis yang TERTULIS JELAS pada Naskah Sumber (cocokkan tahun dengan Tanggal Terbit Sumber). "
        "DILARANG KERAS mengarang data, statistik, tahun lain, luas wilayah, hasil survei, atau fakta yang tidak ada di sumber.\n"
        "2. ASAS PRADUGA TAK BERSALAH (MUTLAK UNTUK KASUS HUKUM, KRIMINAL, KECELAKAAN & PERISTIWA):\n"
        "   - Wajib menggunakan kata 'diduga', 'terduga', 'disangkakan', atau 'menurut keterangan aparat penegak hukum'.\n"
        "   - Samarkan nama/identitas korban anak-anak dan korban kejahatan asusila.\n"
        "   - Hindari penghakiman sepihak sebelum adanya keputusan hukum tetap dari pengadilan.\n"
        "3. KUTIPAN BERSYARAT: Sertakan tag <blockquote><p>Kutipan... - Nama Narasumber, Jabatan</p></blockquote> "
        "HANYA JIKA di Naskah Sumber terdapat kutipan langsung yang memiliki nama narasumber yang jelas. "
        "Jangan gunakan tanda petik ganda tambahan di dalam <p> di dalam <blockquote>. "
        "Jika Naskah Sumber tidak memiliki kutipan langsung bernarasumber jelas, JANGAN membuat <blockquote> dan "
        "DILARANG mengarang atribusi generik seperti 'Tokoh Adat setempat' atau 'Sumber resmi'.\n"
        "4. KEMURNIAN BAHASA: Tulis 100% dalam Bahasa Indonesia jurnalistik yang jernih, kalimat aktif, dan mengalir. "
        "DILARANG mencampur kata/aksara asing (Inggris, Mandarin, Kiril, dll.) kecuali nama resmi, merek, atau istilah "
        "hukum/teknis yang memang digunakan di Naskah Sumber.\n"
        "5. LARANGAN KERAS FRASA KLISE & BACA JUGA:\n"
        "   - DILARANG menulis bagian 'Baca Juga' atau 'Simak Juga' di dalam teks naskah.\n"
        "   - DILARANG menggunakan frasa klise AI seperti: 'Dalam era digital...', 'Secara keseluruhan...', 'Bukan rahasia lagi...', 'Tak dapat dipungkiri...'.\n"
        "6. KONTEKS LOKAL & DAMPAK KEBIJAKAN:\n"
        "   - Sisipkan 1 paragraf Konteks Lokal atau Dampak Kebijakan yang relevan bagi masyarakat Sumatera Utara (Medan, Tapanuli Raya, Danau Toba, Pantai Timur, Dataran Tinggi, atau Nias).\n"
        "7. STRUKTUR PIRAMIDA TERBALIK & ANTI-THIN CONTENT:\n"
        "   - 'lead_paragraph': Paragraf pembuka 2–3 kalimat padat langsung ke inti fakta utama (5W+1H). JANGAN menulis awalan 'BoaBoa.com -', 'Bataktive.com -' atau nama kota di awal kalimat.\n"
        "   - 'body_html': 3 hingga 5 paragraf mengalir (target total artikel >= 280 kata) dengan subjudul <h2> yang informatif. DILARANG memakai tag <h1>, <script>, <iframe>, atau JSON-LD.\n"
        "8. FORMULA JUDUL BER-HOOK KUAT & SEO-FRIENDLY (IDEAL 50–70 KARAKTER, MAKSIMAL 72 KARAKTER):\n"
        "   - DAFTAR FRASA KLISE TERLARANG DALAM JUDUL:\n"
        "     * JANGAN memakai kata/pola: 'Dorong Ekonomi / Inovasi', 'Masih Sesuai Tahapan', 'Tekankan Pentingnya', 'Hormati Jasa', 'Hadiri Acara / Rapat', 'Gelar Sosialisasi / Integrasi', 'Ikuti Anev', 'Peringati HKN / Hari Jadi', 'Tutup Kegiatan', 'Sinergi Ekonomi'. Judul pasif seperti ini membosankan dan diabaikan pembaca!\n"
        "   - WAJIB MEMILIH SALAH SATU FORMULA HOOK JURNALISTIK BERTARING:\n"
        "     a) FORMULA KONTRAS / KEJUTAN / UNIK: Hal baru, terobosan unik, atau perkembangan tak terduga yang memicu rasa ingin tahu.\n"
        "     b) FORMULA PERTARUHAN / SOLUSI RISIKO NYATA: Masalah krusial, anggaran, atau risiko yang berhasil diatasi/dijamin aman.\n"
        "     c) FORMULA AKSI TEROBOSAN / MANFAAT NYATA BAGI MASYARAKAT: Komitmen nyata, perbaikan fasilitas publik, atau pembebasan beban warga.\n"
        "     d) FORMULA KONTROL SOSIAL / URGENSI LAPANGAN: Pengawasan proyek, desakan warga, atau respon aparat terhadap keresahan masyarakat.\n"
        "   - SYARAT SEO MUTLAK:\n"
        "     * Pertahankan kata kunci entitas lokasi (Sumut, Medan, Samosir, Simalungun, Sibolga, Tarutung, Toba, Sergai, Dairi, Langkat, dll.) dan subjek berita di dalam judul.\n"
        f"     * Panjang judul wajib tepat {SEO_TITLE_IDEAL_MIN}–{SEO_TITLE_IDEAL_MAX} karakter (maksimal mutlak {SEO_TITLE_MAX_CHARS} karakter).\n"
        "   - LARANGAN CLICKBAIT MURAHAN: Wajib 100% faktual berdasarkan naskah sumber. DILARANG memakai kata pembodohan seperti 'Bikin Syok', 'Ini Faktanya', 'Gak Nyangka', 'Viral', atau tanda tanya sensasional.\n"
        "9. 8 LABEL BAKU BLOGGER BOABOA (PILIH 1 HINGGA MAKSIMAL 2 LABEL SAJA):\n"
        f"   - Pilih 1 hingga maksimal 2 label HANYA dari 8 label baku berikut: [{labels_str}].\n"
        "   - Panduan pemetaan:\n"
        "     * 'Hukrimpol' untuk hukum, kriminalitas, kepolisian, kecelakaan, bencana, dan politik daerah.\n"
        "     * 'Ekobis' untuk ekonomi, bisnis, UMKM, pertanian, perkebunan sawit, dan pasar.\n"
        "     * 'Olahraga' untuk sepak bola, PSMS Medan, PON, dan atlet Sumut.\n"
        "     * 'Wisata & Kuliner' untuk destinasi Danau Toba, Berastagi, dan kuliner khas daerah.\n"
        "     * 'Budaya & Hata' untuk adat, tradisi, ulos, bahasa daerah, dan sejarah lokal.\n"
        "     * 'Ototekno' untuk otomotif, teknologi, kelistrikan, dan inovasi digital.\n"
        "     * 'Tapanuli' untuk wilayah Tapanuli Raya, Samosir, Toba, Humbahas, Tapteng, Sibolga, Dairi, Tabagsel, Nias.\n"
        "     * 'Berita Sumut' untuk Medan, Deli Serdang, Pantai Timur, Dataran Tinggi, dan Sumut umum.\n"
        "10. PROMPT FOTO ILUSTRASI KONTEKSTUAL (image_prompt):\n"
        "    Tulis 1 kalimat deskripsi prompt visual dalam Bahasa Inggris (15-25 kata) untuk membuat foto ilustrasi jurnalistik yang aman dan relevan di Sumatera Utara.\n"
        "11. FORMAT OUTPUT: Tentukan 'hook_angle' terlebih dahulu sebelum menulis 'title'. Keluarkan HANYA JSON valid dengan kunci tepat:\n"
        "{\n"
        '  "hook_angle": "Fakta paling menarik, kontras, atau berdampak nyata bagi pembaca",\n'
        '  "title": "Judul ber-hook dinamis & SEO-friendly (50-65 karakter, maks 72)",\n'
        '  "executive_summary": "2 kalimat utuh inti 5W+1H yang padat tanpa mengulang judul",\n'
        '  "lead_paragraph": "Paragraf pembuka 2-3 kalimat padat langsung ke fakta utama",\n'
        '  "body_html": "<h2>Subjudul</h2><p>Paragraf isi...</p><p>Konteks lokal...</p>",\n'
        '  "labels": ["Label 1", "Label 2"],\n'
        '  "photo_caption": "Keterangan foto jurnalistik yang ringkas dan informatif",\n'
        '  "editorial_notes": "Catatan hal penting yang perlu diverifikasi redaktur sebelum publish",\n'
        f'  "meta_description": "Deskripsi penelusuran SEO ({META_DESC_IDEAL_MIN}-{META_DESC_IDEAL_MAX} karakter)",\n'
        '  "image_prompt": "Editorial documentary photography of [subject] in [North Sumatra region], journalistic, realistic lighting"\n'
        "}"
    )


def _repair_article(
    groq_client: Groq | None,
    model_name: str | list[str] | None,
    draft_data: dict,
    issues: list[str],
    source_title: str,
    source_text: str,
    source_media: str,
    published_date: str | None = None,
    gemini_api_key: str = "",
) -> dict:
    labels_str = ", ".join(f'"{lbl}"' for lbl in ALLOWED_LABELS)
    repair_system = (
        "Kamu adalah penyunting bahasa, editor SEO, dan pemeriksa fakta (fact-checker) senior di BoaBoa (boaboa.bataktive.com). "
        "Perbaiki draf JSON artikel berita berikut agar 100% akurat terhadap Naskah Sumber dan memenuhi standar SEO boaboa.bataktive.com:\n"
        "- Hapus semua kata/aksara non-Indonesia yang bocor dan terjemahkan ke Bahasa Indonesia baku.\n"
        "- Hapus angka, tahun, fakta, atau kutipan <blockquote> yang tidak berasal dari Naskah Sumber.\n"
        "- DILARANG memakai judul klise siaran pers ('Dorong...', 'Masih Sesuai Tahapan', 'Tekankan...', dll.). Pastikan 'title' memiliki HOOK jurnalistik bertaring (kontras/solusi risiko/aksi terobosan) sepanjang 50–65 karakter serta memuat entitas lokasi/subjek untuk SEO.\n"
        f"- Pastikan 'meta_description' sepanjang {META_DESC_IDEAL_MIN}–{META_DESC_IDEAL_MAX} karakter.\n"
        "- Jangan memakai tag <h1>, <script>, <iframe>, atau JSON-LD di dalam 'content'/'body_html', serta jangan menulis awalan 'BoaBoa.com -' atau 'Bataktive.com -'.\n"
        f"- Pastikan 'labels' berjumlah 1 hingga maksimal 2 label HANYA dari 8 label baku: [{labels_str}].\n"
        "- Sertakan 'image_prompt' dalam Bahasa Inggris (15-25 kata) untuk ilustrasi foto jurnalistik yang relevan.\n"
        "- Pastikan ada 'lead_paragraph' dan 'body_html'.\n"
        "- Keluarkan HANYA JSON valid dengan kunci 'title', 'executive_summary', 'lead_paragraph', 'body_html', 'meta_description', 'image_prompt', 'labels', 'photo_caption', 'editorial_notes'."
    )
    issues_bullet = "\n".join(f"- {iss}" for iss in issues)
    date_line = f"Tanggal Terbit Sumber: {published_date}\n" if published_date else ""
    repair_user = (
        f"Temuan Masalah yang Harus Diperbaiki:\n{issues_bullet}\n\n"
        f"Media Rujukan: {source_media}\n"
        f"{date_line}"
        f"Judul Sumber: {source_title}\n\n"
        f"Naskah Sumber Asli:\n{source_text}\n\n"
        f"Draf JSON Sebelumnya:\n{json.dumps(draft_data, ensure_ascii=False)}"
    )

    key = gemini_api_key or GEMINI_API_KEY
    if key:
        try:
            return _call_gemini_structured(
                api_key=key,
                system_prompt=repair_system,
                user_prompt=repair_user,
            )
        except Exception as e:
            print(f"Peringatan repair Gemini API gagal ({e}), beralih ke Groq...", flush=True)

    if groq_client:
        return _call_groq_json(
            groq_client,
            model_name or GROQ_MODEL_PRIORITY,
            [
                {"role": "system", "content": repair_system},
                {"role": "user", "content": repair_user},
            ],
            temperature=0.1,
        )

    raise RuntimeError("Tidak ada klien AI (Gemini atau Groq) yang tersedia untuk penyuntingan.")


def rewrite_news(
    groq_client: Groq | None = None,
    model_name: str | list[str] | None = None,
    title: str = "",
    full_text_content: str = "",
    source_media: str = "",
    source_url: str = "",
    published_date: str | None = None,
    author: str | None = None,
    gemini_api_key: str = "",
    gemini_model: str = "",
) -> dict:
    source_text = (full_text_content or "").strip()
    sentence_count = count_sentences(source_text)
    if len(source_text) < MIN_SOURCE_CHARS or sentence_count < MIN_SOURCE_SENTENCES:
        raise ValueError(
            f"Naskah sumber terlalu pendek/gagal diekstrak ({len(source_text)} karakter, "
            f"{sentence_count} kalimat) — dilewati untuk mencegah halusinasi."
        )

    meta_lines = [
        f"Judul Sumber: {title}",
        f"Media Sumber: {source_media}",
        f"Tautan Sumber: {source_url}",
    ]
    if published_date:
        meta_lines.append(f"Tanggal Terbit Sumber: {published_date}")
    if author:
        meta_lines.append(f"Penulis Sumber: {author}")

    user_prompt = (
        "\n".join(meta_lines)
        + f"\n\nNaskah Sumber:\n{source_text}"
        + "\n\nInstruksi: Tulis ulang berita di atas menjadi draf berita boaboa.bataktive.com berstandar Dewan Pers dan keluarkan HANYA JSON valid."
    )

    system_instruction = _build_system_instruction()
    raw_data: dict = {}
    key = gemini_api_key or GEMINI_API_KEY

    # 1. Prioritaskan Gemini API jika API Key tersedia
    if key:
        try:
            raw_data = _call_gemini_structured(
                api_key=key,
                system_prompt=system_instruction,
                user_prompt=user_prompt,
                model_name=gemini_model or GEMINI_MODEL,
            )
        except Exception as e:
            print(f"Peringatan eksekusi Gemini API gagal ({e}). Beralih ke fallback Groq...", flush=True)

    # 2. Fallback tangguh ke Groq jika Gemini tidak tersedia atau gagal
    if not raw_data:
        client = groq_client
        if client is None and GROQ_API_KEY:
            client = Groq(api_key=GROQ_API_KEY)
        if client is None:
            raise RuntimeError("Kunci API AI tidak ditemukan (GEMINI_API_KEY atau GROQ_API_KEY wajib ada).")
        raw_data = _call_groq_json(
            client,
            model_name or get_best_groq_model(client),
            [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

    lead = str(raw_data.get("lead_paragraph", "")).strip()
    body = str(raw_data.get("body_html", "")).strip()
    content_raw = str(raw_data.get("content", "")).strip()

    if not content_raw:
        if lead and body:
            raw_data["content"] = f"<p>{lead}</p>\n{body}"
        elif lead:
            raw_data["content"] = f"<p>{lead}</p>"
        elif body:
            raw_data["content"] = body
    elif not lead:
        first_p_match = re.search(r"<p\b[^>]*>(.*?)</p>", content_raw, re.S | re.I)
        if first_p_match:
            lead = first_p_match.group(1).strip()
            raw_data["lead_paragraph"] = lead
            raw_data["body_html"] = content_raw[first_p_match.end():].strip()
        else:
            raw_data["lead_paragraph"] = content_raw[:200]
            raw_data["body_html"] = content_raw

    if not raw_data.get("lead_paragraph") and lead:
        raw_data["lead_paragraph"] = lead

    if not raw_data.get("executive_summary"):
        raw_data["executive_summary"] = raw_data.get("lead_paragraph", "")[:200]

    article_data = sanitize_article_data(raw_data)
    is_valid, issues = validate_article_quality(
        article_data,
        source_text,
        source_title=title,
        published_date=published_date,
    )

    if not is_valid:
        print(f"Validator mendeteksi {len(issues)} catatan kualitas: {issues}. Menjalankan pass penyuntingan...", flush=True)
        repaired_raw = _repair_article(
            groq_client,
            model_name,
            article_data,
            issues,
            title,
            source_text,
            source_media,
            published_date=published_date,
            gemini_api_key=key,
        )
        r_lead = str(repaired_raw.get("lead_paragraph", "")).strip()
        r_body = str(repaired_raw.get("body_html", "")).strip()
        if r_lead and r_body and not repaired_raw.get("content"):
            repaired_raw["content"] = f"<p>{r_lead}</p>\n{r_body}"

        article_data = sanitize_article_data(repaired_raw)
        is_valid, remaining_issues = validate_article_quality(
            article_data,
            source_text,
            source_title=title,
            published_date=published_date,
        )
        if not is_valid:
            if any("blockquote" in iss.lower() or "kutipan" in iss.lower() for iss in remaining_issues):
                article_data["content"] = re.sub(
                    r"<blockquote[^>]*>.*?</blockquote>",
                    "",
                    article_data.get("content", ""),
                    flags=re.S | re.I,
                )
                is_valid, remaining_issues = validate_article_quality(
                    article_data,
                    source_text,
                    source_title=title,
                    published_date=published_date,
                )
            if not is_valid:
                raise ValueError(f"Artikel gagal lolos quality gate setelah penyuntingan: {remaining_issues}")

    return article_data

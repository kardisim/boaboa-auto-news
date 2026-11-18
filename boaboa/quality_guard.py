from datetime import datetime, timezone
from difflib import SequenceMatcher
import re

from boaboa.config import (
    ALLOWED_LABELS,
    GEO_ALIAS_MAP,
    LABEL_ALIASES,
    MAX_LABELS_PER_POST,
    META_DESC_MAX_CHARS,
    META_DESC_MIN_CHARS,
    MIN_ARTICLE_WORDS,
    MIN_LABELS_PER_POST,
    SEO_TITLE_MAX_CHARS,
    SEO_TITLE_MIN_CHARS,
)
from boaboa.history import strip_media_suffix, title_tokens

NON_LATIN_REGEX = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0e00-\u0e7f]")

ENGLISH_LEAK_WORDS = {
    "regarding", "hundreds", "thousands", "approvals", "recommended",
    "vulnerability", "intrinsic", "however", "therefore", "meanwhile",
    "moreover", "furthermore", "unfortunately", "increasingly", "according",
    "between", "without", "because", "although", "through", "including",
    "available", "different", "several", "government", "community",
    "important", "actually", "basically", "currently", "especially",
    "significantly", "approximately", "particularly", "additionally",
    "nevertheless", "consequently", "impressif", "demonstrated",
    "pedigree", "medley",
}

ENGLISH_LEAK_PHRASES = [
    r"\bsolo show\b",
    r"\bsang legend\b",
    r"\bstate-level\b",
    r"\bsuku aquakultur\b",
    r"\bprivate sector\b",
    r"\bgood governance\b",
]

GENERIC_SPEAKER_PATTERNS = [
    r"\btokoh adat setempat\b",
    r"\bsumber resmi\b",
    r"\bdalam keterangan resminya\b",
    r"\bwarga setempat\b",
    r"\bpakar ekologi\b",
    r"\bpengamat\b",
    r"\bnarasumber\b",
    r"\bpenanggung jawab program\b",
]

FALSE_REPORTING_PATTERNS = [
    r"wawancara langsung dengan",
    r"diliput langsung oleh",
    r"pantauan langsung boaboa",
    r"koresponden boaboa",
    r"\(boaboa(?:\.com)?/[a-z]{2,5}",
    r"pantauan langsung bataktive",
    r"koresponden bataktive",
    r"\(bataktive(?:\.com)?/[a-z]{2,5}",
]

TYPO_REPLACEMENTS = [
    (re.compile(r"\bKemnistrian\b", re.I), "Kementerian"),
    (re.compile(r"\bKepolisian\s+Resort\b"), "Kepolisian Resor"),
    (re.compile(r"\bkepolisian\s+resort\b"), "kepolisian resor"),
    (re.compile(r"\bBerserajah\b"), "Bersejarah"),
    (re.compile(r"\bberserajah\b"), "bersejarah"),
    (re.compile(r"\bTerkerjut\b"), "Terkejut"),
    (re.compile(r"\bterkerjut\b"), "terkejut"),
    (re.compile(r"\bSekretarsi\b"), "Sekretaris"),
    (re.compile(r"\bsekretarsi\b"), "sekretaris"),
    (re.compile(r"\bSportifitas\b"), "Sportivitas"),
    (re.compile(r"\bsportifitas\b"), "sportivitas"),
    (re.compile(r"\bmengalamai\b", re.I), "mengalami"),
    (re.compile(r"\bmenjadifokus\b", re.I), "menjadi fokus"),
    (re.compile(r"\bkeamanann\b", re.I), "keamanan"),
    (re.compile(r"\b(?:kreatifitas|kretifitas)\b", re.I), "kreativitas"),
    (re.compile(r"\baktifitas\b", re.I), "aktivitas"),
    (re.compile(r"\b([a-zA-Z]+)\s+\1\b", re.I), r"\1"),
]


def strip_html(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", txt).strip()


def infer_labels_from_context(text: str) -> list[str]:
    """Mendeteksi 2 hingga 4 dari 27 label baku Blogger boaboa.bataktive.com berdasarkan konteks naskah berita."""
    from boaboa.relevance import detect_candidate_labels

    detected = detect_candidate_labels(text)

    # Pastikan minimal ada 1 wilayah dan 1 rubrik
    has_region = any(lbl in GEO_ALIAS_MAP for lbl in detected)
    if not has_region:
        detected.insert(0, "Medan")

    has_rubric = any(lbl not in GEO_ALIAS_MAP and lbl not in ("Polda Sumut", "Kejati Sumut") for lbl in detected)
    if not has_rubric:
        detected.append("Hukrimpol")

    if any(k in detected for k in ("Kriminalitas", "Politik", "Polda Sumut", "Kejati Sumut")):
        if "Hukrimpol" not in detected:
            detected.append("Hukrimpol")

    valid = [lbl for lbl in detected if lbl in ALLOWED_LABELS]
    return valid[:MAX_LABELS_PER_POST]


def normalize_labels(
    raw_labels: list | None,
    fallback_labels: list[str] | None = None,
    title: str = "",
    content: str = "",
) -> list[str]:
    """Menormalisasi label ke 2 hingga 4 label baku boaboa.bataktive.com."""
    allowed_map = {lbl.lower(): lbl for lbl in ALLOWED_LABELS}
    cleaned: list[str] = []

    for lbl in raw_labels or []:
        if not isinstance(lbl, str):
            continue
        key = re.sub(r"\s+", " ", lbl).strip().lower()
        if not key or key in ("kategori1", "kategori2", "berita", "news"):
            continue
        mapped = allowed_map.get(key) or LABEL_ALIASES.get(key)
        if mapped and mapped not in cleaned:
            cleaned.append(mapped)

    if fallback_labels:
        for fb in fallback_labels:
            if not isinstance(fb, str):
                continue
            key = fb.strip().lower()
            mapped = allowed_map.get(key) or LABEL_ALIASES.get(key)
            if mapped and mapped not in cleaned:
                cleaned.append(mapped)

    from boaboa.relevance import detect_candidate_labels
    context_labels = detect_candidate_labels(f"{title} {content}") if (title or content) else []

    # 1. Pastikan minimal ada 1 label wilayah
    has_region = any(lbl in GEO_ALIAS_MAP for lbl in cleaned)
    if not has_region:
        for r in context_labels:
            if r in GEO_ALIAS_MAP and r not in cleaned:
                cleaned.append(r)
                has_region = True
                break
        if not has_region:
            cleaned.append("Medan")

    # 2. Pastikan minimal ada 1 label rubrik
    rubrics = {"Kriminalitas", "Politik", "Ekobis", "Wisata & Kuliner", "Olahraga", "Ototekno", "Hukrimpol"}
    has_rubric = any(lbl in rubrics for lbl in cleaned)
    if not has_rubric:
        for rb in context_labels:
            if rb in rubrics and rb not in cleaned:
                cleaned.append(rb)
                has_rubric = True
                break
        if not has_rubric:
            cleaned.append("Hukrimpol")

    # 3. Label Institusional opsional jika terdeteksi dalam konteks
    for inst in ("Polda Sumut", "Kejati Sumut"):
        if inst in context_labels and inst not in cleaned and len(cleaned) < MAX_LABELS_PER_POST:
            cleaned.append(inst)

    # 4. Aturan Wajib Hukrimpol:
    # Jika artikel memuat Kriminalitas, Politik, Polda Sumut, atau Kejati Sumut -> wajib menyertakan Hukrimpol
    if any(k in cleaned for k in ("Kriminalitas", "Politik", "Polda Sumut", "Kejati Sumut")):
        if "Hukrimpol" not in cleaned:
            cleaned.append("Hukrimpol")

    # 5. Jika total label masih < MIN_LABELS_PER_POST (2), tambahkan kandidat konteks yang valid
    if len(cleaned) < MIN_LABELS_PER_POST:
        for cl in context_labels:
            if cl not in cleaned:
                cleaned.append(cl)
                if len(cleaned) >= MIN_LABELS_PER_POST:
                    break

    final_labels = [lbl for lbl in cleaned if lbl in ALLOWED_LABELS]

    # Aturan prioritas jika melebihi MAX_LABELS_PER_POST (maks 4):
    if len(final_labels) > MAX_LABELS_PER_POST:
        priority_order = []
        for inst in ("Polda Sumut", "Kejati Sumut"):
            if inst in final_labels and inst not in priority_order:
                priority_order.append(inst)
        for kp in ("Kriminalitas", "Politik"):
            if kp in final_labels and kp not in priority_order:
                priority_order.append(kp)
        if "Hukrimpol" in final_labels and "Hukrimpol" not in priority_order:
            priority_order.append("Hukrimpol")
        for reg in final_labels:
            if reg in GEO_ALIAS_MAP and reg not in priority_order:
                priority_order.append(reg)
        for other in final_labels:
            if other not in priority_order:
                priority_order.append(other)
        final_labels = priority_order[:MAX_LABELS_PER_POST]

    # Pastikan minimal 2 label
    if len(final_labels) < MIN_LABELS_PER_POST:
        if "Hukrimpol" not in final_labels:
            final_labels.append("Hukrimpol")
        elif "Medan" not in final_labels:
            final_labels.append("Medan")

    return final_labels


def check_raw_similarity(generated_text: str, source_text: str) -> float:
    """Menghitung persentase kemiripan naskah mentah terhadap sumber (standar anti-plagiasi Dewan Pers < 45%)."""
    gen_clean = re.sub(r"\s+", " ", strip_html(generated_text).lower()).strip()
    src_clean = re.sub(r"\s+", " ", strip_html(source_text).lower()).strip()
    if not gen_clean or not src_clean:
        return 0.0

    gen_tokens = [w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", gen_clean)]
    src_tokens = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", src_clean))
    if not gen_tokens or not src_tokens:
        return 0.0

    gen_4grams = set(zip(gen_tokens, gen_tokens[1:], gen_tokens[2:], gen_tokens[3:])) if len(gen_tokens) >= 4 else set()
    src_token_list = [w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", src_clean)]
    src_4grams = set(zip(src_token_list, src_token_list[1:], src_token_list[2:], src_token_list[3:])) if len(src_token_list) >= 4 else set()

    if gen_4grams and src_4grams:
        ngram_sim = len(gen_4grams & src_4grams) / len(gen_4grams)
        return round(ngram_sim * 100, 1)

    ratio = SequenceMatcher(None, gen_clean, src_clean).ratio()
    return round(ratio * 100, 1)


def check_editorial_quality(
    article_data: dict,
    source_text: str,
    image_url: str = "",
    image_status: str = "",
) -> dict:
    """Asisten Pemeriksa Kualitas Redaksi standar Dewan Pers boaboa.bataktive.com."""
    content = str(article_data.get("content", "")).strip()
    plain_text = strip_html(content)
    words = plain_text.split()
    word_count = len(words)

    raw_similarity = check_raw_similarity(plain_text, source_text)
    has_baca_juga = bool(re.search(r"\b(?:baca juga|simak juga|baca selengkapnya)\b", content, re.I))
    has_valid_image = bool(image_url and str(image_url).startswith(("https://", "http://")))

    labels = article_data.get("labels", [])
    is_hukrimpol = "Hukrimpol" in labels
    presumption_passed = True
    if is_hukrimpol or "Kriminalitas" in labels or "Polda Sumut" in labels:
        content_lower = content.lower()
        has_presumption = any(k in content_lower for k in ("diduga", "terduga", "disangkakan", "proses hukum", "penyelidikan", "penyidikan", "menurut keterangan"))
        presumption_passed = has_presumption

    issues = []
    min_len_target = min(MIN_ARTICLE_WORDS, 140)
    if word_count < min_len_target:
        issues.append(f"Jumlah kata ({word_count}) kurang dari standar minimal Dewan Pers ({min_len_target} kata).")
    if has_baca_juga:
        issues.append("Ditemukan teks tautan 'Baca Juga' / 'Simak Juga' terlarang.")
    if raw_similarity >= 45.0:
        issues.append(f"Kemiripan teks mentah ({raw_similarity}%) melebihi ambang batas toleransi (maks 45%).")
    if not has_valid_image:
        issues.append("Artikel belum memiliki gambar utama yang valid.")
    if not presumption_passed:
        issues.append("Berita Hukrimpol belum memuat kata asas praduga tak bersalah (diduga/terduga/penyelidikan).")

    regions_in_labels = [lbl for lbl in labels if lbl in GEO_ALIAS_MAP]
    region_display = ", ".join(regions_in_labels) if regions_in_labels else "Umum Sumut"

    checklist = [
        f"Jumlah Kata: {word_count} kata (Target >= {min_len_target}) - {'Lolos' if word_count >= min_len_target else 'Catatan'}",
        f"Anti-Plagiasi: Kemiripan Mentah {raw_similarity}% (Batas < 45%) - {'Lolos' if raw_similarity < 45.0 else 'Catatan'}",
        f"Format Teks: Bebas teks 'Baca Juga' - {'Lolos' if not has_baca_juga else 'Ditemukan'}",
        f"Status Gambar: {image_status or ('Tersedia' if has_valid_image else 'Tidak Ada')}",
        f"Etika Dewan Pers: Asas Praduga Tak Bersalah - {'Lolos' if presumption_passed else 'Perlu Dicek'}",
        f"Cakupan Label: {', '.join(labels)} (Wilayah: {region_display})",
    ]

    return {
        "is_pass": len(issues) == 0,
        "word_count": word_count,
        "raw_similarity": raw_similarity,
        "has_baca_juga": has_baca_juga,
        "has_valid_image": has_valid_image,
        "presumption_passed": presumption_passed,
        "issues": issues,
        "checklist": checklist,
    }


def sanitize_article_data(article_data: dict) -> dict:
    data = dict(article_data or {})
    title = strip_media_suffix(str(data.get("title", "")).strip())
    title = re.sub(r"\s+", " ", title).strip(" \"'")

    content = str(data.get("content", "")).strip()

    # Hapus dateline/prefiks BoaBoa / Bataktive ganda di awal paragraf pertama
    def _clean_first_p(match: re.Match) -> str:
        inner = match.group(1).lstrip()
        prev = None
        while inner != prev:
            prev = inner
            inner = re.sub(
                r"^(?:<strong>\s*(?:BoaBoa(?:\.com)?|boaboa\.bataktive\.com|Bataktive(?:\.com)?)\s*</strong>\s*[-–:]\s*)+",
                "",
                inner,
                flags=re.I,
            )
            inner = re.sub(
                r"^(?:[A-Z][A-Za-z\s]{1,25},\s*)?(?:BoaBoa(?:\.com)?|boaboa\.bataktive\.com|Bataktive(?:\.com)?)\s*[-–:]\s*",
                "",
                inner,
                flags=re.I,
            )
            inner = re.sub(
                r"^(?:Jakarta|Medan|Sibolga|Stabat|Balige|Tarutung|Pangururan|Sidikalang|Pematangsiantar)\s*[-–]\s*",
                "",
                inner,
                flags=re.I,
            )
            inner = inner.lstrip()
        return f"<p>{inner}"

    content = re.sub(r"<p\b[^>]*>(.*?)(?=</p>)", _clean_first_p, content, count=1, flags=re.S | re.I)

    # Hapus byline jiplakan di akhir konten
    content = re.sub(
        r"\s*\((?:BoaBoa(?:\.com)?|boaboa\.bataktive\.com|Bataktive(?:\.com)?)(?:\s*[-/|]\s*[A-Za-z0-9./]+)+\)\s*(?=</p>)",
        "",
        content,
        flags=re.I,
    )
    content = re.sub(
        r"<p>\s*(?:Atribusi|Sumber)\s*:.*?</p>\s*$",
        "",
        content,
        flags=re.I | re.S,
    )

    # Bersihkan tag terlarang & turunkan <h1> dalam isi artikel agar tidak bentrok dengan <h1> tema
    content = re.sub(r"<(?:script|style|iframe)\b[^>]*>.*?</(?:script|style|iframe)>", "", content, flags=re.S | re.I)
    content = re.sub(r"<h1(\b[^>]*)>(.*?)</h1>", r"<h2>\2</h2>", content, flags=re.S | re.I)

    for pattern, repl in TYPO_REPLACEMENTS:
        content = pattern.sub(repl, content)
        title = pattern.sub(repl, title)

    # Otomatis potong judul jika melebihi batas SEO maksimum agar tidak menyebabkan kegagalan quality gate
    if len(title) > SEO_TITLE_MAX_CHARS:
        trimmed_title = title[:SEO_TITLE_MAX_CHARS].rsplit(" ", 1)[0].rstrip(" -–:,.")
        if len(trimmed_title) >= SEO_TITLE_MIN_CHARS:
            title = trimmed_title

    if "meta_description" in data and data.get("meta_description") is not None:
        meta_desc = strip_html(str(data.get("meta_description", "")))
        meta_desc = re.sub(r"\s+", " ", meta_desc).strip(" \"'")
        for pattern, repl in TYPO_REPLACEMENTS:
            meta_desc = pattern.sub(repl, meta_desc)

        if len(meta_desc) > META_DESC_MAX_CHARS:
            trimmed_desc = meta_desc[:META_DESC_MAX_CHARS - 1].rsplit(" ", 1)[0].rstrip(" -–:,.") + "."
            if len(trimmed_desc) >= META_DESC_MIN_CHARS:
                meta_desc = trimmed_desc
            else:
                meta_desc = meta_desc[:META_DESC_MAX_CHARS].rstrip(" -–:,.") + "."
        elif len(meta_desc) < META_DESC_MIN_CHARS:
            plain_content = strip_html(content)
            sentences = [s.strip() for s in re.split(r"[.!?]+(?:\s|$)", plain_content) if len(s.strip()) > 15]
            for s in sentences:
                candidate = f"{meta_desc} {s}." if not meta_desc.endswith(".") else f"{meta_desc} {s}."
                candidate = re.sub(r"\s+", " ", candidate).strip()
                if len(candidate) <= META_DESC_MAX_CHARS:
                    meta_desc = candidate
                    if len(meta_desc) >= META_DESC_MIN_CHARS:
                        break
        data["meta_description"] = meta_desc

    if "image_prompt" in data and data.get("image_prompt"):
        data["image_prompt"] = re.sub(r"\s+", " ", str(data.get("image_prompt", "")).strip(" \"'"))

    data["title"] = title
    data["content"] = content.strip()
    data["labels"] = normalize_labels(data.get("labels"), title=title, content=content)
    return data


def _extract_numbers(text: str) -> set[str]:
    clean = strip_html(text)
    nums = set()
    for m in re.findall(r"\b\d[\d.,:]*\b", clean):
        digits_only = re.sub(r"[^\d]", "", m)
        if len(digits_only) >= 2:
            nums.add(digits_only)
    return nums


def _extract_years(text: str) -> set[str]:
    return set(re.findall(r"\b(?:19\d{2}|20\d{2})\b", strip_html(text)))


def validate_article_quality(
    article_data: dict,
    source_text: str,
    source_title: str = "",
    published_date: str | None = None,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    title = str(article_data.get("title", "")).strip()
    content = str(article_data.get("content", "")).strip()
    labels = article_data.get("labels") or []
    meta_desc = str(article_data.get("meta_description", "")).strip() if "meta_description" in article_data else ""
    plain_text = strip_html(content)
    combined_text = f"{title} {meta_desc} {plain_text}".strip()
    source_combined = f"{source_title}\n{source_text}"
    source_lower = source_combined.lower()

    if len(title) < SEO_TITLE_MIN_CHARS or len(title) > SEO_TITLE_MAX_CHARS:
        issues.append(
            f"Panjang judul SEO tidak sesuai standar ({len(title)} karakter; wajib {SEO_TITLE_MIN_CHARS}-{SEO_TITLE_MAX_CHARS})"
        )

    if "meta_description" in article_data and (len(meta_desc) < META_DESC_MIN_CHARS or len(meta_desc) > META_DESC_MAX_CHARS):
        issues.append(
            f"Panjang meta_description tidak sesuai standar SEO ({len(meta_desc)} karakter; wajib {META_DESC_MIN_CHARS}-{META_DESC_MAX_CHARS})"
        )

    # Catatan: ALLOWED_LABELS boaboa memuat '&' (contoh: 'Wisata & Kuliner', 'Budaya & Hata'),
    # sehingga pengecekan label hanya memastikan bahwa setiap label ada di ALLOWED_LABELS dan tidak memakai '/'
    if len(labels) < MIN_LABELS_PER_POST or len(labels) > MAX_LABELS_PER_POST or any(
        lbl not in ALLOWED_LABELS or "/" in lbl for lbl in labels
    ):
        issues.append(
            f"Label tidak sesuai standar (wajib {MIN_LABELS_PER_POST}-{MAX_LABELS_PER_POST} label dari ALLOWED_LABELS): {labels}"
        )

    if any(k in labels for k in ("Kriminalitas", "Politik", "Polda Sumut", "Kejati Sumut")) and "Hukrimpol" not in labels:
        issues.append("Artikel terkait kriminalitas/politik/aparat penegak hukum wajib menyertakan label 'Hukrimpol'")

    if re.search(r"<h1\b|<script\b|application/ld\+json|<iframe\b", content, re.I):
        issues.append("Ditemukan tag HTML/schema terlarang (<h1>, <script>, <iframe>, atau JSON-LD)")

    non_latin = NON_LATIN_REGEX.findall(combined_text)
    if non_latin:
        sample = "".join(sorted(set(non_latin))[:8])
        issues.append(f"Ditemukan karakter non-Latin bocor: {sample}")

    words_in_output = set(re.findall(r"\b[a-zA-Z]{4,}\b", combined_text.lower()))
    leaked_words = sorted(
        w for w in words_in_output
        if w in ENGLISH_LEAK_WORDS and w not in source_lower
    )
    if leaked_words:
        issues.append(f"Kata Inggris/serapan tak baku bocor: {', '.join(leaked_words[:5])}")

    for pat in ENGLISH_LEAK_PHRASES:
        if re.search(pat, combined_text, re.I) and not re.search(pat, source_combined, re.I):
            issues.append(f"Frasa asing/janggal terdeteksi: {pat}")

    for pat in FALSE_REPORTING_PATTERNS:
        if re.search(pat, combined_text, re.I) and not re.search(pat, source_combined, re.I):
            issues.append("Klaim peliputan langsung palsu terdeteksi")

    blockquotes = re.findall(r"<blockquote[^>]*>(.*?)</blockquote>", content, re.S | re.I)
    source_has_quotes = bool(re.search(r'["“”]', source_text))
    for bq in blockquotes:
        bq_text = strip_html(bq)
        bq_lower = bq_text.lower()
        for gpat in GENERIC_SPEAKER_PATTERNS:
            if re.search(gpat, bq_lower) and not re.search(gpat, source_lower):
                issues.append(f"Atribusi kutipan generik/rekaan terdeteksi di blockquote: '{bq_text[:60]}'")
                break
        if not source_has_quotes:
            issues.append("Terdapat <blockquote> kutipan langsung padahal naskah sumber tidak memuat kutipan langsung")
            break
        if " - " in bq_text or " — " in bq_text:
            attr_part = re.split(r"\s[-—]\s", bq_text)[-1]
            name_tokens = [
                t.lower() for t in re.findall(r"[A-Za-z]{3,}", attr_part)
                if t.lower() not in {"wali", "kota", "bupati", "ketua", "kepala", "menteri", "gubernur", "kapolri", "kapolda", "akbp", "iptu", "kombes", "polres", "polda", "dinas", "dprd", "jenderal", "polisi"}
            ]
            if name_tokens and not any(tok in source_lower for tok in name_tokens[:3]):
                issues.append(f"Nama narasumber pada kutipan tidak ditemukan di naskah sumber: '{attr_part}'")

    source_years = _extract_years(source_combined)
    allowed_years = set(source_years)
    if published_date:
        allowed_years.update(_extract_years(published_date))
    else:
        allowed_years.add(str(datetime.now(timezone.utc).year))
    bad_years = sorted(y for y in _extract_years(combined_text) if y not in allowed_years)
    if bad_years:
        issues.append(f"Tahun tidak sesuai sumber/tanggal berita (potensi halusinasi): {', '.join(bad_years[:3])}")

    source_nums = _extract_numbers(source_combined)
    output_nums = _extract_numbers(combined_text)
    ungrounded = sorted(n for n in output_nums if n not in source_nums and n not in allowed_years)
    ungrounded_large = [n for n in ungrounded if len(n) >= 3]
    if len(ungrounded_large) >= 1 or len(ungrounded) >= 2:
        issues.append(f"Angka tidak ditemukan di sumber (potensi halusinasi): {', '.join(ungrounded[:5])}")

    word_count = len(plain_text.split())
    p_count = len(re.findall(r"<p\b", content, re.I))
    source_words = len(source_text.split())
    min_words = max(100, min(MIN_ARTICLE_WORDS, int(source_words * 0.55)))
    if (word_count < min_words and word_count < 140) or p_count < 3:
        issues.append(f"Artikel terlalu pendek atau kurang terstruktur ({word_count} kata, {p_count} paragraf)")

    return len(issues) == 0, issues

import html
import random
import re

import requests

from boaboa.config import FALLBACK_IMAGES_BY_TOPIC
from boaboa.extractor import clean_media_name
from boaboa.history import title_tokens, titles_similar
from boaboa.image_generator import generate_contextual_illustration
from boaboa.quality_guard import strip_html


EVERGREEN_PILLAR_POSTS = [
    {
        "title": "Dongan Partubu & Dongan Parhundul: Kekerabatan Batak Toba",
        "url": "https://boaboa.bataktive.com/2026/11/dongan-partubu-dan-dongan-parhundul.html",
        "labels": ["Budaya & Hata"],
    },
    {
        "title": "Panduan Penyeberangan Ajibata-Ambarita ke Pulau Samosir",
        "url": "https://boaboa.bataktive.com/2026/11/asdp-resmi-terapkan-diskon-100-tarif.html",
        "labels": ["Wisata & Kuliner", "Tapanuli"],
    },
    {
        "title": "Tradisi Marpangir Batak & Wisata Budaya Pantai Pakkodian",
        "url": "https://boaboa.bataktive.com/2026/10/marpangir-2026-ritual-penyucian-batak.html",
        "labels": ["Budaya & Hata", "Wisata & Kuliner"],
    },
    {
        "title": "Andaliman: Rempah Merica Khas Batak, Rasa & Manfaat",
        "url": "https://boaboa.bataktive.com/2022/09/andaliman-harta-terpendam-tano-batak.html",
        "labels": ["Wisata & Kuliner"],
    },
    {
        "title": "Sejarah Stadion Teladan Medan dan Kebanggaan PSMS",
        "url": "https://boaboa.bataktive.com/2026/10/sejarah-stadion-teladan-medan-psms.html",
        "labels": ["Olahraga", "Berita Sumut"],
    },
]


def fetch_boaboa_posts_index(max_results: int = 250) -> list[dict]:
    posts: list[dict] = []
    seen_urls: set[str] = set()
    url = f"https://boaboa.bataktive.com/feeds/posts/default?alt=json&max-results={max_results}"
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            entries = data.get("feed", {}).get("entry", [])
            for e in entries:
                title = e.get("title", {}).get("$t", "").strip()
                labels = [c.get("term") for c in e.get("category", []) if c.get("term")]
                alt_links = [
                    lnk.get("href")
                    for lnk in e.get("link", [])
                    if lnk.get("rel") == "alternate" and lnk.get("href")
                ]
                if title and alt_links:
                    post_url = alt_links[0]
                    seen_urls.add(post_url.rstrip("/"))
                    posts.append({
                        "title": title,
                        "url": post_url,
                        "labels": labels,
                        "tokens": title_tokens(title),
                    })
    except Exception:
        pass

    for pillar in EVERGREEN_PILLAR_POSTS:
        if pillar["url"].rstrip("/") not in seen_urls:
            posts.append({
                "title": pillar["title"],
                "url": pillar["url"],
                "labels": list(pillar["labels"]),
                "tokens": title_tokens(pillar["title"]),
            })
    return posts


# Alias kompatibilitas
fetch_bataktive_posts_index = fetch_boaboa_posts_index


def find_related_posts(article_data: dict, posts_index: list[dict], max_links: int = 3) -> list[dict]:
    if not posts_index:
        return []

    target_title = article_data.get("title", "")
    target_labels = {lbl.lower() for lbl in article_data.get("labels", [])}
    target_tokens = title_tokens(target_title)

    scored = []
    for post in posts_index:
        if titles_similar(target_title, post["title"]):
            continue
        post_labels = {lbl.lower() for lbl in post.get("labels", [])}
        label_overlap = len(target_labels & post_labels)
        tok_overlap = len(target_tokens & post.get("tokens", set()))
        score = label_overlap * 2 + tok_overlap
        if score >= 2:
            scored.append((score, post))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:max_links]]


def build_ecosystem_callout(labels: list[str], plain_text: str) -> str:
    lower_labels = {lbl.lower() for lbl in labels or []}
    lower_text = (plain_text or "").lower()

    is_adat = bool(
        lower_labels & {"budaya & hata", "adat batak", "sejarah batak", "bahasa batak"}
    ) or any(
        kw in lower_text for kw in ("dalihan na tolu", "ulos", "partuturan", "umpasa", "adat batak", "marga", "tarombo", "sinamot", "aksara batak")
    )
    is_wisata = bool(lower_labels & {"wisata & kuliner", "wisata danau toba", "danau toba"}) or any(
        kw in lower_text for kw in ("danau toba", "samosir", "parapat", "ajibata", "berastagi", "andaliman", "naniura")
    )

    if is_adat:
        return (
            '<div style="background:#f8f9fa; border-left:4px solid #b91c1c; padding:14px 16px; margin:18px 0;">\n'
            '  <p style="margin:0 0 8px 0;"><strong>Referensi Budaya &amp; Bahasa Daerah (Ekosistem Bataktive &amp; BoaBoa):</strong></p>\n'
            '  <ul style="margin:0; padding-left:20px;">\n'
            '    <li>Pelajari susunan sapaan kekerabatan di <a href="https://hata.bataktive.com/partuturan?utm_source=boaboa_portal&amp;utm_medium=article_inline&amp;utm_campaign=hata_ecosystem" rel="noopener" target="_blank">Panduan Partuturan Digital HATA</a>.</li>\n'
            '    <li>Jelajahi pantun nasihat adat di <a href="https://hata.bataktive.com/umpasa?utm_source=boaboa_portal&amp;utm_medium=article_inline&amp;utm_campaign=hata_ecosystem" rel="noopener" target="_blank">Pustaka Umpasa Batak HATA</a>.</li>\n'
            '  </ul>\n'
            '</div>\n'
        )
    if is_wisata:
        return (
            '<div style="background:#f8f9fa; border-left:4px solid #b91c1c; padding:14px 16px; margin:18px 0;">\n'
            '  <p style="margin:0 0 8px 0;"><strong>Bekal Wisata &amp; Bahasa Daerah di Ekosistem BoaBoa:</strong></p>\n'
            '  <ul style="margin:0; padding-left:20px;">\n'
            '    <li>Pelajari sapaan dan frasa perjalanan lokal di <a href="https://hata.bataktive.com/frasa?utm_source=boaboa_portal&amp;utm_medium=article_inline&amp;utm_campaign=hata_ecosystem" rel="noopener" target="_blank">Kamus Frasa Sehari-hari HATA</a>.</li>\n'
            '    <li>Temukan inspirasi destinasi Sumatera Utara lainnya di <a href="https://boaboa.bataktive.com/search/label/Wisata%20%26%20Kuliner?utm_source=boaboa_portal&amp;utm_medium=article_inline&amp;utm_campaign=boaboa_ecosystem" rel="noopener" target="_blank">Wisata &amp; Kuliner BoaBoa</a>.</li>\n'
            '  </ul>\n'
            '</div>\n'
        )
    return ""


def choose_fallback_image(labels: list[str]) -> str:
    lower_labels = {lbl.lower() for lbl in labels or []}
    if lower_labels & {"wisata & kuliner", "wisata danau toba", "kuliner batak"}:
        bucket = "wisata_kuliner"
    elif lower_labels & {"budaya & hata", "adat batak", "sejarah batak", "bahasa batak"}:
        bucket = "budaya_hata"
    elif lower_labels & {"hukrimpol", "peristiwa", "hukum kriminal", "politik daerah"}:
        bucket = "hukrimpol"
    elif lower_labels & {"ekobis", "ekonomi", "bisnis"}:
        bucket = "ekobis"
    elif lower_labels & {"olahraga", "sport"}:
        bucket = "olahraga"
    elif lower_labels & {"ototekno", "otomotif", "teknologi"}:
        bucket = "ototekno"
    else:
        bucket = "umum"
    return random.choice(FALLBACK_IMAGES_BY_TOPIC[bucket])


def _clean_blockquote_markup(content: str) -> str:
    styled_bq = (
        '<blockquote style="border-left: 4px solid #b91c1c; margin: 1.4em 0; '
        'padding: 0.9em 1.2em; background-color: #f8f9fa; font-style: italic; color: #222;">'
    )

    def _repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        inner = re.sub(r'(<p[^>]*>)\s*["“]+', r"\1", inner)
        inner = re.sub(r'["”]+(\s*[-—])', r"\1", inner)
        inner = re.sub(r'["”]+(\s*</p>)', r"\1", inner)
        return f"{styled_bq}{inner}</blockquote>"

    return re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", _repl, content, flags=re.S | re.I)


def format_final_html(
    article_data: dict,
    image_url: str | None,
    source_media_name: str,
    real_url: str = "",
    posts_index: list[dict] | None = None,
    image_width: int | None = None,
    image_height: int | None = None,
    additional_images: list[dict] | None = None,
    image_status: str = "",
    quality_report: dict | None = None,
    is_draft: bool = True,
) -> str:
    title = article_data.get("title", "")
    lead_paragraph = (article_data.get("lead_paragraph") or "").strip()
    body_html = (article_data.get("body_html") or "").strip()
    content = (article_data.get("content", "") or "").strip()
    executive_summary = (article_data.get("executive_summary") or "").strip()
    editorial_notes = (article_data.get("editorial_notes") or "Verifikasi kesesuaian data dengan sumber asli").strip()
    labels = article_data.get("labels", [])
    clean_media = clean_media_name(source_media_name, real_url)
    escaped_alt = html.escape(title, quote=True)

    if lead_paragraph and body_html:
        clean_lead = lead_paragraph if lead_paragraph.startswith("<p") else f"<p>{lead_paragraph}</p>"
        main_content = f"{clean_lead}\n{body_html}"
    elif content:
        main_content = content
    else:
        main_content = f"<p>{lead_paragraph or title}</p>"

    if "<p" not in main_content.lower():
        main_content = f"<p>{main_content}</p>"

    main_content = _clean_blockquote_markup(main_content)
    plain_content = strip_html(main_content)
    word_count = len(plain_content.split())

    # Tentukan gambar utama dan caption
    if image_url and str(image_url).startswith(("https://", "http://")):
        final_image = image_url
        raw_cap = article_data.get("photo_caption") or f"Foto/Ilustrasi: {clean_media}"
        photo_caption = html.escape(raw_cap)
        resolved_status = image_status or f"Foto Sumber ({clean_media})"
    else:
        illustration = generate_contextual_illustration(
            image_prompt=article_data.get("image_prompt", ""),
            title=title,
            labels=labels,
            content=plain_content,
        )
        final_image = illustration.get("url") or choose_fallback_image(labels)
        raw_cap = article_data.get("photo_caption") or illustration.get("caption") or "Ilustrasi: Dokumentasi Konseptual Redaksi BoaBoa"
        photo_caption = html.escape(raw_cap)
        resolved_status = image_status or illustration.get("status") or "Ilustrasi AI Gemini"

    w_attr = image_width if isinstance(image_width, int) and image_width > 0 else 1200
    h_attr = image_height if isinstance(image_height, int) and image_height > 0 else 675

    # 1. Kotak Catatan Redaktur (Khusus Mode Draft - Baris Teratas)
    draft_review_box = ""
    if is_draft:
        ref_link = (
            f'<a href="{html.escape(real_url, quote=True)}" target="_blank" rel="noopener" style="color:#b45309;text-decoration:underline;">{html.escape(clean_media)}</a>'
            if real_url else html.escape(clean_media)
        )
        draft_review_box = (
            '<div class="draft-review-box" style="background:#fffbeb;border:1px solid #f59e0b;padding:12px 16px;border-radius:8px;margin-bottom:18px;font-size:13px;color:#78350f;">\n'
            '  <div style="font-weight:bold;margin-bottom:6px;font-size:14px;color:#b45309;">Catatan Redaksi (Draf BoaBoa.com / boaboa.bataktive.com)</div>\n'
            '  <ul style="margin:0;padding-left:18px;line-height:1.5;">\n'
            f'    <li><strong>Sumber Referensi:</strong> {ref_link}</li>\n'
            f'    <li><strong>Status Gambar:</strong> {html.escape(resolved_status)}</li>\n'
            f'    <li><strong>Jumlah Kata:</strong> {word_count} kata</li>\n'
            f'    <li><strong>Poin Cek Redaksi:</strong> {html.escape(editorial_notes)}</li>\n'
            '  </ul>\n'
            '  <div style="margin-top:6px;font-style:italic;font-size:11px;color:#92400e;">* Kotak catatan redaksi ini dapat dihapus 1-klik sebelum artikel dipublikasikan.</div>\n'
            '</div>\n'
        )

    # 2. Gambar Utama Semantik (<figure class="separator">)
    main_image_html = (
        '<figure class="separator" style="clear: both; text-align: center; margin: 0 0 1.5em 0;">\n'
        f'  <a href="{html.escape(final_image, quote=True)}" style="margin-left: 1em; margin-right: 1em;">\n'
        f'    <img border="0" data-original-height="{h_attr}" data-original-width="{w_attr}" '
        f'src="{html.escape(final_image, quote=True)}" alt="{escaped_alt}" '
        f'width="{w_attr}" height="{h_attr}" '
        'referrerpolicy="no-referrer" fetchpriority="high" decoding="async" '
        'style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin: 0 auto;" />\n'
        '  </a>\n'
        f'  <figcaption style="display: block; margin-top: 6px; font-size: 12px; color: #777; font-style: italic;">{photo_caption}</figcaption>\n'
        '</figure>'
    )

    # 3. Hook Ringkasan Tersembunyi untuk Template BoaBoa
    summary_html = ""
    if executive_summary:
        summary_html = f'<div class="article-summary" style="display:none;">{html.escape(executive_summary)}</div>\n'

    # 4. Sisipkan foto liputan tambahan (foto ke-2 dan ke-3 jika ada)
    extra_blocks = []
    for idx, extra in enumerate(additional_images or []):
        extra_url = extra.get("url") if isinstance(extra, dict) else str(extra)
        if not extra_url or extra_url == final_image or not str(extra_url).startswith(("https://", "http://")):
            continue
        raw_cap = extra.get("caption") if isinstance(extra, dict) else ""
        extra_cap = html.escape(raw_cap) if raw_cap else f"Dokumentasi Tambahan: {html.escape(clean_media)}"

        extra_html = (
            '<figure class="separator" style="clear: both; text-align: center; margin: 1.5em 0;">\n'
            f'  <a href="{html.escape(extra_url, quote=True)}" style="margin-left: 1em; margin-right: 1em;">\n'
            f'    <img border="0" data-original-height="675" data-original-width="1200" '
            f'src="{html.escape(extra_url, quote=True)}" alt="{escaped_alt} - Dokumentasi Tambahan {idx + 1}" '
            'width="1200" height="675" '
            'referrerpolicy="no-referrer" loading="lazy" decoding="async" '
            'style="max-width: 100%; height: auto; border-radius: 8px; display: block; margin: 0 auto;" />\n'
            '  </a>\n'
            f'  <figcaption style="display: block; margin-top: 6px; font-size: 12px; color: #777; font-style: italic;">{extra_cap}</figcaption>\n'
            '</figure>'
        )
        extra_blocks.append(extra_html)

    if extra_blocks:
        if "<h2>" in main_content:
            main_content = main_content.replace("<h2>", f"{extra_blocks[0]}\n<h2>", 1)
            if len(extra_blocks) > 1:
                paras = main_content.split("</p>")
                if len(paras) > 3:
                    main_content = "</p>".join(paras[:3]) + f"</p>\n{extra_blocks[1]}\n" + "</p>".join(paras[3:])
                else:
                    main_content = f"{main_content}\n{extra_blocks[1]}"
        else:
            paras = main_content.split("</p>")
            if len(paras) > 2:
                main_content = "</p>".join(paras[:2]) + f"</p>\n{extra_blocks[0]}\n" + "</p>".join(paras[2:])
            else:
                main_content = f"{main_content}\n{extra_blocks[0]}"

    # Atribusi di bagian bawah artikel
    attribution_html = ""
    if real_url and "news.google.com" not in real_url:
        attribution_html = (
            f'\n<p style="font-size: 11px; color: #777; margin-top: 1.5em; line-height: 1.4;"><em>Sumber rujukan: '
            f'<a href="{html.escape(real_url, quote=True)}" rel="nofollow noopener" target="_blank" style="color: #666; text-decoration: underline;">'
            f'{html.escape(clean_media)}</a></em></p>'
        )

    final_output = (
        f"{draft_review_box}"
        f"{main_image_html}\n"
        f"{summary_html}"
        f"{main_content}"
        f"{attribution_html}"
    ).strip()

    return final_output

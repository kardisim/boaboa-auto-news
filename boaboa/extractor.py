import json
import re
import ssl
from urllib.parse import parse_qs, parse_qsl, urlencode, urljoin, urlparse, urlunparse
import urllib.request

from bs4 import BeautifulSoup
import requests
import urllib3

from boaboa.config import (
    BAD_IMAGE_PATTERNS,
    MAX_SOURCE_CHARS,
    MIN_IMAGE_WIDTH,
    PAGINATED_PORTAL_DOMAINS,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 "
        "(compatible; Redaksi BoaBoa/1.0; +https://boaboa.bataktive.com)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

BOILERPLATE_LINE_PATTERNS = [
    r"^baca juga\s*:",
    r"^simak juga\s*:",
    r"^lihat juga\s*:",
    r"^pilihan editor\s*:",
    r"^artikel ini telah tayang",
    r"^scroll to continue",
    r"^advertisement\b",
    r"^copyright\b",
    r"^halaman\s+\d+",
    r"^penulis\s*:",
    r"^editor\s*:",
    r"^pewarta\s*:",
]


def clean_media_name(source_media: str, real_url: str = "") -> str:
    raw = (source_media or "").strip()
    raw = re.sub(r"^[\s\-–|:]+", "", raw).strip()
    if raw.startswith(("http://", "https://")):
        raw = urlparse(raw).netloc
    raw = re.sub(r"^www\.", "", raw, flags=re.I).strip()
    if raw:
        return raw
    if real_url:
        host = urlparse(real_url).netloc
        return re.sub(r"^www\.", "", host, flags=re.I) or "Media Rujukan"
    return "Media Rujukan"


def build_fetch_url(real_url: str) -> str:
    try:
        parsed = urlparse(real_url)
        host = parsed.netloc.lower()
        if any(domain in host for domain in PAGINATED_PORTAL_DOMAINS):
            q_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            if not any(k.lower() == "page" for k, _ in q_pairs):
                q_pairs.append(("page", "all"))
                return urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    urlencode(q_pairs),
                    "",
                ))
    except Exception:
        pass
    return real_url


def resolve_original_url(google_url: str) -> str:
    if "news.google.com" not in (google_url or ""):
        return google_url

    # 1. API terbaru googlenewsdecoder (gnewsdecoder dengan jeda untuk menghindari HTTP 429)
    try:
        from googlenewsdecoder import gnewsdecoder

        res = gnewsdecoder(google_url, interval=1)
        if isinstance(res, dict) and (res.get("status") or res.get("success") or res.get("decoded_url")):
            decoded = res.get("decoded_url")
            if decoded and "google.com" not in decoded:
                return decoded
    except Exception:
        pass

    # 2. Kompatibilitas googlenewsdecoder versi lama (new_decoderv1)
    try:
        from googlenewsdecoder import new_decoderv1

        res = new_decoderv1(google_url)
        if isinstance(res, dict) and res.get("status") and res.get("decoded_url"):
            if "google.com" not in res["decoded_url"]:
                return res["decoded_url"]
        elif isinstance(res, str) and res.startswith("http") and "google.com" not in res:
            return res
    except Exception:
        pass

    # 3. Fallback HTTP session + batchexecute RPC
    try:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        session.cookies.set("SOCS", "CAESEwgDEgk2ODE3ODQzMzEaAmVuIAEaBgiA_LyaBg", domain=".google.com")
        resp = session.get(google_url, timeout=10, allow_redirects=True)
        if "news.google.com" not in resp.url and "google.com" not in resp.url:
            return resp.url

        soup = BeautifulSoup(resp.text, "html.parser")
        c_wiz = soup.find(attrs={"data-n-a-sg": True})
        if c_wiz and "/articles/" in google_url:
            token = google_url.split("/articles/")[1].split("?")[0]
            sig = c_wiz.get("data-n-a-sg")
            ts = c_wiz.get("data-n-a-ts")
            if sig and ts:
                rpc_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
                req_payload = (
                    f'[[["Fbv4je","[\\"garturlreq\\",[\\"en-US\\",\\"US\\",'
                    f'[\\"{token}\\",\\"{sig}\\",{ts}]]]",null,"generic"]]]'
                )
                post_resp = session.post(
                    rpc_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
                    data={"f.req": req_payload},
                    timeout=10,
                )
                urls = re.findall(r'https?://[^\s"\'\\,]+', post_resp.text)
                for u in urls:
                    u_clean = u.replace("\\/", "/")
                    if "google.com" not in u_clean and "gstatic.com" not in u_clean:
                        return u_clean
    except Exception:
        pass

    return google_url


def _fetch_html_urllib(url: str, timeout: int = 25) -> tuple[str | None, str]:
    """Fallback pengambilan HTML menggunakan stdlib urllib dengan konteks TLS permisif
    dan referer Google, efektif saat requests terkena blokir Cloudflare/ModSecurity atau SSL wrapper.
    """
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = "https://www.google.com/"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if resp.status == 200:
                raw = resp.read()
                encoding = "utf-8"
                ctype = resp.headers.get("Content-Type", "")
                if "charset=" in ctype.lower():
                    encoding = ctype.lower().split("charset=")[-1].split(";")[0].strip()
                try:
                    return raw.decode(encoding, errors="replace"), resp.url
                except Exception:
                    return raw.decode("utf-8", errors="replace"), resp.url
    except Exception:
        pass
    return None, url


def fetch_html(url: str, timeout: int = 25) -> tuple[str | None, str]:
    session = requests.Session()
    headers = dict(DEFAULT_HEADERS)
    session.headers.update(headers)
    resp = None

    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True, verify=True)
    except requests.exceptions.SSLError:
        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True, verify=False)
        except Exception:
            resp = None
    except Exception:
        resp = None

    # Tangani proteksi ModSecurity/CDN situs daerah yang mensyaratkan referer Google
    if resp is not None and resp.status_code == 403:
        try:
            retry_headers = dict(headers)
            retry_headers["Referer"] = "https://www.google.com/"
            resp_retry = session.get(url, headers=retry_headers, timeout=timeout, allow_redirects=True, verify=False)
            if resp_retry.status_code == 200:
                resp = resp_retry
        except Exception:
            pass

    if resp is not None and resp.status_code == 200:
        if resp.encoding and resp.encoding.lower() in ("iso-8859-1", "latin-1"):
            resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text, resp.url

    # Fallback ke stdlib urllib dengan konteks SSL permisif jika requests diblokir/gagal koneksi
    fallback_text, final_url = _fetch_html_urllib(url, timeout=timeout)
    if fallback_text:
        return fallback_text, final_url

    return None, resp.url if resp is not None else url


def clean_and_dewatemark_image_url(url: str) -> str:
    """Membersihkan URL gambar dari logo watermark portal berita (misal Detik, Kompas,
    Kumparan, Tribun), membuang parameter cropping buatan CDN, dan mengambil resolusi
    penuh foto liputan asli.
    """
    if not url:
        return ""
    cleaned = url.strip()

    # 1. Detik Network (awsimages.detik.net.id, akcdn.detik.net.id)
    if "detik.net.id" in cleaned or "detik.com" in cleaned:
        if "/api/wm/" in cleaned:
            cleaned = cleaned.replace("/api/wm/", "/community/media/visual/")
        elif "/wm/" in cleaned:
            cleaned = cleaned.replace("/wm/", "/community/media/visual/")
        try:
            parsed = urlparse(cleaned)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            qs.pop("wid", None)
            qs.pop("wm", None)
            qs.pop("watermark", None)
            if "w" in qs:
                qs["w"] = ["1200"]
            cleaned = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(qs, doseq=True), parsed.fragment)
            )
        except Exception:
            pass

    # 2. Kompas Network (asset.kompas.com)
    if "asset.kompas.com" in cleaned and "/data/photo/" in cleaned:
        cleaned = re.sub(r"/crops/[^/]+/data/photo/", "/data/photo/", cleaned)

    # 3. Kumparan (blue.kumparan.com / images.kumparan.com)
    if "kumparan.com" in cleaned:
        cleaned = re.sub(r"/l_text:[^/]+/", "/", cleaned)
        cleaned = cleaned.replace("/og_kumparan/", "/")

    # 4. Tribun Network (tstatic.net)
    if "tstatic.net" in cleaned or "tribunnews.com" in cleaned:
        cleaned = re.sub(r"/crop/[^/]+/", "/", cleaned)
        cleaned = re.sub(r"_(?:100|150|250|300|400)x\d+\.", ".", cleaned)

    # 5. Inilah.com (c.inilah.com)
    if "inilah.com" in cleaned and "/small_" in cleaned:
        cleaned = cleaned.replace("/small_", "/")

    # 6. Pembersihan parameter watermark umum pada query string portal lain
    if any(k in cleaned.lower() for k in ("wm=", "watermark=")):
        try:
            parsed = urlparse(cleaned)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            for key in list(qs.keys()):
                if "wm" in key.lower() or "watermark" in key.lower():
                    qs.pop(key, None)
            cleaned = urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(qs, doseq=True), parsed.fragment)
            )
        except Exception:
            pass

    return cleaned


def is_valid_image_candidate(url: str) -> bool:
    if not url:
        return False
    lower = url.lower().strip()
    if not (lower.startswith("https://") or lower.startswith("http://")):
        return False

    parsed = urlparse(lower)
    path = parsed.path
    if path.endswith((".svg", ".gif", ".ico", ".bmp")):
        return False

    # Abaikan spacer, pixel tracking, dan blank placeholder
    if any(spacer in path for spacer in ("transparent.gif", "spacer.gif", "1x1.", "pixel.gif", "blank.gif")):
        return False

    if any(pat in lower for pat in BAD_IMAGE_PATTERNS):
        return False
    return True


def _extract_image_dimensions(soup: BeautifulSoup) -> tuple[int | None, int | None]:
    w_meta = soup.find("meta", property="og:image:width") or soup.find("meta", attrs={"name": "og:image:width"})
    h_meta = soup.find("meta", property="og:image:height") or soup.find("meta", attrs={"name": "og:image:height"})
    try:
        w = int(str(w_meta["content"]).strip()) if w_meta and w_meta.get("content") else None
        h = int(str(h_meta["content"]).strip()) if h_meta and h_meta.get("content") else None
        if w and h and MIN_IMAGE_WIDTH <= w <= 4000 and 150 <= h <= 4000:
            return w, h
    except Exception:
        pass
    return None, None


def validate_image_remote(url: str, timeout: int = 8, referer: str = "") -> bool:
    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["Referer"] = referer

    try:
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        if resp.status_code == 405 or resp.status_code >= 400:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
    except requests.exceptions.SSLError:
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True, verify=False)
        except Exception:
            return False
    except Exception:
        return False

    if resp.status_code != 200:
        return False
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if ctype and not ctype.startswith("image/"):
        return False
    clen = resp.headers.get("Content-Length")
    if clen and clen.isdigit() and int(clen) < 8000:
        return False
    return True


def _parse_jsonld_news(soup: BeautifulSoup) -> dict:
    meta = {"body": "", "author": None, "date": None, "images": []}
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue

        items = payload if isinstance(payload, list) else [payload]
        expanded = []
        for it in items:
            if isinstance(it, dict) and isinstance(it.get("@graph"), list):
                expanded.extend(it["@graph"])
            elif isinstance(it, dict):
                expanded.append(it)

        for obj in expanded:
            if not isinstance(obj, dict):
                continue
            otype = obj.get("@type", "")
            if isinstance(otype, list):
                otype = " ".join(str(x) for x in otype)
            if any(t in str(otype) for t in ("NewsArticle", "Article", "ReportageNewsArticle")):
                body = obj.get("articleBody")
                if isinstance(body, str) and len(body) > len(meta["body"]):
                    meta["body"] = body.strip()
                if not meta["date"] and obj.get("datePublished"):
                    meta["date"] = str(obj["datePublished"]).strip()
                author = obj.get("author")
                if not meta["author"] and author:
                    if isinstance(author, dict):
                        meta["author"] = author.get("name")
                    elif isinstance(author, list) and author:
                        first = author[0]
                        meta["author"] = first.get("name") if isinstance(first, dict) else str(first)
                    elif isinstance(author, str):
                        meta["author"] = author
                img = obj.get("image")
                if isinstance(img, str):
                    meta["images"].append(img)
                elif isinstance(img, dict) and img.get("url"):
                    meta["images"].append(img["url"])
                elif isinstance(img, list):
                    for im in img:
                        if isinstance(im, str):
                            meta["images"].append(im)
                        elif isinstance(im, dict) and im.get("url"):
                            meta["images"].append(im["url"])
    return meta


def clean_extracted_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    cleaned_lines = []
    seen = set()
    for line in raw_text.splitlines():
        txt = re.sub(r"\s+", " ", line).strip()
        if len(txt) < 30:
            continue
        lower = txt.lower()
        if any(re.search(pat, lower) for pat in BOILERPLATE_LINE_PATTERNS):
            continue
        if txt in seen:
            continue
        seen.add(txt)
        cleaned_lines.append(txt)

    joined = "\n\n".join(cleaned_lines)
    if len(joined) > MAX_SOURCE_CHARS:
        joined = joined[:MAX_SOURCE_CHARS].rsplit(" ", 1)[0]
    return joined


def count_sentences(text: str) -> int:
    if not text:
        return 0
    parts = [s.strip() for s in re.split(r"[.!?]+(?:\s|$)", text) if len(s.strip()) > 20]
    return len(parts)


def _extract_with_bs4(soup: BeautifulSoup) -> str:
    work = BeautifulSoup(str(soup), "html.parser")
    for unwanted in work(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        unwanted.decompose()

    candidates = work.find_all(["article", "main", "div"], class_=re.compile(
        r"content|berita|detail|post|entry|article|body|read|text", re.I
    ))
    candidates.extend(work.find_all(["article", "main"]))
    if not candidates:
        candidates = [work]

    best_paragraphs = []
    best_score = 0
    for scope in candidates:
        paras = []
        total_len = 0
        for p in scope.find_all("p"):
            txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
            lower = txt.lower()
            if len(txt) > 35 and not any(re.search(pat, lower) for pat in BOILERPLATE_LINE_PATTERNS):
                paras.append(txt)
                total_len += len(txt)
        if total_len > best_score:
            best_score = total_len
            best_paragraphs = paras

    return clean_extracted_text("\n\n".join(best_paragraphs))


def _parse_srcset(srcset_str: str) -> list[str]:
    if not srcset_str:
        return []
    candidates = []
    for part in str(srcset_str).split(","):
        tokens = part.strip().split()
        if not tokens:
            continue
        cand_url = tokens[0].strip()
        width = 0
        if len(tokens) > 1:
            m = re.search(r"(\d+)w", tokens[1])
            if m:
                width = int(m.group(1))
        candidates.append((width, cand_url))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [url for _, url in candidates if url]


def _collect_img_urls(img) -> list[str]:
    urls = []
    for cand in _parse_srcset(img.get("data-srcset") or img.get("srcset")):
        urls.append(cand)
    for attr in (
        "data-orig-file",
        "data-large-file",
        "data-lazy-src",
        "data-src",
        "data-original",
        "data-hi-res-src",
        "data-highres",
        "data-src-large",
        "data-full-url",
        "src",
    ):
        val = img.get(attr)
        if val and isinstance(val, str) and not val.strip().lower().startswith("data:image"):
            urls.append(val.strip())
    return urls


def _normalize_image_key(url: str) -> str:
    path = urlparse(url).path
    filename = path.split("/")[-1].lower()
    stem = re.sub(r"[-_](?:\d+x\d+|169|scaled|large)\b", "", filename)
    stem = re.sub(r"\.[a-z0-9]+$", "", stem)
    return stem if len(stem) > 4 else filename


UNWANTED_IMAGE_CONTAINER_SELECTORS = (
    ".baca-juga",
    ".bacajuga",
    ".baca_juga",
    ".read__also",
    ".read-also",
    ".terkait",
    ".artikel-terkait",
    ".related",
    ".related-article",
    ".related-news",
    ".berita-terkait",
    ".trending",
    ".populer",
    ".terpopuler",
    ".recommendation",
    ".rekomendasi",
    ".sidebar",
    ".widget",
    ".banner",
    ".ads",
    ".advertisement",
    ".iklan",
    "aside",
    "footer",
    "header",
    "nav",
    ".comment",
    ".komentar",
    ".author-bio",
    ".profile",
    ".social-share",
)

OFF_TOPIC_POLITICAL_OR_VIRAL_KEYWORDS = {
    "mpr", "dpr", "dpd", "gibran", "wapres", "presiden", "pilpres",
    "prabowo", "jokowi", "kaesang", "paspampres", "koalisi", "menteri",
    "kemendikbud", "kemensos", "kemlu", "timnas", "pssi", "shin tae-yong",
    "liga inggris", "manchester", "real madrid", "barcelona", "bmkg gempa",
}


def is_image_relevant_to_article(
    caption: str,
    alt: str,
    cand_url: str,
    article_text: str = "",
    article_title: str = "",
) -> bool:
    context = f"{article_title} {article_text}".lower()
    cap_lower = f"{caption} {alt}".lower().strip()

    for off_kw in OFF_TOPIC_POLITICAL_OR_VIRAL_KEYWORDS:
        if re.search(r"\b" + re.escape(off_kw) + r"\b", cap_lower) and not re.search(r"\b" + re.escape(off_kw) + r"\b", context):
            return False

    cap_tokens = [
        w for w in re.findall(r"\b[a-zA-Z]{4,}\b", cap_lower)
        if w not in {"foto", "ilustrasi", "antara", "dokumen", "istimewa", "detik", "kompas", "tribun", "inilah", "arsip"}
    ]
    if len(cap_tokens) >= 4 and len(context) > 100:
        matches = [t for t in cap_tokens if t in context]
        if not matches:
            return False

    return True


def extract_all_article_images(
    soup: BeautifulSoup,
    base_url: str,
    trafilatura_image: str | None = None,
    jsonld_images: list[str] | None = None,
    validate_remote: bool = True,
    max_images: int = 3,
    article_text: str = "",
    article_title: str = "",
) -> list[dict]:
    raw_candidates = []

    work_soup = BeautifulSoup(str(soup), "html.parser")
    for sel in UNWANTED_IMAGE_CONTAINER_SELECTORS:
        for tag in work_soup.select(sel):
            tag.decompose()

    editorial_selectors = (
        "figure",
        ".featured-image",
        ".post-thumbnail",
        ".single-featured-image-header",
        ".entry-thumbnail",
        ".wp-block-image",
        ".detail__media",
        ".foto__media",
        ".read__media",
        ".photo__img",
        ".lead__image",
        ".img-view",
        ".post-image",
        ".entry-image",
        ".article-image",
        ".media-image",
        ".hero-image",
        ".main-image",
    )
    for sel in editorial_selectors:
        for container in work_soup.select(sel):
            caption = ""
            fc = container.find("figcaption")
            if fc:
                caption = fc.get_text(" ", strip=True)

            for src_el in container.find_all("source"):
                for cand in _parse_srcset(src_el.get("srcset") or src_el.get("data-srcset")):
                    raw_candidates.append((cand, caption, 1))

            for img in container.find_all("img"):
                img_cap = caption or img.get("alt") or img.get("title") or ""
                for cand in _collect_img_urls(img):
                    raw_candidates.append((cand, img_cap, 1))

    if jsonld_images:
        for j_img in jsonld_images:
            raw_candidates.append((j_img, "", 2))

    if trafilatura_image:
        raw_candidates.append((trafilatura_image, "", 2))

    content_area = work_soup.find(["article", "main", "div"], class_=re.compile(r"content|berita|detail|post|entry|article", re.I))
    search_scope = content_area if content_area else work_soup
    for img in search_scope.find_all("img"):
        img_cap = img.get("alt") or img.get("title") or ""
        parent = img.parent
        if parent and parent.name == "figure":
            fc = parent.find("figcaption")
            if fc:
                img_cap = fc.get_text(" ", strip=True)
        for cand in _collect_img_urls(img):
            raw_candidates.append((cand, img_cap, 3))

    for meta in work_soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
        if prop in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src", "image"):
            cnt = meta.get("content")
            if cnt:
                raw_candidates.append((cnt.strip(), "", 4))

    raw_candidates.sort(key=lambda x: x[2])

    validated_images = []
    seen_urls = set()
    seen_keys = set()

    for cand_url, caption, _ in raw_candidates:
        if len(validated_images) >= max_images:
            break
        if not cand_url:
            continue
        full_url = urljoin(base_url, cand_url.strip())
        full_url = clean_and_dewatemark_image_url(full_url)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        key = _normalize_image_key(full_url)
        if key in seen_keys:
            continue

        if not is_valid_image_candidate(full_url):
            continue

        if not is_image_relevant_to_article(
            caption=caption,
            alt=caption,
            cand_url=full_url,
            article_text=article_text,
            article_title=article_title,
        ):
            continue

        if not validate_remote or validate_image_remote(full_url, referer=base_url):
            seen_keys.add(key)
            validated_images.append({
                "url": full_url,
                "caption": caption.strip() if caption else "",
            })

    return validated_images


def extract_best_image(
    soup: BeautifulSoup,
    base_url: str,
    trafilatura_image: str | None = None,
    jsonld_images: list[str] | None = None,
    validate_remote: bool = True,
    article_text: str = "",
    article_title: str = "",
) -> str | None:
    images = extract_all_article_images(
        soup=soup,
        base_url=base_url,
        trafilatura_image=trafilatura_image,
        jsonld_images=jsonld_images,
        validate_remote=validate_remote,
        max_images=1,
        article_text=article_text,
        article_title=article_title,
    )
    return images[0]["url"] if images else None


def extract_article_details(
    real_url: str,
    html_override: str | None = None,
    validate_image: bool = True,
) -> dict:
    result = {
        "text": "",
        "image_url": None,
        "images": [],
        "image_width": None,
        "image_height": None,
        "author": None,
        "published_date": None,
        "sitename": None,
        "title": None,
        "char_count": 0,
        "sentence_count": 0,
        "extraction_method": "none",
        "final_url": real_url,
    }

    if not real_url or "news.google.com" in real_url:
        return result

    html = html_override
    final_url = real_url
    if html is None:
        fetch_target = build_fetch_url(real_url)
        try:
            html, final_url = fetch_html(fetch_target)
        except Exception as e:
            print(f"Kendala saat mengambil HTML sumber ({real_url}): {e}", flush=True)
            return result

    if not html:
        return result

    result["final_url"] = final_url
    soup = BeautifulSoup(html, "html.parser")
    jsonld = _parse_jsonld_news(soup)
    result["author"] = jsonld.get("author")
    result["published_date"] = jsonld.get("date")

    trafilatura_image = None
    extracted_text = ""

    # 1. Prioritaskan Trafilatura
    try:
        from trafilatura import bare_extraction

        traf = bare_extraction(
            html,
            url=final_url,
            with_metadata=True,
            include_comments=False,
            favor_precision=True,
        )
        if traf is not None and not isinstance(traf, dict):
            if hasattr(traf, "as_dict"):
                traf = traf.as_dict()
            else:
                traf = {
                    "text": getattr(traf, "text", None),
                    "image": getattr(traf, "image", None),
                    "author": getattr(traf, "author", None),
                    "date": getattr(traf, "date", None),
                    "sitename": getattr(traf, "sitename", None),
                    "title": getattr(traf, "title", None),
                }
        if isinstance(traf, dict):
            extracted_text = clean_extracted_text(traf.get("text") or "")
            trafilatura_image = traf.get("image")
            result["author"] = result["author"] or traf.get("author")
            result["published_date"] = result["published_date"] or traf.get("date")
            result["sitename"] = traf.get("sitename")
            result["title"] = traf.get("title")
            if extracted_text:
                result["extraction_method"] = "trafilatura"
    except Exception:
        pass

    # 2. Fallback atau lengkapi dari JSON-LD articleBody & density-scored BeautifulSoup
    bs4_text = _extract_with_bs4(soup)
    jsonld_text = clean_extracted_text(jsonld.get("body") or "")

    best_text = max(
        [(extracted_text, result["extraction_method"]), (jsonld_text, "jsonld"), (bs4_text, "bs4_density")],
        key=lambda item: len(item[0]),
    )
    if best_text[0]:
        result["text"] = best_text[0]
        result["extraction_method"] = best_text[1]

    result["char_count"] = len(result["text"])
    result["sentence_count"] = count_sentences(result["text"])
    result["images"] = extract_all_article_images(
        soup,
        final_url,
        trafilatura_image=trafilatura_image,
        jsonld_images=jsonld.get("images"),
        validate_remote=validate_image,
        max_images=3,
        article_text=result["text"],
        article_title=result.get("title") or "",
    )
    if result["images"]:
        result["image_url"] = result["images"][0]["url"]
        img_w, img_h = _extract_image_dimensions(soup)
        result["image_width"] = img_w
        result["image_height"] = img_h
    return result

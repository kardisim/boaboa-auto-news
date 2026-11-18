from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
import os
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from boaboa.config import HISTORY_FILE, HISTORY_MAX_ITEMS

STOPWORDS_ID = {
    "yang", "dan", "di", "ke", "dari", "pada", "untuk", "dengan", "akan",
    "ini", "itu", "atau", "juga", "dalam", "atas", "oleh", "sebagai",
    "terkait", "soal", "usai", "saat", "setelah", "karena", "agar", "jadi",
    "ini", "kata", "begini", "fakta", "ungkap", "resmi", "baru", "tahun",
}

TRACKING_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "oc",
}


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        filtered_q = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in TRACKING_QUERY_PARAMS
        ]
        clean_path = parsed.path.rstrip("/") or "/"
        return urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            clean_path,
            "",
            urlencode(filtered_q),
            "",
        ))
    except Exception:
        return url.strip()


def strip_media_suffix(title: str) -> str:
    if not title:
        return ""
    return re.sub(r"\s+[-–|]\s+[^-–|]{2,60}$", "", title).strip()


def normalize_title(title: str) -> str:
    base = strip_media_suffix(title).lower()
    base = re.sub(r"[^a-z0-9\s]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def title_tokens(title: str) -> set[str]:
    norm = normalize_title(title)
    return {
        tok for tok in norm.split()
        if len(tok) >= 3 and tok not in STOPWORDS_ID
    }


def calculate_jaccard_similarity(title_a: str, title_b: str) -> float:
    tokens_a = title_tokens(title_a)
    tokens_b = title_tokens(title_b)
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def titles_similar(title_a: str, title_b: str, threshold: float = 0.55) -> bool:
    norm_a = normalize_title(title_a)
    norm_b = normalize_title(title_b)
    if not norm_a or not norm_b:
        return False
    if norm_a == norm_b:
        return True

    tokens_a = title_tokens(title_a)
    tokens_b = title_tokens(title_b)
    if len(tokens_a) >= 3 and len(tokens_b) >= 3:
        intersection = len(tokens_a & tokens_b)
        union = len(tokens_a | tokens_b)
        jaccard = intersection / union if union else 0.0
        overlap_min = intersection / min(len(tokens_a), len(tokens_b))
        if jaccard >= threshold or (intersection >= 4 and overlap_min >= 0.7):
            return True

    seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    return seq_ratio >= 0.74


def load_history(history_file: str = HISTORY_FILE) -> list:
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    return []


def save_history(history: list, history_file: str = HISTORY_FILE) -> None:
    trimmed = history[-HISTORY_MAX_ITEMS:]
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False, indent=2)


def is_duplicate_story(
    google_url: str,
    title: str,
    history: list,
    real_url: str | None = None,
    jaccard_threshold: float = 0.60,
    check_recent_window: int = 100,
) -> tuple[bool, str]:
    canon_google = canonicalize_url(google_url)
    canon_real = canonicalize_url(real_url) if real_url else ""

    # 1. Pengecekan kesamaan URL pada seluruh riwayat
    for item in history:
        if isinstance(item, str):
            if item == google_url or (canon_google and canonicalize_url(item) == canon_google):
                return True, "URL Google News sudah ada di riwayat"
            if canon_real and canonicalize_url(item) == canon_real:
                return True, "URL situs asli sudah ada di riwayat"
        elif isinstance(item, dict):
            prev_google = item.get("google_url", "")
            prev_real = item.get("real_url", "")
            if prev_google and (prev_google == google_url or canonicalize_url(prev_google) == canon_google):
                return True, "URL Google News sudah ada di riwayat"
            if canon_real and prev_real and canonicalize_url(prev_real) == canon_real:
                return True, "URL situs asli sudah ada di riwayat"

    # 2. Pengecekan kemiripan semantik & entitas (Jaccard >= 0.60) terhadap 100 entri terakhir
    recent_entries = history[-check_recent_window:] if len(history) > check_recent_window else history
    tokens_current = title_tokens(title)

    for item in recent_entries:
        if not isinstance(item, dict):
            continue
        prev_title = item.get("title", "")
        if not prev_title:
            continue

        tokens_prev = title_tokens(prev_title)
        if tokens_current and tokens_prev:
            jaccard = len(tokens_current & tokens_prev) / len(tokens_current | tokens_prev)
            if jaccard >= jaccard_threshold:
                return True, f"Kemiripan semantik serupa sudah ada di 100 riwayat terakhir (Jaccard={jaccard:.2f}): {prev_title}"

        if titles_similar(title, prev_title):
            return True, f"Topik serupa sudah pernah diproses: {prev_title}"

    return False, ""


def make_history_record(
    google_url: str,
    real_url: str,
    title: str,
    source_media: str,
) -> dict:
    return {
        "google_url": google_url,
        "real_url": canonicalize_url(real_url),
        "title": strip_media_suffix(title),
        "normalized_title": normalize_title(title),
        "source": source_media,
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }

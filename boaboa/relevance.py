import re

from boaboa.config import (
    ALLOWED_LABELS,
    GEO_ALIAS_MAP,
    MIN_RELEVANCE_SCORE,
    TOPIC_KEYWORD_MAP,
    UGC_OPINION_DOMAINS,
    UGC_OPINION_SOURCES,
    VIDEO_ONLY_DOMAINS,
    VIDEO_ONLY_SOURCES,
)
from boaboa.history import strip_media_suffix, title_tokens, titles_similar

CORE_SUMUT_KEYWORDS = {
    # Kawasan Aglomerasi Medan & Pantai Timur
    "medan", "kota medan", "deli serdang", "lubuk pakam", "langkat", "stabat",
    "binjai", "tebing tinggi", "asahan", "kisaran", "batubara", "tanjungbalai",
    "labuhanbatu", "rantauprapat", "labusel", "labura", "sergai", "serdang bedagai",
    # Kawasan Dataran Tinggi, Simalungun & Karo
    "simalungun", "pematangsiantar", "siantar", "karo", "berastagi", "kabanjahe",
    # Kawasan Tapanuli Raya, Danau Toba & Samosir
    "tapanuli", "taput", "tapteng", "tapsel", "sibolga", "tarutung", "balige",
    "toba", "toba samosir", "samosir", "pangururan", "humbahas", "humbang hasundutan",
    "doloksanggul", "siborongborong", "siborong-borong", "dairi", "sidikalang",
    "pakpak", "pakpak bharat", "salak", "danau toba", "parapat", "ajibata", "ambarita",
    # Kawasan Tabagsel & Kepulauan Nias
    "padangsidimpuan", "padang lawas", "palas", "paluta", "mandailing", "mandailing natal",
    "madina", "panyabungan", "sipirok", "nias", "gunungsitoli", "nias selatan", "nias utara", "nias barat",
    # Institusi, Identitas & Komunitas Provinsi Sumatera Utara
    "sumut", "sumatera utara", "pemprov sumut", "polda sumut", "kejati sumut", "kodam i/bb", "polrestabes medan",
    "batak", "ulos", "dalihan na tolu", "marga", "bona pasogit", "psms", "psms medan",
    "sinamot", "pariban", "boru", "umpasa", "aksara batak", "partuturan",
}

# Hukrimpol (Hukum, Kriminalitas, Kepolisian, Kecelakaan, Bencana, Politik & Pilkada Daerah) - JANGAN DIBLOKIR
HUKRIMPOL_KEYWORDS = {
    "polisi", "polres", "polda", "polsek", "polrestabes", "narkoba", "sabu", "ganja", "tangkap", "ditangkap",
    "maling", "curat", "curas", "begal", "curanmor", "judi", "tahanan", "diringkus",
    "tersangka", "pelaku", "kejari", "kejati", "vonis", "lapas", "rutan", "pembunuhan", "aniaya",
    "penjara", "kriminal", "sat reskrim", "sat narkoba", "razia", "sidang", "korupsi", "pungli",
    "kecelakaan", "tabrakan", "laka lantas", "kebakaran", "longsor", "banjir", "bencana",
    "operasi", "tewas", "korban", "penyelundupan", "politik", "pilkada", "pemilu", "bawaslu", "kpu", "caleg", "dprd",
}

# Ekobis (Ekonomi, Bisnis, Pasar, Pertanian, Perkebunan, UMKM Daerah)
EKOBIS_KEYWORDS = {
    "ekonomi", "bisnis", "pasar", "inflasi", "perbankan", "bank", "umkm", "sawit", "kelapa sawit",
    "karet", "kopi", "pertanian", "perkebunan", "petani", "komoditas", "investasi", "industri",
    "pelabuhan", "belawan", "ekspor", "harga pangan", "beras", "apbd",
}

# Olahraga Daerah Sumatera Utara
SUMUT_SPORTS_KEYWORDS = {
    "psms", "psms medan", "ayam kinantan", "stadion teladan", "stadion baharoeddin",
    "pon sumut", "atlet sumut", "koni sumut", "liga 2", "liga 3",
}

# Olahraga umum/nasional/internasional tanpa kaitan Sumatera Utara
OFF_NICHE_NATIONAL_SPORTS_KEYWORDS = {
    "timnas indonesia", "pssi", "liga 1", "liga inggris", "liga spanyol",
    "liga champions", "super league", "badminton", "bulutangkis",
    "all england", "indonesia open", "ufc", "mma", "byon combat",
    "sepak bola", "piala asia", "piala dunia", "motogp", "formula 1",
}

# Wilayah di luar Sumatera Utara
OFF_TOPIC_REGIONAL_KEYWORDS = {
    "bekasi", "depok", "bogor", "karawang", "tangerang", "bandung",
    "surabaya", "semarang", "solo", "yogyakarta", "jogja", "banten",
    "jawa barat", "jabar", "jawa tengah", "jateng", "jawa timur", "jatim",
    "makassar", "sulawesi", "kalimantan", "papua", "bali", "ntt", "ntb",
}


def _match_keywords(text: str, keywords: set[str] | list[str]) -> list[str]:
    matched = []
    for kw in keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text):
            matched.append(kw)
    return matched


def detect_candidate_labels(title: str, summary: str = "") -> list[str]:
    """Mendeteksi kandidat label awal dari judul dan ringkasan berdasarkan 27 label baku."""
    combined = f"{title} {summary}".lower()
    labels: list[str] = []

    # 1. Deteksi Wilayah dari 18 Klaster 33 Kab/Kota Sumut
    for region, aliases in GEO_ALIAS_MAP.items():
        matched = False
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias.lower())}\b", combined):
                matched = True
                break
        if matched and region not in labels:
            labels.append(region)

    # 2. Deteksi Institusional & Rubrik Tematik
    for topic, keywords in TOPIC_KEYWORD_MAP.items():
        matched = False
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw.lower())}\b", combined):
                matched = True
                break
        if matched and topic not in labels:
            labels.append(topic)

    # 3. Aturan Wajib Hukrimpol:
    # Jika artikel terdeteksi Kriminalitas, Politik, Polda Sumut, atau Kejati Sumut -> otomatis wajib menyertakan Hukrimpol
    if any(k in labels for k in ("Kriminalitas", "Politik", "Polda Sumut", "Kejati Sumut")):
        if "Hukrimpol" not in labels:
            labels.append("Hukrimpol")

    return [lbl for lbl in labels if lbl in ALLOWED_LABELS]


def score_candidate(
    title: str,
    source_media: str,
    base_score: int = 0,
    url: str = "",
) -> tuple[int, str]:
    clean_title = strip_media_suffix(title).lower()
    src_lower = (source_media or "").strip().lower()
    url_lower = (url or "").strip().lower()

    if src_lower in VIDEO_ONLY_SOURCES or any(d in url_lower for d in VIDEO_ONLY_DOMAINS):
        return -10, "Sumber khusus video (minim naskah artikel)"

    if src_lower in UGC_OPINION_SOURCES or any(d in url_lower for d in UGC_OPINION_DOMAINS):
        return -10, "Platform opini/blog warga (bukan portal berita resmi)"

    if re.match(r"^(?:\[?video\]?|\[?galeri\]?|foto:|infografis:)\b", clean_title):
        return -10, "Judul format video/galeri tanpa naskah berita"

    if "jemput bola" in clean_title and not _match_keywords(clean_title, CORE_SUMUT_KEYWORDS):
        return -10, "False positive frasa 'jemput bola' non-olahraga"

    score = base_score
    matched_sumut = _match_keywords(clean_title, CORE_SUMUT_KEYWORDS)
    matched_hukrimpol = _match_keywords(clean_title, HUKRIMPOL_KEYWORDS)
    matched_ekobis = _match_keywords(clean_title, EKOBIS_KEYWORDS)
    matched_sumut_sports = _match_keywords(clean_title, SUMUT_SPORTS_KEYWORDS)
    matched_nat_sports = _match_keywords(clean_title, OFF_NICHE_NATIONAL_SPORTS_KEYWORDS)
    matched_other_region = _match_keywords(clean_title, OFF_TOPIC_REGIONAL_KEYWORDS)

    candidate_labels = detect_candidate_labels(clean_title)

    # 1. Olahraga daerah Sumut (PSMS Medan, PON Sumut, atlet Sumut) didukung penuh untuk kanal Olahraga boaboa
    if matched_sumut_sports:
        score += 4 + min(len(matched_sumut_sports), 2)
    elif matched_nat_sports and not matched_sumut:
        # Olahraga nasional/internasional murni tanpa kaitan Sumut dipotong skornya
        return -8, f"Off-niche olahraga luar daerah tanpa kaitan Sumut ({matched_nat_sports[:2]})"

    # 2. Entitas wilayah / identitas Sumatera Utara
    if matched_sumut:
        score += 3 + min(len(matched_sumut), 3)

    # Bonus untuk daerah luar Medan agar cakupan wilayah merata
    non_medan_regions = [lbl for lbl in candidate_labels if lbl in GEO_ALIAS_MAP and lbl != "Medan"]
    if non_medan_regions:
        score += 3

    # 3. Rubrik Hukrimpol lokal Sumut TIDAK DIBLOKIR dan diberi prioritas
    if matched_hukrimpol and matched_sumut:
        score += 2 + min(len(matched_hukrimpol), 2)

    # 4. Rubrik Ekobis lokal Sumut
    if matched_ekobis and matched_sumut:
        score += 2 + min(len(matched_ekobis), 2)

    # 5. Penalti jika judul secara eksplisit merujuk wilayah luar Sumut
    if matched_other_region and not matched_sumut:
        score -= 5

    # Wajib ada minimal sinyal Sumut jika base_score rendah
    if not matched_sumut and not matched_sumut_sports and base_score < 3:
        score -= 2

    # Hindari artikel seremonial pejabat daerah luar Sumut pada feed umum
    if any(w in clean_title for w in ("bupati ", "wali kota ", "pemkot ", "pemkab ", "dprd ")) and not matched_sumut:
        score -= 4

    reason_parts = [f"skor={score}"]
    if candidate_labels:
        reason_parts.append(f"labels={candidate_labels}")
    if matched_sumut:
        reason_parts.append(f"sumut={matched_sumut[:3]}")
    if matched_sumut_sports:
        reason_parts.append(f"olahraga_sumut={matched_sumut_sports[:2]}")
    if matched_hukrimpol:
        reason_parts.append(f"hukrimpol={matched_hukrimpol[:2]}")
    if matched_ekobis:
        reason_parts.append(f"ekobis={matched_ekobis[:2]}")
    if matched_other_region:
        reason_parts.append(f"luar_wilayah={matched_other_region[:2]}")

    reason = ", ".join(reason_parts)
    if score < MIN_RELEVANCE_SCORE:
        return score, f"Skor relevansi rendah ({reason})"

    return score, f"Layak ({reason})"


def cluster_candidate_stories(candidates: list[dict], similarity_threshold: float = 0.55) -> list[dict]:
    """Mengelompokkan 2–3 sumber berbeda yang memberitakan peristiwa yang sama
    dalam 24 jam terakhir menjadi satu paket sumber (multi-source input).
    """
    clusters: list[dict] = []

    for cand in candidates:
        matched_cluster = None
        cand_tokens = title_tokens(cand.get("title", ""))
        for cl in clusters:
            head_title = cl.get("title", "")
            head_tokens = title_tokens(head_title)
            if titles_similar(cand.get("title", ""), head_title):
                matched_cluster = cl
                break
            if cand_tokens and head_tokens:
                jaccard = len(cand_tokens & head_tokens) / len(cand_tokens | head_tokens)
                if jaccard >= similarity_threshold:
                    matched_cluster = cl
                    break

        if matched_cluster is not None:
            matched_cluster["cluster_sources"].append(cand)
            matched_cluster.setdefault("clustered_sources", []).append(cand)
            matched_cluster["score"] = max(matched_cluster["score"], cand.get("score", 0)) + 1
            matched_cluster["is_clustered"] = True
        else:
            cl_item = dict(cand)
            cl_item["cluster_sources"] = [cand]
            cl_item["clustered_sources"] = []
            cl_item["is_clustered"] = False
            clusters.append(cl_item)

    clusters.sort(key=lambda item: item.get("score", 0), reverse=True)
    return clusters

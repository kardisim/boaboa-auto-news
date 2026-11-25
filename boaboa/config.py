import os

BLOG_ID = os.environ.get("BLOGGER_BLOG_ID", "").strip() or "8826247154815720532"
PUBLISH_AS_DRAFT = True  # Wajib dikirim ke Blogger sebagai Draft, dilarang auto-publish
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
GEMINI_MODEL_FALLBACKS = [
    "gemini-3.8-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.5-flash",
]
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL_OVERRIDE = os.environ.get("GROQ_MODEL", "").strip()
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "kardisim/boaboa-auto-news").strip()
HISTORY_FILE = os.environ.get("HISTORY_FILE", "posted_history.json")
HISTORY_MAX_ITEMS = 600

# Kontrol kualitas & batas generasi
MIN_SOURCE_CHARS = 450
MIN_SOURCE_SENTENCES = 3
MAX_SOURCE_CHARS = 9500
MAX_POSTS_PER_RUN = int(os.environ.get("MAX_POSTS_PER_RUN", "8"))
MAX_CANDIDATES_PER_FEED = 4
MIN_RELEVANCE_SCORE = 1
MIN_IMAGE_WIDTH = 300

# Standar SEO & Jurnalistik Dewan Pers boaboa.bataktive.com (2-4 label per post)
MIN_LABELS_PER_POST = 2
MAX_LABELS_PER_POST = 4
SEO_TITLE_MIN_CHARS = 25
SEO_TITLE_IDEAL_MIN = 50
SEO_TITLE_IDEAL_MAX = 65
SEO_TITLE_MAX_CHARS = 72
META_DESC_MIN_CHARS = 110
META_DESC_IDEAL_MIN = 135
META_DESC_IDEAL_MAX = 155
META_DESC_MAX_CHARS = 160
MIN_ARTICLE_WORDS = 160

# Daftar prioritas model Groq (prioritaskan model flagship yang stabil untuk JSON object)
GROQ_MODEL_PRIORITY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "qwen/qwen3-32b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

# Daftar Persis 27 Label Baku Blogger boaboa.bataktive.com
ALLOWED_LABELS = [
    # Institusional (2)
    "Polda Sumut",
    "Kejati Sumut",
    # Rubrik Tematik (7)
    "Kriminalitas",
    "Politik",
    "Ekobis",
    "Wisata & Kuliner",
    "Olahraga",
    "Ototekno",
    "Hukrimpol",
    # Klaster Wilayah 33 Kabupaten/Kota Sumut (18)
    "Medan",
    "Deli Serdang",
    "Binjai",
    "Langkat",
    "Tebing Tinggi",
    "Pematangsiantar",
    "Simalungun",
    "Karo",
    "Dairi",
    "Samosir",
    "Toba",
    "Taput",
    "Humbahas",
    "Sibolga - Tapteng",
    "Asahan",
    "Labuhanbatu",
    "Nias",
    "Tapsel",
]

# Kamus Pemetaan Kata Kunci 33 Kabupaten/Kota di Sumatera Utara ke 18 Klaster Wilayah Baku
GEO_ALIAS_MAP = {
    "Medan": ["medan", "belawan", "marelan", "amplas", "helvetia", "polrestabes medan", "pemko medan"],
    "Deli Serdang": ["deli serdang", "deliserdang", "lubuk pakam", "tanjung morawa", "percut sei tuan", "sunggal", "pancur batu", "kualanamu", "namorambe", "galang"],
    "Binjai": ["binjai", "pemko binjai", "polres binjai"],
    "Langkat": ["langkat", "stabat", "tanjung pura", "pangkalan brandan", "besitang", "bahorok", "bukit lawang", "kuala", "sei bingai"],
    "Tebing Tinggi": ["tebing tinggi", "serdang bedagai", "sergai", "sei rampah", "perbaungan", "dolok masihul", "tanjung beringin", "bandar khalipah"],
    "Pematangsiantar": ["pematangsiantar", "pematang siantar", "siantar", "pemko siantar", "polres pematangsiantar"],
    "Simalungun": ["simalungun", "parapat", "pematang raya", "raya", "perdagangan", "tanah jawa", "saribudolok", "bosar maligas", "girsang sipangan bolon", "tigaras"],
    "Karo": ["karo", "tanah karo", "kabanjahe", "berastagi", "tigapanah", "merek", "sinabung", "lau kawar", "gundaling"],
    "Dairi": ["dairi", "sidikalang", "pakpak bharat", "salak", "sumbul", "tigalingga", "parbuluan"],
    "Samosir": ["samosir", "pangururan", "tomok", "tuktuk", "simanindo", "nainggolan", "palipi", "onan runggu", "sianjur mula-mula", "pusuk buhit"],
    "Toba": ["toba", "balige", "laguboti", "porsea", "ajibata", "lumban julu", "sigumpar", "silaen", "habinsaran"],
    "Taput": ["tapanuli utara", "taput", "tarutung", "siborongborong", "silangit", "pahae", "sipoholon", "muara", "adiankoting"],
    "Humbahas": ["humbang hasundutan", "humbahas", "doloksanggul", "dolok sanggul", "lintongnihuta", "baktiraja", "pollung", "paranginan", "pakkat"],
    "Sibolga - Tapteng": ["sibolga", "tapanuli tengah", "tapteng", "pandan", "barus", "pinangsori", "sorkam", "tukka", "badiri"],
    "Asahan": ["asahan", "kisaran", "batubara", "batu bara", "limapuluh", "lima puluh", "indrapura", "tanjungbalai", "tanjung balai", "air joman", "simpang empat"],
    "Labuhanbatu": ["labuhanbatu", "rantauprapat", "rantau prapat", "labuhanbatu utara", "labura", "aek kanopan", "kualuh", "labuhanbatu selatan", "labusel", "kotapinang", "kota pinang", "torgamba", "bilah"],
    "Nias": ["nias", "gunungsitoli", "gunung sitoli", "nias selatan", "nisel", "teluk dalam", "telukdalam", "nias utara", "nisut", "lotu", "lahewa", "nias barat", "nisbar", "lahomi", "sirombu", "kepulauan batu"],
    "Tapsel": ["tapanuli selatan", "tapsel", "sipirok", "batang toru", "padangsidimpuan", "padang sidimpuan", "mandailing natal", "madina", "panyabungan", "natal", "kotanopan", "padang lawas", "palas", "sibuhuan", "padang lawas utara", "paluta", "gunung tua", "tabagsel"],
}

# Kamus Pemetaan Kata Kunci Rubrik & Institusi
TOPIC_KEYWORD_MAP = {
    "Polda Sumut": [
        "polda sumut", "kapolda sumut", "wakapolda sumut", "ditreskrimum polda sumut",
        "ditreskrimsus polda sumut", "ditresnarkoba polda sumut", "bidhumas polda sumut",
        "propam polda sumut", "polrestabes medan", "polres pelabuhan belawan",
    ],
    "Kejati Sumut": [
        "kejati sumut", "kajati sumut", "kejaksaan tinggi sumatera utara", "kejari medan",
        "kejari", "kejaksaan negeri",
    ],
    "Kriminalitas": [
        "kriminal", "kriminalitas", "pembunuhan", "begal", "curanmor", "curat", "curas",
        "narkoba", "sabu", "ganja", "ekstasi", "judi", "judol", "judi online",
        "penganiayaan", "perampokan", "penipuan", "korupsi", "pungli", "tangkap",
        "ditangkap", "tersangka", "pelaku kejahatan", "pelaku kriminal", "tahanan", "diringkus", "vonis",
        "lapas", "rutan", "razia", "aniaya", "maling", "pencurian", "jambret",
    ],
    "Politik": [
        "politik", "pilkada", "pemilu", "pilgub", "pilbup", "pilwalkot", "kpu", "bawaslu",
        "dprd", "dprd sumut", "partai", "caleg", "fraksi", "politisi", "koalisi",
    ],
    "Ekobis": [
        "ekobis", "ekonomi", "bisnis", "pasar", "inflasi", "perbankan", "bank", "umkm",
        "sawit", "kelapa sawit", "karet", "kopi", "pertanian", "perkebunan", "petani",
        "komoditas", "investasi", "industri", "pelabuhan", "ekspor", "impor", "harga pangan",
        "beras", "apbd", "keuangan",
    ],
    "Wisata & Kuliner": [
        "wisata", "pariwisata", "kuliner", "destinasi", "hotel", "danau toba", "berastagi",
        "bukit lawang", "tangkahan", "andaliman", "arsik", "saksang", "naniura", "durian",
        "bika ambon", "kopi sidikalang", "kopi lintong", "festival", "turis", "kaldera",
        "parapat", "tuktuk", "tomok", "lontong medan",
    ],
    "Olahraga": [
        "olahraga", "sport", "sports", "sepak bola", "sepakbola", "bola", "psms",
        "psms medan", "ayam kinantan", "liga 2", "liga 3", "pon", "pon sumut", "atlet",
        "atlet sumut", "stadion teladan", "stadion baharoeddin", "koni", "koni sumut",
        "futsal", "bulutangkis", "badminton", "wushu", "gulat", "tinju", "renang",
    ],
    "Ototekno": [
        "ototekno", "otomotif", "teknologi", "motor", "mobil", "kendaraan listrik", "ev",
        "gadget", "smartphone", "aplikasi", "internet", "digital", "pln", "pln sumut",
        "telkomsel", "inovasi", "startup",
    ],
    "Hukrimpol": [
        "hukum", "polisi", "polres", "polsek", "polrestabes", "pengadilan", "laka lantas",
        "kecelakaan", "tabrakan", "kebakaran", "longsor", "banjir", "bencana",
    ],
}

# Saluran RSS Utama Berdasarkan Tier
RSS_URLS = [
    {
        "name": "Tier 1 - Pemprov Sumut, Polda Sumut & Antara Sumut",
        "url": "https://news.google.com/rss/search?q=(%22Pemprov+Sumut%22+OR+%22Pemerintah+Provinsi+Sumatera+Utara%22+OR+%22Gubernur+Sumut%22+OR+%22Polda+Sumut%22+OR+%22Pemko+Medan%22+OR+site:antaranews.com/sumut+OR+%22Antara+Sumut%22)+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
    {
        "name": "Tier 1 - Pemkab Tapanuli Raya & Danau Toba",
        "url": "https://news.google.com/rss/search?q=((%22Pemkab+Taput%22+OR+%22Pemkab+Toba%22+OR+%22Pemkab+Samosir%22+OR+%22Pemkab+Humbahas%22+OR+%22Pemkab+Tapteng%22+OR+%22Pemkab+Dairi%22+OR+%22Pemkab+Pakpak+Bharat%22+OR+%22Pemko+Sibolga%22+OR+%22Tapanuli+Utara%22+OR+%22Toba+Samosir%22+OR+%22Humbang+Hasundutan%22+OR+%22Tapanuli+Tengah%22+OR+%22Tapanuli+Selatan%22+OR+Padangsidimpuan+OR+Nias))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
    {
        "name": "Tier 1 - Medan, Pantai Timur & Simalungun-Karo",
        "url": "https://news.google.com/rss/search?q=((%22Deli+Serdang%22+OR+Langkat+OR+Binjai+OR+%22Pemkab+Karo%22+OR+%22Pemkab+Simalungun%22+OR+%22Pemko+Pematangsiantar%22+OR+Asahan+OR+Batubara+OR+Tanjungbalai+OR+Labuhanbatu)+AND+(pemerintah+OR+proyek+OR+pelayanan+OR+masyarakat))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 4,
        "tier": 1,
    },
    {
        "name": "Tier 2 - Hukrimpol Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Polda+Sumut%22+OR+%22Polrestabes+Medan%22+OR+%22Polres%22+OR+%22Kejati+Sumut%22+OR+%22Kejari%22+OR+%22Pengadilan+Negeri%22)+AND+(Medan+OR+Sumut+OR+Tapanuli+OR+Siantar+OR+Simalungun+OR+Langkat+OR+Asahan+OR+Nias)+AND+(tangkap+OR+narkoba+OR+tersangka+OR+begal+OR+judi+OR+korupsi+OR+kecelakaan+OR+sidang+OR+razia))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 4,
        "tier": 2,
    },
    {
        "name": "Tier 2 - Ekobis & Pertanian Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Sumatera+Utara%22+OR+Sumut+OR+Medan+OR+Tapanuli)+AND+(ekonomi+OR+bisnis+OR+pasar+OR+inflasi+OR+umkm+OR+sawit+OR+karet+OR+kopi+OR+pertanian+OR+investasi+OR+pelabuhan+OR+perdagangan))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    {
        "name": "Tier 2 - Olahraga Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22PSMS+Medan%22+OR+%22PSMS%22+OR+%22atlet+Sumut%22+OR+%22PON+Sumut%22+OR+%22Stadion+Teladan%22+OR+%22KONI+Sumut%22+OR+(%22olahraga%22+AND+(Medan+OR+Sumut+OR+Simalungun+OR+Tapanuli))))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    {
        "name": "Tier 2 - Wisata & Kuliner Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Danau+Toba%22+OR+Samosir+OR+Parapat+OR+Berastagi+OR+%22Bukit+Lawang%22+OR+Tangkahan+OR+%22Kuliner+Medan%22+OR+Andaliman+OR+%22Kopi+Sidikalang%22)+AND+(wisata+OR+destinasi+OR+kuliner+OR+hotel+OR+festival+OR+turis))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    # --- Media Lokal Sumatera Utara (RSS Langsung) ---
    {
        "name": "Hetanews - Berita Harian Sumut",
        "url": "https://www.hetanews.com/feed",
        "base_score": 5,
        "tier": 1,
    },
    {
        "name": "SumutPos - Harian Sumatera Utara",
        "url": "https://www.sumutpos.co/feed",
        "base_score": 5,
        "tier": 1,
    },
    {
        "name": "Mataberita.id - Portal Berita Sumut",
        "url": "https://www.mataberita.id/feed",
        "base_score": 4,
        "tier": 1,
    },
    # --- Media Nasional dengan Konten Sumut (RSS Langsung) ---
    {
        "name": "Tribunnews - Berita Nasional & Regional",
        "url": "https://www.tribunnews.com/rss",
        "base_score": 3,
        "tier": 2,
    },
    # --- Media Lokal Sumut via Google News site: filter (tidak punya RSS langsung) ---
    {
        "name": "Tier 1 - Waspada, HarianSIB & BeritaSumut (site filter)",
        "url": "https://news.google.com/rss/search?q=(site:waspada.id+OR+site:hariansib.com+OR+site:beritasumut.com)+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
    {
        "name": "Tier 1 - MedanBisnis, GoSumut & Tribunnews Medan (site filter)",
        "url": "https://news.google.com/rss/search?q=(site:medanbisnisdaily.com+OR+site:gosumut.com+OR+site:medan.tribunnews.com)+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
]

# Targeted Query Feeds Berdasarkan Zona Daerah, Rubrik Khusus, & Institusional
TARGETED_QUERY_FEEDS = {
    "institusional": [
        {
            "name": "Targeted - Polda Sumut",
            "url": "https://news.google.com/rss/search?q=%22Polda+Sumut%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Polda Sumut", "Hukrimpol"],
            "base_score": 4,
            "tier": 2,
        },
        {
            "name": "Targeted - Kejati Sumut",
            "url": "https://news.google.com/rss/search?q=%22Kejati+Sumut%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Kejati Sumut", "Hukrimpol"],
            "base_score": 4,
            "tier": 2,
        },
    ],
    "rubrik": [
        {
            "name": "Targeted - Ototekno Sumut",
            "url": "https://news.google.com/rss/search?q=(%22Otomotif%22+OR+%22Teknologi%22)+%22Sumatera+Utara%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Ototekno"],
            "base_score": 3,
            "tier": 2,
        },
        {
            "name": "Targeted - Wisata & Kuliner Sumut",
            "url": "https://news.google.com/rss/search?q=(%22Wisata%22+OR+%22Kuliner%22)+%22Sumatera+Utara%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Wisata & Kuliner"],
            "base_score": 3,
            "tier": 2,
        },
        {
            "name": "Targeted - Olahraga Sumut",
            "url": "https://news.google.com/rss/search?q=(%22Olahraga%22+OR+%22PSMS%22)+%22Sumatera+Utara%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Olahraga"],
            "base_score": 3,
            "tier": 2,
        },
        {
            "name": "Targeted - Ekobis Sumut",
            "url": "https://news.google.com/rss/search?q=(%22Ekonomi%22+OR+%22Bisnis%22+OR+%22UMKM%22)+%22Sumatera+Utara%22+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Ekobis"],
            "base_score": 3,
            "tier": 2,
        },
    ],
    "zona": [
        {
            "name": "Targeted - Zona Tabagsel & Pantai Barat",
            "url": "https://news.google.com/rss/search?q=(%22Tapanuli+Selatan%22+OR+%22Padangsidimpuan%22+OR+%22Mandailing+Natal%22+OR+%22Padang+Lawas%22+OR+%22Sibolga%22+OR+%22Tapanuli+Tengah%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Tapsel", "Sibolga - Tapteng"],
            "base_score": 4,
            "tier": 1,
        },
        {
            "name": "Targeted - Zona Kepulauan Nias",
            "url": "https://news.google.com/rss/search?q=(%22Gunungsitoli%22+OR+%22Nias+Selatan%22+OR+%22Nias+Utara%22+OR+%22Nias+Barat%22+OR+%22Kepulauan+Nias%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Nias"],
            "base_score": 4,
            "tier": 1,
        },
        {
            "name": "Targeted - Zona Dairi, Pakpak & Karo",
            "url": "https://news.google.com/rss/search?q=(%22Dairi%22+OR+%22Sidikalang%22+OR+%22Pakpak+Bharat%22+OR+%22Kabanjahe%22+OR+%22Berastagi%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Dairi", "Karo"],
            "base_score": 4,
            "tier": 1,
        },
        {
            "name": "Targeted - Zona Kawasan Danau Toba",
            "url": "https://news.google.com/rss/search?q=(%22Samosir%22+OR+%22Toba%22+OR+%22Balige%22+OR+%22Tapanuli+Utara%22+OR+%22Tarutung%22+OR+%22Humbang+Hasundutan%22+OR+%22Doloksanggul%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Samosir", "Toba", "Taput", "Humbahas"],
            "base_score": 4,
            "tier": 1,
        },
        {
            "name": "Targeted - Zona Siantar, Simalungun & Pesisir Timur",
            "url": "https://news.google.com/rss/search?q=(%22Pematangsiantar%22+OR+%22Simalungun%22+OR+%22Parapat%22+OR+%22Asahan%22+OR+%22Batubara%22+OR+%22Tanjungbalai%22+OR+%22Labuhanbatu%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Pematangsiantar", "Simalungun", "Asahan", "Labuhanbatu"],
            "base_score": 4,
            "tier": 1,
        },
        {
            "name": "Targeted - Zona Langkat, Binjai, Deli Serdang & Sergai",
            "url": "https://news.google.com/rss/search?q=(%22Langkat%22+OR+%22Stabat%22+OR+%22Binjai%22+OR+%22Deli+Serdang%22+OR+%22Tebing+Tinggi%22+OR+%22Serdang+Bedagai%22)+when:48h&hl=id&gl=ID&ceid=ID:id",
            "labels": ["Langkat", "Binjai", "Deli Serdang", "Tebing Tinggi"],
            "base_score": 4,
            "tier": 1,
        },
    ],
}

# Pemetaan alias variasi topik dan wilayah ke 27 Label Baku
LABEL_ALIASES = {}
for _target_label, _aliases in GEO_ALIAS_MAP.items():
    LABEL_ALIASES[_target_label.lower()] = _target_label
    for _a in _aliases:
        LABEL_ALIASES[_a.lower()] = _target_label

for _target_label, _aliases in TOPIC_KEYWORD_MAP.items():
    LABEL_ALIASES[_target_label.lower()] = _target_label
    for _a in _aliases:
        LABEL_ALIASES[_a.lower()] = _target_label

# Legacy aliases
LABEL_ALIASES.update({
    "berita sumut": "Medan",
    "tapanuli": "Taput",
    "budaya & hata": "Wisata & Kuliner",
    "adat batak": "Wisata & Kuliner",
    "budaya": "Wisata & Kuliner",
    "adat": "Wisata & Kuliner",
    "hukum": "Hukrimpol",
    "kriminal": "Kriminalitas",
    "kriminalitas": "Kriminalitas",
    "politik": "Politik",
    "politik daerah": "Politik",
    "hukum kriminal": "Hukrimpol",
    "hukum & kriminal": "Hukrimpol",
    "peristiwa": "Hukrimpol",
})

# Filter foto berita & aturan ilustrasi kontekstual AI
REQUIRE_REAL_IMAGE = os.environ.get("REQUIRE_REAL_IMAGE", "0").strip().lower() in ("1", "true", "yes")

FALLBACK_IMAGES_BY_TOPIC = {
    "wisata_kuliner": [
        "https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    ],
    "hukrimpol": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1453733190371-0a9bedd82893?auto=format&fit=crop&w=1200&q=80",
    ],
    "kriminalitas": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1453733190371-0a9bedd82893?auto=format&fit=crop&w=1200&q=80",
    ],
    "politik": [
        "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?auto=format&fit=crop&w=1200&q=80",
    ],
    "polda_sumut": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
    ],
    "kejati_sumut": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
    ],
    "ekobis": [
        "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80",
    ],
    "olahraga": [
        "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1200&q=80",
    ],
    "ototekno": [
        "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1200&q=80",
    ],
    "umum": [
        "https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    ],
}

BAD_IMAGE_PATTERNS = [
    "lh3.googleusercontent.com",
    "gstatic.com",
    "google.com",
    "favicon",
    "logo_",
    "/logo",
    "_logo",
    "-logo",
    "/icon",
    "icon_",
    "_icon",
    "-icon",
    "/avatar",
    "avatar_",
    "author-avatar",
    "user-avatar",
    "gravatar.com",
    "/ads/",
    "/ad/",
    "googleads",
    "doubleclick",
    "banner_ad",
    "_ads.",
    "adsbygoogle",
    "ads_wrapper",
    "taboola",
    "outbrain",
    "/banners/",
    "iklan",
    "share-button",
    "share-icon",
    "social-share",
    "widget_",
    "/widget",
    "small_",
    "_330x",
    "150x150",
    "100x100",
    "60x60",
    "50x50",
    "l_text:",
    "og_kumparan",
    "watermark",
    "watermarked",
    "/api/wm/",
    "/wm/",
    "wm=",
    "placeholder",
    "no-image",
    "picture_not_available",
    "default-thumb",
    "transparent.gif",
    "spacer.gif",
    "1x1.",
    "pixel.gif",
    "blank.gif",
]

PAGINATED_PORTAL_DOMAINS = (
    "tribunnews.com",
    "kompas.com",
    "okezone.com",
    "sindonews.com",
)

VIDEO_ONLY_SOURCES = {
    "20detik",
    "youtube",
    "tiktok",
}

VIDEO_ONLY_DOMAINS = (
    "20.detik.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "instagram.com",
)

UGC_OPINION_DOMAINS = (
    "kompasiana.com",
    "retizen.republika.co.id",
    "kaskus.co.id",
    "quora.com",
)

UGC_OPINION_SOURCES = {
    "kompasiana",
    "kaskus",
    "retizen",
}

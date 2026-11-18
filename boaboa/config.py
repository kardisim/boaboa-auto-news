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
MAX_POSTS_PER_RUN = int(os.environ.get("MAX_POSTS_PER_RUN", "5"))
MAX_CANDIDATES_PER_FEED = 4
MIN_RELEVANCE_SCORE = 1
MIN_IMAGE_WIDTH = 300

# Standar SEO & Jurnalistik Dewan Pers boaboa.bataktive.com
MIN_LABELS_PER_POST = 1
MAX_LABELS_PER_POST = 2
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

# Saluran RSS Terkurasi Berdasarkan Tier Prioritas untuk Portal Berita Harian Cepat Sumatera Utara
RSS_URLS = [
    # Tier 1 (Prioritas Utama): Berita Resmi Pemprov Sumut, Antara Sumut, Pemko Medan & Polda Sumut
    {
        "name": "Tier 1 - Pemprov Sumut, Polda Sumut & Antara Sumut",
        "url": "https://news.google.com/rss/search?q=(%22Pemprov+Sumut%22+OR+%22Pemerintah+Provinsi+Sumatera+Utara%22+OR+%22Gubernur+Sumut%22+OR+%22Polda+Sumut%22+OR+%22Pemko+Medan%22+OR+site:antaranews.com/sumut+OR+%22Antara+Sumut%22)+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
    # Tier 1 (Wilayah Tapanuli Raya & Danau Toba): Taput, Toba, Samosir, Humbahas, Tapteng, Sibolga, Dairi, Pakpak Bharat
    {
        "name": "Tier 1 - Pemkab Tapanuli Raya & Danau Toba",
        "url": "https://news.google.com/rss/search?q=((%22Pemkab+Taput%22+OR+%22Pemkab+Toba%22+OR+%22Pemkab+Samosir%22+OR+%22Pemkab+Humbahas%22+OR+%22Pemkab+Tapteng%22+OR+%22Pemkab+Dairi%22+OR+%22Pemkab+Pakpak+Bharat%22+OR+%22Pemko+Sibolga%22+OR+%22Tapanuli+Utara%22+OR+%22Toba+Samosir%22+OR+%22Humbang+Hasundutan%22+OR+%22Tapanuli+Tengah%22+OR+%22Tapanuli+Selatan%22+OR+Padangsidimpuan+OR+Nias))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 5,
        "tier": 1,
    },
    # Tier 1 (Wilayah Aglomerasi Medan, Pantai Timur & Dataran Tinggi): Deli Serdang, Langkat, Binjai, Karo, Simalungun, Siantar, Asahan
    {
        "name": "Tier 1 - Medan, Pantai Timur & Simalungun-Karo",
        "url": "https://news.google.com/rss/search?q=((%22Deli+Serdang%22+OR+Langkat+OR+Binjai+OR+%22Pemkab+Karo%22+OR+%22Pemkab+Simalungun%22+OR+%22Pemko+Pematangsiantar%22+OR+Asahan+OR+Batubara+OR+Tanjungbalai+OR+Labuhanbatu)+AND+(pemerintah+OR+proyek+OR+pelayanan+OR+masyarakat))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 4,
        "tier": 1,
    },
    # Tier 2 (Hukrimpol Sumut): Berita hukum, kriminalitas, kepolisian daerah, kecelakaan, pengadilan & peristiwa
    {
        "name": "Tier 2 - Hukrimpol Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Polda+Sumut%22+OR+%22Polrestabes+Medan%22+OR+%22Polres%22+OR+%22Kejati+Sumut%22+OR+%22Kejari%22+OR+%22Pengadilan+Negeri%22)+AND+(Medan+OR+Sumut+OR+Tapanuli+OR+Siantar+OR+Simalungun+OR+Langkat+OR+Asahan+OR+Nias)+AND+(tangkap+OR+narkoba+OR+tersangka+OR+begal+OR+judi+OR+korupsi+OR+kecelakaan+OR+sidang+OR+razia))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 4,
        "tier": 2,
    },
    # Tier 2 (Ekobis Sumut): Ekonomi, bisnis, perbankan, perkebunan sawit, UMKM & harga pangan daerah
    {
        "name": "Tier 2 - Ekobis & Pertanian Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Sumatera+Utara%22+OR+Sumut+OR+Medan+OR+Tapanuli)+AND+(ekonomi+OR+bisnis+OR+pasar+OR+inflasi+OR+umkm+OR+sawit+OR+karet+OR+kopi+OR+pertanian+OR+investasi+OR+pelabuhan+OR+perdagangan))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    # Tier 2 (Olahraga Sumut): PSMS Medan, atlet Sumut, PON, stadion & prestasi olahraga daerah
    {
        "name": "Tier 2 - Olahraga Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22PSMS+Medan%22+OR+%22PSMS%22+OR+%22atlet+Sumut%22+OR+%22PON+Sumut%22+OR+%22Stadion+Teladan%22+OR+%22KONI+Sumut%22+OR+(%22olahraga%22+AND+(Medan+OR+Sumut+OR+Simalungun+OR+Tapanuli))))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    # Tier 2 (Wisata & Kuliner): Destinasi Danau Toba, Berastagi, kuliner khas Medan/Sumut
    {
        "name": "Tier 2 - Wisata & Kuliner Sumatera Utara",
        "url": "https://news.google.com/rss/search?q=((%22Danau+Toba%22+OR+Samosir+OR+Parapat+OR+Berastagi+OR+%22Bukit+Lawang%22+OR+Tangkahan+OR+%22Kuliner+Medan%22+OR+Andaliman+OR+%22Kopi+Sidikalang%22)+AND+(wisata+OR+destinasi+OR+kuliner+OR+hotel+OR+festival+OR+turis))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    # Tier 2 (Budaya & Hata): Budaya Batak, Melayu Deli, Karo, Nias, tradisi & bahasa daerah
    {
        "name": "Tier 2 - Budaya & Hata Daerah",
        "url": "https://news.google.com/rss/search?q=((%22Budaya+Batak%22+OR+%22Adat+Batak%22+OR+Ulos+OR+%22Melayu+Deli%22+OR+%22Adat+Karo%22+OR+%22Budaya+Nias%22+OR+%22Bahasa+Batak%22+OR+Aksara)+AND+(tradisi+OR+budaya+OR+sejarah+OR+kesenian+OR+upacara))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 3,
        "tier": 2,
    },
    # Tier 3 (Ototekno & Inovasi Daerah): Otomotif, teknologi, infrastruktur digital & energi Sumut
    {
        "name": "Tier 3 - Ototekno & Inovasi Daerah",
        "url": "https://news.google.com/rss/search?q=((Medan+OR+Sumut+OR+%22Sumatera+Utara%22)+AND+(otomotif+OR+teknologi+OR+%22kendaraan+listrik%22+OR+%22PLN+Sumut%22+OR+digital+OR+internet+OR+aplikasi+OR+inovasi))+when:24h&hl=id&gl=ID&ceid=ID:id",
        "base_score": 2,
        "tier": 3,
    },
]

# Daftar 8 Label Baku Blogger boaboa.bataktive.com (Sinkron persis dengan navigasi & kanal tematik template)
ALLOWED_LABELS = [
    "Berita Sumut",
    "Tapanuli",
    "Hukrimpol",
    "Ekobis",
    "Wisata & Kuliner",
    "Olahraga",
    "Budaya & Hata",
    "Ototekno",
]

# Pemetaan alias variasi topik dan wilayah ke 8 Label Baku
LABEL_ALIASES = {
    # Hukrimpol (Hukum, Kriminalitas, Kepolisian, Kecelakaan, Bencana, Politik & Pilkada Daerah)
    "hukrimpol": "Hukrimpol",
    "hukum": "Hukrimpol",
    "kriminal": "Hukrimpol",
    "kriminalitas": "Hukrimpol",
    "hukum kriminal": "Hukrimpol",
    "hukum & kriminal": "Hukrimpol",
    "hukum/kriminal": "Hukrimpol",
    "peristiwa": "Hukrimpol",
    "polisi": "Hukrimpol",
    "polres": "Hukrimpol",
    "polda": "Hukrimpol",
    "polrestabes": "Hukrimpol",
    "sat reskrim": "Hukrimpol",
    "sat narkoba": "Hukrimpol",
    "kecelakaan": "Hukrimpol",
    "laka lantas": "Hukrimpol",
    "tabrakan": "Hukrimpol",
    "bencana": "Hukrimpol",
    "kebakaran": "Hukrimpol",
    "banjir": "Hukrimpol",
    "longsor": "Hukrimpol",
    "narkoba": "Hukrimpol",
    "sabu": "Hukrimpol",
    "ganja": "Hukrimpol",
    "judi": "Hukrimpol",
    "begal": "Hukrimpol",
    "curanmor": "Hukrimpol",
    "curat": "Hukrimpol",
    "kejari": "Hukrimpol",
    "kejati": "Hukrimpol",
    "pengadilan": "Hukrimpol",
    "sidang": "Hukrimpol",
    "vonis": "Hukrimpol",
    "lapas": "Hukrimpol",
    "rutan": "Hukrimpol",
    "razia": "Hukrimpol",
    "korupsi": "Hukrimpol",
    "pungli": "Hukrimpol",
    "politik": "Hukrimpol",
    "politik daerah": "Hukrimpol",
    "pilkada": "Hukrimpol",
    "pemilu": "Hukrimpol",
    "kpu": "Hukrimpol",
    "bawaslu": "Hukrimpol",
    "caleg": "Hukrimpol",
    "dprd": "Hukrimpol",
    "dprd sumut": "Hukrimpol",
    "partai": "Hukrimpol",

    # Ekobis (Ekonomi, Bisnis, Perbankan, UMKM, Pertanian, Perkebunan, Pasar)
    "ekobis": "Ekobis",
    "ekonomi": "Ekobis",
    "bisnis": "Ekobis",
    "ekonomi & bisnis": "Ekobis",
    "ekonomi bisnis": "Ekobis",
    "pasar": "Ekobis",
    "inflasi": "Ekobis",
    "perbankan": "Ekobis",
    "bank": "Ekobis",
    "umkm": "Ekobis",
    "sawit": "Ekobis",
    "kelapa sawit": "Ekobis",
    "karet": "Ekobis",
    "kopi": "Ekobis",
    "pertanian": "Ekobis",
    "perkebunan": "Ekobis",
    "petani": "Ekobis",
    "komoditas": "Ekobis",
    "investasi": "Ekobis",
    "industri": "Ekobis",
    "pelabuhan": "Ekobis",
    "belawan": "Ekobis",
    "ekspor": "Ekobis",
    "impor": "Ekobis",
    "harga pangan": "Ekobis",
    "keuangan": "Ekobis",
    "apbd": "Ekobis",

    # Olahraga (PSMS Medan, Sepak Bola, PON, Atlet Sumut, Olahraga Daerah)
    "olahraga": "Olahraga",
    "sport": "Olahraga",
    "sports": "Olahraga",
    "sepak bola": "Olahraga",
    "sepakbola": "Olahraga",
    "bola": "Olahraga",
    "psms": "Olahraga",
    "psms medan": "Olahraga",
    "ayam kinantan": "Olahraga",
    "liga 2": "Olahraga",
    "liga 3": "Olahraga",
    "pon": "Olahraga",
    "pon sumut": "Olahraga",
    "atlet": "Olahraga",
    "atlet sumut": "Olahraga",
    "stadion teladan": "Olahraga",
    "futsal": "Olahraga",
    "bulutangkis": "Olahraga",
    "badminton": "Olahraga",
    "wushu": "Olahraga",
    "gulat": "Olahraga",
    "tinju": "Olahraga",
    "renang": "Olahraga",
    "koni": "Olahraga",

    # Wisata & Kuliner (Pariwisata Danau Toba, Berastagi, Kuliner Medan/Batak/Daerah)
    "wisata & kuliner": "Wisata & Kuliner",
    "wisata": "Wisata & Kuliner",
    "pariwisata": "Wisata & Kuliner",
    "wisata danau toba": "Wisata & Kuliner",
    "pariwisata danau toba": "Wisata & Kuliner",
    "danau toba": "Wisata & Kuliner",
    "destinasi": "Wisata & Kuliner",
    "hotel": "Wisata & Kuliner",
    "kuliner": "Wisata & Kuliner",
    "kuliner batak": "Wisata & Kuliner",
    "kuliner medan": "Wisata & Kuliner",
    "masakan": "Wisata & Kuliner",
    "makanan": "Wisata & Kuliner",
    "parapat": "Wisata & Kuliner",
    "berastagi": "Wisata & Kuliner",
    "bukit lawang": "Wisata & Kuliner",
    "tangkahan": "Wisata & Kuliner",
    "kaldera": "Wisata & Kuliner",
    "andaliman": "Wisata & Kuliner",
    "arsik": "Wisata & Kuliner",
    "saksang": "Wisata & Kuliner",
    "naniura": "Wisata & Kuliner",
    "durian ucok": "Wisata & Kuliner",
    "bika ambon": "Wisata & Kuliner",
    "lontong medan": "Wisata & Kuliner",
    "kopi sidikalang": "Wisata & Kuliner",
    "kopi lintong": "Wisata & Kuliner",

    # Budaya & Hata (Adat, Tradisi, Ulos, Aksara, Bahasa Daerah, Budaya Batak/Melayu/Karo/Nias)
    "budaya & hata": "Budaya & Hata",
    "budaya batak": "Budaya & Hata",
    "adat batak": "Budaya & Hata",
    "tradisi batak": "Budaya & Hata",
    "sejarah batak": "Budaya & Hata",
    "bahasa batak": "Budaya & Hata",
    "aksara batak": "Budaya & Hata",
    "kamus batak": "Budaya & Hata",
    "hata batak": "Budaya & Hata",
    "hata": "Budaya & Hata",
    "bahasa daerah": "Budaya & Hata",
    "ulos": "Budaya & Hata",
    "dalihan na tolu": "Budaya & Hata",
    "budaya": "Budaya & Hata",
    "adat": "Budaya & Hata",
    "tradisi": "Budaya & Hata",
    "sejarah": "Budaya & Hata",
    "melayu deli": "Budaya & Hata",
    "istana maimun": "Budaya & Hata",
    "budaya karo": "Budaya & Hata",
    "budaya nias": "Budaya & Hata",
    "tor-tor": "Budaya & Hata",
    "gondang": "Budaya & Hata",
    "partuturan": "Budaya & Hata",
    "umpasa": "Budaya & Hata",
    "komunitas batak": "Budaya & Hata",
    "komunitas": "Budaya & Hata",
    "diaspora": "Budaya & Hata",
    "marga": "Budaya & Hata",
    "tarombo": "Budaya & Hata",
    "sinamot": "Budaya & Hata",
    "pariban": "Budaya & Hata",
    "boru": "Budaya & Hata",
    "boru batak": "Budaya & Hata",

    # Ototekno (Otomotif, Teknologi, Gadget, Kendaraan Listrik, PLN, Digital)
    "ototekno": "Ototekno",
    "otomotif": "Ototekno",
    "teknologi": "Ototekno",
    "motor": "Ototekno",
    "mobil": "Ototekno",
    "kendaraan listrik": "Ototekno",
    "ev": "Ototekno",
    "gadget": "Ototekno",
    "smartphone": "Ototekno",
    "aplikasi": "Ototekno",
    "internet": "Ototekno",
    "digital": "Ototekno",
    "pln": "Ototekno",
    "pln sumut": "Ototekno",
    "telkomsel": "Ototekno",
    "inovasi": "Ototekno",
    "startup": "Ototekno",

    # Tapanuli (Tapanuli Raya, Samosir, Toba, Humbahas, Tapteng, Sibolga, Dairi, Pakpak, Madina, Palas, Nias)
    "tapanuli": "Tapanuli",
    "tapanuli utara": "Tapanuli",
    "tapanuli tengah": "Tapanuli",
    "tapanuli selatan": "Tapanuli",
    "taput": "Tapanuli",
    "tapteng": "Tapanuli",
    "tapsel": "Tapanuli",
    "sibolga": "Tapanuli",
    "tarutung": "Tapanuli",
    "humbang hasundutan": "Tapanuli",
    "humbahas": "Tapanuli",
    "doloksanggul": "Tapanuli",
    "dairi": "Tapanuli",
    "sidikalang": "Tapanuli",
    "pakpak bharat": "Tapanuli",
    "salak": "Tapanuli",
    "samosir": "Tapanuli",
    "pangururan": "Tapanuli",
    "toba": "Tapanuli",
    "balige": "Tapanuli",
    "toba samosir": "Tapanuli",
    "padangsidimpuan": "Tapanuli",
    "padang lawas": "Tapanuli",
    "palas": "Tapanuli",
    "padang lawas utara": "Tapanuli",
    "paluta": "Tapanuli",
    "mandailing natal": "Tapanuli",
    "madina": "Tapanuli",
    "nias": "Tapanuli",
    "gunungsitoli": "Tapanuli",
    "nias selatan": "Tapanuli",
    "nias barat": "Tapanuli",
    "nias utara": "Tapanuli",

    # Berita Sumut (Ibu Kota Medan, Aglomerasi Deli Serdang, Pantai Timur, Dataran Tinggi & Umum Sumut)
    "berita sumut": "Berita Sumut",
    "sumatera utara": "Berita Sumut",
    "sumut": "Berita Sumut",
    "medan": "Berita Sumut",
    "kota medan": "Berita Sumut",
    "deli serdang": "Berita Sumut",
    "lubuk pakam": "Berita Sumut",
    "langkat": "Berita Sumut",
    "stabat": "Berita Sumut",
    "binjai": "Berita Sumut",
    "pematangsiantar": "Berita Sumut",
    "siantar": "Berita Sumut",
    "simalungun": "Berita Sumut",
    "karo": "Berita Sumut",
    "kabanjahe": "Berita Sumut",
    "tebing tinggi": "Berita Sumut",
    "asahan": "Berita Sumut",
    "kisaran": "Berita Sumut",
    "batubara": "Berita Sumut",
    "tanjungbalai": "Berita Sumut",
    "labuhanbatu": "Berita Sumut",
    "rantauprapat": "Berita Sumut",
    "labuhanbatu selatan": "Berita Sumut",
    "labusel": "Berita Sumut",
    "labuhanbatu utara": "Berita Sumut",
    "labura": "Berita Sumut",
    "serdang bedagai": "Berita Sumut",
    "sergai": "Berita Sumut",
    "pemerintahan": "Berita Sumut",
    "pemprov sumut": "Berita Sumut",
    "daerah": "Berita Sumut",
}

# Filter foto berita & aturan ilustrasi kontekstual AI
REQUIRE_REAL_IMAGE = os.environ.get("REQUIRE_REAL_IMAGE", "0").strip().lower() in ("1", "true", "yes")

FALLBACK_IMAGES_BY_TOPIC = {
    "wisata_kuliner": [
        "https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    ],
    "budaya_hata": [
        "https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80",
    ],
    "hukrimpol": [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80",
        "https://images.unsplash.com/photo-1453733190371-0a9bedd82893?auto=format&fit=crop&w=1200&q=80",
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
    # Avatar Google / Akun (bukan Blogger CDN)
    "lh3.googleusercontent.com",
    "gstatic.com",
    "google.com",
    # Ikon, Logo, Avatar & Profil Penulis
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
    # Iklan & Banner Promosi
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
    # Tombol Berbagi & Widget
    "share-button",
    "share-icon",
    "social-share",
    "widget_",
    "/widget",
    # Thumbnail Sangat Kecil / Icon
    "small_",
    "_330x",
    "150x150",
    "100x100",
    "60x60",
    "50x50",
    # Pola Watermark & Crop Portal Komersial
    "l_text:",
    "og_kumparan",
    "watermark",
    "watermarked",
    "/api/wm/",
    "/wm/",
    "wm=",
    # Placeholder & Tracking Pixel
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

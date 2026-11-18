# BoaBoa Auto News (boaboa.bataktive.com)

[![BoaBoa Auto News](https://github.com/kardisim/boaboa-auto-news/actions/workflows/auto_news.yml/badge.svg)](https://github.com/kardisim/boaboa-auto-news/actions/workflows/auto_news.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Bot agregasi, kurasi, dan penulisan ulang berita cerdas berbasis AI untuk portal berita harian cepat se-Sumatera Utara: **[boaboa.bataktive.com](https://boaboa.bataktive.com)**.

Sistem ini memindai berita aktual Sumatera Utara dari berbagai sumber RSS terpercaya, melakukan deduplikasi semantik, menyaring konten, menulis ulang naskah sesuai standar jurnalistik Dewan Pers Indonesia (PUEBI/EYD V), menghasilkan ilustrasi editorial 16:9 via Gemini AI jika foto asli tidak tersedia, dan mengunggah draf artikel ke Google Blogger.

---

## 🌟 Fitur Utama & Standar Arsitektur

1. **Mode Publikasi Draft Aman:**
   - Seluruh artikel dikirim ke Blogger dengan status **Draft** (`PUBLISH_AS_DRAFT = True`), memberikan kendali penuh kepada redaksi manusia untuk peninjauan akhir sebelum tayang.
   - Maksimal pemrosesan 5 artikel per putaran (`MAX_POSTS_PER_RUN = 5`) untuk menjaga keteraturan dan kualitas terbitan.
   - Dilengkapi **Kotak Catatan Redaksi** (`draft-review-box`) di baris teratas draf artikel (memuat tautan media sumber rujukan, status gambar, jumlah kata, dan poin cek redaksi) yang dapat dihapus 1-klik sebelum dipublikasikan.

2. **Dukungan 8 Label Baku Blogger boaboa.bataktive.com:**
   Setiap artikel secara otomatis dipetakan ke tepat 2 label baku yang sinkron dengan navigasi template:
   - `Berita Sumut`: Berita umum, pemerintahan provinsi, Medan, Deli Serdang, Langkat, Binjai, Tebing Tinggi, Asahan, Batubara, Labuhanbatu, Sergai.
   - `Tapanuli`: Wilayah Tapanuli Raya (Taput, Toba, Samosir, Humbahas, Tapteng, Sibolga, Dairi, Pakpak Bharat, Tabagsel, Nias).
   - `Hukrimpol`: Berita hukum, kriminalitas, kepolisian daerah, kecelakaan lalu lintas, bencana, pengadilan, dan politik daerah.
   - `Ekobis`: Ekonomi, bisnis, perbankan, pasar, inflasi, perkebunan kelapa sawit, karet, pertanian, komoditas, dan UMKM.
   - `Wisata & Kuliner`: Destinasi Danau Toba, Berastagi, Bukit Lawang, serta kuliner khas Medan dan daerah.
   - `Olahraga`: Sepak bola daerah, PSMS Medan (Ayam Kinantan), Stadion Teladan, PON Sumut, dan atlet daerah.
   - `Budaya & Hata`: Adat istiadat, tradisi, kain ulos, aksara Batak, bahasa daerah (Hata), Melayu Deli, dan sejarah lokal.
   - `Ototekno`: Otomotif, kendaraan listrik, kelistrikan (PLN Sumut), teknologi, dan inovasi digital regional.

3. **Mesin AI Dual-Engine (Gemini API & Groq Fallback):**
   - **Primary Engine:** Google Gemini API (`gemini-3.8-flash` via SDK `google-genai`) dengan fallback model otomatis (`gemini-2.0-flash`, `gemini-1.5-flash`).
   - **Secondary Engine:** Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, dsb.) dengan penanganan format reasoning tersembunyi.
   - Mekanisme **Self-Healing Repair Pass**: Jika validator mendeteksi catatan kualitas (kebocoran bahasa asing, angka tanpa dasar sumber, atau judul melampaui batas), sistem melakukan pass perbaikan otomatis sebelum memutuskan hasil akhir.

4. **Penanganan Gambar & Fallback Ilustrasi Editorial 16:9:**
   - Validasi ketat terhadap gambar sumber asli (resolusi lebar minimal `300px`, pembersihan watermark portal komersial seperti Detik, Kompas, Kumparan, Tribun).
   - Jika sumber tidak memuat foto liputan yang valid, sistem secara otomatis menerjemahkan konteks berita menjadi prompt visual netral (bebas filter kekerasan/kriminalitas dan **tanpa teks** di dalam gambar), lalu menghasilkan gambar editorial 16:9 via Gemini Imagen 3 / Pollinations Flux.
   - Gambar disimpan ke direktori `generated_images/` dalam format `.jpg` terkompresi Pillow dan dilayani via CDN publik jsDelivr:
     `https://cdn.jsdelivr.net/gh/{GITHUB_REPOSITORY}@main/generated_images/{filename}`.

5. **Anti-Duplikasi & Filter Kualitas Jurnalistik:**
   - **Semantic Deduplication:** Pengecekan Jaccard similarity & token overlap (ambang batas `>= 0.60`) terhadap riwayat 100 entri terakhir di `posted_history.json`.
   - **Multi-Source Story Clustering:** Mengelompokkan liputan dari berbagai media berbeda untuk peristiwa yang sama menjadi satu masukan artikel yang komprehensif.
   - **Etika Dewan Pers:** Penegakan asas praduga tak bersalah (*presumption of innocence*) untuk berita kriminal/hukum (`Hukrimpol`), larangan tegas terhadap blok "Baca Juga" fiktif, serta penghapusan frasa klise AI.

---

## 📁 Struktur Repositori

```text
boaboa-auto-news/
├── .github/
│   └── workflows/
│       └── auto_news.yml        # Workflow GitHub Actions (terjadwal setiap 3 jam, menit 25)
├── boaboa/
│   ├── __init__.py
│   ├── config.py                # Konfigurasi, daftar 8 label baku, RSS terkurasi, dan batas sistem
│   ├── extractor.py             # Ekstraksi konten artikel, dewatermarking, dan deteksi foto liputan
│   ├── history.py               # Penyimpanan riwayat & algoritma anti-duplikasi semantik (Jaccard)
│   ├── html_formatter.py        # Pemformatan HTML semantik, draft-review-box, dan atribusi
│   ├── image_generator.py       # Pembuatan ilustrasi AI editorial 16:9 & kompresi ke folder lokal
│   ├── quality_guard.py         # Quality gate, pembersih dateline/byline, dan pemeriksa Dewan Pers
│   ├── relevance.py             # Penilaian relevansi berita Sumatera Utara & clustering peristiwa
│   └── writer.py                # Redaktur AI: penulisan ulang naskah & self-healing repair pass
├── generated_images/
│   └── .gitkeep                 # Folder penampung gambar hasil generate AI
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_history.py
│   ├── test_html_formatter.py
│   ├── test_image_generator.py
│   ├── test_quality_guard.py
│   ├── test_relevance.py
│   └── test_writer.py
├── .gitignore
├── main.py                      # Skrip utama orkestrasi pemrosesan berita
├── posted_history.json          # Basis data riwayat artikel yang telah diproses
├── README.md
└── requirements.txt
```

---

## ⚙️ Persyaratan & Instalasi

### Prasyarat
- Python 3.12 atau yang lebih baru.
- Kunci API Google Gemini (`GEMINI_API_KEY`) atau Groq (`GROQ_API_KEY`).
- Kredensial OAuth 2.0 Blogger (`token.json`).

### Langkah Instalasi Lokal
1. **Kloning Repositori:**
   ```bash
   git clone https://github.com/kardisim/boaboa-auto-news.git
   cd boaboa-auto-news
   ```

2. **Buat Virtual Environment & Pasang Dependensi:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Menjalankan Pengujian Unit Test:**
   ```bash
   pytest -v
   # atau menggunakan unittest:
   python -m unittest discover -s tests -v
   ```

4. **Uji Coba Eksekusi Lokal (Dry-Run):**
   ```bash
   export GEMINI_API_KEY="kunci-gemini-anda"
   # atau set GEMINI_API_KEY="kunci-gemini-anda" di Windows CMD / $env:GEMINI_API_KEY di PowerShell
   python main.py --dry-run
   ```

---

## 🔐 Konfigurasi GitHub Actions & Secrets

Agar bot dapat berjalan otomatis di GitHub Actions, atur konfigurasi berikut di menu **Settings > Secrets and variables > Actions**:

### Secrets
| Nama Secret | Deskripsi |
| :--- | :--- |
| `BLOGGER_TOKEN` | Konten berkas JSON token otorisasi OAuth 2.0 Blogger (`token.json`). |
| `GEMINI_API_KEY` | Kunci API Google AI Studio / Gemini API (Mesin Utama). |
| `GROQ_API_KEY` | Kunci API Groq (Mesin Cadangan / Fallback). |

### Variables (Opsional)
| Nama Variabel | Default | Deskripsi |
| :--- | :--- | :--- |
| `BLOGGER_BLOG_ID` | `8826247154815720532` | ID Blog Blogger boaboa.bataktive.com |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Model Gemini yang digunakan |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Model Groq yang digunakan |
| `MAX_POSTS_PER_RUN`| `5` | Batas maksimum artikel per run |

---

## 📜 Lisensi & Atribusi

Proyek ini berada di bawah lisensi [MIT](LICENSE). Dikembangkan khusus untuk jaringan portal berita **BoaBoa** (`boaboa.bataktive.com`).

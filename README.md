# BoaBoa Auto News (boaboa.bataktive.com)

[![BoaBoa Auto News](https://github.com/kardisim/boaboa-auto-news/actions/workflows/auto_news.yml/badge.svg)](https://github.com/kardisim/boaboa-auto-news/actions/workflows/auto_news.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Bot agregasi, kurasi, dan penulisan ulang berita cerdas berbasis AI untuk sentra berita harian Sumatera Utara: **[boaboa.bataktive.com](https://boaboa.bataktive.com)** yang mencakup seluruh 33 kabupaten/kota di Sumatera Utara dan menyeimbangkan distribusi 27 label target (*Label Coverage Balancing*).

Sistem ini memindai berita aktual Sumatera Utara dari saluran RSS utama dan saluran terarah per zona wilayah/rubrik, melakukan deduplikasi semantik, menyaring konten, menulis ulang naskah sesuai standar jurnalistik Dewan Pers Indonesia (PUEBI/EYD V), menghasilkan ilustrasi editorial 16:9 via Gemini AI jika foto asli tidak tersedia, dan mengunggah draf artikel ke Google Blogger.

---

## 🌟 Fitur Utama & Standar Arsitektur

1. **Mode Publikasi Draft Aman & Kapasitas 8 Draf/Run:**
   - Seluruh artikel dikirim ke Blogger dengan status **Draft** (`PUBLISH_AS_DRAFT = True`), memberikan kendali penuh kepada redaksi manusia untuk peninjauan akhir sebelum tayang.
   - Batas maksimal pemrosesan dinaikkan menjadi **8 artikel per putaran** (`MAX_POSTS_PER_RUN = 8`).
   - Dilengkapi **Kotak Catatan Redaksi** (`draft-review-box`) di baris teratas draf artikel (memuat daftar label terpilih, cakupan wilayah, tautan sumber rujukan, status gambar, jumlah kata, dan poin cek redaksi) yang dapat dihapus 1-klik sebelum dipublikasikan.

2. **Dukungan 27 Label Baku & Cakupan 33 Kabupaten/Kota Sumut:**
   Setiap artikel secara otomatis diklasifikasikan ke dalam **2 hingga 4 label** dari 27 label baku berikut:
   - **Institusional (2):** `Polda Sumut`, `Kejati Sumut`
   - **Rubrik Tematik (7):** `Kriminalitas`, `Politik`, `Ekobis`, `Wisata & Kuliner`, `Olahraga`, `Ototekno`, `Hukrimpol`
   - **Klaster Wilayah 33 Kabupaten/Kota Sumut (18):**
     1. `Medan` (Kota Medan, Belawan, Marelan, Amplas, Helvetia)
     2. `Deli Serdang` (Lubuk Pakam, Tanjung Morawa, Percut Sei Tuan, Sunggal, Pancur Batu, Kualanamu)
     3. `Binjai` (Kota Binjai)
     4. `Langkat` (Stabat, Tanjung Pura, Pangkalan Brandan, Besitang, Bahorok, Bukit Lawang)
     5. `Tebing Tinggi` (Kota Tebing Tinggi, Serdang Bedagai/Sergai, Sei Rampah, Perbaungan)
     6. `Pematangsiantar` (Kota Pematangsiantar / Siantar)
     7. `Simalungun` (Pematang Raya, Parapat, Perdagangan, Tanah Jawa, Saribudolok, Tigaras)
     8. `Karo` (Kabanjahe, Berastagi, Tigapanah, Merek, Sinabung, Gundaling)
     9. `Dairi` (Sidikalang, Pakpak Bharat, Salak, Sumbul, Tigalingga)
     10. `Samosir` (Pangururan, Tomok, Tuktuk, Simanindo, Nainggolan, Palipi, Pusuk Buhit)
     11. `Toba` (Balige, Laguboti, Porsea, Ajibata, Lumban Julu, Sigumpar)
     12. `Taput` (Tapanuli Utara, Tarutung, Siborongborong, Silangit, Pahae, Sipoholon, Muara)
     13. `Humbahas` (Humbang Hasundutan, Doloksanggul, Lintongnihuta, Baktiraja, Pollung)
     14. `Sibolga - Tapteng` (Kota Sibolga, Tapanuli Tengah, Pandan, Barus, Pinangsori, Sorkam)
     15. `Asahan` (Kisaran, Batubara, Limapuluh, Indrapura, Tanjungbalai)
     16. `Labuhanbatu` (Rantauprapat, Labura/Aek Kanopan, Labusel/Kotapinang)
     17. `Nias` (Gunungsitoli, Nias Selatan/Teluk Dalam, Nias Utara, Nias Barat)
     18. `Tapsel` (Tapanuli Selatan/Sipirok, Padangsidimpuan, Mandailing Natal/Madina/Panyabungan, Palas/Sibuhuan, Paluta/Gunung Tua)

3. **Penyeimbang Kuota Label (*Label Coverage Balancing & Greedy Diversity*):**
   - **Label Deficit Priority:** Menghitung frekuensi kemunculan masing-masing label pada 150 riwayat terakhir di `posted_history.json`. Label yang masih berfrekuensi `0` atau sedikit mendapatkan bonus skor prioritas tinggi.
   - **Targeted Query Feed Rotation:** Memuat feed utama ditambah rotasi feed query Google News berdasarkan zona wilayah dan rubrik khusus yang mengalami defisit.
   - **Greedy Diversity Selection:** Memilih 8 kandidat teratas dengan penalti in-memory sementara untuk label yang baru saja terpilih dalam batch yang sama agar dalam 1 kali eksekusi tidak didominasi satu wilayah/rubrik saja.

4. **Aturan Klasifikasi Multi-Label & Relasi Hukrimpol:**
   - Komposisi wajib 2–4 label: 1–2 Label Wilayah + 1 Rubrik Utama.
   - **Aturan Wajib `Hukrimpol`:** Jika artikel menyangkut `Kriminalitas`, `Politik`, `Polda Sumut`, atau `Kejati Sumut`, artikel wajib menyertakan label `Hukrimpol`.

5. **Mesin AI Dual-Engine (Gemini API & Groq Fallback):**
   - **Primary Engine:** Google Gemini API (`gemini-3.8-flash` via SDK `google-genai`) dengan fallback model otomatis (`gemini-2.0-flash`, `gemini-1.5-flash`).
   - **Secondary Engine:** Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, dsb.) dengan penanganan format reasoning tersembunyi.
   - **Self-Healing Repair Pass:** Menjalankan penyuntingan otomatis jika validator mendeteksi catatan kualitas sebelum memutuskan hasil akhir.

6. **Penanganan Gambar & Fallback Ilustrasi Editorial 16:9:**
   - Validasi ketat terhadap gambar sumber asli (resolusi lebar minimal `300px`, pembersihan watermark portal komersial).
   - Fallback otomatis pembuatan ilustrasi kontekstual 16:9 via Gemini Imagen 3 / Pollinations Flux (bebas teks dan filter kriminalitas netral).
   - Gambar tersimpan di `generated_images/` dan disajikan lewat CDN publik jsDelivr:
     `https://cdn.jsdelivr.net/gh/{GITHUB_REPOSITORY}@main/generated_images/{filename}`.

7. **Anti-Duplikasi & Filter Dewan Pers:**
   - **Semantic Deduplication:** Pengecekan Jaccard similarity & token overlap (ambang batas `>= 0.60`) terhadap riwayat 100 entri terakhir di `posted_history.json`.
   - **Multi-Source Story Clustering:** Menggabungkan fakta dari berbagai media berbeda untuk peristiwa yang sama.
   - **Etika Jurnalistik:** Penegakan asas praduga tak bersalah (*presumption of innocence*), larangan tegas terhadap blok "Baca Juga" fiktif, serta penghapusan frasa klise AI.

---

## 📁 Struktur Repositori

```text
boaboa-auto-news/
├── .github/
│   └── workflows/
│       └── auto_news.yml        # Workflow GitHub Actions (terjadwal setiap 3 jam, menit 25)
├── boaboa/
│   ├── __init__.py
│   ├── config.py                # Konfigurasi, 27 label baku, GEO_ALIAS_MAP, TOPIC_KEYWORD_MAP, TARGETED_QUERY_FEEDS
│   ├── extractor.py             # Ekstraksi konten artikel, dewatermarking, dan deteksi foto liputan
│   ├── history.py               # Riwayat riwayat artikel, label counts, dan anti-duplikasi semantik (Jaccard)
│   ├── html_formatter.py        # Pemformatan HTML semantik, draft-review-box berlabel, dan atribusi
│   ├── image_generator.py       # Pembuatan ilustrasi AI editorial 16:9 & kompresi ke folder lokal
│   ├── quality_guard.py         # Quality gate, normalisasi multi-label 2-4, dan pemeriksa Dewan Pers
│   ├── relevance.py             # Deteksi kandidat label awal, scoring wilayah/rubrik & clustering peristiwa
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
| `MAX_POSTS_PER_RUN`| `8` | Batas maksimum artikel per run |

---

## 📜 Lisensi & Atribusi

Proyek ini berada di bawah lisensi [MIT](LICENSE). Dikembangkan khusus untuk jaringan portal berita **BoaBoa** (`boaboa.bataktive.com`).

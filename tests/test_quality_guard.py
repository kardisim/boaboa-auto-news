import unittest

from boaboa.config import ALLOWED_LABELS
from boaboa.quality_guard import normalize_labels, sanitize_article_data, validate_article_quality

SAMPLE_SOURCE = (
    "Polres Tapanuli Tengah mengamankan seorang pria berinisial SS (45) di Jalan Sibolga-Padangsidimpuan "
    "pada Minggu (25/10/2026) sekitar pukul 04.00 WIB. Petugas menyita 234 liter Pertalite dalam enam jeriken "
    "serta 14 tabung LPG 3 kilogram dari mobil Suzuki Carry bernomor polisi BK 1510 YP yang dihentikan tim patroli. "
    "Pemeriksaan lanjutan dilakukan di Mapolres Tapteng guna menelusuri asal perolehan BBM bersubsidi tersebut dan pihak terkait. "
    "Kapolres Tapteng melalui Kasat Reskrim IPTU Dian A. Perdana menyampaikan bahwa pemeriksaan dilakukan setelah laporan warga sekitar. "
    "\"Dari hasil pemeriksaan, petugas menemukan enam jeriken berisi Pertalite serta 14 tabung LPG 3 kg,\" ujar IPTU Dian A. Perdana."
)


class TestQualityGuard(unittest.TestCase):
    def test_sanitize_removes_double_dateline_typos_and_copied_byline(self):
        raw = {
            "title": "Kemnistrian PU Gelar Kegiatan Berserajah di Sibolga - Waspada.id",
            "meta_description": (
                "<p>Kemnistrian PU mempercepat pembangunan fasilitas sanitasi terpadu bagi warga "
                "di wilayah Sibolga guna meningkatkan taraf kesehatan lingkungan masyarakat.</p>"
            ),
            "content": (
                "<h1>Subjudul Salah</h1>"
                "<p>BoaBoa.com - Jakarta, BoaBoa.com – Kemnistrian PU mempercepat pembangunan sanitasi "
                "untuk menjaga keamanann warga dan kretifitas daerah.</p>"
                "<p>Pembangunan berlangsung bertahap sepanjang tahun ini. (BoaBoa/RAS/PAI)</p>"
                "<script>alert(1)</script>"
            ),
            "labels": ["Sumatera Utara", "Hukum & Kriminal", "Sibolga", "Kategori1"],
        }
        cleaned = sanitize_article_data(raw)
        self.assertEqual(cleaned["title"], "Kementerian PU Gelar Kegiatan Bersejarah di Sibolga")
        self.assertIn("<h2>Subjudul Salah</h2>", cleaned["content"])
        self.assertNotIn("<h1>", cleaned["content"])
        self.assertNotIn("<script>", cleaned["content"])
        self.assertNotIn("BoaBoa.com", cleaned["content"])
        self.assertNotIn("(BoaBoa/RAS/PAI)", cleaned["content"])
        self.assertIn("keamanan", cleaned["content"])
        self.assertIn("kreativitas", cleaned["content"])
        self.assertEqual(
            cleaned["meta_description"],
            "Kementerian PU mempercepat pembangunan fasilitas sanitasi terpadu bagi warga di wilayah Sibolga guna meningkatkan taraf kesehatan lingkungan masyarakat.",
        )
        # 2-4 label standar dari daftar 27 master labels
        self.assertGreaterEqual(len(cleaned["labels"]), 2)
        self.assertLessEqual(len(cleaned["labels"]), 4)
        self.assertIn("Hukrimpol", cleaned["labels"])
        self.assertIn("Sibolga - Tapteng", cleaned["labels"])

    def test_normalize_labels_enforces_core_and_max_two(self):
        self.assertEqual(len(ALLOWED_LABELS), 27)
        # Input label acak/kosong selalu dilengkapi menjadi 2-4 label standar SEO
        res_acak = normalize_labels(["Kategori1", "Acak"])
        self.assertGreaterEqual(len(res_acak), 2)
        self.assertLessEqual(len(res_acak), 4)
        self.assertIn("Medan", res_acak)
        self.assertIn("Hukrimpol", res_acak)

        res_olahraga = normalize_labels(["Olahraga", "Sepak Bola"])
        self.assertGreaterEqual(len(res_olahraga), 2)
        self.assertLessEqual(len(res_olahraga), 4)
        self.assertEqual(res_olahraga[0], "Olahraga")

        res = normalize_labels(["Adat Batak", "Tapanuli", "Berita Sumut", "Medan"])
        self.assertGreaterEqual(len(res), 2)
        self.assertLessEqual(len(res), 4)
        self.assertIn("Wisata & Kuliner", res)
        self.assertIn("Taput", res)

        # Topik Ekobis
        res_ekobis = normalize_labels(["Sawit", "Pasar"])
        self.assertGreaterEqual(len(res_ekobis), 2)
        self.assertLessEqual(len(res_ekobis), 4)
        self.assertEqual(res_ekobis[0], "Ekobis")

    def test_detects_non_latin_english_overlong_title_and_bad_year(self):
        bad_article = {
            "title": "Polres Langkat Gencarkan Edukasi Keselamatan Lalu Lintas Selama Dua Pekan Bersama Warga dan Pemuda Setempat",
            "meta_description": "Ringkasan terlalu pendek.",
            "content": (
                "<h1>Judul Ganda Terlarang</h1>"
                "<p>Polres Langkat также menyerukan pentingnya keselamatan pada tahun 2024 untuk mencegah risiko失控 kendaraan.</p>"
                "<p>Petugas menilai kondisi ini regarding keselamatan dan hundreds pengguna jalan lain di Sumatera Utara.</p>"
                "<p>Program berlangsung selama dua pekan bersama warga sekitar serta para tokoh masyarakat setempat secara tertib.</p>"
            ),
            "labels": ["Berita Sumut"],
        }
        valid, issues = validate_article_quality(bad_article, SAMPLE_SOURCE, published_date="2026-11-10")
        self.assertFalse(valid)
        joined = " | ".join(issues)
        self.assertIn("Panjang judul SEO", joined)
        self.assertIn("meta_description", joined)
        self.assertIn("<h1>", joined)
        self.assertIn("non-Latin", joined)
        self.assertIn("Kata Inggris", joined)
        self.assertIn("Tahun tidak sesuai", joined)

    def test_detects_fabricated_quote_and_generic_speaker(self):
        source_no_quotes = (
            "Pemerintah Kabupaten Samosir menyalurkan bantuan stimulan kepada puluhan pelaku UMKM di Kecamatan Pangururan "
            "pada Selasa pagi. Program ini bertujuan memperkuat ekonomi keluarga di kawasan Danau Toba. "
            "Bantuan diberikan dalam bentuk peralatan usaha dan pendampingan administrasi keuangan. "
            "Pemerintah daerah menargetkan penerima bantuan dapat meningkatkan produksi secara bertahap."
        )
        fabricated = {
            "title": "Pemkab Samosir Salurkan Bantuan Stimulan untuk UMKM",
            "content": (
                "<p>Pemerintah Kabupaten Samosir resmi menyalurkan bantuan stimulan kepada pelaku usaha mikro di Pangururan untuk memperkuat daya saing ekonomi masyarakat pesisir Danau Toba.</p>"
                "<p>Penyaluran dilakukan dalam bentuk peralatan usaha serta pelatihan pengelolaan keuangan agar pelaku usaha mampu mencatat arus kas secara tertib dan transparan setiap bulan.</p>"
                "<blockquote><p>\"Bantuan ini adalah nafas baru bagi pelaku usaha di Samosir agar tidak tergerus zaman.\" - Tokoh Adat setempat</p></blockquote>"
                "<p>Program pendampingan akan dipantau secara berkala oleh dinas terkait agar manfaatnya terasa langsung bagi peningkatan kesejahteraan keluarga penerima manfaat di seluruh kecamatan.</p>"
            ),
            "labels": ["Tapanuli", "Ekobis"],
        }
        valid, issues = validate_article_quality(fabricated, source_no_quotes)
        self.assertFalse(valid)
        joined = " | ".join(issues)
        self.assertTrue("generik" in joined or "tidak memuat kutipan" in joined)

    def test_detects_ungrounded_numbers(self):
        ungrounded = {
            "title": "Polres Tapteng Amankan Pelaku Penyelundupan BBM",
            "content": (
                "<p>Kepolisian Resor Tapanuli Tengah mengamankan seorang pria di Jalan Sibolga-Padangsidimpuan pada Minggu pagi atas dugaan penyalahgunaan bahan bakar bersubsidi.</p>"
                "<p>Dalam operasi tersebut petugas menyita sekitar 3.500 liter bahan bakar serta mengamankan kerugian negara senilai 890 juta rupiah di lokasi penangkapan pada pagi hari itu.</p>"
                "<p>Saat ini tersangka beserta barang bukti telah dibawa ke markas kepolisian setempat guna proses penyidikan dan pemeriksaan lebih lanjut sesuai hukum yang berlaku di wilayah Sumatera Utara.</p>"
            ),
            "labels": ["Hukrimpol", "Tapanuli"],
        }
        valid, issues = validate_article_quality(ungrounded, SAMPLE_SOURCE)
        self.assertFalse(valid)
        self.assertIn("Angka tidak ditemukan", " | ".join(issues))

    def test_passes_clean_grounded_article(self):
        good = {
            "title": "Polres Tapteng Sita 234 Liter Pertalite dan 14 LPG",
            "meta_description": (
                "Polres Tapanuli Tengah menyita barang bukti 234 liter Pertalite dan 14 tabung LPG bersubsidi "
                "di Jalan Sibolga-Padangsidimpuan pada Minggu."
            ),
            "content": (
                "<p>Kepolisian Resor Tapanuli Tengah mengamankan seorang pria berinisial SS (45) di Jalan Sibolga-Padangsidimpuan pada Minggu (25/10/2026) sekitar pukul 04.00 WIB karena diduga menyalahgunakan bahan bakar minyak dan gas bersubsidi.</p>"
                "<p>Dalam pemeriksaan terhadap mobil Suzuki Carry bernomor polisi BK 1510 YP yang dihentikan tim patroli tersebut, petugas menyita barang bukti berupa enam jeriken berisi 234 liter Pertalite serta 14 tabung LPG ukuran 3 kilogram.</p>"
                "<h2>Pemeriksaan Lapangan Berawal dari Laporan Warga</h2>"
                "<p>Kapolres Tapanuli Tengah melalui Kasat Reskrim IPTU Dian A. Perdana menjelaskan bahwa penangkapan ini merupakan tindak lanjut cepat dari laporan masyarakat sekitar yang mencurigai aktivitas pengangkutan BBM di lokasi tersebut.</p>"
                "<blockquote><p>Dari hasil pemeriksaan, petugas menemukan enam jeriken berisi Pertalite serta 14 tabung LPG 3 kg - IPTU Dian A. Perdana, Kasat Reskrim Polres Tapteng</p></blockquote>"
                "<p>Pemeriksaan lanjutan kini dilakukan di Mapolres Tapteng guna menelusuri asal perolehan BBM bersubsidi tersebut dan menindak pihak terkait sesuai ketentuan hukum yang berlaku.</p>"
            ),
            "labels": ["Sibolga - Tapteng", "Hukrimpol"],
        }
        valid, issues = validate_article_quality(good, SAMPLE_SOURCE, published_date="2026-10-25")
        self.assertTrue(valid, msg=f"Seharusnya valid, malah muncul issues: {issues}")

    def test_sanitize_auto_trims_title_and_meta_description_at_word_boundary(self):
        overlong_title = "Pemerintah Kabupaten Samosir Percepat Pembangunan Sarana dan Prasarana Wisata Toba"
        overlong_meta = (
            "Pemerintah Kabupaten Samosir terus mempercepat pembangunan infrastruktur dan fasilitas "
            "pendukung pariwisata di seputaran Danau Toba guna menyambut kunjungan wisatawan internasional."
        )
        data = {
            "title": overlong_title,
            "meta_description": overlong_meta,
            "content": "<p>Pemerintah daerah optimis pembangunan selesai tepat waktu pada akhir tahun ini.</p>",
            "labels": ["Wisata & Kuliner", "Samosir"],
        }
        sanitized = sanitize_article_data(data)
        self.assertLessEqual(len(sanitized["title"]), 72)
        self.assertGreaterEqual(len(sanitized["title"]), 50)
        self.assertFalse(sanitized["title"].endswith(" "))
        self.assertLessEqual(len(sanitized["meta_description"]), 160)
        self.assertGreaterEqual(len(sanitized["meta_description"]), 110)
        self.assertTrue(sanitized["meta_description"].endswith("."))

    def test_check_editorial_quality_and_raw_similarity(self):
        from boaboa.quality_guard import check_editorial_quality, check_raw_similarity

        src = "Polda Sumatera Utara berhasil mengamankan dua orang terduga pelaku begal di kawasan Medan Amplas setelah pengejaran dramatis."
        gen_clean = (
            "<p>Petugas Kepolisian Daerah Sumatera Utara mengamankan dua pria yang diduga melakukan aksi pencurian dengan kekerasan di Medan.</p>"
            "<p>Penindakan hukum ini dilakukan tim patroli presisi setelah menerima laporan keresahan warga sekitar jalur lintas jalan raya.</p>"
            "<p>Kini kedua terduga pelaku telah dibawa ke kantor kepolisian setempat guna menjalani proses pemeriksaan dan penyidikan lebih lanjut.</p>"
        )
        sim = check_raw_similarity(gen_clean, src)
        self.assertLess(sim, 45.0)

        report = check_editorial_quality(
            article_data={
                "title": "Polda Sumut Bekuk Terduga Begal di Medan Amplas",
                "content": gen_clean,
                "labels": ["Hukrimpol", "Berita Sumut"],
            },
            source_text=src,
            image_url="https://cdn.example.com/foto.jpg",
            image_status="Foto Sumber (Antara)",
        )
        self.assertTrue(report["has_valid_image"])
        self.assertFalse(report["has_baca_juga"])
        self.assertTrue(report["presumption_passed"])
        self.assertIn("Lolos", report["checklist"][2])


if __name__ == "__main__":
    unittest.main()

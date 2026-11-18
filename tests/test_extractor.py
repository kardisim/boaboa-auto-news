import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

HAS_REAL_BS4 = True
try:
    import bs4  # noqa: F401
except ImportError:
    HAS_REAL_BS4 = False
    bs4_stub = types.ModuleType("bs4")
    bs4_stub.BeautifulSoup = MagicMock
    sys.modules["bs4"] = bs4_stub

try:
    import requests  # noqa: F401
except ImportError:
    req_stub = types.ModuleType("requests")
    req_stub.exceptions = SimpleNamespace(SSLError=OSError)
    sys.modules["requests"] = req_stub

try:
    import urllib3  # noqa: F401
except ImportError:
    u3_stub = types.ModuleType("urllib3")
    u3_stub.disable_warnings = lambda *a, **k: None
    u3_stub.exceptions = SimpleNamespace(InsecureRequestWarning=Warning)
    sys.modules["urllib3"] = u3_stub

from boaboa.extractor import (
    build_fetch_url,
    clean_and_dewatemark_image_url,
    clean_extracted_text,
    clean_media_name,
    count_sentences,
    extract_article_details,
    is_image_relevant_to_article,
    is_valid_image_candidate,
)


class TestExtractor(unittest.TestCase):
    def test_clean_media_name(self):
        self.assertEqual(clean_media_name("- Kementerian Agama Kota Medan"), "Kementerian Agama Kota Medan")
        self.assertEqual(clean_media_name("https://sibolgakota.go.id/"), "sibolgakota.go.id")
        self.assertEqual(clean_media_name("", "https://www.kompas.com/a/b"), "kompas.com")

    def test_build_fetch_url_adds_page_all_for_paginated_portals(self):
        self.assertEqual(
            build_fetch_url("https://medan.tribunnews.com/2026/11/10/contoh-berita"),
            "https://medan.tribunnews.com/2026/11/10/contoh-berita?page=all",
        )
        self.assertEqual(
            build_fetch_url("https://www.antaranews.com/berita/123"),
            "https://www.antaranews.com/berita/123",
        )

    def test_is_valid_image_candidate_filters_watermarks_and_small_thumbs(self):
        self.assertTrue(is_valid_image_candidate("http://samosirkab.go.id/foto-berita.jpg"))
        self.assertTrue(is_valid_image_candidate("https://intelpostnews.com/wp-content/uploads/2026/11/ImgResizer_IMG-20261112-WA0011.jpg"))
        self.assertTrue(is_valid_image_candidate("https://www.hariansib.com/cdn/uploads/images/2026/11/foto_berita.png"))
        self.assertTrue(is_valid_image_candidate("https://samosirkab.go.id/wp-content/uploads/2026/11/wakil-bupati-hadiri-forum.jpg"))
        self.assertTrue(is_valid_image_candidate("https://topmetro.news/wp-content/uploads/2026/11/creative-hub-samosir.jpg"))
        self.assertFalse(is_valid_image_candidate("https://example.com/assets/transparent.gif"))
        self.assertFalse(is_valid_image_candidate("https://example.com/spacer.gif"))
        self.assertFalse(is_valid_image_candidate("https://example.com/logo.svg"))
        self.assertFalse(is_valid_image_candidate("https://example.com/favicon.ico"))
        self.assertFalse(is_valid_image_candidate("https://example.com/wp-content/uploads/ads/banner_ad.jpg"))
        self.assertFalse(is_valid_image_candidate("https://googleads.g.doubleclick.net/pagead/imgad?id=123"))
        self.assertFalse(is_valid_image_candidate("https://awsimages.detik.net.id/api/wm/2026/11/08/foto.jpeg"))
        self.assertFalse(is_valid_image_candidate("https://c.inilah.com/reborn/2026/11/small_a_123.jpeg"))
        self.assertFalse(is_valid_image_candidate("https://beritabuana.co/wp-content/uploads/IMG_330x182.jpg"))
        self.assertFalse(is_valid_image_candidate("https://blue.kumparan.com/image/upload/l_text:Heebo_20_bold:Konten/v1/abc.jpg"))
        self.assertTrue(is_valid_image_candidate("https://cdn.antaranews.com/cache/1200x800/2026/11/08/foto.jpg"))

    def test_is_image_relevant_to_article_filters_unrelated_widgets(self):
        title = "Polisi Bekingi Dua Pengedar Sabu 11 Gram di Padangsidimpuan"
        text = (
            "Polres Padangsidimpuan menangkap dua tersangka pengedar sabu seberat 11 gram di Kota Padangsidimpuan. "
            "Kapolres AKBP Noval menegaskan proses hukum berjalan transparan tanpa pandang bulu terhadap oknum."
        )

        self.assertFalse(
            is_image_relevant_to_article(
                caption="Hari Ini MPR Rapat Gabungan Tentukan Jadwal Pemilihan Wapres Pengganti Gibran",
                alt="MPR Rapat Pemilihan Wapres",
                cand_url="https://example.com/mpr_gibran.jpg",
                article_text=text,
                article_title=title,
            )
        )

        self.assertTrue(
            is_image_relevant_to_article(
                caption="Kapolres Padangsidimpuan menggelar konferensi pers penangkapan tersangka narkoba",
                alt="Konferensi pers pengedar sabu Padangsidimpuan",
                cand_url="https://example.com/polres_padangsidimpuan.jpg",
                article_text=text,
                article_title=title,
            )
        )

    def test_clean_and_dewatemark_image_url(self):
        detik_raw = "https://awsimages.detik.net.id/api/wm/2026/11/08/wanita-tewas_169.jpeg?wid=54&w=650&v=1&t=jpeg"
        detik_clean = clean_and_dewatemark_image_url(detik_raw)
        self.assertIn("/community/media/visual/", detik_clean)
        self.assertNotIn("/api/wm/", detik_clean)
        self.assertNotIn("wid=", detik_clean)
        self.assertIn("w=1200", detik_clean)

        kompas_raw = "https://asset.kompas.com/crops/abc1234=/data/photo/2026/11/10/672fc123.jpg"
        self.assertEqual(
            clean_and_dewatemark_image_url(kompas_raw),
            "https://asset.kompas.com/data/photo/2026/11/10/672fc123.jpg",
        )

        kump_raw = "https://blue.kumparan.com/image/upload/l_text:Heebo_20_bold:Konten/v1/abc.jpg"
        self.assertEqual(
            clean_and_dewatemark_image_url(kump_raw),
            "https://blue.kumparan.com/image/upload/v1/abc.jpg",
        )

        tribun_raw = "https://cdn-1.tstatic.net/medan/foto/bank/images/crop/0x0:0x0/contoh_berita_250x150.jpg"
        self.assertEqual(
            clean_and_dewatemark_image_url(tribun_raw),
            "https://cdn-1.tstatic.net/medan/foto/bank/images/contoh_berita.jpg",
        )

        inilah_raw = "https://c.inilah.com/reborn/2026/11/small_a_123.jpeg"
        self.assertEqual(
            clean_and_dewatemark_image_url(inilah_raw),
            "https://c.inilah.com/reborn/2026/11/a_123.jpeg",
        )

    def test_clean_extracted_text_and_sentence_count(self):
        raw = (
            "Baca juga: Artikel Lainnya\n"
            "Pemerintah Kabupaten Samosir menggelar rapat koordinasi pembangunan kawasan Danau Toba pada Senin pagi.\n"
            "Rapat dihadiri oleh perwakilan dinas terkait serta tokoh masyarakat setempat di Pangururan.\n"
            "Dalam pertemuan tersebut dibahas langkah peningkatan layanan dermaga penyeberangan wisatawan.\n"
            "Copyright 2026 Portal Berita\n"
            "Pemerintah berharap penataan tersebut meningkatkan kenyamanan pengunjung menjelang akhir tahun.\n"
        )
        cleaned = clean_extracted_text(raw)
        self.assertNotIn("Baca juga", cleaned)
        self.assertNotIn("Copyright", cleaned)
        self.assertEqual(count_sentences(cleaned), 4)

    @unittest.skipUnless(HAS_REAL_BS4, "BeautifulSoup4 tidak terpasang di environment lokal")
    def test_extract_article_details_with_mock_html(self):
        sample_html = """
        <html><head>
          <meta property="og:image" content="https://cdn.example.com/hero-1200x800.jpg" />
        </head><body>
          <div class="header-content"><p>Menu singkat navigasi situs berita daerah.</p></div>
          <article class="article-detail">
            <p>Kepolisian Resor Tapanuli Utara melakukan pengamanan jalur wisata menuju Balige sejak pagi hari.</p>
            <p>Sebanyak 45 personel dikerahkan untuk mengatur arus lalu lintas dan mengantisipasi kemacetan.</p>
            <p>Baca juga: Jadwal Feri Danau Toba Terbaru</p>
            <p>Kapolres menyampaikan bahwa rekayasa lalu lintas dilakukan secara situasional mengikuti kepadatan kendaraan.</p>
            <p>Warga diimbau mematuhi rambu serta arahan petugas di lapangan demi keselamatan bersama.</p>
          </article>
        </body></html>
        """
        res = extract_article_details(
            "https://contohmedia.id/berita/taput",
            html_override=sample_html,
            validate_image=False,
        )
        self.assertGreater(res["char_count"], 300)
        self.assertEqual(res["sentence_count"], 4)
        self.assertEqual(res["image_url"], "https://cdn.example.com/hero-1200x800.jpg")
        self.assertNotIn("Baca juga", res["text"])


if __name__ == "__main__":
    unittest.main()

import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

try:
    import bs4  # noqa: F401
except ImportError:
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

from boaboa.history import title_tokens
from boaboa.html_formatter import build_ecosystem_callout, format_final_html


class TestHtmlFormatter(unittest.TestCase):
    def test_format_final_html_clean_structure_and_internal_links(self):
        article = {
            "title": "Tradisi Joting Batak Toba Kembali Disosialisasikan",
            "content": (
                "<p>Masyarakat Batak Toba di Kabupaten Samosir kembali mengangkat tradisi joting sebagai warisan budaya lisan.</p>"
                "<h2>Pelestarian Tradisi Lisan</h2>"
                "<blockquote><p>\"Tradisi ini mengajarkan tata krama bertutur.\" - Manahan Sihotang, Tokoh Budaya</p></blockquote>"
                "<p>Para pelajar diajak mempelajari makna adat istiadat melalui kegiatan sanggar desa secara rutin.</p>"
            ),
            "labels": ["Budaya & Hata", "Tapanuli"],
        }
        posts_index = [
            {
                "title": "Dongan Partubu dan Dongan Parhundul dalam Adat Batak Toba",
                "url": "https://boaboa.bataktive.com/2026/11/dongan-partubu.html",
                "labels": ["Budaya & Hata"],
                "tokens": title_tokens("Dongan Partubu dan Dongan Parhundul dalam Adat Batak Toba"),
            },
            {
                "title": "Jadwal Pertandingan Liga Inggris Pekan Ini",
                "url": "https://boaboa.bataktive.com/2026/11/liga-inggris.html",
                "labels": ["Berita Sumut"],
                "tokens": title_tokens("Jadwal Pertandingan Liga Inggris Pekan Ini"),
            },
        ]

        html_out = format_final_html(
            article_data=article,
            image_url="https://cdn.example.com/foto.jpg",
            source_media_name="- Antara Sumut",
            real_url="https://sumut.antaranews.com/berita/123/joting",
            posts_index=posts_index,
            image_width=1280,
            image_height=720,
        )

        self.assertNotIn("<strong>BoaBoa.com</strong> - ", html_out)
        self.assertNotIn("<strong>Bataktive.com</strong> - ", html_out)
        self.assertTrue(
            html_out.startswith('<div class="draft-review-box"')
            or html_out.startswith('<figure class="separator"')
            or html_out.startswith('<div class="separator"')
        )
        self.assertIn('class="draft-review-box"', html_out)
        self.assertIn("Catatan Redaksi", html_out)
        self.assertIn('class="separator"', html_out)
        self.assertIn('data-original-width="1280"', html_out)
        self.assertIn('data-original-height="720"', html_out)
        self.assertIn("Foto/Ilustrasi: Antara Sumut", html_out)
        self.assertIn("<p>Masyarakat Batak Toba", html_out)
        # Atribut CWV gambar hero: width/height eksplisit & fetchpriority high
        self.assertIn('width="1280" height="720"', html_out)
        self.assertIn('fetchpriority="high"', html_out)
        self.assertNotIn('loading="lazy"', html_out)
        # Kutipan di blockquote bersih tanpa tanda kutip ganda berlebih
        self.assertIn("<p>Tradisi ini mengajarkan tata krama bertutur. - Manahan Sihotang, Tokoh Budaya</p>", html_out)
        # Sumber rujukan memakai URL situs asli
        self.assertIn('href="https://sumut.antaranews.com/berita/123/joting"', html_out)
        self.assertIn("font-size: 11px", html_out)
        self.assertIn("Sumber rujukan:", html_out)
        self.assertNotIn("liga-inggris.html", html_out)

    def test_ecosystem_callout_supports_budaya_and_wisata(self):
        callout = build_ecosystem_callout(["Budaya & Hata"], "Pembahasan musyawarah keluarga.")
        self.assertIn("https://hata.bataktive.com/partuturan", callout)
        self.assertIn("https://hata.bataktive.com/umpasa", callout)

    def test_format_final_html_inserts_multiple_editorial_images(self):
        article = {
            "title": "Gebrakan Pariwisata Danau Toba",
            "content": "<p>Paragraf 1 berita pembuka.</p><h2>Subjudul 1</h2><p>Paragraf 2 isi.</p><p>Paragraf 3 keterangan.</p>",
            "labels": ["Wisata & Kuliner"],
        }
        extra_imgs = [
            {"url": "https://cdn.example.com/foto2.jpg", "caption": "Suasana Dermaga Balige"},
        ]
        html_out = format_final_html(
            article_data=article,
            image_url="https://cdn.example.com/foto1.jpg",
            source_media_name="Antara",
            real_url="https://sumut.antaranews.com/berita/1",
            additional_images=extra_imgs,
        )
        self.assertIn("https://cdn.example.com/foto1.jpg", html_out)
        self.assertIn("https://cdn.example.com/foto2.jpg", html_out)
        self.assertIn("Suasana Dermaga Balige", html_out)
        self.assertIn('loading="lazy"', html_out)


if __name__ == "__main__":
    unittest.main()

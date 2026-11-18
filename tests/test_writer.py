import json
import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

try:
    import groq  # noqa: F401
except ImportError:
    groq_stub = types.ModuleType("groq")
    groq_stub.Groq = MagicMock
    sys.modules["groq"] = groq_stub

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

from boaboa.writer import (
    _call_groq_json,
    _parse_json_response,
    get_best_groq_model,
    get_groq_model_candidates,
    rewrite_news,
)

LONG_SOURCE = (
    "Pemerintah Kabupaten Tapanuli Utara mempercepat penataan kawasan wisata rohani dan alam di sekitar Danau Toba. "
    "Kepala Dinas Pariwisata Tapanuli Utara menyampaikan bahwa perbaikan akses jalan serta fasilitas dermaga "
    "ditargetkan rampung sebelum masa libur akhir tahun mendatang guna menyambut lonjakan kunjungan wisatawan nusantara. "
    "Program ini juga melibatkan pelaku usaha mikro lokal agar wisatawan dapat menikmati kuliner khas daerah dengan nyaman dan tertib. "
    "Selain membenahi jalur pejalan kaki dan area parkir, pemerintah daerah menyiapkan pusat informasi perjalanan di sekitar Tarutung. "
    "\"Penataan ini bukan hanya soal fisik, melainkan bagaimana warga ikut merasakan manfaat ekonomi langsung,\" "
    "ujar Rudi Simanjuntak, Kepala Dinas Pariwisata Tapanuli Utara, di Tarutung."
)


class TestWriter(unittest.TestCase):
    def test_get_best_groq_model_ignores_small_models_when_flagship_available(self):
        client = MagicMock()
        client.models.list.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(id="whisper-large-v3"),
                SimpleNamespace(id="llama-3.1-8b-instant"),
                SimpleNamespace(id="qwen/qwen3-32b"),
                SimpleNamespace(id="llama-3.3-70b-versatile"),
            ]
        )
        chosen = get_best_groq_model(client)
        self.assertEqual(chosen, "llama-3.3-70b-versatile")

    def test_hard_gate_rejects_short_source_without_calling_llm(self):
        client = MagicMock()
        with self.assertRaises(ValueError):
            rewrite_news(
                groq_client=client,
                model_name="llama-3.3-70b-versatile",
                title="Berita Singkat",
                full_text_content="Hanya satu baris judul saja.",
                source_media="Media.id",
                source_url="https://example.com/1",
            )
        client.chat.completions.create.assert_not_called()

    def test_self_healing_repair_pass_fixes_foreign_leakage(self):
        bad_draft = {
            "title": "Pemkab Taput Percepat Penataan Wisata Danau Toba",
            "meta_description": (
                "Pemkab Tapanuli Utara mempercepat penataan fasilitas dermaga dan jalan akses kawasan wisata "
                "Danau Toba menjelang libur akhir tahun ini."
            ),
            "content": (
                "<p>Pemerintah Kabupaten Tapanuli Utara mempercepat penataan kawasan wisata Danau Toba untuk menghadapi libur akhir tahun.</p>"
                "<p>Upaya ini dilakukan regarding peningkatan fasilitas dermaga dan jalan akses bagi wisatawan serta warga lokal.</p>"
                "<h2>Keterlibatan Pelaku Usaha Mikro</h2>"
                "<p>Pelaku UMKM lokal dilibatkan untuk menyajikan kuliner khas daerah agar perekonomian warga di sekitar kawasan wisata turut bertumbuh.</p>"
                "<p>Dinas Pariwisata menargetkan seluruh pekerjaan fisik dapat selesai tepat waktu dengan mutu terjaga.</p>"
            ),
            "labels": ["Tapanuli", "Wisata & Kuliner"],
        }
        repaired_draft = {
            "title": "Pemkab Tapanuli Utara Percepat Penataan Wisata Danau Toba",
            "meta_description": (
                "Pemkab Tapanuli Utara mempercepat penataan fasilitas dermaga dan akses jalan kawasan wisata "
                "Danau Toba menjelang libur akhir tahun ini."
            ),
            "content": (
                "<p>Pemerintah Kabupaten Tapanuli Utara mempercepat penataan kawasan wisata rohani dan alam di sekitar Danau Toba menjelang masa libur akhir tahun mendatang guna menyambut lonjakan kunjungan wisatawan nusantara.</p>"
                "<p>Upaya penataan ini difokuskan pada perbaikan akses jalan menuju lokasi wisata serta peningkatan fasilitas dermaga agar arus kunjungan wisatawan berjalan aman dan lancar.</p>"
                "<h2>Keterlibatan Pelaku Usaha Mikro Lokal</h2>"
                "<p>Selain membenahi infrastruktur fisik, pemerintah daerah turut melibatkan pelaku usaha mikro lokal agar wisatawan dapat menikmati sajian kuliner khas daerah dengan nyaman dan tertib di sekitar kawasan kunjungan.</p>"
                "<blockquote><p>Penataan ini bukan hanya soal fisik, melainkan bagaimana warga ikut merasakan manfaat ekonomi langsung - Rudi Simanjuntak, Kepala Dinas Pariwisata Tapanuli Utara</p></blockquote>"
                "<p>Pemerintah daerah turut menyiapkan jalur pejalan kaki, area parkir, serta pusat informasi perjalanan di Tarutung agar wisatawan memperoleh panduan lengkap dengan standar kenyamanan terbaik selama berlibur.</p>"
            ),
            "labels": ["Tapanuli", "Wisata & Kuliner", "Berita Sumut"],
        }

        client = MagicMock()
        client.chat.completions.create.side_effect = [
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(bad_draft)))]),
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(repaired_draft)))]),
        ]

        result = rewrite_news(
            groq_client=client,
            model_name="llama-3.3-70b-versatile",
            title="Pemkab Taput Percepat Penataan Wisata",
            full_text_content=LONG_SOURCE,
            source_media="Antara Sumut",
            source_url="https://example.com/taput",
        )
        self.assertEqual(client.chat.completions.create.call_count, 2)
        self.assertNotIn("regarding", result["content"].lower())
        self.assertEqual(result["labels"], ["Tapanuli", "Wisata & Kuliner"])

    def test_parse_json_response_cleans_think_tags_and_trailing_commas(self):
        raw_with_think = (
            "<think>Analyzing news facts and SEO standards...</think>\n"
            "```json\n"
            '{\n  "title": "Uji Coba Judul Berita Terkini Danau Toba",\n  "meta_description": "Ringkasan deskripsi penelusuran.",\n  "labels": ["Wisata & Kuliner",],\n}\n'
            "```"
        )
        parsed = _parse_json_response(raw_with_think)
        self.assertEqual(parsed["title"], "Uji Coba Judul Berita Terkini Danau Toba")
        self.assertEqual(parsed["labels"], ["Wisata & Kuliner"])

    def test_call_groq_json_sets_hidden_reasoning_for_reasoning_models(self):
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"status": "ok"}'))]
        )
        _call_groq_json(
            groq_client=client,
            model_name="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "test"}],
        )
        _, kwargs = client.chat.completions.create.call_args
        self.assertIn("extra_body", kwargs)
        self.assertEqual(kwargs["extra_body"].get("reasoning_format"), "hidden")

    def test_call_groq_json_falls_back_to_next_model_on_error(self):
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            RuntimeError("Groq 400 json_validate_failed"),
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"status": "ok"}'))]),
        ]
        res = _call_groq_json(
            groq_client=client,
            model_name=["openai/gpt-oss-120b", "llama-3.3-70b-versatile"],
            messages=[{"role": "user", "content": "test"}],
            max_retries=2,
        )
        self.assertEqual(res, {"status": "ok"})
        self.assertEqual(client.chat.completions.create.call_count, 2)
        call_models = [c.kwargs.get("model") for c in client.chat.completions.create.call_args_list]
        self.assertEqual(call_models, ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"])

    def test_get_groq_model_candidates_prioritizes_flagship_instruct(self):
        client = MagicMock()
        client.models.list.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(id="openai/gpt-oss-120b"),
                SimpleNamespace(id="llama-3.1-8b-instant"),
                SimpleNamespace(id="llama-3.3-70b-versatile"),
            ]
        )
        candidates = get_groq_model_candidates(client)
        self.assertEqual(candidates[0], "llama-3.3-70b-versatile")
        self.assertIn("openai/gpt-oss-120b", candidates)

    def test_build_system_instruction_contains_dynamic_headline_hook(self):
        from boaboa.writer import _build_system_instruction

        prompt = _build_system_instruction()
        self.assertIn("FORMULA JUDUL BER-HOOK KUAT", prompt)
        self.assertIn("DAFTAR FRASA KLISE TERLARANG", prompt)
        self.assertIn("FORMULA KONTRAS / KEJUTAN / UNIK", prompt)
        self.assertIn('"hook_angle"', prompt)


if __name__ == "__main__":
    unittest.main()

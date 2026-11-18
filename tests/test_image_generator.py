import unittest

from boaboa.image_generator import (
    build_pollinations_url,
    clean_image_prompt,
    generate_contextual_illustration,
)


class TestImageGenerator(unittest.TestCase):
    def test_clean_image_prompt_custom(self):
        raw = '  "Editorial documentary photo of high school marching band in Padangsidimpuan"  '
        cleaned = clean_image_prompt(raw)
        self.assertEqual(
            cleaned,
            "Editorial documentary photo of high school marching band in Padangsidimpuan",
        )

    def test_clean_image_prompt_auto_fallback_from_title(self):
        cleaned = clean_image_prompt(
            "",
            title="Paskibra MAN 1 Padangsidimpuan Raih Prestasi",
            labels=["Tapanuli"],
        )
        self.assertIn("Editorial documentary photo", cleaned)
        self.assertIn("Padangsidimpuan", cleaned)
        self.assertIn("Tapanuli", cleaned)

    def test_build_pollinations_url_format(self):
        prompt = "Police press conference in North Sumatra"
        url = build_pollinations_url(prompt)
        self.assertTrue(url.startswith("https://image.pollinations.ai/prompt/"))
        self.assertIn("width=1200", url)
        self.assertIn("height=675", url)
        self.assertIn("model=flux", url)
        self.assertIn("nologo=true", url)

    def test_generate_contextual_illustration_returns_expected_structure(self):
        result = generate_contextual_illustration(
            image_prompt="High school ceremony in North Sumatra",
            title="Upacara Sekolah",
            labels=["Berita Sumut"],
            verify_remote=False,
        )
        self.assertIsInstance(result, dict)
        self.assertTrue(result["is_ai"])
        self.assertTrue(
            result["url"].startswith("https://cdn.jsdelivr.net/gh/")
            or result["url"].startswith("https://image.pollinations.ai/prompt/")
        )
        self.assertEqual(result["caption"], "Ilustrasi: Dokumentasi Konseptual Redaksi BoaBoa")


if __name__ == "__main__":
    unittest.main()

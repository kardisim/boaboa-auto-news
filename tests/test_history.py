import json
import os
import tempfile
import unittest

from boaboa.history import (
    canonicalize_url,
    is_duplicate_story,
    load_history,
    make_history_record,
    save_history,
    strip_media_suffix,
    titles_similar,
)


class TestHistory(unittest.TestCase):
    def test_strip_media_suffix(self):
        self.assertEqual(
            strip_media_suffix("Panda Nababan Dimakamkan di Siborongborong - Inilah.com"),
            "Panda Nababan Dimakamkan di Siborongborong",
        )

    def test_canonicalize_url_strips_tracking_params(self):
        u1 = "https://www.Kompas.com/read/2026/11/10/test/?utm_source=google&page=all"
        u2 = "https://www.kompas.com/read/2026/11/10/test?page=all"
        self.assertEqual(canonicalize_url(u1), canonicalize_url(u2))

    def test_cross_media_story_deduplication(self):
        t1 = "Putra: Jenazah Panda Nababan Dimakamkan Kamis di Siborongborong dengan Adat Batak - gesuri.id"
        t2 = "Jenazah Panda Nababan Dimakamkan di Siborongborong Secara Adat - Tribunnews.com"
        self.assertTrue(titles_similar(t1, t2))

        t3 = "ASDP Resmi Terapkan Diskon 100% Tarif Pelabuhan Ajibata-Ambarita - beritabuana.co"
        self.assertFalse(titles_similar(t1, t3))

    def test_legacy_and_dict_history_compatibility(self):
        history = [
            "https://news.google.com/rss/articles/ABC123?oc=5",
            make_history_record(
                "https://news.google.com/rss/articles/DEF456?oc=5",
                "https://www.kompas.com/berita/panda-nababan?utm_source=gn",
                "Panda Nababan Dimakamkan di Siborongborong Secara Adat - Kompas.com",
                "Kompas.com",
            ),
        ]
        dup1, _ = is_duplicate_story("https://news.google.com/rss/articles/ABC123?oc=5", "Judul lain", history)
        self.assertTrue(dup1)

        dup2, _ = is_duplicate_story(
            "https://news.google.com/rss/articles/XYZ999?oc=5",
            "Jenazah Panda Nababan Dimakamkan di Siborongborong Secara Adat - Inilah.com",
            history,
        )
        self.assertTrue(dup2)

        dup3, _ = is_duplicate_story(
            "https://news.google.com/rss/articles/NEW111?oc=5",
            "Topik Baru Wisata Danau Toba - Waspada.id",
            history,
            real_url="https://www.kompas.com/berita/panda-nababan",
        )
        self.assertTrue(dup3)

    def test_load_and_save_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hist.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(["https://news.google.com/rss/articles/OLD1?oc=5"], f)
            loaded = load_history(path)
            self.assertEqual(len(loaded), 1)
            loaded.append(make_history_record("https://news.google.com/2", "https://example.com/2", "Judul Dua", "Media"))
            save_history(loaded, path)
            reloaded = load_history(path)
            self.assertEqual(len(reloaded), 2)

    def test_jaccard_similarity_and_semantic_deduplication(self):
        from boaboa.history import calculate_jaccard_similarity

        t1 = "Polda Sumut Tangkap Pelaku Curanmor di Medan Amplas"
        t2 = "Polda Sumut Ringkus Pelaku Curanmor di Wilayah Medan Amplas"
        sim = calculate_jaccard_similarity(t1, t2)
        self.assertGreaterEqual(sim, 0.60)

        history = [
            make_history_record(
                "https://news.google.com/old",
                "https://media.com/old",
                t1,
                "Media A",
            )
        ]
        is_dup, reason = is_duplicate_story("https://news.google.com/new", t2, history)
        self.assertTrue(is_dup)
        self.assertIn("semantik", reason.lower())

    def test_get_label_counts_tracks_all_allowed_labels(self):
        from boaboa.config import ALLOWED_LABELS
        from boaboa.history import get_label_counts

        history = [
            make_history_record("https://n1", "https://m1", "Judul 1", "Media 1", labels=["Medan", "Ekobis"]),
            make_history_record("https://n2", "https://m2", "Judul 2", "Media 2", labels=["Toba", "Wisata & Kuliner"]),
            {"labels": ["Medan", "Hukrimpol"]},
        ]
        counts = get_label_counts(history)
        self.assertEqual(len(counts), len(ALLOWED_LABELS))
        self.assertEqual(counts["Medan"], 2)
        self.assertEqual(counts["Ekobis"], 1)
        self.assertEqual(counts["Toba"], 1)
        self.assertEqual(counts["Wisata & Kuliner"], 1)
        self.assertEqual(counts["Hukrimpol"], 1)
        self.assertEqual(counts["Nias"], 0)


if __name__ == "__main__":
    unittest.main()

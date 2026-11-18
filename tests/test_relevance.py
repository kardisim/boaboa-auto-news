import unittest

from boaboa.relevance import cluster_candidate_stories, score_candidate


class TestRelevance(unittest.TestCase):
    def test_rejects_false_positive_jemput_bola_bekasi(self):
        score, _ = score_candidate(
            "Jemput Bola, Bupati Asep Serukan Perusahaan Salurkan CSR untuk Warga Kabupaten Bekasi - bekasikab",
            "bekasikab",
            base_score=1,
        )
        self.assertLess(score, 1)

    def test_rejects_unrelated_regional_sports(self):
        score, _ = score_candidate(
            "Sepak Bola Putri Depok Alihkan Fokus ke Kabupaten Karawang Usai Kalah Tipis dari Bogor - Pemerintah Kota Depok",
            "Pemerintah Kota Depok",
            base_score=1,
        )
        self.assertLess(score, 1)

    def test_rejects_video_only_items(self):
        score, _ = score_candidate(
            "Video Mendiang Panda Nababan akan Dimakamkan di Siborongborong - 20detik",
            "20detik",
            base_score=4,
        )
        self.assertLess(score, 1)

    def test_rejects_ugc_opinion_blogs(self):
        score, reason = score_candidate(
            "Cita-Cita Sumatera: Persatuan dan Kesetaraan Jiwa - Kompasiana.com",
            "Kompasiana.com",
            base_score=4,
            url="https://www.kompasiana.com/user/post123",
        )
        self.assertLess(score, 1)
        self.assertIn("opini", reason.lower())

    def test_accepts_batak_toba_and_sumut_news(self):
        score1, _ = score_candidate(
            "Tradisi Joting Batak Toba Terancam Hilang Tergerus Zaman, Ini Kata Antropolog - Bisnis.com",
            "Bisnis.com",
            base_score=4,
        )
        self.assertGreaterEqual(score1, 7)

        score2, _ = score_candidate(
            "Pemkab Samosir Salurkan Bantuan Stimulan - Waspada.id",
            "Waspada.id",
            base_score=4,
        )
        self.assertGreaterEqual(score2, 7)

        score3, _ = score_candidate(
            "Jadwal Timnas Indonesia vs Filipina di Kualifikasi Piala Asia U-17 - CNN Indonesia",
            "CNN Indonesia",
            base_score=1,
        )
        self.assertLess(score3, 1)

        score_solok, _ = score_candidate(
            "Resolusi Ekonomi Daerah dan Pembangunan Wisata di Kabupaten Toba - Waspada.id",
            "Waspada.id",
            base_score=4,
        )
        self.assertGreaterEqual(score_solok, 7)

        # PSMS Medan diterima untuk kanal Olahraga
        score_psms, reason_psms = score_candidate(
            "PSMS Medan Matangkan Persiapan Hadapi Laga Kandang di Stadion Teladan - Sumut Pos",
            "Sumut Pos",
            base_score=2,
        )
        self.assertGreaterEqual(score_psms, 5)
        self.assertIn("olahraga_sumut", reason_psms)

    def test_accepts_local_peristiwa_and_crime_news(self):
        score_kriminal, reason = score_candidate(
            "Polres Tapteng Bekuk Pengedar Sabu di Sibolga",
            "Tribrata News",
            base_score=2,
        )
        self.assertGreaterEqual(score_kriminal, 6)
        self.assertIn("hukrimpol", reason)

        score_laka, reason_laka = score_candidate(
            "Kecelakaan Truk dan Minibus di Jalinsum Tarutung, Dua Korban Dievakuasi",
            "Harian SIB",
            base_score=2,
        )
        self.assertGreaterEqual(score_laka, 6)

    def test_cluster_candidate_stories(self):
        candidates = [
            {
                "title": "Polres Simalungun Tangkap Pengedar Narkoba di Perdagangan",
                "link": "https://source1.com/berita1",
                "source_media": "Media A",
                "score": 8,
            },
            {
                "title": "Polres Simalungun Amankan Pengedar Narkoba di Daerah Perdagangan",
                "link": "https://source2.com/berita2",
                "source_media": "Media B",
                "score": 7,
            },
            {
                "title": "Pemkab Samosir Resmikan Jembatan Baru di Pangururan",
                "link": "https://source3.com/berita3",
                "source_media": "Media C",
                "score": 9,
            },
        ]
        clustered = cluster_candidate_stories(candidates, similarity_threshold=0.50)
        self.assertEqual(len(clustered), 2)
        narkoba_item = next(c for c in clustered if "Simalungun" in c["title"])
        self.assertEqual(len(narkoba_item.get("clustered_sources", [])), 1)
        self.assertEqual(narkoba_item["clustered_sources"][0]["source_media"], "Media B")

    def test_detect_candidate_labels_geo_and_mandatory_hukrimpol(self):
        from boaboa.relevance import detect_candidate_labels

        labels1 = detect_candidate_labels("Polda Sumut Tangkap Pelaku Begal di Belawan")
        self.assertIn("Medan", labels1)
        self.assertIn("Polda Sumut", labels1)
        self.assertIn("Kriminalitas", labels1)
        self.assertIn("Hukrimpol", labels1)

        labels2 = detect_candidate_labels("Festival Danau Toba dan Kuliner Andaliman di Balige")
        self.assertIn("Toba", labels2)
        self.assertIn("Wisata & Kuliner", labels2)
        self.assertNotIn("Hukrimpol", labels2)

        labels3 = detect_candidate_labels("Panen Raya Padi dan Harga Beras di Kisaran Asahan")
        self.assertIn("Asahan", labels3)
        self.assertIn("Ekobis", labels3)


if __name__ == "__main__":
    unittest.main()

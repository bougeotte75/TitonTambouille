import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tambouille import config, journal


class TestJournal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        config.utiliser_dossier(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ajout_et_relecture(self):
        journal.ajouter("Dahl trop liquide.", maintenant=datetime(2026, 11, 4, 20, 45))
        journal.ajouter("Moutabal fumé.", liens=[journal.Lien("https://exemple.fr/m", "Recette")],
                        maintenant=datetime(2026, 11, 5, 13, 10))
        journal.ajouter("Café.", maintenant=datetime(2026, 11, 5, 16, 0))
        entrees = journal.lire()
        self.assertEqual([(e.jour, e.heure) for e in entrees],
                         [("2026-11-04", "20:45"), ("2026-11-05", "13:10"), ("2026-11-05", "16:00")])
        self.assertEqual(entrees[1].liens[0].url, "https://exemple.fr/m")
        contenu = config.F_JOURNAL.read_text(encoding="utf-8")
        self.assertEqual(contenu.count("## 2026-11-05"), 1)     # un seul titre par jour

    def test_texte_qui_ressemble_a_une_balise(self):
        texte = "## pas un jour\n[pas un lien](https://exemple.fr)\n\\déjà échappé\nfin"
        journal.ajouter(texte, maintenant=datetime(2026, 11, 5, 9, 0))
        entrees = journal.lire()
        self.assertEqual(len(entrees), 1)
        self.assertEqual(entrees[0].texte, texte)
        self.assertEqual(entrees[0].liens, [])

    def test_photo(self):
        config.DOSSIER_PHOTOS.mkdir(parents=True)
        (config.DOSSIER_PHOTOS / "a.jpg").write_bytes(b"x")
        journal.ajouter("", photos=[journal.Photo("photos/a.jpg", "le [moutabal]")],
                        maintenant=datetime(2026, 11, 5, 9, 0))
        e = journal.lire()[0]
        self.assertEqual(e.photos[0].fichier, "photos/a.jpg")
        self.assertEqual(e.photos[0].legende, "le (moutabal)")

    def test_refus(self):
        with self.assertRaises(journal.ErreurEntree):
            journal.ajouter("   ")
        with self.assertRaises(journal.ErreurEntree):
            journal.ajouter("x", liens=[journal.Lien("javascript:alert(1)")])
        with self.assertRaises(journal.ErreurEntree):
            journal.ajouter("x", photos=[journal.Photo("photos/../../secret.jpg")])
        with self.assertRaises(journal.ErreurEntree):
            journal.ajouter("x", photos=[journal.Photo("photos/absente.jpg")])

    def test_fichier_modifie_a_la_main(self):
        config.F_JOURNAL.write_text("Notes libres en tête\n\n## 2026-11-01\n### 08:00\nPain perdu.\n", encoding="utf-8")
        journal.ajouter("Suite.", maintenant=datetime(2026, 11, 1, 12, 0))
        entrees = journal.lire()
        self.assertEqual([e.texte for e in entrees], ["Pain perdu.", "Suite."])
        self.assertTrue(config.F_JOURNAL.read_text(encoding="utf-8").startswith("Notes libres en tête"))


if __name__ == "__main__":
    unittest.main()

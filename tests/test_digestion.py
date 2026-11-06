import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from tambouille import config, digestion, journal, stockage


class TestDigestion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        config.utiliser_dossier(Path(self.tmp.name))
        journal.ajouter("Sablés de maman : 100 g de farine, 50 g de beurre, 100 g de sucre.",
                        maintenant=datetime(2026, 10, 12, 16, 0))
        journal.ajouter("Trop sucrés, 80 g de sucre la prochaine fois. M adore.",
                        maintenant=datetime(2026, 10, 13, 9, 0))
        self.k1, self.k2 = [k for k, _ in digestion.a_digerer()]

    def tearDown(self):
        self.tmp.cleanup()

    def ops(self):
        return [
            {"type": "recette", "origine": self.k1, "id": "sables-maman", "nom": "Sablés de maman", "categorie": "Desserts"},
            {"type": "recette_source", "origine": self.k1, "id": "sables-maman",
             "source": {"titre": "maman", "date": "2026-10-12"},
             "ingredients": ["100 g de farine", "50 g de beurre", "100 g de sucre"], "etapes": []},
            {"type": "recette_cuisinee", "origine": self.k1, "id": "sables-maman", "date": "2026-10-12"},
            {"type": "recette_correction", "origine": self.k2, "id": "sables-maman", "ingredient": "sucre",
             "ancien": "100 g", "nouveau": "80 g", "date": "2026-10-13"},
            {"type": "avis", "origine": self.k2, "membre": "M", "sujet": "sables-maman", "niveau": 3, "date": "2026-10-13"},
            {"type": "avis", "origine": self.k2, "membre": "M", "sujet": "emmental", "niveau": 3, "date": "2026-10-13", "note": "adore"},
            {"type": "lieu", "origine": self.k2, "id": "sur-les-quais", "nom": "Sur les Quais", "type_lieu": "commerce"},
            {"type": "lieu_mention", "origine": self.k2, "id": "sur-les-quais", "date": "2026-10-13", "texte": "confiture"},
        ]

    def test_application_complete(self):
        resumes = digestion.appliquer(self.ops())
        self.assertEqual(len(resumes), 8)
        r = digestion.lire_onglet("recettes")["recettes"][0]
        sucre = r["ingredients"][2]
        self.assertEqual(sucre, {"texte": "de sucre", "correction": {"ancien": "100 g", "nouveau": "80 g", "date": "2026-10-13"}})
        self.assertEqual((r["fois"], r["derniere"], r["foyer"]), (1, "2026-10-12", {"M": 3}))
        foyer = digestion.lire_onglet("foyer")
        self.assertEqual(next(m for m in foyer["membres"] if m["initiale"] == "M")["gouts"][0]["aliment"], "emmental")
        self.assertEqual(digestion.a_digerer(), [])
        # Après une digestion, plus d'exemples : les vraies données, même vides.
        o = stockage.lire_onglets()
        self.assertEqual(o["exemples"], [])
        self.assertEqual(o["idees"], {"idees": []})

    def test_tout_ou_rien(self):
        mauvais = self.ops() + [{"type": "recette_note", "id": "inconnue", "date": "2026-10-13", "texte": "x"}]
        with self.assertRaises(digestion.ErreurDigestion):
            digestion.appliquer(mauvais)
        self.assertFalse((config.DOSSIER_DONNEES / "recettes.json").exists())
        self.assertEqual(len(digestion.a_digerer()), 2)

    def test_essai_ne_modifie_rien(self):
        digestion.appliquer(self.ops(), essai=True)
        self.assertFalse((config.DOSSIER_DONNEES / "recettes.json").exists())

    def test_annuler(self):
        digestion.appliquer(self.ops()[:3], maintenant=datetime(2026, 10, 14, 8, 0, 0))
        digestion.appliquer(self.ops()[3:], maintenant=datetime(2026, 10, 14, 8, 0, 1))
        digestion.annuler_derniere()
        r = digestion.lire_onglet("recettes")["recettes"][0]
        self.assertNotIn("correction", r["ingredients"][2])
        self.assertFalse((config.DOSSIER_DONNEES / "lieux.json").exists())
        self.assertEqual([k for k, _ in digestion.a_digerer()], [self.k2])
        digestion.annuler_derniere()
        self.assertFalse((config.DOSSIER_DONNEES / "recettes.json").exists())
        with self.assertRaises(digestion.ErreurDigestion):
            digestion.annuler_derniere()

    def test_entree_modifiee_redevient_a_digerer(self):
        digestion.marquer_digerees([self.k1, self.k2])
        self.assertEqual(digestion.a_digerer(), [])
        texte = config.F_JOURNAL.read_text(encoding="utf-8").replace("M adore.", "M adore vraiment.")
        config.F_JOURNAL.write_text(texte, encoding="utf-8")
        self.assertEqual(len(digestion.a_digerer()), 1)

    def test_refus(self):
        for op in [{"type": "inconnu"}, {"type": "recette", "id": "Avec Espaces", "nom": "x"},
                   {"type": "avis", "membre": "Z", "sujet": "x", "niveau": 2, "date": "2026-01-01"},
                   {"type": "lieu", "id": "x", "nom": "x", "type_lieu": "boulangerie"}]:
            with self.assertRaises(digestion.ErreurDigestion):
                digestion.appliquer([op])

    def test_preferences_ardoise(self):
        a = digestion.enregistrer_preferences_ardoise({"midis_semaine": True}, "mardi pressé")
        self.assertTrue(a["repas_a_prevoir"]["midis_semaine"] and a["repas_a_prevoir"]["soirs"])
        digestion.appliquer([{"type": "ardoise", "semaine": "2026-11-09",
                              "jours": [{"jour": "Lundi", "repas": [{"moment": "Soir", "plat": "Dahl", "dessert": "Yaourt"}]}]}])
        a = digestion.lire_onglet("ardoise")
        self.assertEqual((a["contraintes"], a["jours"][0]["jour"]), ("mardi pressé", "Lundi"))


class TestNettoyageLiens(unittest.TestCase):
    def test_pistage(self):
        self.assertEqual(journal.nettoyer_url("https://a.fr/p?utm_source=g&gclid=1&id=3"), "https://a.fr/p?id=3")
        self.assertEqual(journal.nettoyer_url("https://a.fr/p"), "https://a.fr/p")


if __name__ == "__main__":
    unittest.main()

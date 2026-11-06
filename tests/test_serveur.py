import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from tambouille import config, serveur


class TestServeur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        config.utiliser_dossier(Path(cls.tmp.name))
        cls.srv = serveur.creer_serveur(port=0)
        cls.base = f"http://{config.HOTE}:{cls.srv.server_port}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.tmp.cleanup()

    def req(self, chemin, donnees=None, entetes=None, methode=None):
        r = urllib.request.Request(self.base + chemin, data=donnees, headers=entetes or {}, method=methode)
        try:
            with urllib.request.urlopen(r) as rep:
                return rep.status, rep.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def test_parcours_complet(self):
        code, corps = self.req("/")
        self.assertEqual(code, 200)
        self.assertIn(b"TitonTambouille", corps)

        code, corps = self.req("/api/photos", b"\xff\xd8image", {"X-Nom-Fichier": "IMG_1.JPEG"}, "POST")
        self.assertEqual(code, 201)
        photo = json.loads(corps)["fichier"]
        self.assertTrue(photo.startswith("photos/") and photo.endswith(".jpg"))

        entree = {"texte": "Moutabal fumé", "photos": [{"fichier": photo, "legende": "le moutabal"}],
                  "liens": [{"url": "https://exemple.fr", "titre": "Recette"}]}
        code, _ = self.req("/api/journal", json.dumps(entree).encode(), {"Content-Type": "application/json"}, "POST")
        self.assertEqual(code, 201)

        code, corps = self.req("/api/journal")
        e = json.loads(corps)["entrees"][-1]
        self.assertEqual(e["texte"], "Moutabal fumé")
        self.assertEqual(e["photos"][0]["legende"], "le moutabal")

        code, corps = self.req("/" + photo)
        self.assertEqual((code, corps), (200, b"\xff\xd8image"))

    def test_onglets_exemples(self):
        code, corps = self.req("/api/onglets")
        d = json.loads(corps)
        self.assertEqual(code, 200)
        self.assertIn("recettes", d["exemples"])
        self.assertTrue(d["recettes"]["recettes"])

    def test_refus(self):
        self.assertEqual(self.req("/api/photos", b"x", {"X-Nom-Fichier": "virus.exe"}, "POST")[0], 400)
        self.assertEqual(self.req("/photos/..%2Fjournal.md")[0], 404)
        self.assertEqual(self.req("/interface/../tambouille/config.py")[0], 404)
        self.assertEqual(self.req("/api/journal", b'{"texte":"x"}', {"Content-Type": "application/json",
                                                                      "Origin": "https://ailleurs.fr"}, "POST")[0], 403)
        self.assertEqual(self.req("/api/journal", b'{"texte":"x"}', {"Content-Type": "text/plain"}, "POST")[0], 415)


if __name__ == "__main__":
    unittest.main()

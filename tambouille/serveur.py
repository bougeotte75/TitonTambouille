"""
Petit serveur web local (bibliothèque standard uniquement).

Routes :
    GET  /                      interface
    GET  /interface/…           fichiers de l'interface (CSS, JS, polices)
    GET  /photos/<nom>          une photo du journal
    GET  /api/journal           toutes les entrées
    POST /api/journal           ajoute une entrée  {texte, photos:[{fichier, legende}], liens:[{url, titre}]}
    POST /api/photos            envoie une photo (corps brut, nom dans l'en-tête X-Nom-Fichier)
    GET  /api/onglets           données des onglets Recettes, Idées, Ardoise, Carte
    GET  /api/digestion         nombre d'entrées à digérer, dernières digestions
    POST /api/digestion/annuler annule la dernière digestion
    POST /api/ardoise/preferences  enregistre « Repas à prévoir » et « Cette semaine »
"""
from __future__ import annotations

import json
import mimetypes
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import config, digestion, journal, stockage

mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("image/heic", ".heic")
mimetypes.add_type("text/javascript", ".js")


class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "TitonTambouille"

    # ------------------------------------------------------------------ réponses

    def _envoyer(self, code: int, corps: bytes, type_contenu: str, cache: bool = False) -> None:
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Cache-Control", "max-age=3600" if cache else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(corps)

    def _json(self, code: int, donnees) -> None:
        self._envoyer(code, json.dumps(donnees, ensure_ascii=False).encode("utf-8"),
                      "application/json; charset=utf-8")

    def _erreur(self, code: int, message: str) -> None:
        self._json(code, {"erreur": message})

    def _fichier(self, chemin: Path, cache: bool = False) -> None:
        type_contenu = mimetypes.guess_type(chemin.name)[0] or "application/octet-stream"
        if type_contenu.startswith("text/") or type_contenu.endswith("javascript"):
            type_contenu += "; charset=utf-8"
        self._envoyer(200, chemin.read_bytes(), type_contenu, cache)

    def log_message(self, format, *args):     # silence dans le Terminal
        pass

    # ------------------------------------------------------------------ sécurité

    def _origine_acceptee(self) -> bool:
        """Refuse les envois venant d'un autre site (protection contre les requêtes forgées)."""
        origine = self.headers.get("Origin")
        if origine is None:
            return True
        hote = self.headers.get("Host", "")
        return urlparse(origine).netloc == hote

    def _lire_corps(self, limite: int) -> bytes | None:
        try:
            taille = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if taille < 0 or taille > limite:
            return None
        return self.rfile.read(taille)

    # ------------------------------------------------------------------ GET

    def do_GET(self):
        chemin = unquote(urlparse(self.path).path)
        if chemin in ("/", "/index.html"):
            return self._fichier(config.DOSSIER_INTERFACE / "index.html")
        if chemin == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return None
        if chemin.startswith("/interface/"):
            cible = (config.DOSSIER_INTERFACE / chemin[len("/interface/"):]).resolve()
            racine = config.DOSSIER_INTERFACE.resolve()
            if racine in cible.parents and cible.is_file():
                return self._fichier(cible, cache=cible.suffix == ".ttf")
            return self._erreur(404, "Fichier introuvable.")
        if chemin.startswith("/photos/"):
            cible = stockage.chemin_photo(chemin[len("/photos/"):])
            if cible:
                return self._fichier(cible, cache=True)
            return self._erreur(404, "Photo introuvable.")
        if chemin == "/api/journal":
            entrees = journal.lire()
            return self._json(200, {"entrees": [e.en_dict(i) for i, e in enumerate(entrees)]})
        if chemin == "/api/onglets":
            return self._json(200, stockage.lire_onglets())
        if chemin == "/api/digestion":
            return self._json(200, {"a_digerer": len(digestion.a_digerer()),
                                    "historique": digestion.historique()[:5]})
        return self._erreur(404, "Page introuvable.")

    # ------------------------------------------------------------------ POST

    def do_POST(self):
        chemin = urlparse(self.path).path
        if not self._origine_acceptee():
            return self._erreur(403, "Origine refusée.")

        if chemin == "/api/photos":
            corps = self._lire_corps(config.TAILLE_MAX_PHOTO)
            if corps is None:
                return self._erreur(413, "La photo dépasse 25 Mo.")
            nom = unquote(self.headers.get("X-Nom-Fichier", ""))
            try:
                return self._json(201, {"fichier": stockage.enregistrer_photo(nom, corps)})
            except stockage.ErreurPhoto as e:
                return self._erreur(400, str(e))

        if chemin == "/api/journal":
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._erreur(415, "Format attendu : JSON.")
            corps = self._lire_corps(config.TAILLE_MAX_REQUETE)
            if corps is None:
                return self._erreur(413, "Entrée trop longue.")
            try:
                d = json.loads(corps.decode("utf-8"))
                photos = [journal.Photo(fichier=str(p["fichier"]), legende=str(p.get("legende", "")))
                          for p in d.get("photos", [])]
                liens = [journal.Lien(url=str(l["url"]).strip(), titre=str(l.get("titre", "")))
                         for l in d.get("liens", [])]
                entree = journal.ajouter(str(d.get("texte", "")), photos, liens)
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                message = str(e) if isinstance(e, journal.ErreurEntree) else "Entrée illisible."
                return self._erreur(400, message)
            numero = len(journal.lire()) - 1
            return self._json(201, entree.en_dict(numero))

        if chemin == "/api/digestion/annuler":
            try:
                d = digestion.annuler_derniere()
            except digestion.ErreurDigestion as e:
                return self._erreur(400, str(e))
            return self._json(200, {"annulee": d["date"]})

        if chemin == "/api/ardoise/preferences":
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._erreur(415, "Format attendu : JSON.")
            corps = self._lire_corps(config.TAILLE_MAX_REQUETE)
            try:
                d = json.loads((corps or b"").decode("utf-8"))
                a = digestion.enregistrer_preferences_ardoise(d.get("repas_a_prevoir", {}), d.get("contraintes", ""))
            except (ValueError, AttributeError) as e:
                return self._erreur(400, str(e) if isinstance(e, digestion.ErreurDigestion) else "Préférences illisibles.")
            return self._json(200, a)

        return self._erreur(404, "Page introuvable.")


# --------------------------------------------------------------------------- démarrage

class Serveur(ThreadingHTTPServer):
    daemon_threads = True


def _port_libre(port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((config.HOTE, port)) != 0:
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((config.HOTE, 0))
        return s.getsockname()[1]


def creer_serveur(port: int | None = None) -> ThreadingHTTPServer:
    return Serveur((config.HOTE, _port_libre(config.PORT if port is None else port)), Gestionnaire)


def demarrer(ouvrir_navigateur: bool = True) -> None:
    serveur = creer_serveur()
    adresse = f"http://{config.HOTE}:{serveur.server_port}/"
    print(f"TitonTambouille {config.VERSION} — {adresse}")
    print(f"Journal : {config.F_JOURNAL}")
    print("Ctrl+C pour arrêter.")
    if ouvrir_navigateur:
        threading.Timer(0.6, webbrowser.open, args=(adresse,)).start()
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt.")
    finally:
        serveur.server_close()

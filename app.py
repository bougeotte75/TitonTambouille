"""
TitonTambouille — point d'entrée.

Lancement :  python3 app.py               (ou double-clic sur lancer.command)
Option     :  python3 app.py --sans-navigateur
"""
import sys

from tambouille.serveur import demarrer

if __name__ == "__main__":
    demarrer(ouvrir_navigateur="--sans-navigateur" not in sys.argv)

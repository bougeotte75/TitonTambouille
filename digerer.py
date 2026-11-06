"""
Digestion du journal en ligne de commande (voir DIGESTION.md).

    python3 digerer.py a-digerer                    entrées en attente + état des onglets (JSON)
    python3 digerer.py appliquer FICHIER [--essai]  applique des opérations (ou vérifie seulement)
    python3 digerer.py rien ORIGINE [ORIGINE…]      marque des entrées digérées sans rien ranger
    python3 digerer.py annuler                      annule la dernière digestion
    python3 digerer.py historique                   liste des dernières digestions
"""
import json
import sys
from pathlib import Path

from tambouille import digestion


def main(args: list[str]) -> int:
    if not args:
        print(__doc__)
        return 1
    commande, reste = args[0], args[1:]
    try:
        if commande == "a-digerer":
            print(json.dumps(digestion.contexte(), ensure_ascii=False, indent=2))
        elif commande == "appliquer" and reste:
            ops = json.loads(Path(reste[0]).read_text(encoding="utf-8"))
            ops = ops["operations"] if isinstance(ops, dict) else ops
            essai = "--essai" in reste
            for ligne in digestion.appliquer(ops, essai=essai):
                print("·", ligne)
            print("(essai : rien n'a été modifié)" if essai else "Appliqué.")
        elif commande == "rien" and reste:
            digestion.marquer_digerees(reste)
            print("Marqué digéré.")
        elif commande == "annuler":
            d = digestion.annuler_derniere()
            print(f"Digestion du {d['date']} annulée ({len(d['modifications'])} modifications).")
        elif commande == "historique":
            for d in digestion.historique()[:10]:
                etat = " (annulée)" if d["annulee"] else ""
                print(f"{d['date']}{etat} — {len(d['modifications'])} modifications")
        else:
            print(__doc__)
            return 1
    except digestion.ErreurDigestion as e:
        print(f"Refusé : {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

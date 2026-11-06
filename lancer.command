#!/bin/bash
# =============================================================================
#  TitonTambouille — lanceur
#  Double-clic (après un premier clic droit → Ouvrir), ou « bash lancer.command »
#  dans le Terminal. Aucune dépendance à installer : Python 3 suffit.
# =============================================================================
cd "$(dirname "$0")" || exit 1

PY=""
for v in python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$v" >/dev/null 2>&1; then PY="$v"; break; fi
done
if [ -z "$PY" ]; then echo "Python 3 introuvable."; read -r -p "Entrée pour fermer…"; exit 1; fi

"$PY" app.py

"""Crée data/demo/exemples.json : 10 clients des 20 % mis de côté, SANS identifiant.

Usage : .venv\\Scripts\\python -I scripts\\creer_demo.py

Règle fixe : pour chaque segment, dans l'ordre des identifiants, le premier client typique et
non frontière, puis le premier client atypique ou à la frontière. Seules les 8 variables (unités
d'origine) et le segment attendu sont gardés. Licence : data/demo/LICENCE.md (CC BY-NC-SA 4.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import explication as X  # noqa: E402
from segmentation import segments as S  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402

LICENCE = """# Licence des données de démonstration

Les fichiers de ce dossier sont **dérivés** du jeu de données public
*Brazilian E-Commerce Public Dataset by Olist* (Kaggle :
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), publié par Olist sous licence
**Creative Commons Attribution – Pas d'utilisation commerciale – Partage dans les mêmes
conditions 4.0 International (CC BY-NC-SA 4.0)** : https://creativecommons.org/licenses/by-nc-sa/4.0/

- Données **réelles et anonymisées** par Olist (texte de la page Kaggle : « This is real
  commercial data, it has been anonymised »).
- Modifications : les commandes ont été agrégées par client (8 variables de profil, montants en
  réals brésiliens R$) ; aucun identifiant de client, de commande ou de vendeur n'est conservé.
- Ces fichiers sont partagés sous la **même licence CC BY-NC-SA 4.0** : usage non commercial,
  citation de la source, partage dans les mêmes conditions.
- Remerciement repris de la page du jeu : « Thanks to Olist for releasing this dataset. »
"""


def main() -> int:
    proteger_sorties()
    v = config.VARIABLES_PROFIL
    segs = S.charger()
    centres = S.centres(segs)
    noms = {s["id"]: s["nom"] for s in segs["segments"]}
    expl = json.loads((config.DOSSIER_MODELES / "explication.json").read_text(encoding="utf-8"))
    z20 = pd.read_csv(config.PREPARES_MISE_DE_COTE, index_col="customer_unique_id")
    prof20 = pd.read_csv(config.PROFILS_MISE_DE_COTE, index_col="customer_unique_id").loc[z20.index]
    d = X.diagnostic(z20[v].to_numpy(dtype=float), centres, expl["seuils_atypiques"])
    d.index = z20.index

    exemples = []
    ordre = sorted(z20.index)
    for s in range(segs["k"]):
        typique = next(i for i in ordre if d.loc[i, "segment"] == s
                       and not d.loc[i, "atypique"] and not d.loc[i, "frontiere"])
        particulier = next(i for i in ordre if d.loc[i, "segment"] == s
                           and (d.loc[i, "atypique"] or d.loc[i, "frontiere"]))
        genre_particulier = "atypique" if d.loc[particulier, "atypique"] else "à la frontière"
        for i, genre in ((typique, "typique"), (particulier, genre_particulier)):
            ligne = prof20.loc[i, v]
            exemples.append({
                "nom": f"Exemple {len(exemples) + 1} : S{s} « {noms[s]} », {genre}",
                "segment_attendu": int(s),
                "client": {c: (int(ligne[c]) if c == "frequence" else float(ligne[c])) for c in v},
            })
    dossier = config.RACINE / "data" / "demo"
    dossier.mkdir(parents=True, exist_ok=True)
    with open(dossier / "exemples.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(exemples, f, ensure_ascii=False, indent=2)
        f.write("\n")
    (dossier / "LICENCE.md").write_text(LICENCE, encoding="utf-8", newline="\n")
    print(f"{len(exemples)} exemples écrits dans data/demo/exemples.json (sans identifiant)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

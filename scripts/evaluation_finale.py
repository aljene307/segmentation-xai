"""Évaluation finale sur les 20 % mis de côté : ouverte UNE SEULE FOIS.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\evaluation_finale.py --verification
        fait tourner tout le code sur les 80 % (mêmes fonctions), sans ouvrir les avis des 20 %
        et sans rien écrire ;
    .venv\\Scripts\\python -I scripts\\evaluation_finale.py
        l'unique ouverture : refuse de démarrer si un fichier de résultats existe déjà, puis
        écrit les résultats en mode « création seulement » (impossible d'écraser).

Attentes et seuils : docs/CHOIX.md (écrits et poussés avant l'ouverture). Rien n'est modifié
après l'ouverture.
Sorties : reports/evaluation_finale.json et reports/evaluation_finale.md (versionnés).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import evaluation_finale as E  # noqa: E402
from segmentation import partitions as P  # noqa: E402
from segmentation import segments as S  # noqa: E402
from segmentation.avis import note_client  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.donnees import charger_avis, charger_tables  # noqa: E402
from segmentation.profil import commandes_retenues  # noqa: E402

RESULTATS_JSON = config.DOSSIER_RAPPORTS / "evaluation_finale.json"
RESULTATS_MD = config.DOSSIER_RAPPORTS / "evaluation_finale.md"


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def texte(x):
    if isinstance(x, list):
        return " ; ".join(texte(e) for e in x)
    if isinstance(x, float):
        return f"{x:g}".replace(".", ",")
    return str(x)


def main() -> int:
    proteger_sorties()
    parser = argparse.ArgumentParser()
    parser.add_argument("--verification", action="store_true")
    verification = parser.parse_args().verification

    if not verification and (RESULTATS_JSON.exists() or RESULTATS_MD.exists()):
        raise SystemExit("REFUS : l'évaluation finale a déjà été faite (fichier de résultats "
                         "présent). Elle ne s'ouvre qu'une seule fois.")

    # Fichiers produits par les étapes 1 à 12 de la reproduction (absents d'un clone neuf).
    E.exiger_fichiers([config.DOSSIER_OLIST / f for f in (*config.TABLES.values(), config.TABLE_AVIS)]
                      + [config.PREPARES_APPRENTISSAGE, config.PREPARES_MISE_DE_COTE,
                         config.PROFILS_APPRENTISSAGE, config.PROFILS_MISE_DE_COTE,
                         config.SEGMENTS_APPRENTISSAGE])

    v = config.VARIABLES_PROFIL
    segs = S.charger()
    centres = S.centres(segs)
    expl = json.loads((config.DOSSIER_MODELES / "explication.json").read_text(encoding="utf-8"))
    seuils, arbre = expl["seuils_atypiques"], expl["arbre"]

    z80 = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    z20 = pd.read_csv(config.PREPARES_MISE_DE_COTE, index_col="customer_unique_id")
    prof80 = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id").loc[z80.index]
    prof20 = pd.read_csv(config.PROFILS_MISE_DE_COTE, index_col="customer_unique_id").loc[z20.index]
    if set(z80.index) & set(z20.index):
        raise SystemExit("ARRÊT : un client est dans les deux groupes.")
    seg80 = S.segments_apprentissage().loc[z80.index]
    seg20 = S.affecter_prepares(z20, segs)

    t = commandes_retenues(charger_tables(sauf=("geolocalisation",)),
                           config.DEBUT_ACHATS, config.FIN_ACHATS)
    plusieurs = t.groupby("customer_unique_id")["nb_vendeurs"].max() > 1
    avis = charger_avis()

    def notes_de(ids):
        cmd = t[t["customer_unique_id"].isin(set(ids))]["customer_unique_id"]
        return note_client(avis[avis["order_id"].isin(cmd.index)], cmd)

    ech80 = P.ordre_echantillon(z80.index, config.GRAINE)[:config.N_ECHANTILLON_COMMUN]
    m80 = E.mesurer(z80, prof80, seg80, notes_de(z80.index), plusieurs, centres, seuils, arbre,
                    ech80, v)
    if verification:
        print("Vérification sur les 80 % (avis des 20 % NON ouverts, rien n'est écrit) :")
        for cle in ("parts", "silhouette", "atypiques", "frontiere", "fidelite_arbre",
                    "sans_avis", "satisfaits", "satisfaits_par_segment", "ari", "nmi",
                    "ecart_retard", "s3_ecart"):
            print(f"  {cle} : {m80[cle]}")
        return 0

    # ---- Unique ouverture des avis des 20 % ----
    ech20 = P.ordre_echantillon(z20.index, config.GRAINE)[:config.N_ECHANTILLON_COMMUN]
    notes20 = notes_de(z20.index)
    if set(notes20.index) - set(z20.index):
        raise SystemExit("ARRÊT : une note n'appartient pas aux 20 %.")
    m20 = E.mesurer(z20, prof20, seg20, notes20, plusieurs, centres, seuils, arbre, ech20, v)
    verdicts = E.verdicts(m80, m20)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                            cwd=config.RACINE).stdout.strip()
    resultats = {"date": datetime.now().isoformat(timespec="seconds"), "commit": commit,
                 "mesures_80": m80, "mesures_20": m20, "verdicts": verdicts}

    noms = {s["id"]: s["nom"] for s in segs["segments"]}
    atteintes = sum(x["atteinte"] for x in verdicts)
    md = ["# Évaluation finale sur les 20 % mis de côté (ouverte une seule fois)", "",
          f"Calculée le {resultats['date']}, au commit `{commit[:7]}`. Attentes et seuils écrits "
          "et poussés avant l'ouverture (`docs/CHOIX.md`). Rien n'a été modifié après "
          "l'ouverture.", "",
          f"**Attentes atteintes : {atteintes} sur {len(verdicts)}.**", "",
          tableau(["n°", "mesure", "80 % (référence)", "20 %", "attente", "atteinte", "statut"],
                  [[x["code"], x["mesure"], texte(x["valeur_80"]), texte(x["valeur_20"]),
                    x["attente"], "**oui**" if x["atteinte"] else "**NON**", x["statut"]]
                   for x in verdicts]), "",
          "## Détail par segment (20 %)", "",
          tableau(["segment", "part (%)", "clients avec avis", "satisfaits (%)", "atypiques (%)"],
                  [[f"S{s} {noms[s]}", f"{100 * m20['parts'][s]:.2f}",
                    m20["clients_avec_avis_par_segment"][s],
                    f"{100 * m20['satisfaits_par_segment'][s]:.1f}",
                    f"{100 * m20['atypiques_par_segment'][s]:.1f}"] for s in range(len(noms))]), "",
          f"Lien retard / note (20 %) : {100 * m20['satisfaits_a_l_heure']:.1f} % de satisfaits à "
          f"l'heure contre {100 * m20['satisfaits_en_retard']:.1f} % en retard. Hypothèse S3 "
          f"(20 %) : {m20['s3_plusieurs_vendeurs']} clients à plusieurs vendeurs contre "
          f"{m20['s3_un_vendeur']} à un seul.", ""]

    with open(RESULTATS_JSON, "x", encoding="utf-8", newline="\n") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(RESULTATS_MD, "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(md))
    print(f"Attentes atteintes : {atteintes} / {len(verdicts)}")
    print("Résultats : reports/evaluation_finale.json et reports/evaluation_finale.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

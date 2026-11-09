"""Hypothèse sur S3 (description seulement, rien ne change dans la segmentation).

Dans S3 « Achats de plusieurs articles », la satisfaction est-elle plus basse quand une commande
avait plusieurs vendeurs (livraison probablement en plusieurs colis) ?
Clients d'apprentissage (80 %) seulement ; les avis des 20 % ne sont pas lus.

Usage : .venv\\Scripts\\python -I scripts\\analyser_s3.py
Sortie : reports/hypothese_s3.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation.avis import note_client  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402
from segmentation.donnees import charger_avis, charger_tables  # noqa: E402
from segmentation.profil import commandes_retenues  # noqa: E402
from segmentation.segments import segments_apprentissage  # noqa: E402

S3 = 3


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def ecart_ic95(p1: float, n1: int, p2: float, n2: int) -> tuple[float, float, float]:
    """Écart de deux proportions (en points) et intervalle de confiance à 95 % (approx. normale)."""
    d = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    return 100 * d, 100 * (d - 1.96 * se), 100 * (d + 1.96 * se)


def main() -> int:
    proteger_sorties()
    seg = segments_apprentissage()
    cote = set(pd.read_csv(config.PROFILS_MISE_DE_COTE, usecols=["customer_unique_id"])[
        "customer_unique_id"])
    t = commandes_retenues(charger_tables(sauf=("geolocalisation",)),
                           config.DEBUT_ACHATS, config.FIN_ACHATS)
    t = t[t["customer_unique_id"].isin(set(seg.index))]
    avis = charger_avis()
    notes = note_client(avis[avis["order_id"].isin(t.index)], t["customer_unique_id"])
    if set(notes.index) & cote:
        raise SystemExit("ARRÊT : un client mis de côté apparaît.")

    plusieurs = t.groupby("customer_unique_id")["nb_vendeurs"].max() > 1
    df = pd.DataFrame({"segment": seg, "plusieurs_vendeurs": plusieurs}).join(notes)
    df = df[df["note_client"].notna()]

    def ligne(nom, d):
        return [nom, f"{len(d)}", f"{100 * d['satisfait'].mean():.1f}",
                f"{d['note_client'].mean():.2f}", f"{100 * (d['note_client'] == 1).mean():.1f}"]

    lignes, ecarts = [], {}
    for nom, d in (("S3", df[df["segment"] == S3]), ("tous les autres segments",
                                                     df[df["segment"] != S3])):
        a, b = d[d["plusieurs_vendeurs"]], d[~d["plusieurs_vendeurs"]]
        lignes += [ligne(f"{nom} — au moins une commande à plusieurs vendeurs", a),
                   ligne(f"{nom} — un seul vendeur par commande", b)]
        ecarts[nom] = ecart_ic95(a["satisfait"].mean(), len(a), b["satisfait"].mean(), len(b))

    d3, e3 = df[df["segment"] == S3], ecarts["S3"]
    net = e3[2] < 0 and abs(e3[0]) >= 10
    md = ["# Hypothèse sur S3 : plusieurs vendeurs, plusieurs colis ?", "",
          "Rapport généré par `scripts/analyser_s3.py`. **Description seulement** : rien ne change "
          "dans la segmentation. Clients d'apprentissage avec avis (80 %) ; avis des 20 % non lus. "
          "« Plusieurs vendeurs » = au moins une commande retenue du client comptait des articles "
          "de plusieurs vendeurs (donc, probablement, plusieurs colis).", "",
          tableau(["groupe", "clients avec avis", "satisfaits (%)", "note moyenne", "note = 1 (%)"],
                  lignes), "",
          tableau(["comparaison", "écart de satisfaits (points)", "intervalle de confiance à 95 %"],
                  [[f"{nom} : plusieurs vendeurs moins un seul", f"{e[0]:.1f}",
                    f"[{e[1]:.1f} ; {e[2]:.1f}]"] for nom, e in ecarts.items()]), "",
          f"Part des clients de S3 concernés par plusieurs vendeurs : "
          f"{100 * d3['plusieurs_vendeurs'].mean():.1f} %.", "",
          "**Lecture** : " + (
              "l'écart est net (au moins 10 points, intervalle entièrement sous 0). C'est une piste "
              "qui soutient l'hypothèse, sans la prouver : la comparaison est descriptive, et "
              "d'autres différences entre ces clients peuvent jouer." if net else
              "l'écart n'est pas net (moins de 10 points, ou intervalle qui contient 0). "
              "L'hypothèse n'est pas soutenue par cette comparaison."), ""]
    (config.DOSSIER_RAPPORTS / "hypothese_s3.md").write_text("\n".join(md), encoding="utf-8",
                                                             newline="\n")
    print("Rapport : reports/hypothese_s3.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

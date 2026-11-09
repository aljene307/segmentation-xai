"""Crée la synthèse du projet en PDF (2 pages A4) à partir des fichiers de résultats.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\creer_synthese.py

Aucun chiffre n'est tapé à la main : tout est lu dans reports/, models/ et app/donnees/.
Aucune donnée brute n'est nécessaire (le script tourne sur un clone du dépôt).
Sorties : reports/synthese.pdf (versionné) ; aperçus PNG dans captures_brutes/ (non versionnés).
"""

from __future__ import annotations

import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation.avis import SEUIL_SATISFAIT  # noqa: E402
from segmentation import regle_k as R  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402

COULEURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
ENCRE, ENCRE_2, FOND = "#0b0b0b", "#52514e", "#ffffff"
A4 = (8.27, 11.69)


def lire(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8"))


def n(v: float, d: int = 0) -> str:
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def p(v: float, d: int = 1) -> str:
    return n(100 * v, d) + " %"


class Page:
    """Mise en page simple : du texte qui descend, ligne après ligne."""

    def __init__(self, pdf: PdfPages, numero: int):
        self.pdf, self.numero = pdf, numero
        self.fig = plt.figure(figsize=A4)
        self.fig.patch.set_facecolor(FOND)
        self.y = 0.955

    def titre(self, texte: str, taille: float = 15):
        self.fig.text(0.07, self.y, texte, fontsize=taille, fontweight="bold", color=ENCRE,
                      va="top")
        self.y -= 0.032 if taille > 12 else 0.026

    def texte(self, texte: str, taille: float = 8.4, largeur: int = 120, couleur=ENCRE, gras=False,
              retrait: float = 0.07):
        for ligne in textwrap.wrap(texte, largeur - 12 if gras else largeur):
            self.fig.text(retrait, self.y, ligne, fontsize=taille, color=couleur, va="top",
                          fontweight="bold" if gras else "normal")
            self.y -= taille * 0.00205
        self.y -= 0.004

    def puce(self, texte: str):
        lignes = textwrap.wrap(texte, 114)
        for i, ligne in enumerate(lignes):
            self.fig.text(0.075, self.y, "•" if i == 0 else "", fontsize=8.4, color=ENCRE, va="top")
            self.fig.text(0.09, self.y, ligne, fontsize=8.4, color=ENCRE, va="top")
            self.y -= 0.0172
        self.y -= 0.002

    def tableau(self, entetes, lignes, colonnes, hauteur_ligne=0.0185):
        x0 = 0.07
        for j, e in enumerate(entetes):
            self.fig.text(x0 + sum(colonnes[:j]), self.y, e, fontsize=7.8, fontweight="bold",
                          color=ENCRE_2, va="top")
        self.y -= hauteur_ligne
        self.fig.add_artist(plt.Line2D([x0, x0 + sum(colonnes)], [self.y + 0.004] * 2,
                                       color="#d6d5d0", linewidth=0.8))
        for ligne in lignes:
            for j, v in enumerate(ligne):
                self.fig.text(x0 + sum(colonnes[:j]), self.y, str(v), fontsize=7.8, color=ENCRE,
                              va="top")
            self.y -= hauteur_ligne
        self.y -= 0.006

    def fin(self, apercu: Path):
        self.fig.text(0.07, 0.025, "Projet Challenge 3 · Data Mining · ENSI · Mohamed Aljene · "
                      "données Olist (CC BY-NC-SA 4.0)", fontsize=6.8, color=ENCRE_2)
        self.fig.text(0.93, 0.025, f"{self.numero} / 2", fontsize=6.8, color=ENCRE_2, ha="right")
        self.pdf.savefig(self.fig)
        self.fig.savefig(apercu, dpi=110)
        plt.close(self.fig)


def main() -> int:
    proteger_sorties()
    r = config.RACINE
    seg = lire(config.SEGMENTS)
    expl = lire(r / "models" / "explication.json")
    acp = lire(config.ACP)
    ev = lire(r / "reports" / "evaluation_finale.json")
    explo = lire(r / "app" / "donnees" / "exploration.json")
    sil = lire(r / "app" / "donnees" / "silhouette_k.json")[str(config.K_RETENU)]
    ind = pd.read_csv(r / "reports" / "indices_partitions.csv")
    km = ind[ind["methode"] == "K-Means (8 variables)"].set_index("k")
    choix = R.choisir_k(km)
    vp = np.asarray(acp["valeurs_propres"])
    k_axes = acp["decision"]["retenus"]
    m80, m20 = ev["mesures_80"], ev["mesures_20"]
    ch = explo["chaine_clients"]
    noms = {s["id"]: s["nom"] for s in seg["segments"]}
    total = seg["clients_apprentissage"]
    atteintes = sum(v["atteinte"] for v in ev["verdicts"])
    texte_k = (r / "reports" / "choix_k.md").read_text(encoding="utf-8")
    sous, tirages = map(int, re.search(r"Tirages sous 0,80 : (\d+) sur (\d+)", texte_k).groups())
    part_f4 = 100 * vp[:4].sum() / vp.sum()
    bas, haut = (100 * c for c in config.CENTILES_ECRETAGE)
    seuil_axes = 100 * acp["part_minimale"]
    sortie = r / "reports" / "synthese.pdf"
    apercus = r / "captures_brutes"
    apercus.mkdir(exist_ok=True)

    with PdfPages(sortie, metadata={"Title": "Segmentation explicable des clients Olist",
                                    "Author": "Mohamed Aljene", "CreationDate": None}) as pdf:
        # --- Page 1 ---------------------------------------------------------------------
        pg = Page(pdf, 1)
        pg.titre("Segmentation explicable des clients Olist", 16)
        pg.texte("Projet Challenge 3 – Application web de segmentation explicable · Data Mining, "
                 "ENSI (II3-IF) · Mohamed Aljene", couleur=ENCRE_2)
        pg.titre("Données", 11.5)
        pg.texte("Brazilian E-Commerce Public Dataset by Olist (Kaggle) : données réelles et "
                 "anonymisées, licence CC BY-NC-SA 4.0. « Thanks to Olist for releasing this "
                 "dataset. » Montants en réals brésiliens (R$).")
        pg.texte(f"{n(ch['tous'])} clients → {n(ch['au_moins_une_livree'])} avec au moins une "
                 f"commande livrée → {n(ch['periode'])} dans la période retenue (achats du "
                 f"{explo['periode']['debut']} au 2018-06-30 ; fin de 2016 = période d'essai ; "
                 "après juin 2018 = coupure de l'extraction). 80 % pour apprendre "
                 f"({n(total)} clients), 20 % mis de côté jusqu'à l'évaluation finale.")
        pg.titre("Méthode", 11.5)
        for t in (
            "Profil par client : 8 variables (Récence, Fréquence, Montant, part des frais de "
            "port, mensualités, articles par commande, délai de livraison, écart à la date "
            "promise). La note d'avis n'entre jamais dans le clustering.",
            "Préparation apprise sur les 80 % : log(1 + x) des variables positives asymétriques, "
            f"écrêtage aux {n(bas, 1)}e et {n(haut, 1)}e centiles, standardisation ; réappliquée "
            "telle quelle.",
            f"ACP normée : {k_axes} axes retenus ({n(100 * vp[:k_axes].sum() / vp.sum(), 1)} % de "
            f"l'information) par la règle max(Kaiser, part cumulée ≥ {n(seuil_axes)} %).",
            "Algorithmes comparés : K-Means (référence, 8 variables), CAH de Ward, classification "
            "mixte (CAH sur les axes puis consolidation par K-Means), HDBSCAN.",
            "Les choix principaux ont été écrits et poussés avant le calcul ; les exceptions "
            "sont tracées dans le journal docs/CHOIX.md.",
        ):
            pg.puce(t)
        pg.titre("Choix du nombre de segments", 11.5)
        rangs = choix["rangs"]
        pg.texte(f"Règle : k admissible si le plus petit segment ≥ {n(100 * R.PART_MIN)} %, l'ARI "
                 f"bootstrap moyen ≥ {n(R.ARI_MIN, 2)} et chaque Jaccard ≥ {n(R.JACCARD_MIN, 2)} ; "
                 "puis la plus petite somme des rangs (silhouette, Calinski-Harabasz, "
                 "Davies-Bouldin).")
        pg.tableau(["k"] + [str(k) for k in rangs.index],
                   [["somme des rangs"] + [str(int(s)) for s in rangs["somme"]],
                    ["ARI bootstrap moyen"] + [n(km.loc[k, "ari_boot_moyen"], 2) for k in rangs.index]],
                   [0.2] + [0.09] * len(rangs))
        pg.texte(f"k = {choix['k']} retenu ; critère métier validé (une action différente par "
                 f"segment). Silhouette {n(sil['moyenne'], 3)} ({p(sil['part_negative'])} de "
                 "clients négatifs) : un nuage continu, découpé plutôt que naturellement séparé.",
                 gras=False)
        pg.titre("Les 5 segments", 11.5)
        lignes = []
        for s in seg["segments"]:
            i = s["id"]
            lignes.append([f"S{i} {s['nom']}", p(s["clients"] / total),
                           p(expl["part_ca"][str(i)] / 100),
                           p(m80["satisfaits_par_segment"][i]), p(m20["satisfaits_par_segment"][i])])
        pg.tableau(["segment", "clients", "part du CA", "satisfaits 80 %", "satisfaits 20 %"],
                   lignes, [0.33, 0.12, 0.13, 0.15, 0.15])
        for s in seg["segments"]:
            pg.puce(f"S{s['id']} « {s['nom']} » : {s['action']}.")
        pg.fin(apercus / "synthese_page_1.png")

        # --- Page 2 ---------------------------------------------------------------------
        pg = Page(pdf, 2)
        pg.titre("Carte de l'ACP et satisfaction", 11.5)
        carte = pd.read_csv(r / "app" / "donnees" / "carte.csv")
        ax = pg.fig.add_axes([0.08, 0.6, 0.5, 0.31])
        for i in range(config.K_RETENU):
            c = carte[carte["segment_k5"] == i]
            ax.scatter(c["F1"], c["F2"], s=3, color=COULEURS[i], alpha=0.5, label=f"S{i}")
        ax.set_xlabel("F1 Valeur de l'achat", fontsize=8)
        ax.set_ylabel("F2 Expérience de livraison", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, markerscale=4, frameon=False, loc="upper left")
        for cote in ("top", "right"):
            ax.spines[cote].set_visible(False)
        ax2 = pg.fig.add_axes([0.66, 0.6, 0.29, 0.29])
        x = np.arange(config.K_RETENU)
        ax2.bar(x - 0.2, [100 * v for v in m80["satisfaits_par_segment"]], 0.38,
                color=COULEURS[0], label="80 %")
        ax2.bar(x + 0.2, [100 * v for v in m20["satisfaits_par_segment"]], 0.38,
                color=COULEURS[1], label="20 % (jamais vus)")
        ax2.set_xticks(x, [f"S{i}" for i in x], fontsize=7)
        ax2.set_ylabel("clients satisfaits (%)", fontsize=8)
        ax2.tick_params(labelsize=7)
        ax2.set_ylim(0, 100)
        ax2.legend(fontsize=6.5, frameon=False, loc="lower center", ncols=2,
                   bbox_to_anchor=(0.5, 1.0))
        for cote in ("top", "right"):
            ax2.spines[cote].set_visible(False)
        pg.y = 0.56
        pg.titre("Évaluation", 11.5)
        pg.texte(f"Externe (note d'avis, « satisfait » si note ≥ {SEUIL_SATISFAIT}) : ARI {n(m80['ari'], 3)}, NMI "
                 f"{n(m80['nmi'], 3)}, faibles par nature avec une étiquette à deux classes. Le "
                 "segment S2 est lié à la note par construction (retards) : clients livrés à "
                 f"l'heure {p(m80['satisfaits_a_l_heure'])} de satisfaits, en retard "
                 f"{p(m80['satisfaits_en_retard'])}.")
        pg.texte(f"Finale, sur les 20 % mis de côté, ouverte une seule fois, attentes écrites "
                 f"avant l'ouverture : {atteintes} attentes atteintes sur {len(ev['verdicts'])} "
                 "(tailles des segments, silhouette, atypiques, frontière, fidélité de l'arbre, "
                 "satisfaction par segment et ordre des segments, indices externes).", gras=True)
        pg.titre("Explicabilité", 11.5)
        a = expl["arbre"]
        pg.texte(f"Arbre de décision de substitution (profondeur {a['profondeur']}) : fidélité "
                 f"{p(a['fidelite_80'], 2)} sur les 80 %, {p(a['fidelite_20'], 2)} sur les 20 %, "
                 f"{len(expl['regles'])} règles traduites en phrases. Pour chaque client : "
                 f"segment, distance au centre, indicateurs « atypique » "
                 f"({n(100 * expl['centile_atypique'])}e centile du segment) "
                 "et « à la frontière », variables qui l'éloignent du client moyen et du centre "
                 "de son segment.")
        pg.texte(f"Constat : dans S3 « {noms[3]} », les clients dont une commande avait "
                 f"plusieurs vendeurs sont nettement moins satisfaits (écart de "
                 f"{n(100 * m80['s3_ecart'], 1)} points sur les 80 %, {n(100 * m20['s3_ecart'], 1)} "
                 "sur les 20 %) : une piste (plusieurs colis), pas une preuve.")
        pg.titre("Limites", 11.5)
        for t in (
            f"Nuage continu : silhouettes faibles ; une découpe concurrente apparaît dans {sous} "
            f"tirages bootstrap sur {tirages} (S2 y disparaît).",
            "Les 20 % viennent de la même période : la segmentation devrait être refaite "
            "régulièrement (habitudes et délais changent).",
            "L'axe F4 de l'ACP est un axe du temps (Récence) ; le nombre d'axes est fragile "
            f"({n(part_f4, 2)} % à F4 pour un seuil de {n(seuil_axes)} %).",
            "API sur l'offre gratuite de Render : mise en veille après 15 minutes sans requête "
            "(fait de l'hébergeur ; premier appel lent).",
        ):
            pg.puce(t)
        pg.titre("Réalisation", 11.5)
        pg.texte("Code : https://github.com/aljene307/segmentation-xai (licence MIT ; données "
                 "dérivées sous CC BY-NC-SA 4.0). API FastAPI : "
                 "https://segmentation-xai-api.onrender.com. Application Streamlit : voir le "
                 "README. Journal complet des choix : docs/CHOIX.md.")
        pg.fin(apercus / "synthese_page_2.png")

    print(f"Synthèse : reports/synthese.pdf ({sortie.stat().st_size // 1024} Ko) ; aperçus : "
          "captures_brutes/synthese_page_1.png et synthese_page_2.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())

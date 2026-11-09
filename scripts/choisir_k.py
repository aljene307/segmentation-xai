"""Applique la règle de choix de k (docs/CHOIX.md) sans rien y changer, et décrit le k obtenu.

Usage (depuis la racine du projet) :
    .venv\\Scripts\\python -I scripts\\choisir_k.py

Ne charge AUCUN avis. Sortie : reports/choix_k.md (plus des fichiers dans data/processed/).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from segmentation import config  # noqa: E402
from segmentation import partitions as P  # noqa: E402
from segmentation import regle_k as R  # noqa: E402
from segmentation.console import proteger_sorties  # noqa: E402

NOMS = {
    "recence_j": "Récence (j)", "frequence": "Fréquence", "montant_rs": "Montant (R$)",
    "part_frais_port": "Part frais de port", "mensualites_moy": "Mensualités",
    "articles_par_commande": "Articles/commande", "delai_livraison_moy_j": "Délai livraison (j)",
    "ecart_prevision_moy_j": "Écart date promise (j)",
}


def tableau(entetes, lignes):
    out = ["| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
    return "\n".join(out + ["| " + " | ".join(map(str, l)) + " |" for l in lignes])


def profil(prof: pd.DataFrame, e: np.ndarray) -> pd.DataFrame:
    g = prof.groupby(e)
    p = g[config.VARIABLES_PROFIL].median()
    p.insert(0, "clients", g.size())
    p.insert(1, "pct", 100 * g.size() / len(prof))
    p["part_ca_pct"] = 100 * g["montant_rs"].sum() / prof["montant_rs"].sum()
    p["pct_en_retard"] = 100 * g["ecart_prevision_moy_j"].apply(lambda s: (s > 0).mean())
    p["pct_plusieurs_commandes"] = 100 * g["frequence"].apply(lambda s: (s > 1).mean())
    return p


def lignes_profil(p: pd.DataFrame, nom_seg=lambda s: s) -> list[list]:
    out = []
    for s, r in p.iterrows():
        out.append([nom_seg(s), f"{int(r.clients)} ({r.pct:.1f} %)"]
                   + [f"{r[v]:.2f}" for v in config.VARIABLES_PROFIL]
                   + [f"{r.part_ca_pct:.1f}", f"{r.pct_en_retard:.1f}",
                      f"{r.pct_plusieurs_commandes:.1f}"])
    return out


ENTETES_PROFIL = (["segment", "clients"] + [NOMS[v] for v in config.VARIABLES_PROFIL]
                  + ["part du CA (%)", "en retard (%)", "plusieurs commandes (%)"])


def main() -> int:
    proteger_sorties()
    z = pd.read_csv(config.PREPARES_APPRENTISSAGE, index_col="customer_unique_id")
    x = z[config.VARIABLES_PROFIL].to_numpy(dtype=float)
    lab = pd.read_csv(config.PARTITIONS, index_col="customer_unique_id").loc[z.index]
    prof = pd.read_csv(config.PROFILS_APPRENTISSAGE, index_col="customer_unique_id").loc[z.index]
    publies = pd.read_csv(config.INDICES_PARTITIONS)
    publies = publies[publies["methode"] == "K-Means (8 variables)"].set_index("k")

    position = pd.Series(np.arange(len(z)), index=z.index)
    i_commun = position[P.ordre_echantillon(z.index, config.GRAINE)
                        [:config.N_ECHANTILLON_COMMUN]].to_numpy()

    # 1. Valeurs exactes recalculées à partir des étiquettes enregistrées.
    t = []
    for k in config.K_VALEURS:
        e = lab[f"kmeans_k{k}"].to_numpy()
        ind = P.indices_internes(x, e, x[i_commun], e[i_commun])
        t.append({"k": k, **ind,
                  "plus_petit_pct": 100 * np.bincount(e).min() / len(e),
                  "ari_boot_moyen": publies.loc[k, "ari_boot_moyen"],
                  "jaccard_min": publies.loc[k, "jaccard_min"]})
    t = pd.DataFrame(t).set_index("k")
    ecart_publie = max(abs(t.loc[k, c] - publies.loc[k, c]) / abs(publies.loc[k, c])
                       for k in t.index for c in ("silhouette", "calinski_harabasz",
                                                  "davies_bouldin"))
    choix = R.choisir_k(t)
    k = choix["k"]

    # 2. Les 50 ARI du k obtenu (mêmes tirages que le calcul publié).
    ref = lab[f"kmeans_k{k}"].to_numpy()
    b = P.stabilite_bootstrap(x, {k: ref}, config.TIRAGES_BOOTSTRAP_K, config.N_INIT_BOOTSTRAP,
                              config.GRAINE, garder_partitions=True)[k]
    ari = b["ari"]
    np.save(config.DOSSIER_PROCESSED / f"bootstrap_k{k}_partitions.npy", b["partitions"])
    bas = np.where(ari < R.ARI_MIN)[0]

    md = ["# Application de la règle de choix de k", "",
          "Rapport généré par `scripts/choisir_k.py`. Règle appliquée telle qu'écrite dans "
          "`docs/CHOIX.md` (poussée avant tout calcul). **Aucun avis chargé.**", "",
          "## 1. Valeurs exactes (toutes les décimales)", "",
          "Silhouette (échantillon commun de 8 000), Calinski-Harabasz et Davies-Bouldin "
          "recalculés à partir des étiquettes enregistrées (écart relatif maximal avec les "
          f"valeurs publiées, arrondies à 6 chiffres : {ecart_publie:.1e}). ARI bootstrap moyen "
          "et Jaccard le plus faible : valeurs publiées (6 chiffres significatifs).", "",
          tableau(["k", "plus petit segment (%)", "ARI bootstrap moyen", "Jaccard le plus faible",
                   "silhouette", "Calinski-Harabasz", "Davies-Bouldin"],
                  [[kk, repr(float(r.plus_petit_pct)), repr(float(r.ari_boot_moyen)),
                    repr(float(r.jaccard_min)), repr(float(r.silhouette)),
                    repr(float(r.calinski_harabasz)), repr(float(r.davies_bouldin))]
                   for kk, r in t.iterrows()]), "",
          "## 2. Admissibilité", "",
          "(a) plus petit segment ≥ 2 % ; (b) ARI bootstrap moyen ≥ 0,80 ; (c) Jaccard moyen de "
          "chaque segment ≥ 0,60.", "",
          tableau(["k", "(a)", "(b)", "(c)", "admissible"],
                  [[kk, *("oui" if v else "non" for v in r)]
                   for kk, r in choix["admissibilite"].iterrows()]), ""]
    if choix["rangs"] is not None:
        r = choix["rangs"]
        md += ["## 3. Rangs parmi les k admissibles (1 = meilleur)", "",
               "Silhouette : la plus haute = 1 ; Calinski-Harabasz : le plus haut = 1 ; "
               "Davies-Bouldin : le plus bas = 1. La plus petite somme gagne ; égalité : le plus "
               "petit k.", "",
               tableau(["k", "rang silhouette", "rang Calinski-Harabasz", "rang Davies-Bouldin",
                        "somme"],
                       [[kk, *row] for kk, row in r.iterrows()]), ""]
    md += [f"**k obtenu : {k}** ({choix['voie']}).", "",
           f"## 4. Les 50 ARI bootstrap pour k = {k}", "",
           f"Moyenne recalculée : {float(ari.mean())!r} (publiée : "
           f"{float(publies.loc[k, 'ari_boot_moyen'])!r}) ; minimum {ari.min():.4f} ; médiane "
           f"{np.median(ari):.4f}.", "",
           f"**Tirages sous 0,80 : {len(bas)} sur {len(ari)}.**", "",
           tableau(["tranche d'ARI", "tirages"],
                   [[lab_, int(((ari >= lo) & (ari < hi)).sum())]
                    for lab_, lo, hi in (("< 0,40", 0, .4), ("0,40 – 0,60", .4, .6),
                                         ("0,60 – 0,80", .6, .8), ("0,80 – 0,90", .8, .9),
                                         ("0,90 – 0,95", .9, .95), ("≥ 0,95", .95, 1.01))]), "",
           "ARI de chaque tirage (dans l'ordre) : " + ", ".join(f"{a:.3f}" for a in ari), ""]

    if len(bas):
        parts = b["partitions"][bas]
        accord = [adjusted_rand_score(parts[i], parts[j])
                  for i in range(len(bas)) for j in range(i + 1, len(bas))]
        pire = bas[np.argmin(ari[bas])]
        e_alt = P.renumeroter_par_taille(b["partitions"][pire])
        croise = pd.crosstab(pd.Series(ref, name="référence"),
                             pd.Series(e_alt, name="concurrente"), normalize="index") * 100
        md += [f"## 5. La découpe « concurrente » (tirages sous 0,80)", "",
               f"Accord entre les {len(bas)} partitions concurrentes : ARI de "
               f"{min(accord):.3f} à {max(accord):.3f}"
               + (" (elles se ressemblent : c'est une seule et même autre découpe)."
                  if accord and min(accord) > 0.8 else ".") if accord else "", "",
               f"Tirage le plus éloigné (n° {pire + 1}, ARI {ari[pire]:.3f}) : répartition de "
               "chaque segment de référence (lignes, en %) dans les segments de la découpe "
               "concurrente (colonnes).", "",
               tableau(["référence \\ concurrente"] + [f"C{c}" for c in croise.columns],
                       [[f"S{s}"] + [f"{v:.1f}" for v in row] for s, row in croise.iterrows()]),
               "", "Profil des segments de la découpe concurrente (médianes, unités d'origine) :",
               "", tableau(ENTETES_PROFIL, lignes_profil(profil(prof, e_alt),
                                                         lambda s: f"C{s}")), ""]

    md += [f"## 6. Profil des {k} segments retenus par la règle (médianes, unités d'origine)",
           "", "Segments numérotés du plus grand au plus petit. Montants en R$.", "",
           tableau(ENTETES_PROFIL, lignes_profil(profil(prof, ref), lambda s: f"S{s}")), "",
           "**Ce rapport n'est pas un choix final** : le critère métier (règle 4) reste à "
           "juger, et rien n'est commité avant cela. Aucun avis n'a été chargé.", ""]
    (config.DOSSIER_RAPPORTS / "choix_k.md").write_text("\n".join(md), encoding="utf-8",
                                                        newline="\n")
    print(f"k obtenu par la règle : {k} ; tirages sous 0,80 : {len(bas)} / {len(ari)}")
    print("Rapport : reports/choix_k.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Explicabilité des segments (module 5) : profils, arbre de substitution, explication d'un client.

Règles fixées et poussées avant tout calcul (docs/CHOIX.md, « Étape 6 »). L'arbre est converti
en une structure simple (listes) : la prédiction et les phrases n'ont pas besoin de scikit-learn.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

SEUIL_FRONTIERE = 0.90
CENTILE_ATYPIQUE = 0.95
FIDELITE_PROFONDEUR_3 = 0.90
GAIN_MIN_PROFONDEUR_4 = 0.03
VARIABLE_EN_DIFFERENCE = "ecart_prevision_moy_j"

# Libellé, unité, décimales d'affichage.
LIBELLES = {
    "recence_j": ("Récence", "jours", 1),
    "frequence": ("Nombre de commandes", "", 1),
    "montant_rs": ("Montant", "R$", 2),
    "part_frais_port": ("Part des frais de port", "", 2),
    "mensualites_moy": ("Mensualités moyennes", "", 1),
    "articles_par_commande": ("Articles par commande", "", 1),
    "delai_livraison_moy_j": ("Délai de livraison moyen", "jours", 1),
    "ecart_prevision_moy_j": ("Écart à la date promise", "jours", 1),
}


def nombre(v: float, decimales: int) -> str:
    """Nombre à la française : espace pour les milliers, virgule décimale."""
    return f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")


def avec_unite(variable: str, v: float) -> str:
    _, unite, d = LIBELLES[variable]
    return nombre(v, d) + (f" {unite}" if unite else "")


# --- Profils ------------------------------------------------------------------------------

def indices_profil(prof: pd.DataFrame, seg: pd.Series, variables: list[str]) -> pd.DataFrame:
    """Moyenne du segment / moyenne globale ; différence (en unités) pour l'écart à la date promise."""
    moy_seg = prof[variables].groupby(seg).mean()
    moy_glob = prof[variables].mean()
    ip = moy_seg / moy_glob
    if VARIABLE_EN_DIFFERENCE in variables:
        ip[VARIABLE_EN_DIFFERENCE] = moy_seg[VARIABLE_EN_DIFFERENCE] - moy_glob[VARIABLE_EN_DIFFERENCE]
    return ip


def part_ca(prof: pd.DataFrame, seg: pd.Series) -> pd.Series:
    return 100 * prof["montant_rs"].groupby(seg).sum() / prof["montant_rs"].sum()


# --- Arbre de substitution ------------------------------------------------------------------

def apprendre_arbre(x: pd.DataFrame, y: pd.Series, profondeur: int, feuille_min: int,
                    graine: int) -> dict:
    m = DecisionTreeClassifier(max_depth=profondeur, min_samples_leaf=feuille_min,
                               criterion="gini", random_state=graine).fit(x.to_numpy(), y.to_numpy())
    t = m.tree_
    classes = [int(c) for c in m.classes_]
    # Effectifs par classe dans chaque nœud (scikit-learn ≥ 1.4 stocke des fractions).
    effectifs = (t.value[:, 0, :] * t.n_node_samples[:, None]).round().astype(int)
    return {
        "profondeur": profondeur, "variables": list(x.columns), "classes": classes,
        "gauche": t.children_left.tolist(), "droite": t.children_right.tolist(),
        "variable": t.feature.tolist(), "seuil": t.threshold.tolist(),
        "effectifs": effectifs.tolist(),
    }


def predire_arbre(arbre: dict, x: pd.DataFrame) -> np.ndarray:
    """Prédiction sans scikit-learn : gauche si valeur ≤ seuil, sinon droite."""
    v = x[arbre["variables"]].to_numpy(dtype=float)
    sortie = np.empty(len(v), dtype=int)
    for i, ligne in enumerate(v):
        n = 0
        while arbre["gauche"][n] != -1:
            n = arbre["gauche"][n] if ligne[arbre["variable"][n]] <= arbre["seuil"][n] \
                else arbre["droite"][n]
        sortie[i] = arbre["classes"][int(np.argmax(arbre["effectifs"][n]))]
    return sortie


def choisir_profondeur(fidelite_3: float, fidelite_4: float) -> int:
    """Règle fixée : 3 si ≥ 90 % ; sinon 4 si gain ≥ 3 points ; sinon 3."""
    if fidelite_3 >= FIDELITE_PROFONDEUR_3:
        return 3
    return 4 if fidelite_4 - fidelite_3 >= GAIN_MIN_PROFONDEUR_4 - 1e-12 else 3


def regles(arbre: dict) -> list[dict]:
    """Une règle par feuille : intervalles par variable, segment majoritaire, effectif, pureté."""
    sortie = []

    def parcourir(n, bornes):
        if arbre["gauche"][n] == -1:
            eff = arbre["effectifs"][n]
            total = sum(eff)
            j = int(np.argmax(eff))
            sortie.append({"conditions": {v: list(b) for v, b in bornes.items()},
                           "segment": arbre["classes"][j], "clients": total,
                           "purete": eff[j] / total})
            return
        v = arbre["variables"][arbre["variable"][n]]
        s = arbre["seuil"][n]
        bas, haut = bornes.get(v, (None, None))
        parcourir(arbre["gauche"][n], {**bornes, v: (bas, s if haut is None else min(haut, s))})
        parcourir(arbre["droite"][n], {**bornes, v: (s if bas is None else max(bas, s), haut)})

    parcourir(0, {})
    return sortie


# Sujet de la phrase et genre (pour « supérieur » / « supérieure »).
SUJETS = {
    "recence_j": ("la récence", "f"),
    "frequence": ("le nombre de commandes", "m"),
    "montant_rs": ("le montant", "m"),
    "part_frais_port": ("la part des frais de port", "f"),
    "mensualites_moy": ("le nombre moyen de mensualités", "m"),
    "articles_par_commande": ("le nombre moyen d'articles par commande", "m"),
    "delai_livraison_moy_j": ("le délai de livraison moyen", "m"),
    "ecart_prevision_moy_j": ("l'écart à la date promise", "m"),
}


# Variables à valeurs entières : seuils affichés sous forme naturelle (« au moins 2 commandes »).
VARIABLES_ENTIERES = {"frequence": "commande"}


def _commandes(n: int, mot: str) -> str:
    return f"{n} {mot}{'s' if n > 1 else ''}"


def condition_en_mots(variable: str, bas, haut) -> str:
    if variable in VARIABLES_ENTIERES:
        mot = VARIABLES_ENTIERES[variable]
        mini = None if bas is None else math.floor(bas) + 1   # x > 1,5  ⇔  x ≥ 2
        maxi = None if haut is None else math.floor(haut)     # x ≤ 1,5  ⇔  x ≤ 1
        if mini is not None and maxi is not None:
            return (f"le client a exactement {_commandes(mini, mot)}" if mini == maxi
                    else f"le client a entre {mini} et {_commandes(maxi, mot)}")
        if maxi is not None:
            return f"le client a au plus {_commandes(maxi, mot)}"
        return f"le client a au moins {_commandes(mini, mot)}"
    sujet, genre = SUJETS[variable]
    if bas is not None and haut is not None:
        return f"{sujet} est entre {avec_unite(variable, bas)} et {avec_unite(variable, haut)}"
    if haut is not None:
        return f"{sujet} est au plus de {avec_unite(variable, haut)}"
    return f"{sujet} est supérieur{'e' if genre == 'f' else ''} à {avec_unite(variable, bas)}"


def phrase(regle: dict, noms_segments: dict[int, str]) -> str:
    conds = [condition_en_mots(v, b[0], b[1]) for v, b in regle["conditions"].items()]
    debut = "Si " + (", ".join(conds[:-1]) + " et " + conds[-1] if len(conds) > 1 else conds[0])
    s = regle["segment"]
    return (f"{debut}, alors le client est le plus souvent dans S{s} « {noms_segments[s]} » "
            f"({nombre(100 * regle['purete'], 0)} % des {nombre(regle['clients'], 0)} clients "
            "de cette règle).")


# --- Explication d'un client --------------------------------------------------------------

def distances(z: np.ndarray, centres: np.ndarray) -> np.ndarray:
    return np.sqrt(((z[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2))


def seuils_atypiques(z: np.ndarray, seg: np.ndarray, centres: np.ndarray) -> list[float]:
    d = distances(z, centres)[np.arange(len(z)), seg]
    return [float(np.quantile(d[seg == s], CENTILE_ATYPIQUE)) for s in range(len(centres))]


def diagnostic(z: np.ndarray, centres: np.ndarray, seuils: list[float]) -> pd.DataFrame:
    """Segment, distances, frontière et atypique pour chaque ligne de z (préparée)."""
    d = distances(z, centres)
    ordre = np.argsort(d, axis=1)
    seg = ordre[:, 0]
    d1 = d[np.arange(len(z)), seg]
    d2 = d[np.arange(len(z)), ordre[:, 1]]
    return pd.DataFrame({"segment": seg, "distance": d1, "segment_2": ordre[:, 1],
                         "distance_2": d2, "rapport": d1 / d2,
                         "frontiere": d1 / d2 >= SEUIL_FRONTIERE,
                         "atypique": d1 > np.asarray(seuils)[seg]})


def principales(ecarts: np.ndarray, variables: list[str], n: int = 3) -> list[tuple[str, float, float]]:
    """(variable, part dans la distance, écart signé) des n variables qui pèsent le plus."""
    carres = ecarts ** 2
    total = carres.sum()
    ordre = np.argsort(-carres, kind="stable")[:n]
    return [(variables[i], float(carres[i] / total) if total > 0 else math.nan,
             float(ecarts[i])) for i in ordre]


def expliquer(z_client: np.ndarray, brut_client: pd.Series, centres: np.ndarray,
              seuils: list[float], variables: list[str], moyennes: dict, medianes: dict) -> dict:
    """Explication complète d'un client (z_client : ses 8 variables préparées)."""
    diag = diagnostic(z_client[None, :], centres, seuils).iloc[0]
    s = int(diag["segment"])

    def detail(liste):
        return [{"variable": v, "part": p, "sens": "au-dessus" if e > 0 else "en dessous",
                 "valeur": float(brut_client[v]), "moyenne_globale": moyennes[v],
                 "mediane_segment": medianes[s][v]} for v, p, e in liste]

    return {
        "segment": s, "distance": float(diag["distance"]),
        "segment_2": int(diag["segment_2"]), "distance_2": float(diag["distance_2"]),
        "frontiere": bool(diag["frontiere"]), "atypique": bool(diag["atypique"]),
        "seuil_atypique": seuils[s],
        "loin_du_client_moyen": detail(principales(z_client, variables)),
        "loin_du_centre_du_segment": detail(principales(z_client - centres[s], variables)),
    }

"""ACP normée apprise sur les clients d'apprentissage préparés (étape 3).

Les données d'entrée sont déjà standardisées (moyenne 0, écart-type 1 sur les 80 %) :
la matrice de covariance est donc la matrice des corrélations, et l'ACP est normée.
`apprendre` calcule les axes ; `projeter` les réutilise sans rien réapprendre.
Règles (nombre d'axes, noms, axe du temps) : voir docs/CHOIX.md, fixées avant le calcul.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = 1


def nombre_axes(valeurs_propres, part_minimale: float) -> dict:
    """Règle fixée : max(Kaiser strict > 1, plus petit nombre d'axes atteignant la part)."""
    vp = np.asarray(valeurs_propres, dtype=float)
    part_cumulee = np.cumsum(vp) / vp.sum()
    kaiser = int((vp > 1).sum())
    cumul = int(np.argmax(part_cumulee >= part_minimale - 1e-12) + 1)
    chutes = vp[:-1] - vp[1:]
    return {
        "kaiser": kaiser,
        "part_cumulee": cumul,
        # Indication seulement (le coude ne décide pas) : axe après lequel la chute est maximale.
        "coude_indicatif": int(np.argmax(chutes) + 1),
        "retenus": max(kaiser, cumul),
    }


def apprendre(z: pd.DataFrame, variables: list[str], part_minimale: float) -> dict:
    x = z[variables].to_numpy(dtype=float)
    if np.isnan(x).any():
        raise ValueError("Valeurs manquantes dans les données préparées.")
    moyenne = x.mean(axis=0)
    xc = x - moyenne
    covariance = xc.T @ xc / len(x)
    vp, vecteurs = np.linalg.eigh(covariance)
    ordre = np.argsort(vp)[::-1]
    vp, vecteurs = vp[ordre], vecteurs[:, ordre]
    # Convention de sens : la variable au plus grand |coefficient| est du côté positif.
    for j in range(vecteurs.shape[1]):
        if vecteurs[np.argmax(np.abs(vecteurs[:, j])), j] < 0:
            vecteurs[:, j] = -vecteurs[:, j]
    decision = nombre_axes(vp, part_minimale)
    return {
        "version": VERSION,
        "variables": list(variables),
        "clients_apprentissage": len(x),
        "part_minimale": part_minimale,
        "moyenne": moyenne.tolist(),
        "valeurs_propres": vp.tolist(),
        "vecteurs": vecteurs.tolist(),  # lignes = variables, colonnes = axes
        "decision": decision,
    }


def noms_axes(acp: dict) -> list[str]:
    return [f"F{j + 1}" for j in range(len(acp["valeurs_propres"]))]


def projeter(z: pd.DataFrame, acp: dict, n_axes: int | None = None) -> pd.DataFrame:
    """Coordonnées des clients sur les axes (non restandardisées)."""
    manquantes = [v for v in acp["variables"] if v not in z.columns]
    if manquantes:
        raise ValueError(f"Variables manquantes : {manquantes}")
    x = z[acp["variables"]].to_numpy(dtype=float) - np.asarray(acp["moyenne"])
    f = x @ np.asarray(acp["vecteurs"])
    noms = noms_axes(acp)
    k = n_axes or len(noms)
    return pd.DataFrame(f[:, :k], index=z.index, columns=noms[:k])


def correlations(acp: dict) -> pd.DataFrame:
    """Corrélation variable–axe (ACP normée) = coefficient × racine(valeur propre)."""
    v = np.asarray(acp["vecteurs"]) * np.sqrt(np.asarray(acp["valeurs_propres"]))
    return pd.DataFrame(v, index=acp["variables"], columns=noms_axes(acp))


def cos2(acp: dict) -> pd.DataFrame:
    return correlations(acp) ** 2


def contributions(acp: dict) -> pd.DataFrame:
    """Part (%) de chaque variable dans la construction de chaque axe."""
    return pd.DataFrame(100 * np.asarray(acp["vecteurs"]) ** 2,
                        index=acp["variables"], columns=noms_axes(acp))


def description_axe(corr: pd.Series, seuil: float = 0.5) -> dict:
    """Variables qui nomment l'axe (|corr| ≥ seuil, sinon les 2 plus fortes) et ses pôles."""
    fortes = corr[corr.abs() >= seuil]
    regle = f"|corrélation| ≥ {seuil:g}"
    if fortes.empty:
        fortes = corr.reindex(corr.abs().sort_values(ascending=False).index[:2])
        regle = "aucune ≥ seuil : les 2 plus fortes"
    fortes = fortes.reindex(fortes.abs().sort_values(ascending=False).index)
    return {
        "regle": regle,
        "variables": fortes.round(2).to_dict(),
        "pole_plus": [f"{v} élevé" if c > 0 else f"{v} faible" for v, c in fortes.items()],
        "pole_moins": [f"{v} faible" if c > 0 else f"{v} élevé" for v, c in fortes.items()],
    }


def axe_du_temps(corr_recence: float, corr_date: float, seuil: float = 0.5) -> bool:
    """Règle fixée : |corr(Récence, axe)| ≥ 0,5 ET |corr(coordonnées, date d'achat)| ≥ 0,5."""
    return abs(corr_recence) >= seuil and abs(corr_date) >= seuil


def cosinus_sous_espaces(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    """Cosinus des angles principaux entre deux sous-espaces (colonnes orthonormées),
    du plus grand au plus petit. Tous à 1 : sous-espaces identiques, même si les axes
    ont tourné à l'intérieur."""
    return np.clip(np.linalg.svd(v1.T @ v2, compute_uv=False), 0, 1)


def stabilite_bootstrap(z: pd.DataFrame, acp: dict, n_tirages: int, graine: int,
                        blocs: dict[str, list[int]]) -> pd.DataFrame:
    """Refait l'ACP sur `n_tirages` tirages avec remise des mêmes clients et compare.

    Renvoie, par tirage : |cos| entre chaque axe du tirage et l'axe de même rang d'origine,
    le meilleur |cos| parmi tous les axes du tirage, le plus petit cosinus principal de
    chaque bloc d'axes (sous-espace), les valeurs propres et le nombre d'axes retenus
    par la règle. Description seulement : rien n'est modifié.
    """
    x = z[acp["variables"]]
    v0 = np.asarray(acp["vecteurs"])
    rng = np.random.default_rng(graine)
    lignes = []
    for t in range(n_tirages):
        idx = rng.integers(0, len(x), len(x))
        b = apprendre(x.iloc[idx].reset_index(drop=True), acp["variables"], acp["part_minimale"])
        vb = np.asarray(b["vecteurs"])
        produit = np.abs(v0.T @ vb)  # [axe d'origine, axe du tirage]
        ligne = {"tirage": t, "retenus": b["decision"]["retenus"]}
        for j in range(v0.shape[1]):
            ligne[f"cos_F{j + 1}"] = float(produit[j, j])
            ligne[f"meilleur_F{j + 1}"] = float(produit[j].max())
            ligne[f"vp_F{j + 1}"] = b["valeurs_propres"][j]
        for nom, axes in blocs.items():
            ligne[f"bloc_{nom}"] = float(cosinus_sous_espaces(v0[:, axes], vb[:, axes]).min())
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def sauver(acp: dict, chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(acp, f, ensure_ascii=False, indent=2)
        f.write("\n")


def charger(chemin: Path) -> dict:
    acp = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if acp.get("version") != VERSION:
        raise ValueError(f"Version d'ACP inattendue : {acp.get('version')}")
    return acp

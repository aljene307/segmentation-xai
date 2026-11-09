"""Préparation des variables : log → écrêtage → standardisation.

`apprendre` calcule les paramètres sur les clients d'apprentissage (80 %) seulement.
`appliquer` les réutilise tels quels (aux 20 % mis de côté, à un nouveau client) :
elle n'apprend rien. Les paramètres tiennent dans un petit fichier JSON.

Règle du log (docs/CHOIX.md) : log(1 + x) pour une variable positive et sans borne
haute, si son asymétrie dépasse le seuil et si le log la réduit.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

VERSION = 1


def decision_log(x: pd.Series, bornee: bool, seuil: float) -> tuple[bool, float, float | None, str]:
    """(log ?, asymétrie brute, asymétrie après log, raison) pour une variable."""
    asym = float(x.skew())
    if bornee:
        return False, asym, None, "proportion bornée : hors de la règle"
    if (x < 0).any():
        return False, asym, None, "valeurs négatives : hors de la règle"
    asym_log = float(np.log1p(x).skew())
    if abs(asym) <= seuil:
        return False, asym, asym_log, f"asymétrie ≤ {seuil:g}"
    if abs(asym_log) >= abs(asym):
        return False, asym, asym_log, "le log ne réduit pas l'asymétrie"
    return True, asym, asym_log, "positive, sans borne, asymétrique : log"


def apprendre(
    df: pd.DataFrame,
    variables: list[str],
    bornees: list[str],
    seuil_asymetrie: float,
    centiles: tuple[float, float],
) -> dict:
    parametres = {}
    for v in variables:
        x = df[v].astype(float)
        if x.isna().any():
            raise ValueError(f"Valeurs manquantes dans {v!r}")
        log, asym, asym_log, raison = decision_log(x, v in bornees, seuil_asymetrie)
        xt = np.log1p(x) if log else x
        bas, haut = (float(q) for q in xt.quantile(list(centiles)))
        xc = xt.clip(bas, haut)
        parametres[v] = {
            "log": log, "raison": raison,
            "asymetrie_brute": asym, "asymetrie_log": asym_log,
            "bas": bas, "haut": haut,
            "moyenne": float(xc.mean()), "ecart_type": float(xc.std(ddof=0)),
        }
    return {"version": VERSION, "variables": list(variables), "centiles": list(centiles),
            "seuil_asymetrie": seuil_asymetrie, "clients_apprentissage": len(df),
            "parametres": parametres}


def _verifier(df: pd.DataFrame, prep: dict) -> None:
    manquantes = [v for v in prep["variables"] if v not in df.columns]
    if manquantes:
        raise ValueError(f"Variables manquantes : {manquantes}")
    if df[prep["variables"]].isna().any().any():
        raise ValueError("Valeurs manquantes : impossible de préparer ce client.")
    for v in prep["variables"]:
        if prep["parametres"][v]["log"] and (df[v] < 0).any():
            raise ValueError(f"Valeur négative impossible pour {v!r}")


def transformer(df: pd.DataFrame, prep: dict) -> pd.DataFrame:
    """Applique le log éventuel (échelle sur laquelle les seuils sont définis)."""
    _verifier(df, prep)
    return pd.DataFrame({
        v: np.log1p(df[v].astype(float)) if prep["parametres"][v]["log"] else df[v].astype(float)
        for v in prep["variables"]
    }, index=df.index)


def ecretages(df: pd.DataFrame, prep: dict) -> pd.DataFrame:
    """Vrai si la valeur (après log) est hors des seuils appris, par variable."""
    t = transformer(df, prep)
    p = prep["parametres"]
    return pd.DataFrame({v: (t[v] < p[v]["bas"]) | (t[v] > p[v]["haut"])
                         for v in prep["variables"]}, index=df.index)


def appliquer(df: pd.DataFrame, prep: dict) -> pd.DataFrame:
    """Log → écrêtage → standardisation, avec les paramètres appris (rien n'est réappris)."""
    t = transformer(df, prep)
    p = prep["parametres"]
    return pd.DataFrame({
        v: (t[v].clip(p[v]["bas"], p[v]["haut"]) - p[v]["moyenne"]) / p[v]["ecart_type"]
        for v in prep["variables"]
    }, index=df.index)


def indicateur_ecretage(df: pd.DataFrame, prep: dict) -> pd.DataFrame:
    """Colonnes de description : écrêté (oui/non) et variables concernées."""
    e = ecretages(df, prep)
    return pd.DataFrame({
        "ecrete": e.any(axis=1),
        "variables_ecretees": e.apply(lambda r: ";".join(r.index[r]), axis=1),
    }, index=df.index)


def seuils_en_unites(prep: dict) -> dict[str, tuple[float, float]]:
    """Seuils ramenés dans l'unité d'origine (inverse du log), pour les lire facilement."""
    out = {}
    for v, p in prep["parametres"].items():
        f = np.expm1 if p["log"] else (lambda y: y)
        out[v] = (float(f(p["bas"])), float(f(p["haut"])))
    return out


def sauver(prep: dict, chemin: Path) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(prep, f, ensure_ascii=False, indent=2)
        f.write("\n")


def charger(chemin: Path) -> dict:
    prep = json.loads(Path(chemin).read_text(encoding="utf-8"))
    if prep.get("version") != VERSION:
        raise ValueError(f"Version de préparation inattendue : {prep.get('version')}")
    return prep

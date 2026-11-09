"""Chargement des tables Olist.

La table des avis n'est JAMAIS renvoyée par `charger_tables` : elle ne s'obtient
qu'avec `charger_avis`, utilisée uniquement pour l'évaluation externe.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from segmentation import config

# Les codes postaux sont des identifiants : on les lit en texte pour garder les zéros initiaux.
_TEXTE = {
    "clients": {"customer_zip_code_prefix": str},
    "vendeurs": {"seller_zip_code_prefix": str},
    "geolocalisation": {"geolocation_zip_code_prefix": str},
}


def charger_table(nom: str, dossier: Path = config.DOSSIER_OLIST) -> pd.DataFrame:
    if nom not in config.TABLES:
        raise KeyError(f"Table inconnue ou réservée à l'évaluation : {nom!r}")
    return pd.read_csv(
        dossier / config.TABLES[nom],
        dtype=_TEXTE.get(nom),
        parse_dates=config.COLONNES_DATES.get(nom, []),
    )


def charger_tables(
    dossier: Path = config.DOSSIER_OLIST, sauf: tuple[str, ...] = ()
) -> dict[str, pd.DataFrame]:
    """Toutes les tables utilisables pour le profil client (sans les avis)."""
    return {nom: charger_table(nom, dossier) for nom in config.TABLES if nom not in sauf}


def charger_avis(dossier: Path = config.DOSSIER_OLIST) -> pd.DataFrame:
    """Table des avis : réservée à l'évaluation externe des segments."""
    return pd.read_csv(dossier / config.TABLE_AVIS, parse_dates=config.COLONNES_DATES_AVIS)

"""Données reçues par l'API : les 8 variables du profil client, en unités d'origine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# Contrainte de chaque variable, en français (reprise dans les messages d'erreur 422).
CONTRAINTES = {
    "recence_j": "doit être positive ou nulle (jours depuis le dernier achat)",
    "frequence": "doit être un nombre entier ≥ 1 (commandes livrées)",
    "montant_rs": "doit être strictement positif (R$, prix des articles)",
    "part_frais_port": "doit être comprise entre 0 et 1 (1 exclu)",
    "mensualites_moy": "doit être au moins 1",
    "articles_par_commande": "doit être au moins 1",
    "delai_livraison_moy_j": "doit être positif ou nul (jours ; 0 = livré le jour même)",
    "ecart_prevision_moy_j": "doit être un nombre fini (jours ; négatif = en avance)",
}


class Client(BaseModel):
    """Profil d'un client : les 8 variables en unités d'origine (montants en R$)."""

    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False,
        json_schema_extra={"examples": [{
            "recence_j": 120, "frequence": 1, "montant_rs": 89.9, "part_frais_port": 0.18,
            "mensualites_moy": 2, "articles_par_commande": 1, "delai_livraison_moy_j": 9.5,
            "ecart_prevision_moy_j": -12}]})

    recence_j: float = Field(ge=0, description="Jours entre le dernier achat et la date de référence")
    frequence: int = Field(ge=1, description="Nombre de commandes livrées")
    montant_rs: float = Field(gt=0, description="Somme des prix des articles, en R$")
    part_frais_port: float = Field(ge=0, lt=1, description="Frais de port / (prix + frais)")
    mensualites_moy: float = Field(ge=1, description="Nombre moyen de mensualités par commande")
    articles_par_commande: float = Field(ge=1, description="Nombre moyen d'articles par commande")
    delai_livraison_moy_j: float = Field(ge=0, description="Délai moyen achat → livraison, en jours")
    ecart_prevision_moy_j: float = Field(description="Livraison − date promise, en jours (> 0 = retard)")


class Lot(BaseModel):
    """Lot de clients pour /affecter/lot (1 à 1 000). Chaque client est validé séparément."""

    model_config = ConfigDict(extra="forbid")
    clients: list[Any] = Field(min_length=1, max_length=1000)

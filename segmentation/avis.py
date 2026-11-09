"""Note d'avis ramenée au client, selon la règle écrite et poussée avant tout calcul de partition.

- seuls les avis des commandes retenues du client comptent ;
- une note par commande : l'avis le plus récent (date de réponse, puis date de création,
  puis review_id par ordre alphabétique) ;
- note du client = moyenne des notes de ses commandes ;
- « satisfait » si la note du client vaut au moins 4 ;
- clients sans avis : aucune valeur inventée (exclus des indices externes).
"""

from __future__ import annotations

import pandas as pd

SEUIL_SATISFAIT = 4


def note_par_commande(avis: pd.DataFrame) -> pd.Series:
    """Une note par commande : l'avis le plus récent."""
    a = avis.sort_values(
        ["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
        ascending=[True, False, False, True], na_position="last")
    return a.drop_duplicates("order_id").set_index("order_id")["review_score"]


def note_client(avis: pd.DataFrame, commandes_clients: pd.Series) -> pd.DataFrame:
    """`commandes_clients` : customer_unique_id indexé par order_id (commandes retenues).

    Renvoie, pour les clients qui ont au moins une note : note moyenne, nombre de
    commandes notées, et l'étiquette « satisfait »."""
    notes = note_par_commande(avis[avis["order_id"].isin(commandes_clients.index)])
    df = pd.DataFrame({"note": notes, "client": commandes_clients.reindex(notes.index)})
    g = df.groupby("client")["note"]
    res = pd.DataFrame({"note_client": g.mean(), "commandes_notees": g.size()})
    res["satisfait"] = res["note_client"] >= SEUIL_SATISFAIT
    res.index.name = "customer_unique_id"
    return res

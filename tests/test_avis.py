"""Tests de la règle qui ramène la note d'avis au client (petites tables construites à la main)."""

import pandas as pd

from segmentation.avis import note_client, note_par_commande

T = pd.Timestamp


def _avis():
    return pd.DataFrame({
        "review_id": ["r1", "r2", "r3", "r4", "r5", "r6"],
        "order_id": ["o1", "o1", "o2", "o3", "o4", "o9"],
        "review_score": [1, 5, 4, 2, 3, 1],
        "review_creation_date": [T("2018-01-01"), T("2018-01-05"), T("2018-02-01"),
                                 T("2018-03-01"), T("2018-03-01"), T("2018-04-01")],
        "review_answer_timestamp": [T("2018-01-02"), T("2018-01-06"), T("2018-02-02"),
                                    T("2018-03-02"), T("2018-03-02"), T("2018-04-02")],
    })


def test_avis_le_plus_recent_par_commande():
    n = note_par_commande(_avis())
    assert n["o1"] == 5  # r2 répondu après r1


def test_egalite_de_dates_review_id_alphabetique():
    a = _avis()
    a.loc[a["review_id"] == "r2", ["review_creation_date", "review_answer_timestamp"]] = [
        T("2018-01-01"), T("2018-01-02")]
    assert note_par_commande(a)["o1"] == 1  # mêmes dates : r1 avant r2


def test_note_client_moyenne_et_seuil():
    commandes = pd.Series({"o1": "A", "o2": "A", "o3": "B", "o4": "C", "o5": "D"})
    res = note_client(_avis(), commandes)
    assert res.loc["A", "note_client"] == 4.5 and res.loc["A", "commandes_notees"] == 2
    assert res.loc["A", "satisfait"]                       # 4,5 ≥ 4
    assert not res.loc["B", "satisfait"]                   # 2
    assert not res.loc["C", "satisfait"]                   # 3
    assert "D" not in res.index                            # sans avis : rien d'inventé


def test_avis_hors_commandes_retenues_ignores():
    res = note_client(_avis(), pd.Series({"o3": "B"}))
    assert list(res.index) == ["B"]  # o9 (et les autres) ne comptent pas

"""Tests de la comparaison à une tolérance près."""

from segmentation.comparaison import presque_egaux


def test_tolerance_sur_les_decimales_lointaines():
    a = {"v": [1.0, 2.0], "x": {"y": 0.1 + 0.2}, "nom": "F1", "log": True, "n": 3}
    b = {"v": [1.0, 2.0 + 1e-14], "x": {"y": 0.3}, "nom": "F1", "log": True, "n": 3}
    assert presque_egaux(a, b)


def test_vraie_difference_detectee():
    assert not presque_egaux({"v": [1.0]}, {"v": [1.0001]})
    assert not presque_egaux({"v": [1.0]}, {"v": [1.0, 2.0]})
    assert not presque_egaux({"a": 1}, {"b": 1})
    assert not presque_egaux({"log": True}, {"log": False})
    assert not presque_egaux("F1", "F2")

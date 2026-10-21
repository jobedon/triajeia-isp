import pandas as pd

from src.evaluate import ic_brecha_subgrupos


def _tabla(n_a, n_b, errores_b):
    filas = [{"g": "a", "y": c, "p": c} for c in ["x", "y"] * (n_a // 2)]
    filas += [{"g": "b", "y": c, "p": c} for c in ["x", "y"] * (n_b // 2)]
    for i in range(errores_b):  # en el grupo b, algunas «x» se predicen como «y»
        filas[n_a + 2 * i]["p"] = "y"
    filas += [{"g": "c", "y": "x", "p": "x"}] * 10  # grupo pequeño: no debe participar
    return pd.DataFrame(filas)


def test_ic_brecha_detecta_diferencia_y_excluye_grupos_pequenos():
    r = ic_brecha_subgrupos(_tabla(60, 60, 15), "g", "y", "p", n_minimo=30, n_boot=300)
    assert r["grupos"] == ["a", "b"]
    v, lo, hi = r["brecha"]
    assert lo <= v <= hi and lo > 0
    par = r["pares"][0]
    assert par["a"] == "a" and par["b"] == "b" and par["ic_inf"] > 0


def test_ic_brecha_sin_diferencia_incluye_cero():
    r = ic_brecha_subgrupos(_tabla(60, 60, 0), "g", "y", "p", n_minimo=30, n_boot=300)
    par = r["pares"][0]
    assert par["dif"] == 0 and par["ic_inf"] <= 0 <= par["ic_sup"]


def test_ic_brecha_con_un_solo_grupo_concluyente():
    r = ic_brecha_subgrupos(_tabla(60, 10, 0), "g", "y", "p", n_minimo=30, n_boot=50)
    assert r["brecha"] is None and r["pares"] == []

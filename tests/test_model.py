"""Pruebas del modelo, del clasificador de triaje y de las funciones de evaluación."""
import numpy as np
import pytest

from src.evaluate import con_erratas, ic_bootstrap, mcnemar, por_subgrupo, riesgo_cobertura, truncar
from src.model import ClasificadorTriaje, construir_svm

PARAMS = {"C": 0.3, "calibracion_cv": 2, "usar_caracteres": True}
AREAS = {"SIN_SERVICIO": "SOPORTE_TECNICO", "FACTURACION": "FACTURACION_COBRANZAS", "WIFI_EQUIPO": "SOPORTE_TECNICO"}


@pytest.fixture
def clasificador(corpus_pequeno):
    df = corpus_pequeno
    modelos = {o: construir_svm(PARAMS).fit(df["queja"], df[o]) for o in ("categoria", "prioridad")}
    return ClasificadorTriaje(modelos, AREAS, umbral=0.5)


def test_prediccion_tiene_formato_completo(clasificador):
    r = clasificador.predecir("me cobraron dos veces la factura de este mes")
    assert r["categoria"]["etiqueta"] in AREAS
    assert r["area_atencion"] == AREAS[r["categoria"]["etiqueta"]]
    assert abs(sum(r["categoria"]["distribucion"].values()) - 1) < 1e-6
    assert isinstance(r["requiere_revision_humana"], bool)
    assert all(isinstance(t, str) for t in r["terminos_influyentes"])


def test_umbral_alto_fuerza_revision_humana(clasificador):
    clasificador.umbral = 1.01
    assert clasificador.predecir("no tengo internet desde ayer")["requiere_revision_humana"] is True


def test_guardar_y_cargar(clasificador, tmp_path):
    p = clasificador.guardar(tmp_path / "m.joblib")
    otro = ClasificadorTriaje.cargar(p)
    texto = "el wifi no llega al cuarto de arriba"
    assert otro.predecir(texto)["categoria"] == clasificador.predecir(texto)["categoria"]
    with pytest.raises(FileNotFoundError):
        ClasificadorTriaje.cargar(tmp_path / "no_existe.joblib")


def test_mcnemar_e_ic():
    y = np.array(list("aabbccaabb"))
    assert mcnemar(y, y, y)["p"] == 1.0
    v, lo, hi = ic_bootstrap(y, y, n=200)
    assert v == lo == hi == 1.0


def test_subgrupos_marca_pocos_casos():
    import pandas as pd
    df = pd.DataFrame({"g": ["x"] * 40 + ["y"] * 5, "r": ["a", "b"] * 22 + ["a"], "p": ["a", "b"] * 22 + ["b"]})
    t = por_subgrupo(df, "g", "r", "p", n_minimo=30, n_boot=100).set_index("grupo")
    assert bool(t.loc["x", "concluyente"]) and not bool(t.loc["y", "concluyente"])


def test_riesgo_cobertura_y_perturbaciones():
    rc = riesgo_cobertura(["a", "b", "a"], ["a", "a", "a"], [0.9, 0.4, 0.8])
    assert rc.loc[rc["umbral"] == 0.0, "cobertura"].item() == 1.0
    assert rc.loc[rc["umbral"] == 0.5, "riesgo"].item() == 0.0
    assert truncar("uno dos tres cuatro", 0.5) == "uno dos"
    assert con_erratas("internet", 0.0) == "internet"

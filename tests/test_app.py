"""Pruebas de las funciones de la aplicación (sin levantar la interfaz)."""

import pandas as pd
import pytest

from app.app import EJEMPLOS, a_csv, alerta_prioridad, clasificar_lote, fila_historial, nombre
from src.data_processing import validar_entrada
from src.model import ClasificadorTriaje, construir_svm


def _resultado(prioridad, p_alta):
    return {
        "categoria": {"etiqueta": "SIN_SERVICIO", "probabilidad": 0.9, "distribucion": {}},
        "prioridad": {"etiqueta": prioridad, "probabilidad": 0.6, "distribucion": {"alta": p_alta}},
        "area_atencion": "SOPORTE_TECNICO",
        "requiere_revision_humana": False,
        "terminos_influyentes": ["internet"],
    }


@pytest.mark.parametrize(
    "prioridad, p_alta, esperado", [("alta", 0.9, False), ("media", 0.35, True), ("baja", 0.05, False)]
)
def test_alerta_prioridad(prioridad, p_alta, esperado):
    assert alerta_prioridad(_resultado(prioridad, p_alta)) is esperado


def test_ejemplos_son_validos():
    assert len(EJEMPLOS) >= 5
    assert all(validar_entrada(t)[0] for t in EJEMPLOS.values())


def test_historial_y_csv():
    fila = fila_historial("no hay internet desde ayer", _resultado("media", 0.3))
    assert fila["confirmar_prioridad"] is True
    contenido = a_csv([fila]).decode("utf-8-sig")
    assert contenido.splitlines()[0].startswith("hora,reclamo,categoria")
    assert nombre("SOPORTE_TECNICO") == "Soporte técnico" and nombre("OTRA") == "OTRA"


def test_clasificar_lote_marca_filas_invalidas(corpus_pequeno):
    modelos = {
        o: construir_svm({"calibracion_cv": 2}).fit(corpus_pequeno["queja"], corpus_pequeno[o])
        for o in ("categoria", "prioridad")
    }
    m = ClasificadorTriaje(modelos, {"SIN_SERVICIO": "S", "FACTURACION": "F", "WIFI_EQUIPO": "S"})
    res = clasificar_lote(m, pd.DataFrame({"q": ["me cobraron dos veces la factura", "😡"]}), "q")
    assert res.loc[0, "error"] == "" and res.loc[1, "error"] != ""


def test_indicadores_y_alertas():
    from app.app import alertas, indicadores

    ahora = pd.Timestamp.now(tz="America/Guayaquil")
    df = pd.DataFrame(
        {
            "fecha_hora": [ahora] * 10,
            "nombre": ["a"] * 5 + ["b"] * 5,
            "ip_hash": ["ip_1"] * 10,
            "decision": ["aceptada"] * 4 + ["corregida"] * 6,
            "requiere_revision": [True] * 3 + [False] * 7,
            "alerta_prioridad": [False] * 10,
            "conf_categoria": [0.9] * 10,
        }
    )
    ind = indicadores(df)
    assert ind["n"] == 10 and ind["personas"] == 2 and ind["aceptacion"] == 0.4 and abs(ind["abstencion"] - 0.3) < 1e-9
    msj = alertas(df)
    assert any("abstención" in m for m in msj) and any("aceptación" in m for m in msj)
    assert indicadores(df.iloc[0:0]) == {"n": 0} and alertas(df.iloc[0:0]) == []

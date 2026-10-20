"""Pruebas de las funciones de la aplicación (sin levantar la interfaz)."""
import pandas as pd
import pytest

from app.app import EJEMPLOS, a_csv, alerta_prioridad, clasificar_lote, fila_historial, nombre
from src.data_processing import validar_entrada
from src.model import ClasificadorTriaje, construir_svm


def _resultado(prioridad, p_alta):
    return {"categoria": {"etiqueta": "SIN_SERVICIO", "probabilidad": 0.9, "distribucion": {}},
            "prioridad": {"etiqueta": prioridad, "probabilidad": 0.6, "distribucion": {"alta": p_alta}},
            "area_atencion": "SOPORTE_TECNICO", "requiere_revision_humana": False, "terminos_influyentes": ["internet"]}


@pytest.mark.parametrize("prioridad, p_alta, esperado", [("alta", 0.9, False), ("media", 0.35, True), ("baja", 0.05, False)])
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
    modelos = {o: construir_svm({"calibracion_cv": 2}).fit(corpus_pequeno["queja"], corpus_pequeno[o])
               for o in ("categoria", "prioridad")}
    m = ClasificadorTriaje(modelos, {"SIN_SERVICIO": "S", "FACTURACION": "F", "WIFI_EQUIPO": "S"})
    res = clasificar_lote(m, pd.DataFrame({"q": ["me cobraron dos veces la factura", "😡"]}), "q")
    assert res.loc[0, "error"] == "" and res.loc[1, "error"] != ""

"""Datos mínimos compartidos por las pruebas (no usan el corpus completo)."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EJEMPLOS = {
    "SIN_SERVICIO": [
        "no tengo internet desde ayer",
        "se fue el internet completamente",
        "sin servicio en toda la casa",
        "no hay nada de señal de internet",
        "hace dos dias sin internet",
    ],
    "FACTURACION": [
        "me cobraron dos veces la factura",
        "la factura vino con un valor mayor",
        "pague y no registran el pago",
        "cobro excesivo en la planilla",
        "me facturaron un servicio cancelado",
    ],
    "WIFI_EQUIPO": [
        "el wifi no llega al cuarto",
        "el router tiene una luz roja",
        "no puedo cambiar la clave del wifi",
        "el celular no se conecta al wifi",
        "el modem se reinicia solo",
    ],
}


@pytest.fixture
def corpus_pequeno() -> pd.DataFrame:
    filas, i = [], 1
    for cat, textos in EJEMPLOS.items():
        for j, t in enumerate(textos * 2):
            filas.append(
                {
                    "id": i,
                    "conjunto": "prueba" if j % 5 == 0 else "entrenamiento",
                    "categoria": cat,
                    "prioridad": "alta" if cat == "SIN_SERVICIO" else "media",
                    "queja": f"{t} numero {i}",
                }
            )
            i += 1
    return pd.DataFrame(filas)

"""Pruebas del registro en base de datos (SQLite temporal)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

from src.registro import (
    anonimizar,
    clasificaciones,
    codigo_ip,
    conectar,
    leer,
    normalizar_url,
    purgar,
    registrar,
    registrar_decision,
)

RES = {
    "categoria": {"etiqueta": "SIN_SERVICIO", "probabilidad": 0.97},
    "area_atencion": "SOPORTE_TECNICO",
    "prioridad": {"etiqueta": "alta", "probabilidad": 0.9},
    "requiere_revision_humana": False,
}


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("mi cel es 0991234567", "mi cel es [TELÉFONO]"),
        ("llamen al +593 99 123 4567", "llamen al [TELÉFONO]"),
        ("cedula 1712345678 por favor", "cedula [CÉDULA] por favor"),
        ("escriban a ana.p@correo.com", "escriban a [CORREO]"),
        ("contrato 4455667 sin internet", "contrato [NÚMERO] sin internet"),
        ("pague $56.28 y 3 dias sin servicio", "pague $56.28 y 3 dias sin servicio"),
    ],
)
def test_anonimizar(texto, esperado):
    assert anonimizar(texto) == esperado


def test_codigo_ip_es_estable_e_irreversible():
    a, b = codigo_ip("181.199.63.98", "sal"), codigo_ip("181.199.63.98", "sal")
    assert a == b and a.startswith("ip_") and "181" not in a
    assert codigo_ip("181.199.63.98", "otra") != a
    assert codigo_ip(None) == "ip_desconocida"


def test_registrar_decidir_y_purgar(tmp_path):
    motor = conectar(f"sqlite:///{tmp_path / 'r.db'}")
    i = registrar(motor, "  María  ", "10.0.0.1", "sin internet, cel 0991234567", RES, alerta=False, version="v2")
    j = registrar(motor, "", "10.0.0.2", "factura doble", RES, alerta=True)
    registrar_decision(motor, i, aceptada=True)
    registrar_decision(motor, j, aceptada=False, categoria="FACTURACION", prioridad="media")
    df = leer(motor).set_index("id")
    assert df.loc[i, "nombre"] == "María" and "[TELÉFONO]" in df.loc[i, "mensaje"]
    assert df.loc[j, "nombre"] == "(anónimo)" and df.loc[j, "correccion_categoria"] == "FACTURACION"
    assert df.loc[i, "decision"] == "aceptada" and df.loc[j, "decision"] == "corregida"
    viejo = datetime.now(timezone.utc) - timedelta(days=40)
    with motor.begin() as c:
        c.execute(update(clasificaciones).where(clasificaciones.c.id == j).values(fecha_hora=viejo))
    assert purgar(motor, dias=30) == 1
    assert list(leer(motor)["id"]) == [i]


def test_normalizar_url_de_neon():
    neon = "postgresql://usuario:clave@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require"
    assert normalizar_url(neon).startswith("postgresql+psycopg://usuario:clave@ep-xyz")
    assert normalizar_url("postgres://a@b/c") == "postgresql+psycopg://a@b/c"
    assert normalizar_url("sqlite:///x.db") == "sqlite:///x.db"

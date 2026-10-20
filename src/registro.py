"""Registro de clasificaciones en base de datos, con protección de datos personales.

- El mensaje se guarda después de borrar cédulas, teléfonos, correos y números largos.
- La IP no se guarda: se guarda un código irreversible (hash con sal secreta).
- Solo se registra si la persona dio su consentimiento; los registros se borran pasados N días.

La conexión se define con una URL de SQLAlchemy: por defecto SQLite local; para la nube basta usar una URL de
PostgreSQL (variable de entorno TRIAJEIA_DB_URL o secreto de Streamlit).
"""
import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, MetaData, String, Table, Text, create_engine,
                        delete, insert, select, update)
from sqlalchemy.engine import Engine

from .utils import RAIZ, obtener_logger

log = obtener_logger(__name__)

DIR_REGISTRO = RAIZ / "data" / "registro"
URL_POR_DEFECTO = f"sqlite:///{DIR_REGISTRO / 'registro.db'}"
DIAS_RETENCION = 30

metadata = MetaData()
clasificaciones = Table(
    "clasificaciones", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fecha_hora", DateTime(timezone=True), nullable=False, index=True),
    Column("nombre", String(80), nullable=False),
    Column("ip_hash", String(16), nullable=False),
    Column("mensaje", Text, nullable=False),
    Column("categoria", String(40), nullable=False),
    Column("conf_categoria", Float, nullable=False),
    Column("area", String(40), nullable=False),
    Column("prioridad", String(10), nullable=False),
    Column("conf_prioridad", Float, nullable=False),
    Column("requiere_revision", Boolean, nullable=False),
    Column("alerta_prioridad", Boolean, nullable=False),
    Column("decision", String(12), nullable=False, default="pendiente"),   # pendiente | aceptada | corregida
    Column("correccion_categoria", String(40)),
    Column("correccion_prioridad", String(10)),
    Column("version_modelo", String(40)),
)

_PATRONES = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[CORREO]"),
    (re.compile(r"(?:\+?593[\s-]?|\b0)9\d(?:[\s-]?\d){7}\b"), "[TELÉFONO]"),
    (re.compile(r"\b\d{10}\b"), "[CÉDULA]"),
    (re.compile(r"\b\d(?:[\s-]?\d){6,}\b"), "[NÚMERO]"),
]


def anonimizar(texto: str) -> str:
    """Reemplaza correos, celulares, cédulas y números largos por marcadores."""
    for patron, marca in _PATRONES:
        texto = patron.sub(marca, texto)
    return texto


def _sal() -> str:
    """Sal secreta para el hash de la IP: variable de entorno o archivo local (no versionado)."""
    if os.environ.get("TRIAJEIA_SAL"):
        return os.environ["TRIAJEIA_SAL"]
    archivo = DIR_REGISTRO / ".sal"
    if not archivo.exists():
        DIR_REGISTRO.mkdir(parents=True, exist_ok=True)
        archivo.write_text(secrets.token_hex(16))
    return archivo.read_text().strip()


def codigo_ip(ip: str | None, sal: str | None = None) -> str:
    """Código irreversible de una IP (permite agrupar por equipo sin guardar la IP)."""
    if not isinstance(ip, str) or not ip:
        return "ip_desconocida"
    return "ip_" + hashlib.sha256(((sal or _sal()) + ip).encode()).hexdigest()[:6]


def normalizar_url(url: str) -> str:
    """Acepta la cadena de conexión tal como la entrega Neon u otro proveedor de PostgreSQL.

    «postgresql://…» o «postgres://…» se convierten a «postgresql+psycopg://…» (controlador psycopg 3).
    """
    for prefijo in ("postgresql://", "postgres://"):
        if url.startswith(prefijo):
            return "postgresql+psycopg://" + url.removeprefix(prefijo)
    return url


def conectar(url: str | None = None) -> Engine:
    """Crea la conexión y la tabla si no existe."""
    url = normalizar_url(url or os.environ.get("TRIAJEIA_DB_URL") or URL_POR_DEFECTO)
    if url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    motor = create_engine(url, pool_pre_ping=True)
    metadata.create_all(motor)
    return motor


def registrar(motor: Engine, nombre: str, ip: str | None, mensaje: str, resultado: dict[str, Any],
              alerta: bool, version: str = "") -> int:
    """Guarda una clasificación y devuelve su id."""
    fila = {
        "fecha_hora": datetime.now(timezone.utc), "nombre": (nombre or "").strip()[:80] or "(anónimo)",
        "ip_hash": codigo_ip(ip), "mensaje": anonimizar(mensaje),
        "categoria": resultado["categoria"]["etiqueta"], "conf_categoria": resultado["categoria"]["probabilidad"],
        "area": resultado["area_atencion"], "prioridad": resultado["prioridad"]["etiqueta"],
        "conf_prioridad": resultado["prioridad"]["probabilidad"],
        "requiere_revision": bool(resultado["requiere_revision_humana"]), "alerta_prioridad": bool(alerta),
        "decision": "pendiente", "version_modelo": version,
    }
    with motor.begin() as c:
        return int(c.execute(insert(clasificaciones).values(**fila)).inserted_primary_key[0])


def registrar_decision(motor: Engine, id_: int, aceptada: bool, categoria: str | None = None,
                       prioridad: str | None = None) -> None:
    """Guarda si la persona aceptó la sugerencia o la corrigió (y a qué)."""
    valores = {"decision": "aceptada"} if aceptada else {
        "decision": "corregida", "correccion_categoria": categoria, "correccion_prioridad": prioridad}
    with motor.begin() as c:
        c.execute(update(clasificaciones).where(clasificaciones.c.id == id_).values(**valores))


def purgar(motor: Engine, dias: int = DIAS_RETENCION) -> int:
    """Borra los registros con más de «dias» días. Devuelve cuántos borró."""
    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    with motor.begin() as c:
        n = c.execute(delete(clasificaciones).where(clasificaciones.c.fecha_hora < limite)).rowcount
    if n:
        log.info("Registros eliminados por retención: %d", n)
    return n


def leer(motor: Engine) -> pd.DataFrame:
    """Todos los registros como DataFrame, con la fecha en hora de Ecuador (UTC−5)."""
    with motor.connect() as c:
        df = pd.read_sql(select(clasificaciones).order_by(clasificaciones.c.fecha_hora.desc()), c)
    if not df.empty:
        df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], utc=True).dt.tz_convert("America/Guayaquil")
    return df

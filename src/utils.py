"""Funciones auxiliares: configuración, rutas, semillas y registro de eventos."""
import json
import logging
import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

RAIZ = Path(__file__).resolve().parent.parent


def ruta(relativa: str | Path) -> Path:
    """Convierte una ruta relativa a la raíz del repositorio en absoluta."""
    p = Path(relativa)
    return p if p.is_absolute() else RAIZ / p


def cargar_config(archivo: str | Path = "config.yaml") -> dict[str, Any]:
    """Lee el archivo de configuración YAML.

    Raises:
        FileNotFoundError: si el archivo no existe.
    """
    p = ruta(archivo)
    if not p.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {p}")
    with p.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def fijar_semilla(semilla: int) -> None:
    """Fija las semillas de Python, NumPy y, si está instalado, PyTorch."""
    random.seed(semilla)
    np.random.seed(semilla)
    os.environ["PYTHONHASHSEED"] = str(semilla)
    try:
        import torch

        torch.manual_seed(semilla)
        torch.cuda.manual_seed_all(semilla)
    except ImportError:
        pass


def obtener_logger(nombre: str = "triajeia") -> logging.Logger:
    """Devuelve un logger con formato homogéneo para todo el proyecto."""
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%H:%M:%S"))
        logger.addHandler(h)
        logger.setLevel(os.environ.get("TRIAJEIA_LOG", "INFO"))
    return logger


def guardar_json(datos: Any, archivo: str | Path) -> Path:
    """Guarda un objeto como JSON legible (UTF-8), creando la carpeta si hace falta."""
    p = ruta(archivo)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=2, default=_a_json)
    return p


def cargar_json(archivo: str | Path) -> Any:
    """Lee un archivo JSON."""
    with ruta(archivo).open(encoding="utf-8") as fh:
        return json.load(fh)


def _a_json(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"Tipo no serializable: {type(o)}")


def es_prueba_rapida() -> bool:
    """True si se ejecuta en modo de verificación de código (los números obtenidos no se usan)."""
    return os.environ.get("PRUEBA_RAPIDA", "0") == "1"

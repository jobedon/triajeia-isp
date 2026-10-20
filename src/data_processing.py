"""Carga, limpieza, validación y división del corpus de quejas."""
import re
import unicodedata

import pandas as pd
from sklearn.model_selection import train_test_split

from .utils import obtener_logger, ruta

log = obtener_logger(__name__)

COLUMNAS_REQUERIDAS = ["id", "conjunto", "categoria", "prioridad", "queja"]
LONGITUD_MIN_PALABRAS = 3
LONGITUD_MAX_CARACTERES = 2000
_URL = re.compile(r"https?://\S+|www\.\S+")
_MENCION = re.compile(r"@\w+")
_ESPACIOS = re.compile(r"\s+")
_LETRAS = re.compile(r"[a-záéíóúñü]", re.IGNORECASE)


def cargar_corpus(archivo: str) -> pd.DataFrame:
    """Lee el corpus CSV y verifica que tenga las columnas y valores esperados.

    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si faltan columnas, hay textos vacíos o ids repetidos.
    """
    p = ruta(archivo)
    if not p.exists():
        raise FileNotFoundError(f"No existe el corpus: {p}")
    df = pd.read_csv(p, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas en el corpus: {faltan}")
    if (df["queja"].str.strip() == "").any():
        raise ValueError("Hay quejas vacías en el corpus")
    if df["id"].duplicated().any():
        raise ValueError("Hay ids repetidos en el corpus")
    df["id"] = df["id"].astype(int)
    log.info("Corpus cargado: %d quejas (%s)", len(df), df["conjunto"].value_counts().to_dict())
    return df


def limpiar_texto(texto: str) -> str:
    """Normaliza una queja sin borrar el estilo de escritura.

    Unifica Unicode, reemplaza enlaces por «<url>» y menciones por «@isp», y compacta espacios.
    No quita tildes ni corrige ortografía: la forma de escribir es parte de lo que el modelo debe tolerar.
    """
    if not isinstance(texto, str):
        return ""
    t = unicodedata.normalize("NFC", texto)
    t = _URL.sub(" <url> ", t)
    t = _MENCION.sub(" @isp ", t)
    return _ESPACIOS.sub(" ", t).strip()


def validar_entrada(texto: str) -> tuple[bool, str]:
    """Comprueba que un texto ingresado por el usuario se pueda clasificar.

    Returns:
        (válido, mensaje). Si no es válido, el mensaje explica qué corregir en lenguaje no técnico.
    """
    if texto is None or not str(texto).strip():
        return False, "Escriba el reclamo antes de clasificarlo."
    t = str(texto).strip()
    if len(t) > LONGITUD_MAX_CARACTERES:
        return False, f"El texto es demasiado largo (máximo {LONGITUD_MAX_CARACTERES} caracteres)."
    if not _LETRAS.search(t):
        return False, "El texto no contiene palabras. Describa el problema con letras, no solo con números o emojis."
    if len(re.findall(r"[a-záéíóúñü]+", t, re.IGNORECASE)) < LONGITUD_MIN_PALABRAS:
        return False, f"Describa el problema con al menos {LONGITUD_MIN_PALABRAS} palabras."
    return True, ""


def dividir(df: pd.DataFrame, objetivo: str, fraccion_validacion: float, semilla: int):
    """Separa entrenamiento, validación y prueba.

    La prueba es la columna «conjunto» == «prueba» (200 quejas fijadas al generar el corpus) y solo se usa
    una vez, al final. La validación se separa del entrenamiento, estratificada por el objetivo.

    Returns:
        (train, val, test) como DataFrames.
    """
    test = df[df["conjunto"] == "prueba"].copy()
    resto = df[df["conjunto"] != "prueba"].copy()
    if test.empty or resto.empty:
        raise ValueError("El corpus debe tener filas de entrenamiento y de prueba en la columna «conjunto»")
    train, val = train_test_split(resto, test_size=fraccion_validacion, random_state=semilla,
                                  stratify=resto[objetivo])
    comunes = set(train["queja"].str.lower()) & set(test["queja"].str.lower())
    if comunes:
        raise ValueError(f"Fuga de datos: {len(comunes)} textos aparecen en entrenamiento y prueba")
    return train.copy(), val.copy(), test


def area_de(categoria: str, areas: dict[str, str]) -> str:
    """Devuelve el área de atención de una categoría según la tabla de config.yaml."""
    try:
        return areas[categoria]
    except KeyError as e:
        raise ValueError(f"Categoría sin área asignada: {categoria}") from e

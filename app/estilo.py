"""Estilo corporativo de la aplicación TriajeIA-ISP: componentes HTML/CSS sobrios y reutilizables."""

from html import escape
from pathlib import Path

PRIMARIO = "#1F3A5F"  # azul marino corporativo
TEXTO_SUAVE = "#5B6675"
BORDE = "#D9DEE5"
COLOR_PRIORIDAD = {"alta": "#B42318", "media": "#B54708", "baja": "#3F6E4F"}
COLOR_DECISION = {"aceptada": "#3F6E4F", "corregida": "#B54708", "pendiente": "#A7B0BC"}
SECUENCIA = ["#1F3A5F", "#3E5C82", "#6E87A8", "#A3B5CB", "#CBD6E3"]

CSS = f"<style>\n{(Path(__file__).parent / 'assets' / 'estilo.css').read_text(encoding='utf-8')}</style>\n"


def barra_app(nombre: str, subtitulo: str, estado: str) -> str:
    """Encabezado de la aplicación: logo, nombre, subtítulo y estado del modelo."""
    return (
        f'<div class="barra-app"><div class="marca"><div class="logo">TI</div><div>'
        f'<div class="nombre">{escape(nombre)}</div><div class="sub">{escape(subtitulo)}</div></div></div>'
        f'<div class="estado">{estado}</div></div>'
    )


def seccion(texto: str) -> str:
    """Título pequeño en mayúsculas que separa las secciones de la página."""
    return f'<div class="seccion">{escape(texto)}</div>'


def aviso(texto: str, color: str = PRIMARIO) -> str:
    """Recuadro de aviso con una franja lateral del color indicado."""
    return f'<div class="aviso" style="--c:{color}">{texto}</div>'


def tarjeta(titulo: str, valor: str, detalle: str = "", confianza: float | None = None, color: str = PRIMARIO) -> str:
    """Tarjeta de resultado con título, valor y, si se indica, medidor de confianza."""
    medidor = (
        (
            f'<div class="medidor" style="--c:{color}"><i style="width:{confianza * 100:.0f}%"></i></div>'
            f'<div class="det">Confianza {confianza:.0%}</div>'
        )
        if confianza is not None
        else ""
    )
    det = f'<div class="det">{escape(detalle)}</div>' if detalle else ""
    return (
        f'<div class="tarjeta"><div class="tit">{escape(titulo)}</div>'
        f'<div class="val">{valor}</div>{medidor}{det}</div>'
    )


def marca_prioridad(etiqueta: str, texto: str) -> str:
    """Marca de color para la prioridad (alta, media o baja)."""
    color = COLOR_PRIORIDAD.get(etiqueta, PRIMARIO)
    return f'<span class="marca-prioridad" style="background:{color}">{escape(texto)}</span>'


def etiquetas(terminos: list[str]) -> str:
    """Lista de términos determinantes como etiquetas."""
    return "".join(f'<span class="etiqueta">{escape(t)}</span>' for t in terminos)


def pasos(lista: list[str]) -> str:
    """Lista numerada de pasos del procedimiento."""
    return "".join(f'<div class="paso"><b>{i}</b><span>{t}</span></div>' for i, t in enumerate(lista, 1))

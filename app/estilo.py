"""Estilo corporativo de la aplicación TriajeIA-ISP: componentes HTML/CSS sobrios y reutilizables."""
from html import escape

PRIMARIO = "#1F3A5F"        # azul marino corporativo
TEXTO_SUAVE = "#5B6675"
BORDE = "#D9DEE5"
COLOR_PRIORIDAD = {"alta": "#B42318", "media": "#B54708", "baja": "#3F6E4F"}
COLOR_DECISION = {"aceptada": "#3F6E4F", "corregida": "#B54708", "pendiente": "#A7B0BC"}
SECUENCIA = ["#1F3A5F", "#3E5C82", "#6E87A8", "#A3B5CB", "#CBD6E3"]
GRANATE = PRIMARIO          # compatibilidad con código existente

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stTextInput, .stTextArea, button, input, textarea {{
    font-family: 'Inter', 'Segoe UI', Roboto, Arial, sans-serif !important;}}
.block-container, [data-testid="stMainBlockContainer"] {{padding-top: 2.4rem !important; max-width: 1200px;}}
h1, h2, h3, h4 {{letter-spacing: -.01em;}}
.barra-app {{display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap;
             border-bottom: 1px solid {BORDE}; padding: 4px 0 14px; margin-bottom: 8px;}}
.barra-app .marca {{display: flex; align-items: center; gap: 12px;}}
.barra-app .logo {{width: 38px; height: 38px; border-radius: 8px; background: {PRIMARIO}; color: #fff;
                   display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: .95rem;}}
.barra-app .nombre {{font-size: 1.25rem; font-weight: 700; color: {PRIMARIO}; line-height: 1.1;}}
.barra-app .sub {{font-size: .85rem; color: {TEXTO_SUAVE};}}
.barra-app .estado {{font-size: .78rem; color: {TEXTO_SUAVE}; border: 1px solid {BORDE}; border-radius: 6px;
                     padding: 5px 10px; background: #F6F8FA;}}
.barra-app .estado b {{color: #3F6E4F;}}
.seccion {{font-size: .75rem; font-weight: 600; text-transform: uppercase; letter-spacing: .08em;
           color: {TEXTO_SUAVE}; margin: 18px 0 8px;}}
.aviso {{border: 1px solid {BORDE}; border-left: 4px solid var(--c); border-radius: 6px; padding: 10px 14px;
         margin: 4px 0 14px; font-size: .92rem; background: #FAFBFC; color: #1D2733;}}
.tarjeta {{border: 1px solid {BORDE}; border-radius: 8px; padding: 14px 16px; min-height: 128px; background: #FFFFFF;}}
.tarjeta .tit {{font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .07em;
                color: {TEXTO_SUAVE}; margin-bottom: 6px;}}
.tarjeta .val {{font-size: 1.25rem; font-weight: 600; color: #1D2733; line-height: 1.25; margin-bottom: 10px;}}
.tarjeta .det {{font-size: .8rem; color: {TEXTO_SUAVE};}}
.marca-prioridad {{display: inline-block; font-size: .72rem; font-weight: 600; text-transform: uppercase;
                   letter-spacing: .06em; padding: 3px 9px; border-radius: 4px; color: #fff; vertical-align: middle;}}
.medidor {{height: 6px; border-radius: 3px; background: #E9EDF2; overflow: hidden; margin: 2px 0 6px;}}
.medidor > i {{display: block; height: 100%; background: var(--c);}}
.etiqueta {{display: inline-block; padding: 2px 9px; margin: 0 6px 6px 0; border-radius: 4px; font-size: .82rem;
            background: #EEF2F7; color: {PRIMARIO}; border: 1px solid #DCE3EC;}}
.paso {{display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; font-size: .86rem; color: #1D2733;}}
.paso b {{background: {PRIMARIO}; color: #fff; border-radius: 4px; min-width: 20px; height: 20px; display: inline-flex;
          align-items: center; justify-content: center; font-size: .72rem;}}
div[data-testid="stMetric"] {{background: #FFFFFF; border-radius: 8px;}}
div[data-testid="stMetricLabel"] p {{font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; color: {TEXTO_SUAVE};}}
section[data-testid="stSidebar"] {{border-right: 1px solid {BORDE};}}
button[data-baseweb="tab"] p {{font-weight: 500;}}
@media (max-width: 640px) {{
  .block-container, [data-testid="stMainBlockContainer"] {{padding: 4.2rem .9rem 2rem !important;}}
  .barra-app {{padding-bottom: 10px;}}
  .barra-app .nombre {{font-size: 1.1rem;}}
  .barra-app .estado {{width: 100%; font-size: .72rem;}}
  .tarjeta {{min-height: 0; padding: 12px 14px;}}
  .tarjeta .val {{font-size: 1.1rem; margin-bottom: 6px;}}
  .seccion {{margin-top: 14px;}}
  div[data-testid="stHorizontalBlock"] {{gap: .6rem;}}
  button[data-baseweb="tab"] {{padding-left: 6px; padding-right: 6px;}}
  div[data-testid="stMetric"] {{padding: 8px 12px !important;}}
  div[data-testid="stMetricValue"] {{font-size: 1.5rem !important;}}
}}
</style>
"""


def barra_app(nombre: str, subtitulo: str, estado: str) -> str:
    return (f'<div class="barra-app"><div class="marca"><div class="logo">TI</div><div>'
            f'<div class="nombre">{escape(nombre)}</div><div class="sub">{escape(subtitulo)}</div></div></div>'
            f'<div class="estado">{estado}</div></div>')


def seccion(texto: str) -> str:
    return f'<div class="seccion">{escape(texto)}</div>'


def aviso(texto: str, color: str = PRIMARIO) -> str:
    return f'<div class="aviso" style="--c:{color}">{texto}</div>'


def tarjeta(titulo: str, valor: str, detalle: str = "", confianza: float | None = None, color: str = PRIMARIO) -> str:
    medidor = (f'<div class="medidor" style="--c:{color}"><i style="width:{confianza * 100:.0f}%"></i></div>'
               f'<div class="det">Confianza {confianza:.0%}</div>') if confianza is not None else ""
    det = f'<div class="det">{escape(detalle)}</div>' if detalle else ""
    return f'<div class="tarjeta"><div class="tit">{escape(titulo)}</div><div class="val">{valor}</div>{medidor}{det}</div>'


def marca_prioridad(etiqueta: str, texto: str) -> str:
    return f'<span class="marca-prioridad" style="background:{COLOR_PRIORIDAD.get(etiqueta, PRIMARIO)}">{escape(texto)}</span>'


def etiquetas(terminos: list[str]) -> str:
    return "".join(f'<span class="etiqueta">{escape(t)}</span>' for t in terminos)


def pasos(lista: list[str]) -> str:
    return "".join(f'<div class="paso"><b>{i}</b><span>{t}</span></div>' for i, t in enumerate(lista, 1))

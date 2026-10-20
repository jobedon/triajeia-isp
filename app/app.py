"""Aplicación Streamlit de TriajeIA-ISP: sugiere categoría, área y prioridad de un reclamo.

Ejecutar desde la raíz del repositorio:  streamlit run app/app.py
"""
import io
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.data_processing import validar_entrada  # noqa: E402
from src.model import ClasificadorTriaje  # noqa: E402
from src.utils import cargar_config, cargar_json, obtener_logger  # noqa: E402

log = obtener_logger("app")
MODELO = RAIZ / "models" / "best_model.joblib"
METRICAS = RAIZ / "results" / "metrics" / "05_evaluacion.json"
UMBRAL_ALERTA_ALTA = 0.20          # si la prioridad sugerida no es alta pero P(alta) ≥ 0,20, se pide confirmar

NOMBRES = {
    "SIN_SERVICIO": "Sin servicio", "INTERMITENCIA": "Intermitencia", "VELOCIDAD_LENTA": "Velocidad lenta",
    "WIFI_EQUIPO": "Wifi / equipo", "FACTURACION": "Facturación", "AGENDAMIENTO_VISITA": "Agendamiento de visita",
    "INSTALACION": "Instalación", "ATENCION_CLIENTE": "Atención al cliente", "DANO_FISICO_RED": "Daño físico de la red",
    "CANCELACION_TRASLADO_PLAN": "Cancelación / traslado / plan", "SOPORTE_TECNICO": "Soporte técnico",
    "PLANTA_EXTERNA": "Planta externa", "FACTURACION_COBRANZAS": "Facturación y cobranzas",
    "INSTALACIONES": "Instalaciones", "SERVICIO_CLIENTE": "Servicio al cliente",
    "alta": "Alta", "media": "Media", "baja": "Baja",
}

EJEMPLOS = {
    "Sin internet y teletrabajo": "Buenas tardes, desde ayer en la mañana no tengo nada de internet, el foco del aparato "
                                  "está en rojo. Trabajo desde la casa y hoy tengo reuniones, por favor ayúdenme.",
    "Cobro duplicado": "me llego la factura con doble cobro de la instalacion, ya pague por transferencia y no me "
                       "registran el pago, q pasa??",
    "Cable caído": "@ISP el cable de fibra quedó colgando en la calle después de la lluvia, ya no hay señal en todo el "
                   "pasaje. Barrio Los Ceibos.",
    "Wifi en el segundo piso": "El wifi no llega al cuarto de arriba, abajo funciona bien. Quisiera saber si me "
                               "pueden cambiar el router o poner un repetidor.",
    "Técnico que no llega": "Aló, buenas, me agendaron la visita del técnico para el martes y nunca vino, ya van tres "
                            "días esperando y nadie me da fecha nueva.",
    "Intermitencia (escritura con errores)": "el internet se va y buelve a cada rrato desde haora en la mañana, "
                                             "nesesito q lo revisen porfavor",
    "Mensaje muy corto (caso difícil)": "no hay servicio",
    "Dos problemas a la vez": "Quiero cambiarme a un plan más barato, pero además esta semana el internet ha estado "
                              "lentísimo, el test me sale 8 megas.",
}


def nombre(clave: str) -> str:
    """Nombre legible de una etiqueta interna."""
    return NOMBRES.get(clave, clave)


def alerta_prioridad(resultado: dict) -> bool:
    """True si la prioridad sugerida no es alta pero la probabilidad de «alta» es apreciable.

    Implementa la asimetría de la Semana 4: el sistema puede subir la prioridad, pero bajarla exige
    confirmación humana.
    """
    pri = resultado["prioridad"]
    return pri["etiqueta"] != "alta" and pri["distribucion"].get("alta", 0.0) >= UMBRAL_ALERTA_ALTA


def fila_historial(texto: str, r: dict) -> dict:
    """Resumen plano de una predicción para el historial y la exportación."""
    return {"hora": datetime.now().strftime("%H:%M:%S"), "reclamo": texto,
            "categoria": r["categoria"]["etiqueta"], "conf_categoria": round(r["categoria"]["probabilidad"], 3),
            "area_atencion": r["area_atencion"], "prioridad": r["prioridad"]["etiqueta"],
            "conf_prioridad": round(r["prioridad"]["probabilidad"], 3),
            "requiere_revision_humana": r["requiere_revision_humana"], "confirmar_prioridad": alerta_prioridad(r),
            "terminos_influyentes": ", ".join(r["terminos_influyentes"])}


def a_csv(filas: list[dict]) -> bytes:
    """CSV en UTF-8 con BOM (se abre bien en Excel)."""
    return pd.DataFrame(filas).to_csv(index=False).encode("utf-8-sig")


def clasificar_lote(modelo: ClasificadorTriaje, df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Clasifica cada fila de un CSV; las filas inválidas quedan marcadas con su motivo."""
    filas = []
    for texto in df[columna].astype(str):
        ok, msg = validar_entrada(texto)
        if ok:
            filas.append(fila_historial(texto, modelo.predecir(texto)) | {"error": ""})
        else:
            filas.append({"reclamo": texto, "error": msg})
    return pd.DataFrame(filas)


# ------------------------------------------------------------------------------------------- interfaz
def main() -> None:
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="TriajeIA-ISP", page_icon="📶", layout="wide")

    @st.cache_resource(show_spinner="Cargando el modelo…")
    def cargar_modelo():
        return ClasificadorTriaje.cargar(MODELO)

    @st.cache_data
    def cargar_metricas():
        return cargar_json(METRICAS) if METRICAS.exists() else None

    try:
        modelo = cargar_modelo()
    except Exception as e:  # el usuario ve un mensaje claro; el detalle va al registro
        log.exception("No se pudo cargar el modelo")
        st.error("No se pudo cargar el modelo. Verifique que exista `models/best_model.joblib`.")
        st.caption(f"Detalle técnico: {e}")
        st.stop()
    met = cargar_metricas()
    st.session_state.setdefault("historial", [])
    st.session_state.setdefault("texto", "")

    st.title("📶 TriajeIA-ISP")
    st.markdown("Sugiere la **categoría**, el **área de atención** y la **prioridad** de un reclamo de internet. "
                "**La herramienta sugiere; la persona decide.**")

    tab_clas, tab_lote, tab_hist, tab_acerca = st.tabs(["Clasificar", "Varios reclamos (CSV)", "Historial", "Acerca del modelo"])

    with tab_clas:
        izq, der = st.columns([3, 2])
        with der:
            st.markdown("**Probar con un ejemplo**")
            ej = st.selectbox("Ejemplo", list(EJEMPLOS), label_visibility="collapsed")
            if st.button("Cargar ejemplo", width="stretch"):
                st.session_state["texto"] = EJEMPLOS[ej]
        with izq:
            texto = st.text_area("Reclamo del cliente", key="texto", height=140, max_chars=2000,
                                 placeholder="Ejemplo: desde ayer no tengo internet y el foco del router está en rojo…",
                                 help="Escriba o pegue el reclamo tal como lo envió el cliente. No incluya cédulas ni teléfonos.")
            clasificar = st.button("Clasificar", type="primary", width="stretch")

        if clasificar:
            ok, msg = validar_entrada(texto)
            if not ok:
                st.warning(msg)
            else:
                try:
                    with st.spinner("Clasificando…"):
                        t0 = time.perf_counter()
                        r = modelo.predecir(texto)
                        ms = (time.perf_counter() - t0) * 1000
                except Exception as e:
                    log.exception("Error al clasificar")
                    st.error("Ocurrió un problema al clasificar el reclamo. Intente de nuevo o revise el texto.")
                    st.caption(f"Detalle técnico: {e}")
                    st.stop()
                st.session_state["historial"].append(fila_historial(texto, r))

                if r["requiere_revision_humana"]:
                    st.warning(f"⚠️ **Requiere revisión humana.** El modelo no está suficientemente seguro "
                               f"(confianza menor a {str(round(modelo.umbral, 2)).replace('.', ',')}). Úselo solo como orientación.")
                else:
                    st.success("Sugerencia con confianza suficiente. Revise y confirme.")
                c1, c2, c3 = st.columns(3)
                c1.metric("Categoría", nombre(r["categoria"]["etiqueta"]))
                c1.caption(f"Confianza: {r['categoria']['probabilidad']:.0%}")
                c2.metric("Área de atención", nombre(r["area_atencion"]))
                c2.caption("Se deduce de la categoría")
                c3.metric("Prioridad", nombre(r["prioridad"]["etiqueta"]))
                c3.caption(f"Confianza: {r['prioridad']['probabilidad']:.0%}")
                if alerta_prioridad(r):
                    st.info(f"🔎 **Confirme la prioridad.** La sugerencia es «{nombre(r['prioridad']['etiqueta'])}», pero hay "
                            f"{r['prioridad']['distribucion']['alta']:.0%} de probabilidad de que sea alta. Bajar una "
                            "prioridad siempre requiere confirmación de una persona.")
                if r["terminos_influyentes"]:
                    st.markdown("**Palabras que más influyeron:** " + " · ".join(f"`{t}`" for t in r["terminos_influyentes"]))

                g1, g2 = st.columns(2)
                for col, obj, titulo in [(g1, "categoria", "Probabilidad por categoría"), (g2, "prioridad", "Probabilidad por prioridad")]:
                    d = pd.DataFrame({"etiqueta": [nombre(k) for k in r[obj]["distribucion"]],
                                      "probabilidad": list(r[obj]["distribucion"].values())}).sort_values("probabilidad")
                    fig = px.bar(d, x="probabilidad", y="etiqueta", orientation="h", range_x=[0, 1], title=titulo,
                                 color_discrete_sequence=["#791632"])
                    fig.update_layout(height=330 if obj == "categoria" else 220, margin=dict(l=0, r=10, t=40, b=0), yaxis_title=None)
                    col.plotly_chart(fig, width="stretch")
                st.caption(f"Tiempo de respuesta: {ms:.0f} ms")

    with tab_lote:
        st.markdown("Suba un archivo **CSV** con una columna de texto para clasificar varios reclamos a la vez.")
        archivo = st.file_uploader("Archivo CSV", type=["csv"])
        if archivo is not None:
            try:
                df = pd.read_csv(io.BytesIO(archivo.getvalue()), dtype=str, encoding="utf-8-sig", keep_default_na=False)
            except Exception:
                st.error("No se pudo leer el archivo. Verifique que sea un CSV separado por comas y en UTF-8.")
                df = None
            if df is not None and df.empty:
                st.warning("El archivo no tiene filas.")
            elif df is not None:
                col = st.selectbox("Columna con el reclamo", list(df.columns),
                                   index=list(df.columns).index("queja") if "queja" in df.columns else 0)
                if len(df) > 500:
                    st.warning("Se procesarán solo las primeras 500 filas.")
                    df = df.head(500)
                if st.button("Clasificar archivo", type="primary"):
                    with st.spinner(f"Clasificando {len(df)} reclamos…"):
                        res = clasificar_lote(modelo, df, col)
                    st.dataframe(res, width="stretch", hide_index=True)
                    if "requiere_revision_humana" in res:
                        st.caption(f"Requieren revisión humana: {int(res['requiere_revision_humana'].fillna(False).sum())} de {len(res)}")
                    st.download_button("Descargar resultados (CSV)", a_csv(res.to_dict("records")), "triaje_resultados.csv", "text/csv")

    with tab_hist:
        h = st.session_state["historial"]
        if not h:
            st.info("Todavía no hay clasificaciones en esta sesión.")
        else:
            dfh = pd.DataFrame(h)
            st.dataframe(dfh, width="stretch", hide_index=True)
            c1, c2 = st.columns(2)
            c1.download_button("Descargar historial (CSV)", a_csv(h), "triaje_historial.csv", "text/csv")
            if c2.button("Borrar historial"):
                st.session_state["historial"] = []
                st.rerun()
            if len(h) > 1:
                fig = px.histogram(dfh, x="categoria", color="prioridad", title="Comparación de las predicciones de la sesión",
                                   color_discrete_map={"alta": "#791632", "media": "#c47a8f", "baja": "#e8c9d2"})
                st.plotly_chart(fig, width="stretch")

    with tab_acerca:
        st.subheader("Qué hace")
        st.markdown("Dos clasificadores **SVM lineales** sobre TF-IDF de palabras y caracteres, con probabilidades calibradas: "
                    "uno para la categoría (10 clases) y otro para la prioridad (alta, media, baja). El área de atención se "
                    "deduce de la categoría con una tabla. Si la confianza de cualquiera de los dos es menor al umbral "
                    f"(**{str(round(modelo.umbral, 2)).replace('.', ',')}**), el reclamo se marca para revisión humana.")
        if met:
            st.subheader("Desempeño (prueba de 200 quejas, evaluada una sola vez)")
            m = met["metricas"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("F1-macro categoría", f"{m['categoria']['f1_macro']:.3f}".replace(".", ","))
            c2.metric("F1-macro prioridad", f"{m['prioridad']['f1_macro']:.3f}".replace(".", ","))
            c3.metric("Recall prioridad alta", f"{met['prioridad']['recall_alta']:.3f}".replace(".", ","))
            c4.metric("Abstención", f"{met['abstencion_total']:.1%}".replace(".", ","))
            st.caption(f"Latencia p95: {met['latencia']['p95_ms']:.0f} ms. Detalle en docs/ y notebooks/05_evaluacion.ipynb.")
        st.subheader("Limitaciones y advertencias")
        st.markdown(
            "- Entrenado con un **corpus sintético** (1.500 quejas redactadas por un modelo de lenguaje con reglas de "
            "etiquetado explícitas). Su desempeño con reclamos reales **no está medido**.\n"
            "- Pierde precisión con **mensajes muy cortos o cortados** y cuando faltan las palabras clave del problema "
            "(pruebas de estrés del notebook 05).\n"
            "- La prioridad es más difícil que la categoría: revise siempre las prioridades bajas.\n"
            "- **No debe usarse** para decidir cortes, cobros ni sanciones, ni para evaluar el desempeño de los operadores.\n"
            "- No ingrese datos personales (cédula, teléfono, dirección exacta). El sistema no guarda los textos fuera de "
            "la sesión.")
        st.caption("TriajeIA-ISP · Proyecto Integrador en IA (MIAR0545), UEES · José Olmedo Bedón Sánchez y Javier Isaías Hidalgo Fernández")


if __name__ == "__main__":
    main()

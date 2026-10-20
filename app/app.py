"""Aplicación Streamlit de TriajeIA-ISP: sugiere categoría, área y prioridad de un reclamo.

Ejecutar desde la raíz del repositorio:  streamlit run app/app.py
"""
import hmac
import io
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.data_processing import validar_entrada  # noqa: E402
from src.model import ClasificadorTriaje  # noqa: E402
from src.registro import DIAS_RETENCION, conectar, leer, purgar, registrar, registrar_decision  # noqa: E402
from src.utils import cargar_config, cargar_json, obtener_logger  # noqa: E402

log = obtener_logger("app")
MODELO = RAIZ / "models" / "best_model.joblib"
METRICAS = RAIZ / "results" / "metrics" / "05_evaluacion.json"
UMBRAL_ALERTA_ALTA = 0.20          # si la prioridad sugerida no es alta pero P(alta) ≥ 0,20, se pide confirmar
GRANATE = "#791632"
META_ACEPTACION, META_ABSTENCION = 0.70, 0.15     # KPI del Documento de Alcance (Semana 1)
AVISO_CONSENTIMIENTO = (f"Acepto que se registren mi nombre y el mensaje (sin cédulas, teléfonos ni correos) con fines "
                        f"académicos. La IP no se guarda: solo un código irreversible. Los registros se borran a los "
                        f"{DIAS_RETENCION} días.")

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


def coma(x: float, dec: int = 2) -> str:
    """Número con coma decimal."""
    return f"{x:.{dec}f}".replace(".", ",")


def ip_cliente(st) -> str | None:
    """IP del visitante: detrás de Cloudflare o de un proxy viene en las cabeceras."""
    try:
        h = st.context.headers
        for clave in ("Cf-Connecting-Ip", "X-Forwarded-For", "X-Real-Ip"):
            v = h.get(clave)
            if isinstance(v, str) and v:
                return v.split(",")[0].strip()
        ip = st.context.ip_address
        return ip if isinstance(ip, str) else None
    except Exception:
        return None


def clave_admin() -> str | None:
    """Contraseña del panel de registro: secreto de Streamlit o variable de entorno."""
    try:
        import streamlit as st
        if "admin_password" in st.secrets:
            return str(st.secrets["admin_password"])
    except Exception:
        pass
    return os.environ.get("TRIAJEIA_ADMIN_PASS")


def indicadores(df: pd.DataFrame) -> dict:
    """Indicadores de monitoreo a partir del registro."""
    if df.empty:
        return {"n": 0}
    decididas = df[df["decision"] != "pendiente"]
    return {
        "n": len(df), "personas": df["nombre"].nunique(), "equipos": df["ip_hash"].nunique(),
        "decididas": len(decididas),
        "aceptacion": float((decididas["decision"] == "aceptada").mean()) if len(decididas) else None,
        "abstencion": float(df["requiere_revision"].mean()), "alerta_prioridad": float(df["alerta_prioridad"].mean()),
        "conf_media": float(df["conf_categoria"].mean()),
    }


def alertas(df: pd.DataFrame, dias_recientes: int = 7) -> list[str]:
    """Alarmas del plan de monitoreo (Semana 4): metas incumplidas o empeoramiento reciente de 5 puntos o más."""
    ind = indicadores(df)
    if not ind["n"]:
        return []
    msj = []
    if ind["abstencion"] > META_ABSTENCION:
        msj.append(f"La abstención ({ind['abstencion']:.0%}) supera la meta de {META_ABSTENCION:.0%}.")
    if ind["aceptacion"] is not None and ind["decididas"] >= 10 and ind["aceptacion"] < META_ACEPTACION:
        msj.append(f"La aceptación de sugerencias ({ind['aceptacion']:.0%}) está bajo la meta de {META_ACEPTACION:.0%}.")
    limite = df["fecha_hora"].max() - pd.Timedelta(days=dias_recientes)
    rec = df[df["fecha_hora"] >= limite]
    if 10 <= len(rec) < len(df):
        if rec["requiere_revision"].mean() - df["requiere_revision"].mean() >= 0.05:
            msj.append(f"La abstención de los últimos {dias_recientes} días subió 5 puntos o más sobre el promedio.")
    return msj


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
def _hay_secretos(st) -> bool:
    try:
        return len(st.secrets) > 0
    except Exception:
        return False


def panel_registro(st, px, motor, umbral: float) -> None:
    """Pestaña protegida: tablero de monitoreo y registro de clasificaciones."""
    clave = clave_admin()
    if motor is None:
        st.error("La base de datos no está disponible.")
        return
    if not clave:
        st.info("El panel está desactivado: falta configurar la contraseña de administración "
                "(`admin_password` en `.streamlit/secrets.toml` o la variable TRIAJEIA_ADMIN_PASS).")
        return
    if not st.session_state.get("admin_ok"):
        with st.form("login"):
            intento = st.text_input("Contraseña de administración", type="password")
            if st.form_submit_button("Entrar"):
                if hmac.compare_digest(intento, clave):
                    st.session_state["admin_ok"] = True
                    st.rerun()
                st.error("Contraseña incorrecta.")
        st.caption("Solo el equipo del proyecto puede ver los nombres y mensajes registrados.")
        return

    df = leer(motor)
    cab1, cab2 = st.columns([4, 1])
    cab1.markdown(f"Registros de los últimos **{DIAS_RETENCION} días** (los anteriores se borran solos). "
                  "Los mensajes se guardan sin cédulas, teléfonos ni correos, y la IP como código irreversible.")
    if cab2.button("Cerrar sesión"):
        st.session_state["admin_ok"] = False
        st.rerun()
    if df.empty:
        st.info("Todavía no hay clasificaciones registradas.")
        return

    f1, f2, f3 = st.columns([2, 2, 2])
    dmin, dmax = df["fecha_hora"].min().date(), df["fecha_hora"].max().date()
    rango = f1.date_input("Fechas", (dmin, dmax), min_value=dmin, max_value=dmax)
    personas = f2.multiselect("Personas", sorted(df["nombre"].unique()), placeholder="Todas")
    cats = f3.multiselect("Categorías", sorted(df["categoria"].unique()), format_func=nombre, placeholder="Todas")
    if isinstance(rango, tuple) and len(rango) == 2:
        df = df[(df["fecha_hora"].dt.date >= rango[0]) & (df["fecha_hora"].dt.date <= rango[1])]
    if personas:
        df = df[df["nombre"].isin(personas)]
    if cats:
        df = df[df["categoria"].isin(cats)]
    if df.empty:
        st.warning("No hay registros con esos filtros.")
        return

    ind = indicadores(df)
    k = st.columns(6)
    k[0].metric("Clasificaciones", ind["n"])
    k[1].metric("Personas", ind["personas"])
    k[2].metric("Equipos", ind["equipos"])
    k[3].metric("Aceptación", "—" if ind["aceptacion"] is None else f"{ind['aceptacion']:.0%}",
                help=f"Sugerencias aceptadas sobre las decididas ({ind['decididas']}). Meta: ≥ {META_ACEPTACION:.0%}.")
    k[4].metric("Abstención", f"{ind['abstencion']:.0%}", help=f"Enviadas a revisión humana. Meta: ≤ {META_ABSTENCION:.0%}.")
    k[5].metric("Confirmar prioridad", f"{ind['alerta_prioridad']:.0%}", help="Prioridad sugerida no alta con P(alta) ≥ 20 %.")
    for a in alertas(df):
        st.warning("🚨 " + a)

    d = df.assign(dia=df["fecha_hora"].dt.date, cat=df["categoria"].map(nombre), pri=df["prioridad"].map(nombre))
    g1, g2 = st.columns(2)
    fig = px.histogram(d, x="dia", color="decision", title="Clasificaciones por día y decisión",
                       color_discrete_map={"aceptada": "#2F6B46", "corregida": GRANATE, "pendiente": "#BBBBBB"})
    fig.update_layout(bargap=0.15, xaxis_title=None, yaxis_title="clasificaciones", legend_title=None)
    g1.plotly_chart(fig, width="stretch")
    vc = d["cat"].value_counts().sort_values()
    fig = px.bar(x=vc.values, y=vc.index, orientation="h", title="Reclamos por categoría", color_discrete_sequence=[GRANATE])
    fig.update_layout(xaxis_title="reclamos", yaxis_title=None)
    g2.plotly_chart(fig, width="stretch")

    g3, g4 = st.columns(2)
    fig = px.pie(d, names="pri", hole=0.5, title="Prioridad sugerida", color="pri",
                 color_discrete_map={"Alta": GRANATE, "Media": "#c47a8f", "Baja": "#e8c9d2"})
    g3.plotly_chart(fig, width="stretch")
    fig = px.histogram(d, x="conf_categoria", nbins=20, range_x=[0, 1], title="Confianza de la categoría",
                       color_discrete_sequence=[GRANATE])
    fig.add_vline(x=umbral, line_dash="dash", annotation_text=f"umbral {coma(umbral)}")
    fig.update_layout(xaxis_title="confianza", yaxis_title="clasificaciones")
    g4.plotly_chart(fig, width="stretch")

    g5, g6 = st.columns(2)
    corr = d[d["decision"] == "corregida"]
    if not corr.empty:
        m = pd.crosstab(corr["categoria"].map(nombre), corr["correccion_categoria"].map(nombre))
        fig = px.imshow(m, text_auto=True, color_continuous_scale="Reds", title="Correcciones: sugerido → corregido",
                        labels={"x": "categoría corregida", "y": "categoría sugerida", "color": "casos"})
        g5.plotly_chart(fig, width="stretch")
    else:
        g5.info("Sin correcciones registradas: aquí aparecerá qué confunde el modelo según las personas.")
    act = d.groupby("nombre").agg(clasificaciones=("id", "size"),
                                  aceptadas=("decision", lambda x: (x == "aceptada").sum())).reset_index()
    fig = px.bar(act.sort_values("clasificaciones"), x="clasificaciones", y="nombre", orientation="h",
                 title="Actividad por persona", color_discrete_sequence=["#c47a8f"])
    fig.update_layout(yaxis_title=None)
    g6.plotly_chart(fig, width="stretch")

    st.subheader("Registro")
    tabla = d[["fecha_hora", "nombre", "ip_hash", "mensaje", "cat", "conf_categoria", "area", "pri", "conf_prioridad",
               "requiere_revision", "alerta_prioridad", "decision", "correccion_categoria", "correccion_prioridad"]].rename(columns={
        "fecha_hora": "Fecha y hora", "nombre": "Nombre", "ip_hash": "Equipo", "mensaje": "Mensaje", "cat": "Categoría",
        "conf_categoria": "Conf. categoría", "area": "Área", "pri": "Prioridad", "conf_prioridad": "Conf. prioridad",
        "requiere_revision": "Revisión humana", "alerta_prioridad": "Confirmar prioridad", "decision": "Decisión",
        "correccion_categoria": "Categoría corregida", "correccion_prioridad": "Prioridad corregida"})
    tabla["Fecha y hora"] = tabla["Fecha y hora"].dt.strftime("%d/%m/%Y %H:%M")
    for c in ("Área", "Categoría corregida", "Prioridad corregida"):
        tabla[c] = tabla[c].map(lambda v: nombre(v) if isinstance(v, str) else "")
    st.dataframe(tabla, width="stretch", hide_index=True,
                 column_config={"Conf. categoría": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                                "Conf. prioridad": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f")})
    st.download_button("Descargar registro (CSV)", a_csv(tabla.to_dict("records")), "triaje_registro.csv", "text/csv")
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

    @st.cache_resource(show_spinner=False)
    def conectar_bd():
        if _hay_secretos(st) and st.secrets.get("ip_sal"):
            os.environ["TRIAJEIA_SAL"] = str(st.secrets["ip_sal"])   # clave fija: el código de IP no cambia al reiniciar
        m = conectar(st.secrets.get("db_url") if _hay_secretos(st) else None)
        purgar(m)
        return m

    try:
        motor = conectar_bd()
    except Exception:
        log.exception("Sin base de datos")
        motor = None
    st.session_state.setdefault("historial", [])
    st.session_state.setdefault("texto", "")

    st.title("📶 TriajeIA-ISP")
    st.markdown("Sugiere la **categoría**, el **área de atención** y la **prioridad** de un reclamo de internet. "
                "**La herramienta sugiere; la persona decide.**")

    tab_clas, tab_lote, tab_hist, tab_reg, tab_acerca = st.tabs(
        ["Clasificar", "Varios reclamos (CSV)", "Historial", "Registro y monitoreo", "Acerca del modelo"])

    with tab_clas:
        izq, der = st.columns([3, 2])
        with der:
            st.markdown("**Probar con un ejemplo**")
            ej = st.selectbox("Ejemplo", list(EJEMPLOS), label_visibility="collapsed")
            if st.button("Cargar ejemplo", width="stretch"):
                st.session_state["texto"] = EJEMPLOS[ej]
        with izq:
            nombre_usuario = st.text_input("Nombre o alias (opcional)", max_chars=80, key="nombre_usuario",
                                           placeholder="Ejemplo: María T.")
            texto = st.text_area("Reclamo del cliente", key="texto", height=130, max_chars=2000,
                                 placeholder="Ejemplo: desde ayer no tengo internet y el foco del router está en rojo…",
                                 help="Escriba o pegue el reclamo tal como lo envió el cliente.")
            consiente = st.checkbox("Acepto que se registren mi nombre y el mensaje con fines académicos",
                                    key="consiente", help=AVISO_CONSENTIMIENTO)
            st.caption("🔒 Se borran cédulas, teléfonos y correos; la IP se guarda como código irreversible; "
                       f"los registros se eliminan a los {DIAS_RETENCION} días.")
            clasificar = st.button("Clasificar", type="primary", width="stretch")

        if clasificar:
            ok, msg = validar_entrada(texto)
            if not ok:
                st.warning(msg)
                st.session_state.pop("ultimo", None)
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
                id_reg = None
                if consiente and motor is not None:
                    try:
                        id_reg = registrar(motor, nombre_usuario, ip_cliente(st), texto, r, alerta_prioridad(r),
                                           modelo.metadatos.get("version", ""))
                    except Exception:
                        log.exception("No se pudo guardar el registro")
                        st.toast("No se pudo guardar el registro; la clasificación sí se realizó.")
                st.session_state["historial"].append(fila_historial(texto, r))
                st.session_state["ultimo"] = {"r": r, "ms": ms, "id": id_reg, "decidido": False}

        ultimo = st.session_state.get("ultimo")
        if ultimo:
            r, ms = ultimo["r"], ultimo["ms"]
            if r["requiere_revision_humana"]:
                st.warning(f"⚠️ **Requiere revisión humana.** El modelo no está suficientemente seguro "
                           f"(confianza menor a {coma(modelo.umbral)}). Úselo solo como orientación.")
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

            if ultimo["id"] is not None:
                st.markdown("**¿La sugerencia es correcta?**")
                if ultimo["decidido"]:
                    st.caption(f"✔ Decisión registrada: {ultimo['decidido']}.")
                else:
                    b1, b2 = st.columns([1, 3])
                    if b1.button("✔ Aceptar", width="stretch"):
                        registrar_decision(motor, ultimo["id"], aceptada=True)
                        ultimo["decidido"] = "aceptada"
                        st.rerun()
                    with b2.expander("✎ Corregir"):
                        cats = list(modelo.modelos["categoria"].classes_)
                        pris = ["alta", "media", "baja"]
                        cc = st.selectbox("Categoría correcta", cats, index=cats.index(r["categoria"]["etiqueta"]), format_func=nombre)
                        pc = st.selectbox("Prioridad correcta", pris, index=pris.index(r["prioridad"]["etiqueta"]), format_func=nombre)
                        if st.button("Guardar corrección"):
                            registrar_decision(motor, ultimo["id"], aceptada=False, categoria=cc, prioridad=pc)
                            ultimo["decidido"] = f"corregida a {nombre(cc)} · prioridad {nombre(pc)}"
                            st.rerun()
            else:
                st.caption("Esta clasificación no se registró (no se marcó el consentimiento).")

            g1, g2 = st.columns(2)
            for col, obj, titulo in [(g1, "categoria", "Probabilidad por categoría"), (g2, "prioridad", "Probabilidad por prioridad")]:
                d = pd.DataFrame({"etiqueta": [nombre(k) for k in r[obj]["distribucion"]],
                                  "probabilidad": list(r[obj]["distribucion"].values())}).sort_values("probabilidad")
                fig = px.bar(d, x="probabilidad", y="etiqueta", orientation="h", range_x=[0, 1], title=titulo,
                             color_discrete_sequence=[GRANATE])
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

    with tab_reg:
        panel_registro(st, px, motor, modelo.umbral)

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

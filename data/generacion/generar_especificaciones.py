"""Genera la especificación de las 1.500 quejas del corpus sintético v2 (TriajeIA-ISP).

Cada fila fija de antemano las etiquetas (categoría, área, prioridad) y las condiciones de redacción (persona,
canal, registro, dificultad, longitud). Las etiquetas salen de reglas explícitas, documentadas en
guia_etiquetado.md; el texto lo redacta después un generador que debe respetar la especificación.

Uso: python generar_especificaciones.py   → escribe especificaciones.csv
"""
import csv
import random
from pathlib import Path

SEMILLA = 2026
N_TOTAL, N_PRUEBA = 1500, 200
SALIDA = Path(__file__).with_name("especificaciones.csv")
rng = random.Random(SEMILLA)

# Distribución supuesta (no proviene de datos reales): desigual, como en una operación real.
CATEGORIAS = {
    "SIN_SERVICIO": 0.17, "INTERMITENCIA": 0.14, "VELOCIDAD_LENTA": 0.13, "WIFI_EQUIPO": 0.12,
    "FACTURACION": 0.11, "AGENDAMIENTO_VISITA": 0.08, "ATENCION_CLIENTE": 0.07, "INSTALACION": 0.07,
    "DANO_FISICO_RED": 0.06, "CANCELACION_TRASLADO_PLAN": 0.05,
}
AREA = {
    "SIN_SERVICIO": "SOPORTE_TECNICO", "INTERMITENCIA": "SOPORTE_TECNICO", "VELOCIDAD_LENTA": "SOPORTE_TECNICO",
    "WIFI_EQUIPO": "SOPORTE_TECNICO", "DANO_FISICO_RED": "PLANTA_EXTERNA", "FACTURACION": "FACTURACION_COBRANZAS",
    "ATENCION_CLIENTE": "SERVICIO_CLIENTE", "CANCELACION_TRASLADO_PLAN": "SERVICIO_CLIENTE",
    "INSTALACION": "INSTALACIONES", "AGENDAMIENTO_VISITA": "INSTALACIONES",
}
CIUDADES = {
    "costa": ["Guayaquil", "Durán", "Samborondón", "Daule", "Milagro", "Machala", "Manta", "Portoviejo",
              "Esmeraldas", "Babahoyo", "Quevedo", "Salinas", "La Libertad", "Santo Domingo"],
    "sierra": ["Quito", "Sangolquí", "Cuenca", "Ambato", "Riobamba", "Loja", "Ibarra", "Latacunga", "Otavalo",
               "Azogues", "Tulcán", "Guaranda", "Cayambe"],
    "amazonia": ["Tena", "Puyo", "Nueva Loja", "Macas", "Coca", "Zamora"],
}
P_REGION = {"costa": 0.48, "sierra": 0.44, "amazonia": 0.08}
CANALES = {"WhatsApp": 0.32, "Llamada transcrita": 0.22, "Redes sociales": 0.17, "Correo": 0.12,
           "App": 0.09, "Formulario web": 0.08}
# Registro de escritura: base de las métricas de equidad por subgrupo (Semana 4, R1).
REGISTROS = {"formal": 0.18, "informal": 0.40, "muy_informal": 0.22, "con_errores": 0.16, "mezcla_kichwa": 0.04}
DIFICULTAD = {"normal": 0.75, "ambigua": 0.15, "dos_problemas": 0.10}
LONGITUD = {"corta": 0.25, "media": 0.55, "larga": 0.20}

# Personas: (descripción, dependencia crítica del servicio). La dependencia crítica puede subir la prioridad.
PERSONAS = [
    ("estudiante universitario con clases virtuales", "estudios"),
    ("estudiante de colegio que rinde exámenes en línea", "estudios"),
    ("persona que trabaja desde casa (teletrabajo)", "teletrabajo"),
    ("dueña de una tienda que cobra por transferencia", "negocio"),
    ("dueño de un cyber o centro de copiado", "negocio"),
    ("emprendedora que vende por redes sociales", "negocio"),
    ("hijo que cuida a su madre adulta mayor que hace videollamadas médicas", "salud"),
    ("adulto mayor que vive solo", "salud"),
    ("persona con un familiar con equipo médico o teleconsultas", "salud"),
    ("madre de familia con hijos en clases virtuales", "estudios"),
    ("jubilado con poca experiencia en tecnología", None),
    ("joven gamer", None),
    ("ama de casa", None),
    ("trabajador que llega de noche y usa streaming", None),
    ("profesional que paga puntual y está molesto", None),
    ("cliente nuevo", None),
    ("cliente antiguo de varios años", None),
    ("inquilino que comparte el servicio con otras familias", None),
    ("persona que vive en una zona rural o periférica", None),
    ("migrante retornado que se comunica con familia en el exterior", None),
]


def elegir(dist):
    return rng.choices(list(dist), weights=list(dist.values()))[0]


CRITICAS = {"negocio", "teletrabajo", "salud"}  # "estudios" se menciona pero no sube la prioridad


def prioridad(cat, dependencia, dias, reincidente):
    """Reglas de guia_etiquetado.md. Devuelve (prioridad, motivo)."""
    dependencia = dependencia if dependencia in CRITICAS else None
    if cat in ("SIN_SERVICIO", "DANO_FISICO_RED"):
        return "alta", "afectacion_total_o_riesgo_fisico"
    if cat in ("INTERMITENCIA", "VELOCIDAD_LENTA"):
        if dependencia:
            return "alta", "dependencia_critica"
        if dias >= 5:
            return "alta", "mas_de_4_dias"
        if reincidente:
            return "alta", "reincidencia"
        return "media", "degradacion_parcial"
    if cat in ("WIFI_EQUIPO", "INSTALACION", "AGENDAMIENTO_VISITA"):
        base = "baja" if cat == "WIFI_EQUIPO" else "media"
        if cat == "WIFI_EQUIPO" and dependencia:
            return "media", "dependencia_critica"
        if reincidente:
            return ("media" if base == "baja" else "alta"), "reincidencia"
        return base, "sin_agravante"
    if cat == "FACTURACION":
        return "media", "reclamo_economico"
    return "baja", "sin_afectacion_tecnica"  # ATENCION_CLIENTE, CANCELACION_TRASLADO_PLAN


def main():
    cats = []
    for c, p in CATEGORIAS.items():
        cats += [c] * round(p * N_TOTAL)
    cats = (cats + [max(CATEGORIAS, key=CATEGORIAS.get)] * N_TOTAL)[:N_TOTAL]
    rng.shuffle(cats)
    filas = []
    for i, cat in enumerate(cats, 1):
        region = elegir(P_REGION)
        persona, dep = rng.choice(PERSONAS)
        # La persona puede mencionar su situación aunque no cambie la prioridad (evita que una frase delate la etiqueta).
        menciona_dep = dep is not None and rng.random() < 0.6
        dias = rng.choice([0, 0, 0, 1, 1, 1, 2, 2, 3, 4, 5, 7, 10])
        reincidente = rng.random() < 0.2
        pr, motivo = prioridad(cat, dep if menciona_dep else None, dias, reincidente)
        dific = elegir(DIFICULTAD)
        otra = rng.choice([c for c in CATEGORIAS if c != cat]) if dific != "normal" else ""
        registro = elegir(REGISTROS)
        if registro == "mezcla_kichwa":
            region = "sierra" if rng.random() < 0.8 else "amazonia"
        filas.append({
            "id": i, "conjunto": "", "categoria": cat, "area_atencion": AREA[cat], "prioridad": pr,
            "motivo_prioridad": motivo, "region": region, "ciudad": rng.choice(CIUDADES[region]),
            "canal": elegir(CANALES), "persona": persona,
            "dependencia_mencionada": dep if menciona_dep else "", "dias_problema": dias,
            "reclamo_previo": "si" if reincidente else "no", "registro": registro, "dificultad": dific,
            "categoria_secundaria": otra, "longitud": elegir(LONGITUD),
        })
    # Conjunto de prueba estratificado por categoría.
    por_cat = {}
    for f in filas:
        por_cat.setdefault(f["categoria"], []).append(f)
    prueba = set()
    for c, fs in por_cat.items():
        k = round(N_PRUEBA * len(fs) / N_TOTAL)
        prueba |= {f["id"] for f in rng.sample(fs, k)}
    for f in filas:
        f["conjunto"] = "prueba" if f["id"] in prueba else "entrenamiento"
    with SALIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} especificaciones · prueba = {len(prueba)} → {SALIDA}")


if __name__ == "__main__":
    main()

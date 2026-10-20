# TriajeIA-ISP

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![Licencia: MIT](https://img.shields.io/badge/c%C3%B3digo-MIT-green) ![Datos: CC BY 4.0](https://img.shields.io/badge/datos-CC%20BY%204.0-lightgrey) ![Estado](https://img.shields.io/badge/estado-en%20desarrollo-orange)

Clasificación automática de reclamos de clientes de un proveedor de internet en Ecuador: a partir del texto, el
sistema **sugiere** la categoría, el área de atención y la prioridad, y deja a una persona los casos dudosos.

> Proyecto final del Proyecto Integrador en Inteligencia Artificial (MIAR0545), Maestría en Inteligencia Artificial, UEES.
> README en construcción: los resultados se completan cuando terminen las ejecuciones en Google Colab.

## Estructura

```
├── config.yaml        configuración central (rutas, hiperparámetros, umbrales)
├── data/              corpus sintético v2, guía de etiquetado y scripts de generación
├── notebooks/         01 exploración · 02 preprocesamiento · 03 modelado · 04 optimización · 05 evaluación
├── src/               código: datos, modelo, entrenamiento, evaluación y utilidades
├── models/            modelos entrenados
├── app/               aplicación Streamlit
├── tests/             pruebas unitarias
├── results/           figuras, métricas y reportes
└── docs/              documentación del proyecto
```

## Reproducir los resultados (Google Colab)

1. Abrir los notebooks **en orden** desde GitHub en Colab (Archivo → Abrir notebook → GitHub) con entorno de **GPU T4**.
2. Cada notebook monta Google Drive y trabaja en `MyDrive/triajeia-isp`, de modo que los cinco comparten datos,
   modelos y resultados.
3. Al terminar, `results/` y `models/` quedan en Drive.

## Pruebas

```bash
pip install -r requirements.txt
pytest -q
```

## Autores

José Olmedo Bedón Sánchez · Javier Isaías Hidalgo Fernández (Grupo 20) · Docente: Gladys María Villegas Rugel.

## Licencia

Código bajo [MIT](LICENSE). Datos bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

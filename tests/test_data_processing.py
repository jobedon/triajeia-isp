"""Pruebas de carga, limpieza, validación de entrada y división."""
import pytest

from src.data_processing import area_de, cargar_corpus, dividir, limpiar_texto, validar_entrada


def test_limpiar_texto_normaliza_sin_borrar_estilo():
    assert limpiar_texto("  @MiISP   no hay   internet xq?? ") == "@isp no hay internet xq??"
    assert limpiar_texto("mira https://x.com/a ya") == "mira <url> ya"
    assert limpiar_texto(None) == ""


@pytest.mark.parametrize("texto, valido", [
    ("", False), ("   ", False), ("12345 😡😡", False), ("sin internet", False),
    ("no tengo internet desde ayer", True), ("x" * 2001 + " a b", False),
])
def test_validar_entrada(texto, valido):
    ok, mensaje = validar_entrada(texto)
    assert ok is valido
    assert (mensaje == "") is valido


def test_dividir_respeta_prueba_fija_y_no_hay_fuga(corpus_pequeno):
    train, val, test = dividir(corpus_pequeno, "categoria", 0.2, 42)
    assert set(test["conjunto"]) == {"prueba"}
    assert not set(train["id"]) & set(test["id"])
    assert not set(val["id"]) & set(test["id"])
    assert len(train) + len(val) + len(test) == len(corpus_pequeno)


def test_dividir_detecta_fuga(corpus_pequeno):
    df = corpus_pequeno.copy()
    df.loc[df["conjunto"] == "prueba", "queja"] = df.loc[df["conjunto"] != "prueba", "queja"].iloc[0]
    with pytest.raises(ValueError, match="Fuga"):
        dividir(df, "categoria", 0.2, 42)


def test_cargar_corpus_rechaza_columnas_faltantes(tmp_path):
    p = tmp_path / "malo.csv"
    p.write_text("id,queja\n1,hola\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Faltan columnas"):
        cargar_corpus(str(p))


def test_area_de():
    assert area_de("FACTURACION", {"FACTURACION": "FACTURACION_COBRANZAS"}) == "FACTURACION_COBRANZAS"
    with pytest.raises(ValueError):
        area_de("OTRA", {})

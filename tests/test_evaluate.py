"""Tests de las funciones de comparación de evaluate.py (no necesitan Ollama)."""
from evaluate import (
    compara_diagnostico,
    compara_medicacion,
    normaliza_farmaco,
    normaliza_medicacion,
)


def test_normaliza_farmaco_quita_dosis():
    assert normaliza_farmaco("bisoprolol 5mg") == "bisoprolol"


def test_normaliza_farmaco_quita_intensidad():
    assert normaliza_farmaco("atorvastatina de alta intensidad") == "atorvastatina"


def test_normaliza_farmaco_quita_liberacion_prolongada():
    assert normaliza_farmaco("metformina de liberación prolongada") == "metformina"


def test_normaliza_medicacion_aplana_combinaciones():
    assert normaliza_medicacion(["sacubitrilo/valsartano"]) == {"sacubitrilo", "valsartano"}


def test_normaliza_medicacion_lista_vacia_o_none():
    assert normaliza_medicacion([]) == set()
    assert normaliza_medicacion(None) == set()


def test_compara_medicacion_ignora_orden_y_dosis():
    assert compara_medicacion(["ramipril 5mg", "bisoprolol"], ["bisoprolol", "ramipril"])


def test_compara_medicacion_detecta_farmaco_de_mas():
    assert not compara_medicacion(["acenocumarol"], [])


def test_compara_diagnostico_exacto():
    assert compara_diagnostico("dolor torácico", "Dolor torácico") == ("exacto", 1.0)


def test_compara_diagnostico_ambos_none():
    assert compara_diagnostico(None, None) == ("exacto", 1.0)


def test_compara_diagnostico_parcial_por_inclusion():
    tipo, score = compara_diagnostico("palpitaciones", "Palpitaciones, sin hallazgos agudos")
    assert tipo == "parcial" and score == 0.8


def test_compara_diagnostico_fallo():
    tipo, _ = compara_diagnostico("soplo sistólico", "Insuficiencia mitral leve")
    assert tipo == "fallo"

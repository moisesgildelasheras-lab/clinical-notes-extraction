"""Tests del RAG que no necesitan Ollama ni descargar el modelo de embeddings."""
import pytest

import evaluate_rag
import rag
from index import trocear


# ---------- funciones puras ----------

@pytest.mark.parametrize("texto", [
    "No tengo información sobre eso en las guías disponibles.",
    "Según el contexto, no tengo información sobre dieta.",
    "NO TENGO INFORMACIÓN sobre ese tema",
])
def test_es_abstencion_detecta_abstenciones(texto):
    assert rag.es_abstencion(texto)


@pytest.mark.parametrize("texto", [
    "No, no se recomienda tomar ambos a la vez.",
    "La furosemida es un diurético.",
])
def test_es_abstencion_no_confunde_respuestas_negativas(texto):
    assert not rag.es_abstencion(texto)


def test_trocear_antepone_el_titulo_a_cada_parrafo():
    assert trocear("Título\nPárrafo uno\n\nPárrafo dos\n") == ["Título: Párrafo uno", "Título: Párrafo dos"]


def test_trocear_guia_sin_parrafos_devuelve_el_titulo():
    assert trocear("Solo título") == ["Solo título"]


def test_contiene_palabra_no_casa_dentro_de_otra_palabra():
    assert not evaluate_rag.contiene_palabra("Más información", "no")
    assert evaluate_rag.contiene_palabra("No, no se recomienda", "no")
    assert evaluate_rag.contiene_palabra("Llama al 112 o ve a urgencias.", "112")


# ---------- responder(): umbral de similitud y fuentes ----------

def _trozos(*pares):
    return [{"id": i, "trozo": 0, "texto": f"texto de {i}", "score": s} for i, s in pares]


def test_responder_se_abstiene_sin_llamar_al_llm_si_nada_supera_el_umbral(monkeypatch):
    monkeypatch.setattr(rag, "recuperar", lambda p, k=3: _trozos(("a", 0.2), ("b", 0.1)))
    monkeypatch.setattr(rag, "llamar_llm", lambda *a, **kw: pytest.fail("no debería llamarse al LLM"))
    respuesta, trozos = rag.responder("pregunta fuera de alcance", umbral=0.5)
    assert respuesta == rag.SIN_INFO
    assert len(trozos) == 2  # se devuelven todos los recuperados (para evaluar la recuperación)


def test_responder_solo_cita_trozos_por_encima_del_umbral(monkeypatch):
    monkeypatch.setattr(rag, "recuperar", lambda p, k=3: _trozos(("a", 0.8), ("b", 0.2)))
    monkeypatch.setattr(rag, "llamar_llm", lambda *a, **kw: "Respuesta basada en a.")
    respuesta, _ = rag.responder("pregunta", umbral=0.5)
    assert "[a]" in respuesta and "[b]" not in respuesta


def test_responder_no_anade_fuentes_si_el_llm_se_abstiene(monkeypatch):
    monkeypatch.setattr(rag, "recuperar", lambda p, k=3: _trozos(("a", 0.8)))
    monkeypatch.setattr(rag, "llamar_llm", lambda *a, **kw: rag.SIN_INFO)
    respuesta, _ = rag.responder("pregunta", umbral=0.5)
    assert "Fuentes" not in respuesta


# ---------- evalua_pregunta(): categorías ----------

def _item(guia, claves=()):
    return {"id": 1, "pregunta": "¿?", "guia_esperada": guia, "palabras_clave": list(claves)}


def _simula(monkeypatch, respuesta, ids):
    monkeypatch.setattr(
        evaluate_rag, "responder",
        lambda p, m, k: (respuesta, _trozos(*[(i, 0.9 - 0.1 * n) for n, i in enumerate(ids)])),
    )


def test_categoria_abstencion_correcta(monkeypatch):
    _simula(monkeypatch, rag.SIN_INFO, ["a"])
    assert evaluate_rag.evalua_pregunta(_item(None), "m", 3)["categoria"] == "abstencion_correcta"


def test_categoria_alucinacion(monkeypatch):
    _simula(monkeypatch, "Sí, puedes hacerlo.", ["a"])
    assert evaluate_rag.evalua_pregunta(_item(None), "m", 3)["categoria"] == "alucinacion"


def test_categoria_falso_no_se_conserva_la_recuperacion_correcta(monkeypatch):
    _simula(monkeypatch, rag.SIN_INFO, ["g1"])
    r = evaluate_rag.evalua_pregunta(_item("g1"), "m", 3)
    assert r["categoria"] == "falso_no_se"
    assert r["guia_recuperada"] is True  # la guía sí se recuperó: el fallo es de generación


def test_categoria_fallo_recuperacion(monkeypatch):
    _simula(monkeypatch, "Una respuesta.", ["otra"])
    r = evaluate_rag.evalua_pregunta(_item("g1"), "m", 3)
    assert r["categoria"] == "fallo_recuperacion" and r["guia_recuperada"] is False


def test_categoria_acierto_y_respuesta_incompleta(monkeypatch):
    _simula(monkeypatch, "Controla tu peso cada mañana.", ["g1"])
    assert evaluate_rag.evalua_pregunta(_item("g1", ["peso"]), "m", 3)["categoria"] == "acierto"
    r = evaluate_rag.evalua_pregunta(_item("g1", ["peso", "112"]), "m", 3)
    assert r["categoria"] == "acierto_recuperacion_pero_respuesta_incompleta"
    assert r["palabras_clave_faltantes"] == ["112"]


def test_revision_manual_ignora_entradas_pendientes(tmp_path):
    f = tmp_path / "rev.json"
    f.write_text('[{"id": 1, "fiel": true}, {"id": 2, "fiel": null}, {"id": 3, "fiel": false, "comentario": "x"}]', encoding="utf-8")
    assert set(evaluate_rag.carga_revision_manual(f)) == {1, 3}
    assert evaluate_rag.carga_revision_manual(tmp_path / "no_existe.json") == {}

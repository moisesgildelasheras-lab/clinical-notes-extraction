"""
RAG local: recupera los trozos de guía más relevantes y responde con un LLM
en Ollama. Las fuentes las añade el código (no el modelo), para que nunca
aparezca una cita inventada.

Uso:
    python rag.py "¿Para qué sirve la furosemida?"
    python rag.py "¿Puedo dejar el anticoagulante?" --model llama3.2:3b -k 3
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"
DATA = Path(__file__).parent / "data"
SIN_INFO = "No tengo información sobre eso en las guías disponibles."
# Similitud coseno mínima del trozo recuperado para usarlo como contexto y citarlo.
# 0.0 = desactivado. PENDIENTE de calibrar con las puntuaciones reales (ver README).
UMBRAL_SIMILITUD = 0.0

PROMPT = """Eres un asistente que ayuda a pacientes y cuidadores a entender información clínica, basándote ÚNICAMENTE en el contexto proporcionado.
Reglas:
- Usa solo información que aparezca en el contexto. No añadas consejos generales ni conocimiento propio.
- Si el contexto no contiene la respuesta, responde exactamente: "{sin_info}" y nada más.
- No escribas citas ni nombres de documentos: las fuentes se añaden automáticamente.
- Lenguaje claro y sencillo.

Contexto:
{contexto}

Pregunta del paciente/cuidador: {pregunta}

Respuesta:"""

_emb_model = None
_embeddings = None
_docs = None


def _cargar():
    global _emb_model, _embeddings, _docs
    if _emb_model is None:
        # Import diferido: así los tests de las funciones puras no necesitan torch.
        from sentence_transformers import SentenceTransformer

        _emb_model = SentenceTransformer(MODELO_EMBEDDINGS)
        _embeddings = np.load(DATA / "embeddings.npy")
        _docs = json.loads((DATA / "docs.json").read_text(encoding="utf-8"))
        if len(_docs) != len(_embeddings):
            raise RuntimeError(
                f"docs.json ({len(_docs)} trozos) y embeddings.npy ({len(_embeddings)}) no coinciden: ejecuta python index.py"
            )


def recuperar(pregunta: str, k: int = 3):
    """Devuelve los k trozos más similares (id de guía, texto y similitud coseno)."""
    _cargar()
    q = _emb_model.encode([pregunta], normalize_embeddings=True)[0]
    sims = _embeddings @ q
    top = np.argsort(-sims)[:k]
    return [{**_docs[i], "score": float(sims[i])} for i in top]


def llamar_llm(prompt: str, modelo_llm: str = "llama3.2:3b") -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": modelo_llm, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


def es_abstencion(respuesta: str) -> bool:
    """True si la respuesta es (una paráfrasis de) 'no tengo información'.
    Centralizado aquí para que evaluate_rag.py use el mismo criterio que responder()."""
    return re.search(r"no tengo informaci[oó]n", respuesta.lower()[:120]) is not None


def responder(pregunta: str, modelo_llm: str = "llama3.2:3b", k: int = 3, umbral: float = UMBRAL_SIMILITUD):
    """Devuelve (respuesta, trozos_recuperados). Solo los trozos con similitud >= umbral
    se pasan al LLM y se citan; si ninguno lo supera, se responde SIN_INFO sin llamar al LLM."""
    trozos = recuperar(pregunta, k)
    relevantes = [t for t in trozos if t["score"] >= umbral]
    if not relevantes:
        return SIN_INFO, trozos
    contexto = "\n\n".join(t["texto"] for t in relevantes)
    prompt = PROMPT.format(sin_info=SIN_INFO, contexto=contexto, pregunta=pregunta)
    respuesta = llamar_llm(prompt, modelo_llm)
    if not es_abstencion(respuesta):
        fuentes = list(dict.fromkeys(t["id"] for t in relevantes))  # únicas, en orden de relevancia
        respuesta += "\n\nFuentes: " + ", ".join(f"[{f}]" for f in fuentes)
    return respuesta, trozos


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pregunta")
    ap.add_argument("--model", default="llama3.2:3b")
    ap.add_argument("-k", type=int, default=3)
    a = ap.parse_args()
    respuesta, trozos = responder(a.pregunta, a.model, a.k)
    print("Trozos recuperados:", ", ".join(f"{t['id']}#{t['trozo']} ({t['score']:.2f})" for t in trozos))
    print("\n" + respuesta)

"""
Indexa las guías de data/guias/ con embeddings locales (sentence-transformers).

Cada guía se trocea por párrafos (una línea = un párrafo) porque el modelo de
embeddings solo lee 128 tokens por texto: si se indexa la guía entera, todo lo
que queda después de esos 128 tokens no influye en el vector. Cada trozo lleva
delante el título de su guía para conservar el contexto.

Uso:
    python index.py

Genera data/embeddings.npy y data/docs.json (embeddings.npy no se versiona).
"""
import json
from pathlib import Path

import numpy as np

MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"


def trocear(texto: str):
    """Devuelve trozos 'Título: párrafo'. La primera línea de la guía es el título."""
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]
    titulo, parrafos = lineas[0], lineas[1:]
    if not parrafos:
        return [titulo]
    return [f"{titulo}: {p}" for p in parrafos]


def construir_indice(carpeta="data/guias", salida="data"):
    from sentence_transformers import SentenceTransformer  # import diferido (ver rag.py)

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)
    trozos, textos = [], []
    n_guias = 0
    for f in sorted(Path(carpeta).glob("*.txt")):
        n_guias += 1
        for i, t in enumerate(trocear(f.read_text(encoding="utf-8"))):
            trozos.append({"id": f.stem, "trozo": i, "texto": t})
            textos.append(t)
    if not trozos:
        raise SystemExit(f"No hay .txt en {carpeta}")
    embeddings = modelo.encode(textos, normalize_embeddings=True)
    out = Path(salida)
    np.save(out / "embeddings.npy", embeddings)
    (out / "docs.json").write_text(json.dumps(trozos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Indexadas {n_guias} guías en {len(trozos)} trozos en {out}/")


if __name__ == "__main__":
    construir_indice()

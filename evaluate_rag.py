"""
Evalúa el RAG (index.py + rag.py) contra un conjunto de preguntas con
respuesta esperada, cargado siempre desde data/preguntas_rag.json.

Mide tres cosas por separado, porque son fallos de naturaleza distinta:
1. Recuperación: para preguntas con guía esperada, ¿aparece esa guía entre
   los trozos recuperados?
2. Abstención correcta: para preguntas SIN guía esperada, ¿el sistema dice
   que no tiene información, en vez de inventar con conocimiento general?
3. Falsos "no lo sé": para preguntas CON guía esperada, ¿el sistema se
   abstiene por error aunque la información sí estaba disponible?

Uso:
    python evaluate_rag.py
    python evaluate_rag.py --model llama3.2:3b -k 3

Genera:
    - Salida por terminal con el desglose
    - RESULTADOS_RAG.md con el informe
"""
import argparse
import json
import re
from pathlib import Path

from rag import responder, es_abstencion


def contiene_palabra(texto: str, palabra: str) -> bool:
    """True si 'palabra' aparece como palabra completa (no como trozo de otra: 'no' no casa con 'información')."""
    patron = rf"(?<!\w){re.escape(palabra.lower())}(?!\w)"
    return re.search(patron, texto.lower()) is not None


def evalua_pregunta(item: dict, modelo: str, k: int) -> dict:
    respuesta, trozos = responder(item["pregunta"], modelo, k)
    fuentes_recuperadas = list(dict.fromkeys(t["id"] for t in trozos))
    abstencion = es_abstencion(respuesta)
    guia_esperada = item.get("guia_esperada")

    resultado = {
        "id": item["id"],
        "pregunta": item["pregunta"],
        "guia_esperada": guia_esperada,
        "fuentes_recuperadas": fuentes_recuperadas,
        # Recuperación y generación se miden por separado: la guía correcta puede
        # haberse recuperado y aun así el LLM fallar (o abstenerse).
        "guia_recuperada": (guia_esperada in fuentes_recuperadas) if guia_esperada else None,
        "score_top1": round(trozos[0]["score"], 3) if trozos else None,
        "abstencion": abstencion,
        "respuesta": respuesta,
    }

    if guia_esperada is None:
        # No hay guía: lo correcto es abstenerse. Responder es una alucinación.
        resultado["categoria"] = "abstencion_correcta" if abstencion else "alucinacion"
    elif abstencion:
        # Había información pero el sistema dijo que no la tenía.
        resultado["categoria"] = "falso_no_se"
    elif not resultado["guia_recuperada"]:
        resultado["categoria"] = "fallo_recuperacion"
    else:
        palabras_clave = item.get("palabras_clave", [])
        faltan = [p for p in palabras_clave if not contiene_palabra(respuesta, p)]
        resultado["categoria"] = "acierto" if not faltan else "acierto_recuperacion_pero_respuesta_incompleta"
        resultado["palabras_clave_faltantes"] = faltan

    return resultado


def carga_revision_manual(ruta: Path) -> dict:
    """{id_pregunta: {"fiel": bool, "comentario": str}}. Si el fichero no existe, no hay revisión.
    Las entradas con "fiel": null se consideran pendientes de revisar y se ignoran."""
    if not ruta.exists():
        return {}
    return {r["id"]: r for r in json.loads(ruta.read_text(encoding="utf-8")) if r.get("fiel") is not None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preguntas", default="data/preguntas_rag.json")
    parser.add_argument("--model", default="llama3.2:3b")
    parser.add_argument("-k", type=int, default=3)
    parser.add_argument("--revision", default="data/revision_manual_rag.json", help="Revisión manual de fidelidad (opcional)")
    args = parser.parse_args()

    preguntas = json.loads(Path(args.preguntas).read_text(encoding="utf-8"))
    resultados = [evalua_pregunta(p, args.model, args.k) for p in preguntas]
    revision = carga_revision_manual(Path(args.revision))

    con_guia = [r for r in resultados if r["guia_esperada"] is not None]
    sin_guia = [r for r in resultados if r["guia_esperada"] is None]

    guias_recuperadas = sum(1 for r in con_guia if r["guia_recuperada"])
    respuestas_completas = sum(1 for r in con_guia if r["categoria"] == "acierto")
    falsos_no_se = sum(1 for r in con_guia if r["categoria"] == "falso_no_se")
    fallos_recuperacion = sum(1 for r in con_guia if r["categoria"] == "fallo_recuperacion")
    respuestas_incompletas = sum(1 for r in con_guia if r["categoria"] == "acierto_recuperacion_pero_respuesta_incompleta")

    abstenciones_correctas = sum(1 for r in sin_guia if r["categoria"] == "abstencion_correcta")
    alucinaciones = sum(1 for r in sin_guia if r["categoria"] == "alucinacion")

    # ---- informe por terminal ----
    print("=" * 60)
    print(f"RECUPERACIÓN (preguntas con guía esperada: {len(con_guia)})")
    print("=" * 60)
    print(f"Guía esperada entre las recuperadas : {guias_recuperadas}/{len(con_guia)}")
    print(f"Respuesta completa (palabras clave) : {respuestas_completas}/{len(con_guia)}")
    print(f"Respuesta incompleta                : {respuestas_incompletas}/{len(con_guia)}")
    print(f"Fallo de recuperación               : {fallos_recuperacion}/{len(con_guia)}")
    print(f"Falso 'no lo sé'                    : {falsos_no_se}/{len(con_guia)}")

    print("\n" + "=" * 60)
    print(f"ABSTENCIÓN (preguntas SIN guía esperada: {len(sin_guia)})")
    print("=" * 60)
    print(f"Abstención correcta : {abstenciones_correctas}/{len(sin_guia)}")
    print(f"Alucinación         : {alucinaciones}/{len(sin_guia)}")

    if revision:
        revisadas = [r for r in resultados if r["id"] in revision]
        fieles = sum(1 for r in revisadas if revision[r["id"]]["fiel"])
        print("\n" + "=" * 60)
        print(f"FIDELIDAD (revisión manual): {fieles}/{len(revisadas)} respuestas fieles al contexto")
        print("=" * 60)

    print("\n" + "=" * 60)
    print("DETALLE")
    print("=" * 60)
    for r in resultados:
        print(f"\nPregunta {r['id']}: {r['pregunta']}")
        print(f"  Guía esperada     : {r['guia_esperada']}")
        print(f"  Fuentes recuperadas: {r['fuentes_recuperadas']}")
        print(f"  Categoría         : {r['categoria']}")
        print(f"  Similitud top-1   : {r['score_top1']}")
        if r["categoria"] == "acierto_recuperacion_pero_respuesta_incompleta":
            print(f"  Palabras clave que faltan: {r['palabras_clave_faltantes']}")
        if r["categoria"] in ("alucinacion", "falso_no_se", "fallo_recuperacion"):
            print(f"  Respuesta: {r['respuesta']}")

    # ---- informe markdown ----
    lineas = []
    lineas.append("# Resultados de evaluación del RAG\n")
    lineas.append("## Recuperación (preguntas con guía esperada)\n")
    lineas.append("| Métrica | Resultado |")
    lineas.append("|---|---|")
    lineas.append(f"| Guía esperada entre las recuperadas | {guias_recuperadas}/{len(con_guia)} |")
    lineas.append(f"| Respuesta completa (palabras clave) | {respuestas_completas}/{len(con_guia)} |")
    lineas.append(f"| Respuesta incompleta | {respuestas_incompletas}/{len(con_guia)} |")
    lineas.append(f"| Fallo de recuperación | {fallos_recuperacion}/{len(con_guia)} |")
    lineas.append(f"| Falso 'no lo sé' | {falsos_no_se}/{len(con_guia)} |")
    lineas.append("\n## Abstención (preguntas sin guía esperada)\n")
    lineas.append("| Métrica | Resultado |")
    lineas.append("|---|---|")
    lineas.append(f"| Abstención correcta | {abstenciones_correctas}/{len(sin_guia)} |")
    lineas.append(f"| Alucinación | {alucinaciones}/{len(sin_guia)} |")
    if revision:
        revisadas = [r for r in resultados if r["id"] in revision]
        fieles = sum(1 for r in revisadas if revision[r["id"]]["fiel"])
        lineas.append("\n## Fidelidad al contexto (revisión manual)\n")
        lineas.append(f"{fieles}/{len(revisadas)} respuestas fieles al contexto recuperado.\n")
    lineas.append("\n## Detalle por pregunta\n")
    for r in resultados:
        lineas.append(f"- **Pregunta {r['id']}** — _{r['categoria']}_")
        lineas.append(f"  - Pregunta: {r['pregunta']}")
        lineas.append(f"  - Guía esperada: `{r['guia_esperada']}`")
        lineas.append(f"  - Fuentes recuperadas: `{r['fuentes_recuperadas']}` (similitud top-1: {r['score_top1']})")
        if r["id"] in revision:
            lineas.append(f"  - Revisión manual: {'fiel' if revision[r['id']]['fiel'] else 'NO fiel'} — {revision[r['id']].get('comentario', '')}")
        lineas.append(f"  - Respuesta: {r['respuesta']}")

    out_md = Path(__file__).parent / "RESULTADOS_RAG.md"
    out_md.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nInforme markdown generado en {out_md}")


if __name__ == "__main__":
    main()

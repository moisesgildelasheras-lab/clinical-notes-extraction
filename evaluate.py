"""
Evalúa las predicciones del modelo campo a campo contra el ground truth
(cargado siempre desde data/notas_sinteticas.json, nunca desde el propio
fichero de resultados, para que el ground truth tenga una única fuente
de verdad).

Uso:
    python evaluate.py --resultados data/resultados_llama3.2-3b.json

Genera:
    - Salida por terminal con el desglose
    - RESULTADOS.md con el informe listo para pegar/enlazar en el README
"""
import argparse
import json
import re
from pathlib import Path

# Frases de posología/calificadores conocidos a eliminar de nombres de fármacos.
# No es exhaustivo -- es un parche pragmático, no una solución robusta
# (la solución "real" sería normalizar contra un vocabulario controlado,

CUALIFICADORES_FARMACO = [
    r"\s*\d+([.,]\d+)?\s*(mg|mcg|g|ml|ui)\b.*$",
    r"\s+de alta intensidad\b.*$",
    r"\s+de baja intensidad\b.*$",
    r"\s+de liberación prolongada\b.*$",
]

STOPWORDS_DIAGNOSTICO = {
    "de", "la", "el", "en", "y", "a", "con", "sin", "tras", "por",
    "los", "las", "del", "al", "un", "una",
}


def normaliza_texto(v):
    return v.strip().lower() if isinstance(v, str) else v


def normaliza_farmaco(nombre: str) -> str:
    n = nombre.strip().lower()
    for patron in CUALIFICADORES_FARMACO:
        n = re.sub(patron, "", n).strip()
    return n


def normaliza_medicacion(lista):
    """Aplana combinaciones ('a/b' -> 'a', 'b') y limpia dosis/cualificadores,
    para que el formato de escritura no penalice si el principio activo es el mismo."""
    if not lista:
        return set()
    aplanado = []
    for item in lista:
        partes = item.split("/")
        aplanado.extend(partes)
    return {normaliza_farmaco(p) for p in aplanado if normaliza_farmaco(p)}


def compara_campo_simple(pred, gt):
    return normaliza_texto(pred) == normaliza_texto(gt)


def compara_medicacion(pred, gt):
    return normaliza_medicacion(pred) == normaliza_medicacion(gt)


def jaccard_palabras(a: str, b: str) -> float:
    wa = set(normaliza_texto(a).split()) - STOPWORDS_DIAGNOSTICO
    wb = set(normaliza_texto(b).split()) - STOPWORDS_DIAGNOSTICO
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def compara_diagnostico(pred, gt):
    """Devuelve ('exacto' | 'parcial' | 'fallo', score) -- no colapsamos
    todo a un booleano porque la exactitud de string no es lo que importa
    clínicamente aquí; lo que importa es si captura el concepto correcto."""
    if pred is None or gt is None:
        return ("fallo", 0.0) if pred != gt else ("exacto", 1.0)
    p, g = normaliza_texto(pred), normaliza_texto(gt)
    if p == g:
        return "exacto", 1.0
    if p in g or g in p:
        return "parcial", 0.8
    score = jaccard_palabras(p, g)
    if score >= 0.4:
        return "parcial", score
    return "fallo", score


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resultados", required=True, help="Ruta al fichero de resultados a evaluar")
    parser.add_argument("--notas", default="data/notas_sinteticas.json")
    args = parser.parse_args()

    notas = {n["id"]: n["ground_truth"] for n in json.loads(Path(args.notas).read_text(encoding="utf-8"))}
    resultados = json.loads(Path(args.resultados).read_text(encoding="utf-8"))

    campos_simples = ["edad", "sexo", "fevi_porcentaje"]
    aciertos = {c: 0 for c in campos_simples}
    total = {c: 0 for c in campos_simples}
    diag_conteo = {"exacto": 0, "parcial": 0, "fallo": 0}
    med_aciertos, med_total = 0, 0
    aler_aciertos, aler_total = 0, 0
    fallos_detalle, notas_null_vs_vacio = [], []

    for r in resultados:
        gt = notas.get(r["id"])
        if gt is None:
            continue
        if r["prediccion"] is None:
            fallos_detalle.append({"nota_id": r["id"], "campo": "TODOS", "prediccion": None, "esperado": None, "nota": f"Error de parseo: {r['error']}"})
            continue
        pred = r["prediccion"]

        for c in campos_simples:
            total[c] += 1
            if compara_campo_simple(pred.get(c), gt.get(c)):
                aciertos[c] += 1
            else:
                fallos_detalle.append({"nota_id": r["id"], "campo": c, "prediccion": pred.get(c), "esperado": gt.get(c)})

        tipo, score = compara_diagnostico(pred.get("diagnostico_principal"), gt.get("diagnostico_principal"))
        diag_conteo[tipo] += 1
        if tipo != "exacto":
            fallos_detalle.append({"nota_id": r["id"], "campo": "diagnostico_principal", "prediccion": pred.get("diagnostico_principal"), "esperado": gt.get("diagnostico_principal"), "nota": f"tipo={tipo}, score={score:.2f}"})

        med_total += 1
        if compara_medicacion(pred.get("medicacion"), gt.get("medicacion")):
            med_aciertos += 1
        else:
            fallos_detalle.append({"nota_id": r["id"], "campo": "medicacion", "prediccion": pred.get("medicacion"), "esperado": gt.get("medicacion")})

        aler_total += 1
        pred_aler, gt_aler = pred.get("alergias"), gt.get("alergias")
        # Comparación exacta salvo por orden/mayúsculas dentro de la lista.
        aler_iguales = normaliza_medicacion(pred_aler) == normaliza_medicacion(gt_aler) and (pred_aler is None) == (gt_aler is None)
        if aler_iguales:
            aler_aciertos += 1
        else:
            if pred_aler is None and gt_aler == []:
                notas_null_vs_vacio.append(r["id"])
            fallos_detalle.append({"nota_id": r["id"], "campo": "alergias", "prediccion": pred_aler, "esperado": gt_aler})

    # ---- informe por terminal ----
    print("=" * 60)
    print("PRECISIÓN POR CAMPO")
    print("=" * 60)
    for c in campos_simples:
        print(f"{c:25s}: {aciertos[c]}/{total[c]}  ({100*aciertos[c]/total[c]:.0f}%)")
    n_diag = sum(diag_conteo.values())
    print(f"{'diagnostico_principal':25s}: exacto {diag_conteo['exacto']}/{n_diag} | parcial {diag_conteo['parcial']}/{n_diag} | fallo {diag_conteo['fallo']}/{n_diag}")
    print(f"{'medicacion (normalizada)':25s}: {med_aciertos}/{med_total}  ({100*med_aciertos/med_total:.0f}%)")
    print(f"{'alergias':25s}: {aler_aciertos}/{aler_total}  ({100*aler_aciertos/aler_total:.0f}%)")
    if notas_null_vs_vacio:
        print(f"\n  -> {len(notas_null_vs_vacio)} de esos fallos de alergias son null-vs-[] (notas {notas_null_vs_vacio})")

    print("\n" + "=" * 60)
    print("DETALLE DE FALLOS")
    print("=" * 60)
    for f in fallos_detalle:
        extra = f.get("nota", "")
        print(f"\nNota {f['nota_id']} — {f['campo']}" + (f" ({extra})" if extra else ""))
        print(f"  Predicho : {f['prediccion']}")
        print(f"  Esperado : {f['esperado']}")

    # ---- informe markdown automático ----
    lineas = []
    lineas.append(f"# Resultados de evaluación — `{Path(args.resultados).name}`\n")
    lineas.append("| Campo | Resultado |")
    lineas.append("|---|---|")
    for c in campos_simples:
        lineas.append(f"| {c} | {aciertos[c]}/{total[c]} ({100*aciertos[c]/total[c]:.0f}%) |")
    lineas.append(f"| diagnostico_principal | exacto {diag_conteo['exacto']}/{n_diag}, parcial {diag_conteo['parcial']}/{n_diag}, fallo {diag_conteo['fallo']}/{n_diag} |")
    lineas.append(f"| medicacion (normalizada) | {med_aciertos}/{med_total} ({100*med_aciertos/med_total:.0f}%) |")
    lineas.append(f"| alergias | {aler_aciertos}/{aler_total} ({100*aler_aciertos/aler_total:.0f}%) |")
    lineas.append("\n## Fallos detallados\n")
    for f in fallos_detalle:
        extra = f.get("nota", "")
        lineas.append(f"- **Nota {f['nota_id']} — {f['campo']}**" + (f" _{extra}_" if extra else ""))
        lineas.append(f"  - Predicho: `{f['prediccion']}`")
        lineas.append(f"  - Esperado: `{f['esperado']}`")

    out_md = Path(args.resultados).parent.parent / "RESULTADOS.md"
    out_md.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\nInforme markdown generado en {out_md}")


if __name__ == "__main__":
    main()

"""
Extracción estructurada de información clínica cardiológica
a partir de texto libre en castellano, usando un LLM local vía Ollama.

Uso:
    python extract.py                     # usa el modelo por defecto (llama3.2:3b)
    python extract.py --model qwen2.5:7b   # para comparar con un modelo más grande
"""
import argparse
import json
import re
import sys
from pathlib import Path

import requests
from pydantic import ValidationError

from schema import ExtraccionClinica, JSON_SCHEMA_DESCRIPTION

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT_TEMPLATE = """Eres un asistente que extrae información estructurada de notas clínicas de cardiología en castellano.

Reglas estrictas:
1. Extrae ÚNICAMENTE información que aparece explícitamente en el texto. No infieras diagnósticos, aunque te parezcan clínicamente obvios a partir de otros datos (p.ej. FEVI baja no significa que debas escribir "insuficiencia cardiaca" si el texto no lo dice).
2. "diagnostico_principal": usa el motivo de consulta o diagnóstico tal como se menciona literalmente, de forma breve.
3. "fevi_porcentaje": solo si el texto da un NÚMERO explícito. Si dice "conservada", "normal" o similar SIN número, usa null. No inventes un porcentaje.
4. "medicacion": incluye cada fármaco SIN dosis ni posología (omite "5mg", "de alta intensidad", etc. — solo el nombre del principio activo). Si el texto indica explícitamente que un fármaco YA NO se toma actualmente (p.ej. "actualmente sin anticoagulación", "suspendido", "hasta hace X"), NO lo incluyas.
5. "sexo": dedúcelo también de la concordancia gramatical del texto (p.ej. "derivada", "remitida" = femenino) aunque no diga explícitamente "mujer".
6. "alergias": usa null si el texto no menciona el tema de alergias en absoluto; usa [] si el texto dice explícitamente que no tiene alergias.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional, sin backticks, siguiendo este esquema exacto:
{schema}

Nota clínica:
\"\"\"
{nota}
\"\"\"

JSON:"""


def extraer_json(texto_modelo: str) -> dict:
    texto_modelo = texto_modelo.strip()
    texto_modelo = re.sub(r"^```(json)?", "", texto_modelo).strip()
    texto_modelo = re.sub(r"```$", "", texto_modelo).strip()
    match = re.search(r"\{.*\}", texto_modelo, re.DOTALL)
    if not match:
        raise ValueError(f"No se encontró JSON en la respuesta: {texto_modelo[:200]}")
    return json.loads(match.group(0))


def consultar_modelo(nota: str, modelo: str) -> str:
    prompt = PROMPT_TEMPLATE.format(schema=JSON_SCHEMA_DESCRIPTION, nota=nota)
    resp = requests.post(
        OLLAMA_URL,
        json={"model": modelo, "prompt": prompt, "stream": False, "options": {"temperature": 0}},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.2:3b", help="Nombre del modelo en Ollama")
    parser.add_argument("--out", default=None, help="Ruta de salida (por defecto: data/resultados_<modelo>.json)")
    args = parser.parse_args()

    data_path = Path(__file__).parent / "data" / "notas_sinteticas.json"
    notas = json.loads(data_path.read_text(encoding="utf-8"))

    resultados = []
    for item in notas:
        print(f"[{args.model}] Procesando nota {item['id']}...", file=sys.stderr)
        try:
            respuesta_cruda = consultar_modelo(item["texto"], args.model)
            extraido_dict = extraer_json(respuesta_cruda)
            extraido = ExtraccionClinica(**extraido_dict)
            resultados.append({"id": item["id"], "prediccion": extraido.model_dump(), "error": None})
        except (ValidationError, ValueError, json.JSONDecodeError, requests.RequestException) as e:
            resultados.append({"id": item["id"], "prediccion": None, "error": str(e)})

    modelo_slug = args.model.replace(":", "-").replace("/", "-")
    out_path = Path(args.out) if args.out else Path(__file__).parent / "data" / f"resultados_{modelo_slug}.json"
    out_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultados guardados en {out_path}")


if __name__ == "__main__":
    main()

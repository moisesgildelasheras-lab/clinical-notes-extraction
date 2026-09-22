# Extracción estructurada de información clínica con LLMs locales

Proyecto personal de aprendizaje: convertir texto clínico libre en
castellano en información estructurada, usando un modelo de lenguaje
**desplegado localmente** (sin llamadas a APIs externas, sin que ningún
dato salga del entorno) — el tipo de tarea que aparece habitualmente en
roles de IA aplicada a datos clínicos.

## Por qué este proyecto

Mi experiencia previa en ML (TFG con Random Forest/XGBoost sobre datos
tabulares) no incluía trabajo con LLMs más allá de usarlos como asistente.
Quería tener algo concreto que demostrara diseño de prompts, salida
estructurada validada y evaluación rigurosa — así que construí esto en un
par de días, iterando sobre mis propios errores.

## Qué hace

1. `data/notas_sinteticas.json` — 8 notas clínicas de cardiología
   **sintéticas** (inventadas, ningún dato real de paciente) con su
   extracción "correcta" anotada a mano — y auditada dos veces (ver
   sección "Sobre el ground truth" más abajo).
2. `extract.py` — envía cada nota a un modelo corriendo en local vía
   [Ollama](https://ollama.com) (por defecto `llama3.2:3b`), con un
   prompt que pide una salida JSON siguiendo un esquema fijo
   (`schema.py`, validado con Pydantic) y reglas explícitas sobre casos
   ambiguos (medicación pasada vs. actual, FEVI cualitativa vs.
   numérica, deducción de sexo por concordancia gramatical...).
   Acepta `--model` para comparar modelos distintos.
3. `evaluate.py` — compara la predicción contra el ground truth **campo
   a campo**, con normalización específica por tipo de dato (fármacos
   sin dosis, combinaciones aplanadas, diagnóstico con matching parcial
   por solapamiento de palabras en vez de igualdad exacta de string) y
   genera automáticamente `RESULTADOS.md` con el desglose y el detalle
   de cada fallo.

## Cómo correrlo

```bash
# 1. Instalar Ollama (https://ollama.com/download) y descargar el modelo
ollama pull llama3.2:3b

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # en Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Ejecutar
python extract.py
python evaluate.py --resultados data/resultados_llama3.2-3b.json
```

Esto genera `data/resultados_llama3.2-3b.json` (predicciones) y
`RESULTADOS.md` (informe con el desglose por campo y el detalle de cada
fallo), en la raíz del proyecto.

## Resultados (modelo `llama3.2:3b`)

| Campo | Resultado |
|---|---|
| edad | 8/8 (100%) |
| sexo | 7/8 (88%) |
| FEVI (%) | 8/8 (100%) |
| diagnóstico principal | exacto 0/8, parcial (concepto correcto, distinta redacción) 5/8, fallo 3/8 |
| medicación (normalizada) | 7/8 (88%) |
| alergias | 5/8 (62%) |

El detalle completo, incluyendo cada predicción y su valor esperado, está
en `RESULTADOS.md` (se regenera automáticamente al correr `evaluate.py`).

## Lo que aprendí sobre dónde falla el modelo — y dónde no es culpa del modelo

**Primera iteración:** con un prompt más simple y sin normalización en la
evaluación, casi todos los campos "fallaban" — pero al revisar el detalle,
la mayoría eran falsos negativos de la propia evaluación (comparar
`"bisoprolol 5mg"` contra `"bisoprolol"` como si fueran distintos, o exigir
coincidencia exacta de string en un campo de texto libre como el
diagnóstico). Corregir esto — no el modelo — resolvió la mayoría de los
"fallos".

**Lo que sí es un fallo real del modelo, y persiste con prompt explícito
en contra:**

- **Nunca hay coincidencia exacta de string en el diagnóstico**, ni un
  solo caso de 8. El modelo capta el concepto correcto en la mayoría
  (5/8 parcial), pero siempre con una redacción más breve que la del
  ground truth — esperable, dado que el prompt le pide brevedad
  explícitamente.
- **Distinguir "no se menciona" de "se menciona que no aplica".** En
  alergias, el modelo devuelve `null` en 3 de 8 casos donde el texto dice
  explícitamente *"sin alergias conocidas"* (que debería ser `[]`, no
  `null`). Es una distinción sutil pero clínicamente relevante: no es lo
  mismo no tener el dato que tener confirmado que el paciente no es
  alérgico a nada.
- **Confundir motivo de consulta con diagnóstico confirmado** (nota 6):
  el texto dice *"derivada por soplo sistólico"* (motivo) y más adelante
  *"Ecocardiograma: insuficiencia mitral leve"* (diagnóstico real). El
  modelo se quedó con el motivo inicial en vez de con el hallazgo
  posterior — sugiere que da más peso a la información que aparece
  primero en el texto.
- **Deducción de sexo por concordancia gramatical falla en 1/8** (mismo
  caso, "derivada"), pese a instrucción explícita — un detalle lingüístico
  menor para un hablante nativo, pero no trivial para el modelo.

## Sobre el ground truth (y por qué importa contarlo)

Al construir el dataset cometí 2 errores de anotación reales: en dos
notas escribí como "diagnóstico principal" una conclusión clínica
*inferida* (p.ej. "insuficiencia cardiaca") que el texto no decía
explícitamente — violando mi propia regla de "extrae solo lo explícito".
Los detecté al auditar el dataset a mano, pero decidí no corregirlos:
las notas 1 y 5 siguen incluyendo "insuficiencia cardiaca" como parte
del diagnóstico principal, pese a que el texto no lo dice de forma
explícita. Lo dejo documentado aquí porque me parece más honesto (y más
interesante) que ocultarlo: en cualquier proyecto de extracción de
información, el ground truth también se equivoca, y evaluar bien pasa
por auditarlo, no solo por confiar en él — auditar no siempre implica
corregir de inmediato.

## Limitaciones y siguientes pasos

- Dataset de evaluación pequeño (8 notas) — suficiente para detectar
  patrones de error, no para sacar conclusiones estadísticas robustas.
- La normalización de fármacos (`evaluate.py`) es un parche basado en
  reglas (quitar dosis, aplanar combinaciones por "/"), no una solución
  robusta. La solución "de verdad" pasaría por normalizar contra un
  vocabulario controlado (p.ej. ATC), fuera del alcance de un proyecto de
  un par de días.
- El matching de `diagnostico_principal` usa solapamiento de palabras
  como proxy de similitud semántica — funciona razonablemente aquí, pero
  con textos más variados un embedding semántico (o un LLM como juez)
  sería más fiable.
- Pendiente: repetir con un modelo más grande (`--model qwen2.5:7b` o
  similar) para comprobar si el razonamiento temporal en medicación
  mejora con más parámetros.

## Autor

Moisés Gil de las Heras — Ingeniero Biomédico (UPM, 2026)
[LinkedIn](https://www.linkedin.com/in/moises-gil-de-las-heras-8599442b7/)

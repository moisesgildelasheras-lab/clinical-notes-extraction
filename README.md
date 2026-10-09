# Extracción estructurada de información clínica y RAG con LLMs locales

Proyecto personal de aprendizaje con dos partes, ambas con un modelo de
lenguaje **desplegado localmente** (sin llamadas a APIs externas, sin que
ningún dato salga del entorno):

1. **Extracción estructurada**: convertir texto clínico libre en castellano
   en un JSON validado con un esquema fijo.
2. **RAG**: responder preguntas de un paciente o cuidador usando solo unas
   guías cortas recuperadas por similitud semántica, citando la fuente y
   diciendo "no lo sé" cuando la información no está.

> **Aviso:** es un proyecto educativo. Las notas clínicas son sintéticas y
> los textos de `data/guias/` son material propio del proyecto, no guías
> clínicas oficiales. Nada de lo que genera debe usarse para tomar
> decisiones médicas.

## Por qué este proyecto

Mi experiencia previa en ML (TFG con Random Forest/XGBoost sobre datos
tabulares) no incluía trabajo con LLMs más allá de usarlos como asistente.
Quería tener algo concreto que demostrara diseño de prompts, salida
estructurada validada y evaluación rigurosa. Empecé por la extracción
estructurada y después la amplié con un RAG local, iterando sobre mis
propios errores y documentando los fallos en vez de esconderlos.

## Estructura

```text
clinical-notes-extraction/
├── schema.py               # Esquema Pydantic de la extracción
├── extract.py              # Extracción con LLM local (Ollama)
├── evaluate.py             # Evaluación campo a campo -> RESULTADOS.md
├── index.py                # RAG: trocea las guías y calcula embeddings
├── rag.py                  # RAG: recuperación + respuesta con fuentes
├── evaluate_rag.py         # RAG: evaluación -> RESULTADOS_RAG.md
├── data/
│   ├── notas_sinteticas.json         # 8 notas + ground truth
│   ├── resultados_llama3.2-3b.json   # Predicciones de la extracción
│   ├── guias/                        # 10 textos cortos (una guía = un tema)
│   ├── preguntas_rag.json            # 13 preguntas de evaluación del RAG
│   ├── docs.json                     # Trozos indexados (generado por index.py)
│   └── embeddings.npy                # Embeddings (generado, NO se versiona)
├── tests/                  # Tests unitarios (no necesitan Ollama ni descargar nada)
├── pytest.ini
├── .github/workflows/tests.yml   # Ejecuta los tests en GitHub Actions
├── RESULTADOS.md
├── RESULTADOS_RAG.md
└── requirements.txt
```

## Parte 1 — Extracción estructurada

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

### Resultados (modelo `llama3.2:3b`)

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

### Lo que aprendí sobre dónde falla el modelo — y dónde no es culpa del modelo

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
  `null`). De hecho, en las 8 notas el modelo **no devuelve ni una sola
  vez `[]`**: o una lista con alergias, o `null`. Es una distinción sutil
  pero clínicamente relevante: no es lo mismo no tener el dato que tener
  confirmado que el paciente no es alérgico a nada.
- **Confundir motivo de consulta con diagnóstico confirmado** (nota 6):
  el texto dice *"derivada por soplo sistólico"* (motivo) y más adelante
  *"Ecocardiograma: insuficiencia mitral leve"* (diagnóstico real). El
  modelo se quedó con el motivo inicial en vez de con el hallazgo
  posterior — sugiere que da más peso a la información que aparece
  primero en el texto.
- **Deducción de sexo por concordancia gramatical** (nota 6): el texto
  dice "Paciente de 39 años *derivada*" y el modelo responde `"M"`, pese a
  la instrucción explícita de deducirlo por concordancia. El ground truth
  de esa nota tiene `sexo: null`, así que la predicción cuenta como fallo
  con cualquiera de los dos valores.

### Sobre el ground truth (y por qué importa contarlo)

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

## Parte 2 — RAG local con citas y abstención

```text
pregunta ──► embedding ──► similitud coseno con los trozos de las guías ──► top-k
                                                                             │
 respuesta + fuentes ◄── LLM local (Ollama), solo con ese contexto ◄─────────┘
```

- `index.py` — lee `data/guias/*.txt` (la primera línea es el título; cada
  línea siguiente es un párrafo). Cada párrafo se indexa como un trozo
  `Título: párrafo`, porque el modelo de embeddings solo lee 128 tokens por
  texto y, si se indexase la guía entera, lo que quedase después no
  influiría en el vector. Embeddings con
  `paraphrase-multilingual-MiniLM-L12-v2` (`sentence-transformers`,
  multilingüe y local). 10 guías → 43 trozos.
- `rag.py` — recupera los k trozos más similares (k=3 por defecto) y se los
  pasa a `llama3.2:3b` con un prompt que prohíbe usar conocimiento propio y
  fija la frase exacta de abstención. **Las fuentes las añade el código, no
  el modelo**, para que el LLM nunca pueda inventarse una cita.
- `evaluate_rag.py` — evalúa contra `data/preguntas_rag.json` y genera
  `RESULTADOS_RAG.md`. Mide por separado cosas de naturaleza distinta:
  1. **Recuperación**: ¿está la guía esperada entre los trozos recuperados?
  2. **Respuesta**: ¿contiene las palabras clave esperadas? ¿O se abstiene
     por error aunque la información estaba disponible (falso "no lo sé")?
  3. **Abstención**: ante una pregunta sin guía, ¿dice que no sabe o
     inventa (alucinación)?

### Resultados (13 preguntas: 10 con guía, 3 sin guía)

| Qué se mide | Resultado |
|---|---|
| Guía esperada entre las 3 recuperadas | 10/10 |
| Respuesta completa (palabras clave presentes) | 8/10 |
| Respuesta incompleta | 1/10 (pregunta 8: no menciona el 112) |
| Falso "no lo sé" | 1/10 (pregunta 4: stent) |
| Abstención correcta (preguntas sin guía) | 2/3 |
| Alucinación (preguntas sin guía) | 1/3 (pregunta 12: marcapasos) |

`RESULTADOS_RAG.md` tiene la respuesta completa a cada pregunta.

### Lo que aprendí (y lo que no mide bien mi evaluación)

- **La recuperación funciona; los fallos son de generación.** En las 10
  preguntas con guía, la guía correcta siempre estuvo entre las
  recuperadas, incluso en la pregunta 4, donde el modelo aun así respondió
  "no tengo información" (la guía solo dice que la duración la decide el
  cardiólogo, sin dar una cifra).
- **La alucinación más preocupante es la de la pregunta 12.** Ante
  *"¿Puedo hacer ejercicio intenso si llevo un marcapasos?"*, ninguna guía
  habla de marcapasos, pero el sistema recuperó trozos de betabloqueantes e
  insuficiencia cardiaca y el modelo construyó una respuesta con ese
  contexto. En un dominio clínico, contestar con seguridad algo que no está
  en las fuentes es peor que no contestar. Ahora mismo el sistema **siempre**
  pasa al LLM los k trozos más parecidos, por poco parecidos que sean: no
  hay umbral mínimo de similitud.
- **Las fuentes que se muestran no son solo las usadas.** Se citan todos
  los trozos recuperados, aunque el modelo no los haya usado (la respuesta
  sobre la furosemida cita también la guía de IECA/sacubitrilo-valsartán).
  Evita citas inventadas, pero no garantiza que cada cita sea pertinente.
- **La métrica de palabras clave es débil.** Una pregunta puede contar como
  acierto aunque la respuesta tenga un matiz incorrecto: en la pregunta 7,
  la respuesta manda a urgencias ante síntomas habituales de insuficiencia
  cardiaca, cuando la guía reserva urgencias para los graves y para los
  demás dice "avisar al equipo médico". Por eso la fidelidad al contexto
  hay que revisarla a mano. Además, la palabra clave de la pregunta 6 era
  `"no"`, que se cumplía casi siempre (coincidía dentro de otras palabras);
  la cambié por `"periodo de espera"` y ahora las palabras clave se buscan
  como palabra completa.

### Limitaciones del RAG

- Evaluación pequeña (13 preguntas, solo 3 sin guía): sirve para ver
  patrones de fallo, no para estimar porcentajes fiables.
- Las guías y las preguntas las he preparado yo, y varias palabras clave
  salen del propio texto de las guías, así que el sistema sale favorecido
  frente a preguntas escritas por otra persona.
- Modelo de 3B parámetros: sigue mal las instrucciones de abstención.

## Cómo correrlo

```bash
# 1. Instalar Ollama (https://ollama.com/download) y descargar el modelo
ollama pull llama3.2:3b

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate        # en Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3a. Extracción estructurada
python extract.py
python evaluate.py --resultados data/resultados_llama3.2-3b.json

# 3b. RAG (la primera vez se descarga el modelo de embeddings, unos cientos de MB)
python index.py                 # genera data/embeddings.npy y data/docs.json
python rag.py "¿Para qué sirve la furosemida?"
python evaluate_rag.py

# 4. Tests (no necesitan Ollama)
python -m pytest -q
```

Genera `data/resultados_llama3.2-3b.json` (predicciones), `RESULTADOS.md` y
`RESULTADOS_RAG.md` en la raíz del proyecto. `data/embeddings.npy` no está
versionado: hay que generarlo con `python index.py` antes de usar el RAG.

## Limitaciones y siguientes pasos

- Dataset de evaluación de la extracción pequeño (8 notas) — suficiente
  para detectar patrones de error, no para sacar conclusiones estadísticas
  robustas.
- La normalización de fármacos (`evaluate.py`) es un parche basado en
  reglas (quitar dosis, aplanar combinaciones por "/"), no una solución
  robusta. La solución "de verdad" pasaría por normalizar contra un
  vocabulario controlado (p.ej. ATC), fuera del alcance de este proyecto.
- El matching de `diagnostico_principal` usa solapamiento de palabras
  como proxy de similitud semántica — funciona razonablemente aquí, pero
  con textos más variados un embedding semántico (o un LLM como juez)
  sería más fiable.
- **Pendiente (RAG):** umbral mínimo de similitud para abstenerse antes de
  llamar al LLM, citar solo los trozos realmente usados, revisión manual de
  fidelidad de todas las respuestas y un conjunto de preguntas más grande,
  con más preguntas fuera de alcance.
- **Pendiente (extracción):** probar si un esquema de tres estados para
  alergias (no mencionado / ninguna / lista) o ejemplos en el prompt
  resuelven que el modelo nunca devuelva `[]`, y publicar la comparación
  antes/después.
- **Pendiente:** repetir con un modelo más grande (`--model qwen2.5:7b` o
  similar) para comprobar si el razonamiento temporal en medicación
  mejora con más parámetros.


## Autor

Moisés Gil de las Heras — Ingeniero Biomédico (UPM, 2026)
[LinkedIn](https://www.linkedin.com/in/moises-gil-de-las-heras-8599442b7/)

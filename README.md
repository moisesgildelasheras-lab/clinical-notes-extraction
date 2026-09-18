# Extracción estructurada de información clínica con LLMs locales

Proyecto personal para practicar y con el fin de aprender, consiste en:
convertir texto clínico libre en castellano en información estructurada,
usando un modelo de lenguaje **desplegado localmente** (sin llamadas a APIs
externas, sin que ningún dato salga del entorno).

## Por qué este proyecto

Mi experiencia previa en ML (TFG con Random Forest/XGBoost sobre datos
tabulares) no incluía trabajo con LLMs más allá de usarlos como asistente.
Quería tener algo concreto que demostrara diseño de prompts, salida
estructurada validada y despliegue local.

## Qué hace

1. `data/notas_sinteticas.json` — 8 notas clínicas de cardiología
   **sintéticas** (inventadas, ningún dato real de paciente) con su
   extracción "correcta" anotada a mano.
2. `extract.py` — envía cada nota a un modelo pequeño corriendo en local
   vía [Ollama](https://ollama.com) (`llama3.2:3b`), con un prompt que
   pide una salida JSON siguiendo un esquema fijo (`schema.py`, validado
   con Pydantic).
3. `evaluate.py` — compara la predicción del modelo contra el ground
   truth **campo a campo**, y no solo da un % de acierto: señala patrones
   de error para investigar (p.ej. confundir medicación pasada con
   actual, o no distinguir "no se menciona el dato" de "se menciona que
   no aplica").

## Cómo correrlo

```bash
# 1. Instalar Ollama (https://ollama.com/download) y descargar el modelo
ollama pull llama3.2:3b

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Ejecutar
python extract.py
python evaluate.py --resultados data/resultados_llama3.2-3b.json
```

## Limitaciones y siguientes pasos

- Dataset de evaluación pequeño (8 notas) — suficiente para detectar
  patrones de error, no para sacar conclusiones estadísticas robustas.
- No se ha probado cuantización ni comparación de tamaños de modelo
  (3B vs 7B vs mayor) — sería el siguiente paso lógico, junto con medir
  latencia/memoria en la infraestructura disponible.
- El manejo de negación y de tiempo verbal ("tomaba" vs "toma") es el
  punto más frágil detectado — es un problema conocido de extracción de
  información en texto clínico, no específico de este modelo.

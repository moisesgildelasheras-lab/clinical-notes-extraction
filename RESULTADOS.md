# Resultados de evaluación — `resultados_llama3.2-3b.json`

| Campo | Resultado |
|---|---|
| edad | 8/8 (100%) |
| sexo | 7/8 (88%) |
| fevi_porcentaje | 8/8 (100%) |
| diagnostico_principal | exacto 0/8, parcial 5/8, fallo 3/8 |
| medicacion (normalizada) | 7/8 (88%) |
| alergias | 5/8 (62%) |

## Fallos detallados

- **Nota 1 — diagnostico_principal** _tipo=fallo, score=0.00_
  - Predicho: `disnea de esfuerzo progresiva`
  - Esperado: `Insuficiencia cardiaca / IAM anterior previo`
- **Nota 2 — diagnostico_principal** _tipo=parcial, score=0.80_
  - Predicho: `palpitaciones`
  - Esperado: `Palpitaciones, sin hallazgos agudos`
- **Nota 2 — alergias**
  - Predicho: `None`
  - Esperado: `[]`
- **Nota 3 — diagnostico_principal** _tipo=parcial, score=0.50_
  - Predicho: `miocardiopatía dilatada de origen no isquémico`
  - Esperado: `Miocardiopatía dilatada no isquémica`
- **Nota 4 — diagnostico_principal** _tipo=parcial, score=0.80_
  - Predicho: `dolor torácico atípico`
  - Esperado: `Dolor torácico atípico, coronarias sin lesiones`
- **Nota 5 — diagnostico_principal** _tipo=parcial, score=0.80_
  - Predicho: `fibrilación auricular permanente`
  - Esperado: `Fibrilación auricular permanente, insuficiencia cardiaca`
- **Nota 6 — sexo**
  - Predicho: `M`
  - Esperado: `None`
- **Nota 6 — diagnostico_principal** _tipo=fallo, score=0.00_
  - Predicho: `soplo sistólico`
  - Esperado: `Insuficiencia mitral leve`
- **Nota 6 — alergias**
  - Predicho: `None`
  - Esperado: `[]`
- **Nota 7 — diagnostico_principal** _tipo=fallo, score=0.00_
  - Predicho: `seguimiento tras implante de stent en DA`
  - Esperado: `Post-stent en descendente anterior`
- **Nota 8 — diagnostico_principal** _tipo=parcial, score=0.80_
  - Predicho: `valvulopatía aórtica reumática`
  - Esperado: `Valvulopatía aórtica reumática, recambio valvular`
- **Nota 8 — medicacion**
  - Predicho: `['acenocumarol']`
  - Esperado: `[]`
- **Nota 8 — alergias**
  - Predicho: `None`
  - Esperado: `[]`
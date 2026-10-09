# Resultados de evaluación del RAG

## Recuperación (preguntas con guía esperada)

| Métrica | Resultado |
|---|---|
| Guía esperada entre las recuperadas | 10/10 |
| Respuesta completa (palabras clave) | 8/10 |
| Respuesta incompleta | 1/10 |
| Fallo de recuperación | 0/10 |
| Falso 'no lo sé' | 1/10 |

## Abstención (preguntas sin guía esperada)

| Métrica | Resultado |
|---|---|
| Abstención correcta | 2/3 |
| Alucinación | 1/3 |

## Detalle por pregunta

- **Pregunta 1** — _acierto_
  - Pregunta: ¿Para qué sirve la furosemida?
  - Guía esperada: `diureticos_espironolactona_eplerenona`
  - Fuentes recuperadas: `['diureticos_espironolactona_eplerenona', 'ieca_ara2_sacubitrilo_valsartan']` (similitud top-1: 0.604)
  - Respuesta: La furosemida es un diurético que ayuda a eliminar el exceso de líquido por la orina y alivia la hinchazón y la falta de aire. Es normal orinar más durante las horas siguientes a la toma.

Fuentes: [diureticos_espironolactona_eplerenona], [ieca_ara2_sacubitrilo_valsartan]
- **Pregunta 2** — _acierto_
  - Pregunta: ¿Qué significa tener la FEVI baja?
  - Guía esperada: `fevi_fraccion_eyeccion`
  - Fuentes recuperadas: `['fevi_fraccion_eyeccion']` (similitud top-1: 0.622)
  - Respuesta: Una FEVI baja significa que la fracción de eyección del ventrículo izquierdo es menor que el 40%. Esto indica una función de bombeo reducida.

Fuentes: [fevi_fraccion_eyeccion]
- **Pregunta 3** — _acierto_
  - Pregunta: ¿Puedo dejar de tomar el anticoagulante si me encuentro bien?
  - Guía esperada: `fibrilacion_auricular_anticoagulacion`
  - Fuentes recuperadas: `['diureticos_espironolactona_eplerenona', 'fibrilacion_auricular_anticoagulacion', 'ieca_ara2_sacubitrilo_valsartan']` (similitud top-1: 0.568)
  - Respuesta: No, no es recomendable dejar de tomar el anticoagulante sin hablarlo con el médico.

Fuentes: [diureticos_espironolactona_eplerenona], [fibrilacion_auricular_anticoagulacion], [ieca_ara2_sacubitrilo_valsartan]
- **Pregunta 4** — _falso_no_se_
  - Pregunta: ¿Cuánto tiempo hay que tomar la doble antiagregación después de poner un stent?
  - Guía esperada: `stent_doble_antiagregacion`
  - Fuentes recuperadas: `['stent_doble_antiagregacion']` (similitud top-1: 0.797)
  - Respuesta: No tengo información sobre eso en las guías disponibles.
- **Pregunta 5** — _acierto_
  - Pregunta: Me han recetado bisoprolol, ¿qué efectos secundarios puede dar?
  - Guía esperada: `betabloqueantes_bisoprolol_carvedilol`
  - Fuentes recuperadas: `['betabloqueantes_bisoprolol_carvedilol']` (similitud top-1: 0.671)
  - Respuesta: Según la información disponible, los efectos secundarios más comunes de los betabloqueantes bisoprolol y carvedilol incluyen:

* Pulso lento
* Mareo al levantarse
* Manos y pies fríos

Es importante informar al médico si se experimentan síntomas como un pulso bajo de 50 latidos por minuto, desmayos o falta de aire nueva.

Fuentes: [betabloqueantes_bisoprolol_carvedilol]
- **Pregunta 6** — _acierto_
  - Pregunta: ¿Puedo tomar ramipril y sacubitrilo/valsartán a la vez?
  - Guía esperada: `ieca_ara2_sacubitrilo_valsartan`
  - Fuentes recuperadas: `['ieca_ara2_sacubitrilo_valsartan', 'diureticos_espironolactona_eplerenona', 'betabloqueantes_bisoprolol_carvedilol']` (similitud top-1: 0.496)
  - Respuesta: No, no se recomienda tomar ramipril y sacubitrilo/valsartán a la vez. Debe haber un periodo de espera antes de cambiar de uno a otro.

Fuentes: [ieca_ara2_sacubitrilo_valsartan], [diureticos_espironolactona_eplerenona], [betabloqueantes_bisoprolol_carvedilol]
- **Pregunta 7** — _acierto_
  - Pregunta: Tengo insuficiencia cardiaca, ¿qué debo vigilar cada día en casa?
  - Guía esperada: `insuficiencia_cardiaca_seguimiento`
  - Fuentes recuperadas: `['insuficiencia_cardiaca_seguimiento']` (similitud top-1: 0.828)
  - Respuesta: Para vigilar cada día en casa, debes monitorear tus síntomas y seguir las instrucciones de tu equipo médico. En particular, debes:

- Verificar tu peso cada mañana en ayunas y anotarlo.
- Limitar la cantidad de sal que consumes.
- Seguir la pauta de líquidos que te haya indicado tu equipo médico.
- Tomar tus medicamentos todos los días, incluso si te sientes bien.
- Realizar ejercicio suave y adaptado a tus necesidades.

Es importante que estés atento a los síntomas habituales de la insuficiencia cardiaca, como falta de aire al hacer esfuerzo o al tumbarse, cansancio, hinchazón de tobillos y piernas, y aumento rápido de peso por retención de líquidos. Si experimentas alguno de estos síntomas, es importante que acudas a las urgencias.

Fuentes: [insuficiencia_cardiaca_seguimiento]
- **Pregunta 8** — _acierto_recuperacion_pero_respuesta_incompleta_
  - Pregunta: Me duele el pecho, ¿cuándo debo ir a urgencias?
  - Guía esperada: `dolor_toracico_cuando_consultar`
  - Fuentes recuperadas: `['dolor_toracico_cuando_consultar']` (similitud top-1: 0.782)
  - Respuesta: Si el dolor en el pecho es opresivo intenso que dura más de unos minutos y se extiende al brazo, mandíbula o espalda, acompañado de sudor frío, náuseas o falta de aire, debes ir a urgencias.

Fuentes: [dolor_toracico_cuando_consultar]
- **Pregunta 9** — _acierto_
  - Pregunta: Tengo una prótesis valvular biológica, ¿necesito anticoagulación para siempre?
  - Guía esperada: `valvulopatia_protesis_biologica`
  - Fuentes recuperadas: `['valvulopatia_protesis_biologica', 'fibrilacion_auricular_anticoagulacion']` (similitud top-1: 0.651)
  - Respuesta: No, las prótesis biológicas suelen requerir anticoagulación solo durante los primeros meses tras la operación.

Fuentes: [valvulopatia_protesis_biologica], [fibrilacion_auricular_anticoagulacion]
- **Pregunta 10** — _acierto_
  - Pregunta: Soy alérgico al contraste yodado y tomo metformina, ¿qué debo tener en cuenta antes de una prueba con contraste?
  - Guía esperada: `contrastes_yodados_metformina`
  - Fuentes recuperadas: `['contrastes_yodados_metformina']` (similitud top-1: 0.825)
  - Respuesta: Antes de una prueba con contraste, debes comunicar que eres alérgico al contraste yodado. También es importante que sepas que, si eres diabético y tomas metformina, es posible que debas suspenderla temporalmente antes o después de la prueba, según la decisión del equipo médico.

Fuentes: [contrastes_yodados_metformina]
- **Pregunta 11** — _abstencion_correcta_
  - Pregunta: ¿Qué dieta debo seguir para bajar el colesterol?
  - Guía esperada: `None`
  - Fuentes recuperadas: `['insuficiencia_cardiaca_seguimiento', 'ieca_ara2_sacubitrilo_valsartan']` (similitud top-1: 0.445)
  - Respuesta: No tengo información sobre dieta específica para bajar el colesterol en el contexto de la insuficiencia cardiaca y la hipertensión.
- **Pregunta 12** — _alucinacion_
  - Pregunta: ¿Puedo hacer ejercicio intenso si llevo un marcapasos?
  - Guía esperada: `None`
  - Fuentes recuperadas: `['insuficiencia_cardiaca_seguimiento', 'betabloqueantes_bisoprolol_carvedilol']` (similitud top-1: 0.434)
  - Respuesta: No, no se recomienda realizar ejercicio intenso si tienes un marcapasos. Los betabloqueantes, como el bisoprolol y el carvedilol, pueden afectar la frecuencia cardíaca y reducir la capacidad del corazón para bombear sangre. Realizar ejercicio intenso puede aumentar el riesgo de complicaciones, como desmayos o problemas cardíacos graves. Es importante consultar con tu médico antes de iniciar cualquier programa de ejercicio.

Fuentes: [insuficiencia_cardiaca_seguimiento], [betabloqueantes_bisoprolol_carvedilol]
- **Pregunta 13** — _abstencion_correcta_
  - Pregunta: ¿Qué vacunas necesito antes de viajar a Asia?
  - Guía esperada: `None`
  - Fuentes recuperadas: `['contrastes_yodados_metformina']` (similitud top-1: 0.33)
  - Respuesta: No tengo información sobre eso en las guías disponibles.
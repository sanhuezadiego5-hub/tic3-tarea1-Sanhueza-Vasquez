# Informe corto de la Tarea 1 de TIC3

El informe tiene seis páginas, incluida la portada. Comprende arquitectura,
funcionamiento de la GUI y del servidor, cambio y confirmación de parámetros,
WiFi por prioridades, decisiones de diseño, resultados de adquisición, efecto
de tasa y rango del BMI270 y comparación TCP/UDP con las capturas reales del AP.

- `Informe_Tarea1_TIC3.docx`: versión editable, incluida toda la portada.
- `Informe_Tarea1_TIC3.pdf`: versión para entrega. Después de editar Word,
  volver a exportar y comprobar que conserva el máximo de seis páginas.
- `Anexo_Capturas_Wireshark_TIC3.docx` y `.pdf`: documento independiente de
  17 páginas con los 15 pantallazos originales de Wireshark, descripción e
  interpretación de cada imagen y comparación final de T01 a T05.
- `inventario_capturas_wireshark.json`: rutas y descripciones de las 15 imágenes.
- `analisis_resultados.json`: resultados calculados por sesión y captura.
- `analizar_resultados.py`: cálculo reproducible con Python estándar y el
  codec del proyecto; no altera las capturas ni las sesiones originales.

Portada basada en la referencia proporcionada por el usuario. Integrantes:
Diego Sanhueza Chávez y Vicente Vásquez Garrido. Profesor: Luciano Radriagán.
Asignatura: Taller de Integración TIC (TIC3), sin sección. Fecha: 21-10-2026.

## Recalcular la evidencia

Desde la raíz de este repositorio:

```bash
python3 informe/analizar_resultados.py --output /tmp/analisis_tic3.json
```

La comparación principal utiliza T01/TCP y T02/UDP en paralelo y binario a
400/400 Hz. Se filtra el canal 5001 por el transporte correspondiente; los
bytes de tramas no son bytes de radio WiFi. El intervalo entre primer y último
DATA no se interpreta como latencia absoluta. T04 contiene un bloque de giro
incompleto; el informe no atribuye su causa a una capa sin evidencia.

Las sesiones históricas varían varios parámetros simultáneamente. El informe
explica su efecto sobre escalas y conteos sin presentarlas como una calibración
ni como un experimento controlado para aislar ruido o exactitud.

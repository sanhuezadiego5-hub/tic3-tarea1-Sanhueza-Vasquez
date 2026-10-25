# Capturas y comparación TCP frente a UDP

Las cinco capturas del AP de la Raspberry, realizadas el 21 de octubre de 2026,
están en [ap/](ap/). Los 15 pantallazos originales están en [capturas/](capturas/);
sus rutas relativas coinciden con el inventario de [imágenes y descripciones](../informe/inventario_capturas_wireshark.json).

| Prueba | Transporte | Formato | Adquisición | Archivo PCAP |
|---|---|---|---|---|
| T01 | TCP | Binario | Paralela | [T01](ap/T01_tcp_binario_paralelo.pcap) |
| T02 | UDP | Binario | Paralela | [T02](ap/T02_udp_binario_paralelo.pcap) |
| T03 | TCP | Binario | Secuencial | [T03](ap/T03_tcp_binario_secuencial.pcap.pcap) |
| T04 | UDP | Binario | Secuencial | [T04](ap/T04_udp_binario_secuencial.pcap) |
| T05 | TCP | JSON | Paralela | [T05](ap/T05_tcp_json_paralelo.pcap) |

Condiciones comunes: 400/400 Hz, ±8 g/±2000 °/s, ventana de 1000 ms y objetivo
de 12000 XYZ por sensor. La comparación principal es T01 frente a T02.

El [informe corto](../informe/Informe_Tarea1_TIC3.pdf) describe resultados y límites.
El [anexo de Wireshark](../informe/Anexo_Capturas_Wireshark_TIC3.pdf) conserva los
15 pantallazos completos con descripción e interpretación, incluidos los de
la red común y la vista Follow TCP Stream de T05. Ambos tienen versión DOCX editable.
T03 y T04 tienen PCAP, pero no pantallazos de Wireshark en la colección original.

## Lectura de las evidencias

- `tcp.port == 5001`: conexión y datos TCP; distinguir ACK sin payload y mensajes TIC3.
- `udp.port == 5001`: datagramas de muestras UDP, sin handshake ni ACK de datos.
- `tcp.port == 5000`: órdenes, estado y previsualización en ambos modos.
- `tcp.port == 5000 && tcp.len > 0`: mensajes de control con contenido.

La etiqueta RSL Malformed Packet corresponde al disector aplicado a un protocolo
propio; no demuestra corrupción del sensor. Revisar IPA/ip.access/RSL en
Analyze → Enabled Protocols o Decode As. Un ACK TCP reconoce bytes; el ACK TIC3
confirma guardado. Un paquete o datagrama no equivale necesariamente a un arreglo.

## Reproducir las cifras

Desde la raíz del repositorio:

```bash
python3 informe/analizar_resultados.py --output /tmp/analisis_tic3.json
```

Se cuentan tramas por transporte y puerto 5001, no bytes de radio. En T04 se
reconstruyen 12000/11601 XYZ y queda un bloque de giro incompleto; la captura no
localiza la causa en una capa concreta. El intervalo entre primer y último DATA
no mide latencia absoluta. Los PCAP y los pantallazos se conservan sin cambios.

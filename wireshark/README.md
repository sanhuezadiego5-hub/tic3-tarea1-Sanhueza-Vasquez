# Evidencias de red y comparación TCP frente a UDP

Las cinco capturas del AP de la Raspberry, realizadas el 21 de octubre de 2026,
están en [ap/](ap/). Los 15 pantallazos originales están en [capturas/](capturas/).

| Prueba | Transporte | Formato | Adquisición | Archivo PCAP |
|---|---|---|---|---|
| T01 | TCP | Binario | Paralela | [T01](ap/T01_tcp_binario_paralelo.pcap) |
| T02 | UDP | Binario | Paralela | [T02](ap/T02_udp_binario_paralelo.pcap) |
| T03 | TCP | Binario | Secuencial | [T03](ap/T03_tcp_binario_secuencial.pcap.pcap) |
| T04 | UDP | Binario | Secuencial | [T04](ap/T04_udp_binario_secuencial.pcap) |
| T05 | TCP | JSON | Paralela | [T05](ap/T05_tcp_json_paralelo.pcap) |

Condiciones comunes: 400/400 Hz, ±8 g/±2000 °/s, ventana de 1000 ms y objetivo
de 12000 XYZ por sensor. La comparación principal es T01 frente a T02.

El [informe corto](../informe/Informe_Tarea1_TIC3.pdf) describe los resultados y
sus límites. T03 y T04 tienen PCAP; la colección de pantallazos corresponde a
las capturas generales, T01, T02 y una vista de flujo de T05.

## Breves descripciones de los pantallazos

Cada enlace conserva la imagen original. Los nombres mantienen la hora de captura.

| Pantallazo | Qué se observa |
|---|---|
| [Red común 15:40:04](capturas/Screenshot%20From%202026-10-21%2015-40-04.png) | TCP 5001: paquete 557 con Data de 1440 bytes, [PSH, ACK] y firma TIC3. |
| [Red común 15:40:43](capturas/Screenshot%20From%202026-10-21%2015-40-43.png) | ACK 556 de la Raspberry con Len=0: reconoce bytes sin añadir datos de aplicación. |
| [Red común 15:41:43](capturas/Screenshot%20From%202026-10-21%2015-41-43.png) | Control 5000 interpretado como IPA/RSL; Malformed Packet no acredita corrupción TIC3. |
| [Red común 15:41:50](capturas/Screenshot%20From%202026-10-21%2015-41-50.png) | ACK 574 de control, Len=0; distinto de las filas con mensajes de aplicación. |
| [AP 16:58:40](capturas/Screenshot%20From%202026-10-21%2016-58-40.png) | Cierre de conexión anterior, handshake nuevo y paquete 160 con Data TCP en la red 192.168.50.x. |
| [T05 Follow Stream](capturas/Screenshot%20From%202026-10-21%2017-35-12.png) | Vista servidor → ESP: respuestas TIC3 binarias aunque DATA sea JSON. Elegir ESP → servidor para inspeccionar las muestras JSON. |
| [T01 handshake](capturas/T01/Screenshot%20From%202026-10-21%2017-09-11.png) | SYN 151, SYN/ACK 152 y ACK 153 establecen TCP antes de las muestras. |
| [T01 Data](capturas/T01/Screenshot%20From%202026-10-21%2017-11-38.png) | Paquete 160 con Seq=105 y Len=1440; el 161 responde Ack=1545. Seq/Ack cuentan bytes. |
| [T01 control](capturas/T01/Screenshot%20From%202026-10-21%2017-25-41.png) | ACK 1586 hacia 5000, sin payload; el control usa una conexión distinta a los datos 5001. |
| [T01 ACK](capturas/T01/Screenshot%20From%202026-10-21%2017-26-31.png) | ACK 1374 de Raspberry:5001, Len=0. Window=65535 es recepción TCP, no interval_ms del sensor. |
| [T01 Conversations](capturas/T01/Screenshot%20From%202026-10-21%2017-45-11.png) | Dos conversaciones TCP: 2 + 732 = 734 paquetes; incluyen conexión, DATA y ACK. |
| [T02 UDP Data](capturas/T02/Screenshot%20From%202026-10-21%2017-28-36.png) | Datagrama 862: 1188 bytes TIC3, longitud UDP 1196 y trama 1230; no hay handshake ni Seq/Ack TCP. |
| [T02 control con datos](capturas/T02/Screenshot%20From%202026-10-21%2017-30-05.png) | TCP 5000 con Len=96: mensaje HELLO TIC3. El canal de control sigue siendo TCP en modo UDP. |
| [T02 Conversations](capturas/T02/Screenshot%20From%202026-10-21%2017-46-06.png) | 356 datagramas hacia 5001, sin ACK de datos UDP en sentido inverso. |
| [T02 control general](capturas/T02/Screenshot%20From%202026-10-21%2017-49-22.png) | Estado/órdenes bidireccionales en TCP 5000; la etiqueta RSL pertenece al disector usado. |

## Lectura de las evidencias

- `tcp.port == 5001`: conexión y datos TCP; distinguir ACK sin payload y mensajes TIC3.
- `udp.port == 5001`: datagramas de muestras UDP, sin handshake ni ACK de datos.
- `tcp.port == 5000`: órdenes, estado y previsualización en ambos modos.
- `tcp.port == 5000 && tcp.len > 0`: mensajes de control con contenido.

La etiqueta RSL Malformed Packet corresponde al disector aplicado a un protocolo
propio; no demuestra corrupción del sensor. Revisar IPA/ip.access/RSL en
Analyze → Enabled Protocols o Decode As. Un ACK TCP reconoce bytes; el ACK TIC3
confirma guardado. Un paquete o datagrama no equivale necesariamente a un arreglo.

## Resultado de la comparación

T01 y T02 reconstruyeron 12000 XYZ de aceleración y 12000 de giro. En el canal
5001 se contaron 734 tramas TCP (417744 bytes) frente a 356 datagramas UDP
(385128 bytes): UDP registró 7,8 % menos bytes de tramas en esas ejecuciones.
TCP incluye establecimiento y confirmaciones; no se cuentan control 5000, HTTP
ni SSH. Son bytes de tramas capturadas, no de radio WiFi.

TCP entrega un flujo ordenado que debe reensamblarse; sus segmentos no marcan
los límites de los arreglos. UDP conserva datagramas, pero un arreglo puede
necesitar varios fragmentos TIC3. Los 1188 bytes habituales corresponden a 96
de cabecera TIC3 y 78 registros de 14 bytes. PSH no delimita un arreglo y un
ACK TCP reconoce bytes; el ACK TIC3 confirma persistencia del bloque.

T03–T05 son pruebas complementarias descritas en el informe. T04 conserva un
bloque de giro incompleto: se reconstruyen 12000/11601 XYZ. La captura no
localiza la causa en envío, enlace o captura. La ausencia de ACK UDP no prueba
por sí sola pérdida. El intervalo DATA no equivale a latencia muestra a disco.

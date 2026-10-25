# Firmware ESP32-S3 y sensor BMI270

Código de adquisición de aceleración y velocidad angular mediante I2C y FIFO.
Incluye modos secuencial y paralelo, arreglos por sensor, parámetros remotos,
selección WiFi por prioridades y envío TCP/UDP en binario o JSON.

`main/` contiene los módulos C y sus cabeceras. CMake, Kconfig y
`sdkconfig.defaults` definen la compilación y configuración inicial sin claves.
Las instrucciones de instalación, configuración y flasheo están en el
[README del proyecto](../README.md#compilar-y-grabar-la-esp).

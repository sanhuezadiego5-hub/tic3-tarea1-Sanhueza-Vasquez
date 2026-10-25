# Tarea 1 — TIC 3

Adquisición con ESP32-S3 y BMI270, envío por WiFi y almacenamiento y visualización en Raspberry Pi. La GUI funciona en la red local, sin conexión a Internet.

## Entregables

| Ruta | Contenido solicitado |
|---|---|
| [esp/](esp/README.md) | Firmware ESP32-S3, modos secuencial y paralelo; archivos CMake, Kconfig y valores iniciales necesarios para compilar. |
| [raspi/](raspi/README.md) | Código del servidor, GUI, protocolo, almacenamiento y preparación del AP. |
| `scripts/instalar_acceso_gui.sh` | Instalación del acceso gráfico para ejecutar la GUI. |
| [sensores/](sensores/README.md) | Cinco sesiones reales con distintas frecuencias, rangos y cantidades; su README describe los parámetros. |
| `prompts.md` | Registro consolidado de prompts, herramienta/modelo y resultados. |
| [wireshark/](wireshark/README.md) | Cinco PCAP, pantallazos y breve comparación TCP/UDP en su README. |
| [informe/](informe/README.md) | Informe corto de seis páginas en PDF y versión Word con portada editable. |

## Instalación y operación gráfica

En Raspberry Pi OS con escritorio y Python 3, instalar una vez el componente Tkinter y registrar el acceso:

```bash
sudo apt update
sudo apt install python3-tk
bash scripts/instalar_acceso_gui.sh
```

Después abrir **TIC3 - Captura BMI270** desde el menú de aplicaciones. Pulsar **Iniciar y abrir interfaz**, esperar que aparezca la ESP, configurar los parámetros y pulsar **Iniciar captura**. Para terminar, pulsar **Detener y guardar**, esperar confirmación y cerrar el servidor desde el lanzador. No hace falta editar código ni introducir comandos para las capturas habituales.

El lanzador usa Tkinter y la visualización es web local sin dependencias externas ni Internet. Si ya existe un servidor manual, usar su página o detenerlo antes de iniciar otro. Se escribe `servidor.log` en la carpeta elegida. El cierre bloquea una captura pendiente para evitar cortar el guardado; una desconexión sin confirmar exige resolverla antes de cerrar o revisar el servidor manualmente.

Alternativa por terminal: `python3 raspi/launcher.py`. La instalación, el WiFi y la grabación inicial de firmware siguen siendo preparación técnica. La ESP debe tener los mismos puertos de datos/control que los elegidos en el lanzador.

Para ESP-IDF, seguir la [instalación oficial para Linux](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/get-started/linux-macos-setup.html). El proyecto se compiló con v6.1; el PC necesita ESP-IDF y acceso al puerto USB, la Raspberry no necesita ESP-IDF. Conectar SDA a GPIO42, SCL a GPIO2, alimentación 3,3 V y GND común; sensor en I2C 0x68.


## Ejecutar el servidor y la GUI

Con Python 3 en la Raspberry, desde la raíz del repositorio:

```bash
python3 raspi/imu_server.py --host 0.0.0.0 --port 5001 --control-port 5000 --gui-port 8080 --output sensores
```

Abrir `http://localhost:8080` en la Raspberry o `http://IP_DE_LA_RASPBERRY:8080` en un PC de la misma red. El servidor usa la biblioteca estándar de Python. Iniciar la captura desde la GUI; **Detener y guardar** cierra la sesión y guarda los bloques pendientes. `Ctrl+C` termina el servidor en la terminal. Los archivos nuevos aparecen en `sensores/`. Se versionan cinco sesiones de prueba; las nuevas carpetas de captura se ignoran por defecto para revisarlas antes de publicarlas.

En VS Code se puede abrir la carpeta del repositorio en la Raspberry, o mediante Remote SSH, y ejecutar ese mismo comando en su terminal. El servidor debe estar activo antes de iniciar una captura en la ESP.

## Compilar y grabar la ESP

Instalar/activar ESP-IDF (la versión utilizada fue v6.1) y abrir `esp/` como carpeta de VS Code con la extensión ESP-IDF. Desde una terminal con ESP-IDF activado:

```bash
cd esp
idf.py -B build-tic3 set-target esp32s3
idf.py -B build-tic3 menuconfig
idf.py -B build-tic3 build
idf.py -B build-tic3 -p /dev/ttyACM0 flash monitor
```

Ajustar el puerto a la placa conectada. En **TIC3 - WiFi por prioridad**, habilitar los perfiles deseados y configurar SSID, contraseña, dirección del servidor y puerto 5001. Habilitar WiFi y envío a Raspberry en sus menús. Las credenciales se introducen localmente y quedan en `sdkconfig`, que no se publica. `sdkconfig.defaults` contiene valores iniciales sin contraseñas.

La ESP ejecuta firmware después del flasheo; no se ejecuta `main.c` como un programa del PC. Espera la orden de inicio de la GUI. Salir del monitor con `Ctrl+]` no detiene la placa.

## WiFi compartido o AP de la Raspberry

En una red común, ESP y Raspberry deben comunicarse dentro de esa red; el PC necesita acceso a la Raspberry para abrir la GUI. El cable USB no comparte automáticamente el WiFi del PC con la ESP.

Para preparar el AP en la Raspberry, copiar `raspi/.ap_credentials.example.json` a un archivo privado llamado `.ap_credentials.json`, cambiar su contraseña localmente y protegerlo con `chmod 600 .ap_credentials.json`. Después, desde la raíz del repositorio:

```bash
sudo python3 raspi/setup_ap.py --credentials "$PWD/.ap_credentials.json"
```

Añadir `--activate` desde una terminal local de la Raspberry o con acceso alternativo: activar el AP puede cortar la sesión SSH que utiliza su WiFi anterior. El AP utiliza WPA2/AES, 2,4 GHz, SSID `TIC3-Raccoon`, dirección `192.168.50.1/24` y DHCP. Configurar la misma contraseña en el perfil 1 de la ESP y servidor `192.168.50.1`. Conectar el PC al AP y abrir `http://192.168.50.1:8080`. No necesita Internet. El AP y el servidor no tienen inicio automático configurado por este repositorio.

## Decisiones de adquisición y envío

- Aceleración y velocidad angular tienen arreglos independientes y tasas de 25, 50, 100, 200 o 400 Hz. Una muestra XYZ contiene tres valores; 400 muestras XYZ equivalen a 1200 valores por sensor en una ventana nominal de 1 segundo.
- La GUI permite configurar tasas, rangos, ventana, cantidad objetivo, TCP/UDP, binario/JSON y modo de ejecución mientras la adquisición está detenida. La ESP valida memoria y configuración antes de aceptar cambios.
- Paralelo: adquisición y formación de arreglos en core 1, envío en core 0. Secuencial: adquisición, arreglos y envío bloqueante en core 1; las tareas del sistema siguen funcionando.
- TCP confirma el guardado mediante ACK y permite reintentos y deduplicación. UDP no confirma ni retransmite los datos. Los buffers son finitos y los descartes se contabilizan.
- La GUI muestra valores SI y previsualización; los archivos guardan las muestras completas recibidas. El timestamp del sensor representa la lectura de FIFO, no el instante físico exacto de conversión.

## Organización del código

El [informe corto](informe/Informe_Tarea1_TIC3.pdf) explica arquitectura, decisiones y resultados. La [comparación de Wireshark](wireshark/README.md) relaciona las capturas con el protocolo observado. Los [datos de sensores](sensores/README.md) describen las cinco sesiones incluidas.

- `esp/main/main.c`: punto de entrada.
- `bmi270_sensor.c/.h`: capa de sensor (I2C, imagen Bosch, registros, configuración y lectura de retorno). No depende de WiFi ni sockets.
- `imu_acquisition.c/.h`: ventanas, pools, control de captura y tareas por core.
- `imu_stream.c`: parser FIFO, almacenamiento XYZ y conversión.
- `imu_wifi.c`, `wifi_policy.c`: perfiles y reconexión.
- `imu_transport.c`, `imu_wire.c`: sockets y protocolo.
- `raspi/imu_server.py`, `imu_protocol.py`: recepción y guardado.
- `raspi/imu_control.py`, `imu_settings.py`: órdenes y validación.
- `raspi/imu_gui.py`, `imu_gui.html`, `launcher.py`: interfaz web y lanzador gráfico.

## Archivos generados y privados

Los directorios `build*`, el bootloader generado, CMakeFiles, cachés, `sdkconfig`, contraseñas, claves SSH y capturas de adquisición nuevas fuera de las sesiones seleccionadas no forman parte del repositorio. Las evidencias PCAP y pantallazos seleccionados sí se versionan en `wireshark/`. ESP-IDF vuelve a generar los archivos de compilación a partir de CMake y del código fuente. Se incluyen los archivos necesarios para reproducir el proyecto, no los binarios que contienen la configuración privada de la instalación.

Las direcciones `192.0.2.x`, el usuario `usuario` y las rutas `/ruta/...` son ejemplos para documentación; reemplazarlos por los valores locales. La configuración real del AP está definida en `raspi/setup_ap.py`. No se publican claves ni archivos privados de configuración; las evidencias seleccionadas conservan direcciones IP locales y los documentos pueden citar rutas de la instalación original.

## Almacenamiento de capturas

Los bloques recibidos en modo binario se guardan en `.bin`, conservando las muestras como registros binarios. El modo JSON mantiene archivos `.json`.

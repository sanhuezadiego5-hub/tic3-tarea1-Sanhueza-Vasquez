# Servidor y GUI de la Raspberry Pi

Receptor TCP/UDP de muestras, canal TCP de control y GUI de configuración y
visualización. Valida y reconstruye bloques, gestiona sesiones y guarda las
muestras en binario o JSON. Incluye el lanzador gráfico y la preparación del AP.

- `imu_server.py`: recepción, persistencia y confirmaciones de guardado.
- `imu_protocol.py`, `imu_storage.py`: protocolo TIC3 y archivos de muestras.
- `imu_control.py`, `imu_settings.py`: sesiones y configuración confirmada.
- `imu_gui.py`, `imu_gui.html`: API HTTP e interfaz web.
- `launcher.py`: inicio y parada del servidor desde una ventana Tkinter.
- `setup_ap.py`: preparación de la red WiFi emitida por la Raspberry.

La instalación y ejecución están en el [README del proyecto](../README.md).

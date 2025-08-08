# RMCAB Reports Automation

Este proyecto automatiza la descarga de reportes de calidad del aire desde el portal RMCAB (Red de Monitoreo de Calidad del Aire de Bogotá), usando `Robot Framework` para hacer peticiones HTTP y `Python` para convertir respuestas en archivos Excel.

## 📦 Requisitos

- Python 3.10+
- pip
- Visual Studio Code
- Robot Framework
- Librerías adicionales:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Estructura

- `download_report.robot`: Ejecuta la descarga desde la API de RMCAB.
- `resources/utils.py`: Funciones auxiliares para conversión de fechas y escritura de archivos.
- `appsettings.json`: Configuración de parámetros de consulta.

---

## 🚀 Ejecución rápida

1. Clona el proyecto y entra al directorio:

```bash
cd rmcab-reports
```

2. Crea y activa un entorno virtual:

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows
```

3. Instala dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecuta todo el flujo (descarga + conversión):

```bash
robot download_report.robot
python .\convertir_excel.py  downloads --code-map config/code_title_map.json
```

---

## 🛠 Configuración

Edita `appsettings.json` para personalizar parámetros de estación, fechas y salida.

---

## 📁 Salida

Los archivos `.xlsx` y `.json` se almacenan en `downloads/`. Aquellos con datos válidos serán convertidos automáticamente a Excel.

---

## 📃 Licencia

Uso académico y libre distribución bajo atribución.

import pandas as pd
import os
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Diccionario unificado: código → {nombre legible, unidad}
CODIGO_A_INFO = {
    "S_27_18": {"nombre": "CO", "unidad": "ppm"},
    "S_27_7": {"nombre": "Dir Viento", "unidad": "Grados"},
    "S_27_5": {"nombre": "HR", "unidad": "%"},
    "S_27_14": {"nombre": "NO", "unidad": "ppb"},
    "S_27_15": {"nombre": "NO2", "unidad": "ppb"},
    "S_27_16": {"nombre": "NOX", "unidad": "ppb"},
    "S_27_19": {"nombre": "OZONO", "unidad": "ppb"},
    "S_27_1": {"nombre": "PM10", "unidad": "µg/m3"},
    "S_27_13": {"nombre": "PM2.5", "unidad": "µg/m3"},
    "S_27_8": {"nombre": "Precipitacion", "unidad": "mm"},
    "S_27_4": {"nombre": "Presion Baro", "unidad": "mmHg"},
    "S_27_10": {"nombre": "Rad Solar", "unidad": "W/M²"},
    "S_27_2": {"nombre": "Temperatura", "unidad": "°C"},
    "S_27_6": {"nombre": "Vel Viento", "unidad": "m/s"}
}

# Orden deseado
ORDEN_COLUMNAS = [
    "datetime", "PM10", "Temperatura", "Presion Baro", "HR",
    "Vel Viento", "Dir Viento", "Precipitacion", "Rad Solar",
    "PM2.5", "NO", "NO2", "NOX", "CO", "OZONO"
]

def convertir_json_data_a_csv(ruta_archivo_json):
    try:
        with open(ruta_archivo_json, 'r', encoding='utf-8') as f:
            contenido = json.load(f)

        if "Data" not in contenido:
            raise ValueError("El archivo no contiene la clave 'Data'.")

        datos = contenido["Data"]
        df = pd.DataFrame(datos).replace("----", pd.NA)

        # Mapeo para renombrar columnas con unidad incluida
        nuevo_nombre_columna = {}
        for col in df.columns:
            if col in CODIGO_A_INFO:
                info = CODIGO_A_INFO[col]
                nuevo_nombre_columna[col] = f"{info['nombre']} [{info['unidad']}]"
            else:
                nuevo_nombre_columna[col] = col  # datetime u otros

        df = df.rename(columns=nuevo_nombre_columna)

        # Reordenar columnas con etiquetas nuevas
        columnas_finales = ["datetime"] + [
            nuevo_nombre_columna[codigo]
            for codigo in CODIGO_A_INFO
            if nuevo_nombre_columna.get(codigo) in df.columns and CODIGO_A_INFO[codigo]["nombre"] in ORDEN_COLUMNAS
        ]
        columnas_finales = [col for col in columnas_finales if col in df.columns]
        df = df[columnas_finales]

        # Guardar CSV con encabezado final
        ruta_csv = ruta_archivo_json.replace(".json", ".csv")
        df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
        logging.info(f"✅ CSV generado con columnas nombradas: {ruta_csv} ({len(df)} filas, {len(df.columns)} columnas)")

    except Exception as e:
        logging.error(f"❌ Error procesando {ruta_archivo_json}: {e}")

def procesar_directorio_json(directorio):
    if not os.path.isdir(directorio):
        logging.error(f"El directorio especificado no existe: {directorio}")
        return

    archivos = [f for f in os.listdir(directorio) if f.endswith('.json')]

    if not archivos:
        logging.warning("No se encontraron archivos .json en el directorio.")
        return

    for archivo in archivos:
        ruta_completa = os.path.join(directorio, archivo)
        convertir_json_data_a_csv(ruta_completa)

if __name__ == "__main__":
    directorio_objetivo = "downloads"
    procesar_directorio_json(directorio_objetivo)

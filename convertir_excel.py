import pandas as pd
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def convertir_y_sobrescribir_excel(ruta_archivo):
    try:
        df = pd.read_excel(ruta_archivo)

        # Aquí puedes aplicar transformaciones si es necesario
        # Ejemplo: eliminar filas completamente vacías
        # df = df.dropna(how='all')

        df.to_excel(ruta_archivo, index=False)
        logging.info(f"Archivo procesado: {ruta_archivo} ({len(df)} filas, {len(df.columns)} columnas)")
    except Exception as e:
        logging.error(f"Error procesando {ruta_archivo}: {e}")

def procesar_archivos_excel(directorio):
    if not os.path.isdir(directorio):
        logging.error(f"El directorio especificado no existe: {directorio}")
        return

    archivos = [f for f in os.listdir(directorio) if f.endswith('.xlsx')]

    if not archivos:
        logging.warning("No se encontraron archivos .xlsx en el directorio especificado.")
        return

    for archivo in archivos:
        ruta_completa = os.path.join(directorio, archivo)
        convertir_y_sobrescribir_excel(ruta_completa)

if __name__ == "__main__":
    directorio_objetivo = "downloads"  # Cambia esto al directorio que desees procesar
    procesar_archivos_excel(directorio_objetivo)

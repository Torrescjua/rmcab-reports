from datetime import datetime, timezone

def convert_date_to_ticks(date_str):
    """
    Convierte una fecha (YYYY-MM-DD) a ticks de .NET (100ns desde 0001-01-01)
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    epoch = datetime(1, 1, 1, tzinfo=timezone.utc)
    delta = dt.replace(tzinfo=timezone.utc) - epoch
    ticks = int(delta.total_seconds() * 10**7)
    return ticks

def convert_date_to_ticks_keyword(date_str):
    """
    Función expuesta como palabra clave en Robot Framework.
    Devuelve los ticks como string para usarlos en URLs.
    """
    return str(convert_date_to_ticks(date_str))

def save_response_body_to_file(response, filename):
    """
    Guarda el contenido de una respuesta (objeto de requests) en un archivo binario.
    """
    with open(filename, 'wb') as f:
        f.write(response.content)

def Save_Response_Body_To_File_Keyword(response, filename):
    return save_response_body_to_file(response, filename)

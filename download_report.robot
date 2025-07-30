*** Settings ***
Library           RequestsLibrary
Library           OperatingSystem
Library           Collections
Library           JSONLibrary
Library           resources/utils.py

*** Variables ***
${CONFIG_FILE}    appsettings.json
${MONITOR_FILE}   resources/station_monitors.json

*** Test Cases ***
Descargar Reporte Excel Desde RMCAB
    [Documentation]    Descarga un archivo Excel del RMCAB usando parámetros de appsettings.json y los monitores válidos por estación.

    ${config}=              Load JSON From File    ${CONFIG_FILE}

    ${base_url}=            Get From Dictionary    ${config}    BaseUrl
    ${path}=                Get From Dictionary    ${config}    ReportPath
    ${station_id}=          Get From Dictionary    ${config}    StationId
    ${station_name}=        Get From Dictionary    ${config}    StationName
    ${tb}=                  Get From Dictionary    ${config}    TB
    ${totb}=                Get From Dictionary    ${config}    ToTB
    ${rtype}=               Get From Dictionary    ${config}    ReportType
    ${first}=               Get From Dictionary    ${config}    First
    ${outdir}=              Get From Dictionary    ${config}    OutputDirectory

    # Cargar monitores válidos desde archivo externo
    ${station_monitors}=    Load JSON From File    ${MONITOR_FILE}
    ${monitor_ids}=         Get From Dictionary    ${station_monitors}    ${station_name}

    Run Keyword Unless    ${monitor_ids}    Fail    No hay monitores disponibles para la estación: ${station_name}

    # Fechas configurables
    ${from_date}=      Set Variable    2024-01-01
    ${to_date}=        Set Variable    2024-01-02

    ${from_ticks}=     Convert Date To Ticks Keyword    ${from_date}
    ${to_ticks}=       Convert Date To Ticks Keyword    ${to_date}

    # Convertir listas a JSON
    ${monitor_ids_json}=    Evaluate    json.dumps(${monitor_ids})    json
    ${station_name_json}=   Evaluate    json.dumps(["${station_name}"])    json
    ${tb_json}=             Evaluate    json.dumps(${tb})    json

    Create Directory        ${outdir}
    Create Session          rm    ${base_url}

    ${params}=    Create Dictionary
    ...    ListStationId=[${station_id}]
    ...    ListMonitorIds=${monitor_ids_json}
    ...    FDate=${from_ticks}
    ...    TDate=${to_ticks}
    ...    TB=${tb_json}
    ...    ToTB=${totb}
    ...    ReportType=${rtype}
    ...    first=${first}
    ...    ListStationsNames=${station_name_json}
    ...    take=0
    ...    skip=0
    ...    page=1
    ...    pageSize=0

    ${response}=    GET On Session    rm    ${path}    params=${params}
    Should Be Equal As Integers    ${response.status_code}    200

    ${content_type}=    Get From Dictionary    ${response.headers}    Content-Type
    ${filename}=        Set Variable    ${outdir}/reporte_${station_name}_${from_date}.json

    Run Keyword If    '${content_type}' == 'application/json'
    ...    Log To Console    No se encontraron datos para esta consulta. No se generará archivo.
    ...    ELSE
    ...    Save Response Body To File Keyword    ${response}    ${filename}

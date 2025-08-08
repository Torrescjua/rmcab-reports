import pandas as pd
import os, json, re, logging, argparse
from typing import Dict, Any, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HORA_RE = re.compile(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}")
CODE_RE = re.compile(r"^S_(\d+)_(\d+)$")  # S_<station>_<varId>

# Mapa genérico por varId (opcional como fallback)
VAR_MAP_DEFAULT: Dict[str, Dict[str, str]] = {
    "1":  {"label": "PM10",          "unit": "µg/m3"},
    "2":  {"label": "Temperatura",   "unit": "°C"},
    "4":  {"label": "Presion Baro",  "unit": "mmHg"},
    "5":  {"label": "HR",            "unit": "%"},
    "6":  {"label": "Vel Viento",    "unit": "m/s"},
    "7":  {"label": "Dir Viento",    "unit": "Grados"},
    "8":  {"label": "Precipitacion", "unit": "mm"},
    "10": {"label": "Rad Solar",     "unit": "W/m²"},
    "13": {"label": "PM2.5",         "unit": "µg/m3"},
    "14": {"label": "NO",            "unit": "ppb"},
    "15": {"label": "NO2",           "unit": "ppb"},
    "16": {"label": "NOX",           "unit": "ppb"},
    "18": {"label": "CO",            "unit": "ppm"},
    "19": {"label": "OZONO",         "unit": "ppb"}
}

def load_code_title_map(path: str) -> Tuple[Dict[str, Dict[str, str]], Dict[str, str]]:
    """
    Devuelve:
      - code_map: { "S_27_1": {"label": "...", "unit": "..."}, ... }
      - station_names: { "27": "Bolivia", "8": "Guaymaral", ... }
    """
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"No existe el archivo de mapeo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    stations = cfg.get("stations") or {}
    code_map: Dict[str, Dict[str, str]] = {}
    station_names: Dict[str, str] = {}
    for sid, entry in stations.items():
        station_names[str(sid)] = entry.get("name", str(sid))
        for code, meta in (entry.get("codes") or {}).items():
            # normaliza claves
            code_map[str(code)] = {"label": meta.get("label", str(code)),
                                   "unit": meta.get("unit", "")}
    return code_map, station_names

def build_column_name(code: str, code_map: Dict[str, Dict[str, str]],
                      station_names: Dict[str, str],
                      include_unit: bool, col_prefix: str) -> str:
    """
    col_prefix: "none" | "id" | "name"
    """
    m = CODE_RE.match(code)
    st_id = m.group(1) if m else ""
    mapping = code_map.get(code)
    if mapping:
        label = mapping["label"]
        unit = mapping.get("unit") or ""
    else:
        # sin mapeo: dejar código como label
        label, unit = code, ""

    if include_unit and unit:
        label_unit = f"{label} [{unit}]"
    else:
        label_unit = label

    if col_prefix == "id" and st_id:
        return f"{st_id} - {label_unit}"
    if col_prefix == "name" and st_id:
        st_name = station_names.get(st_id, st_id)
        return f"{st_name} - {label_unit}"
    return label_unit

def rename_columns_by_code(df: pd.DataFrame,
                           code_map: Dict[str, Dict[str, str]],
                           station_names: Dict[str, str],
                           include_unit: bool,
                           col_prefix: str,
                           fallback_varid: bool) -> pd.DataFrame:
    used = set()
    mapping = {}
    for col in df.columns:
        if col == "datetime":
            mapping[col] = col
            continue

        new_name = None
        if col in code_map:
            new_name = build_column_name(col, code_map, station_names, include_unit, col_prefix)
        else:
            # ¿Intentar fallback por varId?
            if fallback_varid:
                m = CODE_RE.match(col)
                if m:
                    var_id = m.group(2)
                    info = VAR_MAP_DEFAULT.get(var_id)
                    if info:
                        base = info["label"]
                        if include_unit and info.get("unit"):
                            base = f"{base} [{info['unit']}]"
                        # prefijo de estación si se pidió
                        st_id = m.group(1)
                        if col_prefix == "id" and st_id:
                            new_name = f"{st_id} - {base}"
                        elif col_prefix == "name" and st_id:
                            new_name = f"{station_names.get(st_id, st_id)} - {base}"
                        else:
                            new_name = base

        if not new_name:
            # deja el original si no hay mapeo
            new_name = col

        # garantizar unicidad
        final = new_name
        i = 2
        while final in used:
            final = f"{new_name}_{i}"
            i += 1
        used.add(final)
        mapping[col] = final

    return df.rename(columns=mapping)

def json_to_csv(input_json: str, out_dir: str | None,
                code_map: Dict[str, Dict[str, str]],
                station_names: Dict[str, str],
                rows_limit: int | None, include_all_rows: bool,
                include_unit: bool, col_prefix: str,
                fallback_varid: bool, delimiter: str):
    with open(input_json, "r", encoding="utf-8") as f:
        payload: Dict[str, Any] = json.load(f)

    data = payload.get("Data") or payload.get("data")
    if not isinstance(data, list):
        raise ValueError("JSON no tiene 'Data' como lista.")

    rows = [r for r in data if isinstance(r, dict)] if include_all_rows \
           else [r for r in data if isinstance(r, dict) and HORA_RE.fullmatch(str(r.get("datetime","")))]

    if rows_limit is not None:
        rows = rows[:rows_limit]

    if not rows:
        logging.warning(f"Sin filas válidas en {input_json}")
        return

    df = pd.DataFrame(rows).replace({"----": pd.NA, "-": pd.NA})

    # Renombrar por código completo usando el JSON
    df = rename_columns_by_code(df, code_map, station_names,
                                include_unit=include_unit,
                                col_prefix=col_prefix,
                                fallback_varid=fallback_varid)

    # No imponemos un orden global: dejamos 'datetime' primero y el resto como vienen
    cols = list(df.columns)
    if "datetime" in cols:
        cols = ["datetime"] + [c for c in cols if c != "datetime"]
        df = df[cols]

    out_dir = out_dir or os.path.dirname(input_json)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(input_json))[0]
    out_path = os.path.join(out_dir, f"{base}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig", sep=delimiter)
    logging.info(f"✅ CSV: {out_path} ({len(df)} filas, {len(df.columns)} cols)")

def parse_args():
    ap = argparse.ArgumentParser(description="RMCAB JSON (Data) → CSV usando mapeo por código completo S_<station>_<varId>")
    ap.add_argument("input", help="Archivo JSON o carpeta con .json")
    ap.add_argument("-o", "--out-dir", default=None, help="Directorio de salida (por defecto, el mismo del input)")
    ap.add_argument("--code-map", default="config/code_title_map.json",
                    help="Ruta a code_title_map.json (estación→codes)")
    ap.add_argument("--rows", type=int, default=None, help="Limitar a las primeras N filas")
    ap.add_argument("--all-rows", action="store_true", help="No filtrar por fecha/hora (incluye Summary, etc.)")
    ap.add_argument("--labels-only", action="store_true", help="No incluir unidades en el encabezado")
    ap.add_argument("--col-prefix", choices=["none","id","name"], default="none",
                    help="Prefijar columnas con id o nombre de estación para evitar duplicados")
    ap.add_argument("--fallback-varid", action="store_true",
                    help="Si el código no está en el JSON, intentar mapear por varId con un mapa genérico")
    ap.add_argument("--delimiter", default=",", help="Delimitador CSV (por defecto ',')")
    return ap.parse_args()

def main():
    args = parse_args()
    code_map, station_names = load_code_title_map(args.code_map)

    # Procesar archivo o carpeta
    if os.path.isdir(args.input):
        files = [os.path.join(args.input, f) for f in os.listdir(args.input) if f.lower().endswith(".json")]
        if not files:
            logging.warning("No hay .json en la carpeta.")
            return
        for fp in files:
            try:
                json_to_csv(fp, args.out_dir, code_map, station_names,
                            rows_limit=args.rows, include_all_rows=args.all_rows,
                            include_unit=not args.labels_only, col_prefix=args.col_prefix,
                            fallback_varid=args.fallback_varid, delimiter=args.delimiter)
            except Exception as e:
                logging.error(f"Error en {fp}: {e}")
    else:
        json_to_csv(args.input, args.out_dir, code_map, station_names,
                    rows_limit=args.rows, include_all_rows=args.all_rows,
                    include_unit=not args.labels_only, col_prefix=args.col_prefix,
                    fallback_varid=args.fallback_varid, delimiter=args.delimiter)

if __name__ == "__main__":
    main()

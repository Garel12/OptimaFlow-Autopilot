"""
connector_master.py -- OPTIMAFLOW V1 | Capa 3: Ejecucion (White Label Edition)
Proposito   : Conectar a Google Sheets, extraer las hojas configuradas en config.json,
              limpiar datos y devolver un JSON estructurado.
              Completamente generico: sin nombres de cliente hardcodeados.
Autor       : Antigravity (Agente AI)
Sesion Log  : /antigravity_core/top/session_001.log
Config      : /antigravity_core/config.json
DIRECTIVA   : #004 — Universalizacion y Empaquetado
"""

import io
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para compatibilidad con Windows CP1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Rutas base ───────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent          # /antigravity_core
LOG_DIR    = BASE_DIR / "top"
LOG_FILE   = LOG_DIR  / "session_001.log"
CREDS_FILE = BASE_DIR.parent / "credentials.json"
CONFIG_FILE = BASE_DIR / "config.json"

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("connector_master")


# ── Carga de configuración ────────────────────────────────────────────────────
def load_config() -> dict:
    """Carga y valida config.json. Lanza un error descriptivo si falta algo."""
    if not CONFIG_FILE.exists():
        log.error(
            "❌ No se encontró config.json en: %s\n"
            "   Crea ese archivo con las claves: sheets, columns, sandbox.",
            CONFIG_FILE,
        )
        sys.exit(1)

    with CONFIG_FILE.open(encoding="utf-8") as f:
        cfg = json.load(f)

    # Validación mínima
    required = ["sheets", "columns", "sandbox"]
    for key in required:
        if key not in cfg:
            log.error("❌ config.json le falta la clave requerida: '%s'", key)
            sys.exit(1)

    log.info("✔ config.json cargado — cliente: %s", cfg.get("cliente", "Desconocido"))
    return cfg


# ── Modo SANDBOX ──────────────────────────────────────────────────────────────
def is_sandbox(cfg: dict) -> bool:
    """
    El modo sandbox se activa si:
      1. La variable de entorno SANDBOX_MODE=true  (prioridad más alta), O
      2. sandbox.enabled = true en config.json
    """
    env_val = os.environ.get("SANDBOX_MODE", "").lower()
    if env_val in ("true", "false"):
        return env_val == "true"
    return cfg.get("sandbox", {}).get("enabled", True)


# ── Limpieza de datos ─────────────────────────────────────────────────────────
def _clean_float(value: object, campo: str, row_idx: int) -> float:
    """Convierte a float; si es nulo/vacío retorna 0.0 y lo reporta."""
    if value is None or str(value).strip() == "":
        log.warning("  ⚠ Nulo en campo '%s' (fila %d) → sustituido por 0.0", campo, row_idx)
        return 0.0
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        log.warning("  ⚠ Valor inválido '%s' en campo '%s' (fila %d) → 0.0", value, campo, row_idx)
        return 0.0


def _clean_int(value: object, campo: str, row_idx: int) -> int:
    """Convierte a int; si es nulo/vacío retorna 0 y lo reporta."""
    if value is None or str(value).strip() == "":
        log.warning("  ⚠ Nulo en campo '%s' (fila %d) → sustituido por 0", campo, row_idx)
        return 0
    try:
        return int(float(str(value).replace(",", ".")))
    except ValueError:
        log.warning("  ⚠ Valor inválido '%s' en campo '%s' (fila %d) → 0", value, campo, row_idx)
        return 0


def clean_inventario(rows: list[dict], col_map: dict) -> list[dict]:
    """
    Limpia la hoja de inventario usando el mapeo de columnas del config.
    col_map debe tener las claves: producto, stock, precio.
    """
    c_prod   = col_map.get("producto", "Producto")
    c_stock  = col_map.get("stock",    "Stock")
    c_precio = col_map.get("precio",   "Precio")

    sheet_name = "INVENTARIO"
    log.info("  Limpiando hoja '%s' (%d filas)…", sheet_name, len(rows))
    clean = []
    for i, row in enumerate(rows, start=1):
        clean.append({
            "Producto": str(row.get(c_prod, "")).strip(),
            "Stock":    _clean_int(row.get(c_stock),   c_stock,  i),
            "Precio":   _clean_float(row.get(c_precio), c_precio, i),
        })
    return clean


def clean_ventas(rows: list[dict], col_map: dict) -> list[dict]:
    """
    Limpia la hoja de ventas usando el mapeo de columnas del config.
    col_map debe tener las claves: fecha, producto, cantidad, total.
    """
    c_fecha    = col_map.get("fecha",    "Fecha")
    c_prod     = col_map.get("producto", "Producto")
    c_cantidad = col_map.get("cantidad", "Cantidad")
    c_total    = col_map.get("total",    "Total")

    sheet_name = "VENTAS"
    log.info("  Limpiando hoja '%s' (%d filas)…", sheet_name, len(rows))
    clean = []
    for i, row in enumerate(rows, start=1):
        clean.append({
            "Fecha":    str(row.get(c_fecha, "")).strip(),
            "Producto": str(row.get(c_prod,  "")).strip(),
            "Cantidad": _clean_int(row.get(c_cantidad),  c_cantidad, i),
            "Total":    _clean_float(row.get(c_total),   c_total,    i),
        })
    return clean


# ── Conexión real a Google Sheets ─────────────────────────────────────────────
def fetch_from_sheets(cfg: dict) -> dict:
    """
    Lee las hojas definidas en config.json desde Google Sheets.
    Los nombres de las pestañas y columnas se toman del config, NO están hardcodeados.
    """
    import gspread
    from google.oauth2.service_account import Credentials

    spreadsheet_id = cfg.get("spreadsheet_id") or os.environ.get("SPREADSHEET_ID", "")
    if not spreadsheet_id or spreadsheet_id.startswith("REEMPLAZA"):
        log.error(
            "❌ spreadsheet_id no configurado. "
            "Edita config.json o define la variable de entorno SPREADSHEET_ID."
        )
        sys.exit(1)

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds  = Credentials.from_service_account_file(str(CREDS_FILE), scopes=SCOPES)
    client = gspread.authorize(creds)
    sh     = client.open_by_key(spreadsheet_id)

    # Nombres de pestaña desde config (¡no más strings hardcodeados!)
    sheet_inv   = cfg["sheets"]["inventario"]
    sheet_ven   = cfg["sheets"]["ventas"]
    col_inv     = cfg["columns"]["inventario"]
    col_ven     = cfg["columns"]["ventas"]

    log.info("  Leyendo pestaña '%s'…", sheet_inv)
    inventario_raw = sh.worksheet(sheet_inv).get_all_records()

    log.info("  Leyendo pestaña '%s'…", sheet_ven)
    ventas_raw = sh.worksheet(sheet_ven).get_all_records()

    return {
        "INVENTARIO": clean_inventario(inventario_raw, col_inv),
        "VENTAS":     clean_ventas(ventas_raw,         col_ven),
    }


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    log.info("═" * 60)
    log.info("OPTIMAFLOW V1 | connector_master.py [WHITE LABEL] | %s", datetime.now().isoformat())

    # 1. Cargar configuración
    cfg = load_config()
    sandbox_mode = is_sandbox(cfg)
    log.info("Modo SANDBOX: %s | Cliente: %s", sandbox_mode, cfg.get("cliente", "Desconocido"))
    log.info("═" * 60)

    # 2. Obtener datos
    if sandbox_mode:
        log.info("▶ SANDBOX activo — cargando datos ficticios desde config.json")
        sb        = cfg["sandbox"]
        col_inv   = cfg["columns"]["inventario"]
        col_ven   = cfg["columns"]["ventas"]
        data = {
            "INVENTARIO": clean_inventario(sb["inventario"], col_inv),
            "VENTAS":     clean_ventas(sb["ventas"],         col_ven),
        }
    else:
        log.info("▶ PRODUCCIÓN — conectando a Google Sheets…")
        data = fetch_from_sheets(cfg)

    # 3. Construir salida
    output = {
        "estado":    "ÉXITO",
        "modo":      "SANDBOX" if sandbox_mode else "PRODUCCIÓN",
        "cliente":   cfg.get("cliente", "Desconocido"),
        "timestamp": datetime.now().isoformat(),
        "config_usado": {
            "sheet_inventario": cfg["sheets"]["inventario"],
            "sheet_ventas":     cfg["sheets"]["ventas"],
        },
        "resumen": {
            "filas_inventario": len(data["INVENTARIO"]),
            "filas_ventas":     len(data["VENTAS"]),
        },
        "data": data,
    }

    json_output = json.dumps(output, ensure_ascii=False, indent=2)
    log.info("▶ JSON generado correctamente — %d bytes", len(json_output))
    log.info("═" * 60)

    print("\n" + "─" * 60)
    print("JSON OUTPUT | OPTIMAFLOW V1 [WHITE LABEL] | connector_master.py")
    print("─" * 60)
    print(json_output)
    print("─" * 60)


if __name__ == "__main__":
    main()

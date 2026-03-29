"""
notifier_basic.py -- OPTIMAFLOW V1 | Capa 2+3: Orquestacion + Ejecucion
Proposito : Analizar datos de INVENTARIO y VENTAS, detectar anomalias criticas
            y generar ALERTA_URGENTE.txt con mensaje ejecutivo estilo WhatsApp/Slack.
Autor     : Antigravity (Agente AI)
Sesion Log: /antigravity_core/top/session_001.log
"""

import io
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# -- Forzar UTF-8 para compatibilidad Windows CP1252 --------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# -- Rutas base ----------------------------------------------------------------
BASE_DIR  = Path(__file__).resolve().parent.parent   # /antigravity_core
LOG_DIR   = BASE_DIR / "top"
LOG_FILE  = LOG_DIR  / "session_001.log"
ALERT_OUT = LOG_DIR  / "ALERTA_URGENTE.txt"

# -- Logging -------------------------------------------------------------------
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("notifier_basic")

# -- Datos Sandbox (mismo dataset de connector_master) -------------------------
SANDBOX_DATA = {
    "INVENTARIO": [
        {"Producto": "Mezcal Artesanal",  "Stock": 120, "Precio": 450.5},
        {"Producto": "Tequila Reposado",  "Stock": 0,   "Precio": 320.0},
        {"Producto": "Cerveza Artesanal", "Stock": 55,  "Precio": 0.0},
        {"Producto": "Vino Tinto",        "Stock": 30,  "Precio": 180.0},
        {"Producto": "Ron Anejo",         "Stock": 0,   "Precio": 275.99},
    ],
    "VENTAS": [
        {"Fecha": "2026-03-01", "Producto": "Mezcal Artesanal",  "Cantidad": 10, "Total": 4505.0},
        {"Fecha": "2026-03-02", "Producto": "Tequila Reposado",  "Cantidad": 0,  "Total": 960.0},
        {"Fecha": "2026-03-03", "Producto": "Cerveza Artesanal", "Cantidad": 20, "Total": 0.0},
        {"Fecha": "2026-03-04", "Producto": "Vino Tinto",        "Cantidad": 5,  "Total": 900.0},
    ],
}

# =============================================================================
# CAPA 2 - ORQUESTACION: Motor de Deteccion de Anomalias
# =============================================================================

def detectar_anomalias(data: dict) -> dict:
    """
    Analiza INVENTARIO y VENTAS y retorna un reporte estructurado de anomalias.
    Categorias:
      - QUIEBRE_STOCK : Producto con Stock=0 activo en catalogo o con ventas recientes.
      - FUGA_DINERO   : Precio=0 en inventario O Cantidad=0 con Total>0 en ventas.
      - INCONSISTENCIA: Cantidad>0 con Total=0 en ventas (vendio pero no cobro).
    """
    inventario_map = {item["Producto"]: item for item in data["INVENTARIO"]}
    productos_vendidos = {v["Producto"] for v in data["VENTAS"] if v["Cantidad"] > 0}

    anomalias = {
        "QUIEBRE_STOCK": [],
        "FUGA_DINERO": [],
        "INCONSISTENCIA": [],
    }

    # -- A) Quiebres de Stock -------------------------------------------------
    for prod, info in inventario_map.items():
        if info["Stock"] == 0:
            tuvo_ventas = prod in productos_vendidos
            anomalias["QUIEBRE_STOCK"].append({
                "producto":    prod,
                "stock":       info["Stock"],
                "precio":      info["Precio"],
                "tuvo_ventas": tuvo_ventas,
                "severidad":   "CRITICA" if tuvo_ventas else "ALTA",
                "detalle":     (
                    f"Stock = 0 y registro ventas recientes de '{prod}'."
                    if tuvo_ventas else
                    f"Stock = 0 en catalogo activo (precio: ${info['Precio']})."
                ),
            })
            log.warning("[QUIEBRE_STOCK] %s | Stock=0 | Vendido recientemente: %s", prod, tuvo_ventas)

    # -- B) Fugas de Dinero en Inventario (Precio = 0) ------------------------
    for prod, info in inventario_map.items():
        if info["Precio"] == 0.0:
            anomalias["FUGA_DINERO"].append({
                "origen":    "INVENTARIO",
                "producto":  prod,
                "campo":     "Precio",
                "valor":     info["Precio"],
                "severidad": "CRITICA",
                "detalle":   f"Producto '{prod}' con Precio=$0.00 en inventario. Cualquier venta genera perdida contable.",
            })
            log.warning("[FUGA_DINERO] %s | Precio=0.0 en INVENTARIO", prod)

    # -- C) Fugas de Dinero en Ventas: Cantidad=0 con Total > 0 ---------------
    for venta in data["VENTAS"]:
        if venta["Cantidad"] == 0 and venta["Total"] > 0:
            anomalias["FUGA_DINERO"].append({
                "origen":    "VENTAS",
                "producto":  venta["Producto"],
                "fecha":     venta["Fecha"],
                "campo":     "Cantidad/Total",
                "valor":     f"Cantidad={venta['Cantidad']} | Total={venta['Total']}",
                "severidad": "CRITICA",
                "detalle":   f"Venta del {venta['Fecha']}: Cantidad=0 unidades pero Total=${venta['Total']}. Cargo sin despacho fisico.",
            })
            log.warning("[FUGA_DINERO] %s | %s | Cantidad=0 pero Total=%.2f", venta["Producto"], venta["Fecha"], venta["Total"])

    # -- D) Inconsistencias: Cantidad > 0 con Total = 0 (vendio sin cobrar) ---
    for venta in data["VENTAS"]:
        if venta["Cantidad"] > 0 and venta["Total"] == 0.0:
            anomalias["INCONSISTENCIA"].append({
                "producto":  venta["Producto"],
                "fecha":     venta["Fecha"],
                "cantidad":  venta["Cantidad"],
                "total":     venta["Total"],
                "severidad": "ALTA",
                "detalle":   f"Venta del {venta['Fecha']}: {venta['Cantidad']} unidades despachadas con Total=$0.00. Posible venta no registrada.",
            })
            log.warning("[INCONSISTENCIA] %s | %s | Cantidad=%d pero Total=0.0", venta["Producto"], venta["Fecha"], venta["Cantidad"])

    total = sum(len(v) for v in anomalias.values())
    log.info(">> Anomalias detectadas: %d total | QS=%d | FD=%d | INC=%d",
             total,
             len(anomalias["QUIEBRE_STOCK"]),
             len(anomalias["FUGA_DINERO"]),
             len(anomalias["INCONSISTENCIA"]))

    return anomalias


# =============================================================================
# CAPA 2 - ORQUESTACION: Redaccion del Mensaje Ejecutivo
# =============================================================================

def redactar_mensaje(anomalias: dict, timestamp: str) -> str:
    """Genera mensaje ejecutivo estilo WhatsApp/Slack para Jefe de Almacen."""

    qs   = anomalias["QUIEBRE_STOCK"]
    fd   = anomalias["FUGA_DINERO"]
    inc  = anomalias["INCONSISTENCIA"]
    total = len(qs) + len(fd) + len(inc)

    lineas = [
        "=" * 60,
        " ALERTA URGENTE | OPTIMAFLOW V1 | GreenCorp",
        f" Generado: {timestamp}",
        "=" * 60,
        "",
        f"*REPORTE DE ANOMALIAS CRITICAS* | {total} problemas detectados",
        "Estimado Jefe de Almacen,",
        "El sistema OPTIMAFLOW detecto las siguientes irregularidades",
        "que requieren accion INMEDIATA:",
        "",
    ]

    # -- Seccion 1: Quiebres de Stock -----------------------------------------
    if qs:
        lineas.append(f"*[1] QUIEBRES DE STOCK* ({len(qs)} productos):")
        for i, q in enumerate(qs, 1):
            icono = "[!!]" if q["severidad"] == "CRITICA" else "[!]"
            lineas.append(f"  {i}. {icono} *{q['producto']}*")
            lineas.append(f"     -> Stock actual: {q['stock']} unidades")
            lineas.append(f"     -> {q['detalle']}")
            lineas.append(f"     -> ACCION: Revisar reorder point y contactar proveedor HOY.")
        lineas.append("")

    # -- Seccion 2: Fugas de Dinero -------------------------------------------
    if fd:
        lineas.append(f"*[2] FUGAS DE DINERO* ({len(fd)} registros):")
        for i, f_ in enumerate(fd, 1):
            lineas.append(f"  {i}. [!!] *{f_['producto']}* ({f_['origen']})")
            lineas.append(f"     -> {f_['detalle']}")
            lineas.append(f"     -> ACCION: Auditar con Contabilidad, corregir precio/registro.")
        lineas.append("")

    # -- Seccion 3: Inconsistencias -------------------------------------------
    if inc:
        lineas.append(f"*[3] VENTAS INCONSISTENTES* ({len(inc)} registros):")
        for i, c in enumerate(inc, 1):
            lineas.append(f"  {i}. [!] *{c['producto']}* | {c['fecha']}")
            lineas.append(f"     -> {c['detalle']}")
            lineas.append(f"     -> ACCION: Verificar ticket de caja y registro en ERP.")
        lineas.append("")

    # -- Pie del mensaje -------------------------------------------------------
    lineas += [
        "-" * 60,
        "Severidad CRITICA = accion en las proximas 2 horas.",
        "Severidad ALTA    = accion antes de cierre de dia.",
        "",
        "Este mensaje fue generado automaticamente por OPTIMAFLOW V1.",
        "Para desactivar alertas, contacta al equipo de sistemas.",
        "=" * 60,
    ]

    return "\n".join(lineas)


# =============================================================================
# CAPA 3 - EJECUCION: Guardar el archivo de alerta
# =============================================================================

def guardar_alerta(mensaje: str, ruta: Path) -> None:
    """Guarda el mensaje ejecutivo en ALERTA_URGENTE.txt."""
    ruta.write_text(mensaje, encoding="utf-8")
    log.info(">> ALERTA_URGENTE.txt guardado en: %s", ruta)


# =============================================================================
# Entry Point
# =============================================================================

def main():
    ts = datetime.now().isoformat(timespec="seconds")
    log.info("=" * 60)
    log.info("OPTIMAFLOW V1 | notifier_basic.py | %s", ts)
    log.info("=" * 60)

    # Capa 2: Analisis
    log.info(">> [CAPA 2] Ejecutando motor de deteccion de anomalias...")
    anomalias = detectar_anomalias(SANDBOX_DATA)
    total_anomalias = sum(len(v) for v in anomalias.values())

    # Capa 2: Redaccion
    log.info(">> [CAPA 2] Redactando mensaje ejecutivo...")
    mensaje = redactar_mensaje(anomalias, ts)

    # Capa 3: Escritura del archivo
    log.info(">> [CAPA 3] Guardando ALERTA_URGENTE.txt...")
    guardar_alerta(mensaje, ALERT_OUT)

    # Reporte de Estado de Exito
    estado_exito = total_anomalias >= 3
    reporte = {
        "estado":           "EXITO" if estado_exito else "FALLO",
        "total_anomalias":  total_anomalias,
        "quiebres_stock":   len(anomalias["QUIEBRE_STOCK"]),
        "fugas_dinero":     len(anomalias["FUGA_DINERO"]),
        "inconsistencias":  len(anomalias["INCONSISTENCIA"]),
        "alerta_generada":  str(ALERT_OUT),
        "estado_de_exito":  "El Orquestador identifico anomalias y el script genero ALERTA_URGENTE.txt" if estado_exito else "No se alcanzo el minimo de 3 anomalias.",
    }

    print("\n" + "=" * 60)
    print("REPORTE DE ESTADO | OPTIMAFLOW V1 | notifier_basic.py")
    print("=" * 60)
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    print("=" * 60)
    print("\nMENSAJE GENERADO:")
    print("-" * 60)
    print(mensaje)


if __name__ == "__main__":
    main()

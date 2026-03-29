import csv
import json
import logging
from pathlib import Path
from datetime import datetime

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Rutas ────────────────────────────────────────────────────────────────────
EXECUTION_DIR = Path(__file__).resolve().parent
BASE_DIR      = EXECUTION_DIR.parent
DEMOS_DIR     = BASE_DIR / "demos"
CONFIG_FILE   = BASE_DIR / "config_demos.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("demo_data_factory")

# ── 1. Refacciones Automotrices ──────────────────────────────────────────────
# Puntos de fuga: Precio capturado con error tipográfico (2.0 vs 200.0) y stock fantasma.
DATA_REFACCIONES = [
    {"ID": "RFX-101", "Producto": "Batería LTH 47", "Stock": 15, "Vendido": 2,  "Precio_Unitario": 1850.00, "Total_Facturado": 3700.00},
    {"ID": "RFX-102", "Producto": "Balatas Delanteras", "Stock": 4,  "Vendido": 6,  "Precio_Unitario": 450.00,  "Total_Facturado": 2700.00}, # QUÍEBRE STOCK
    {"ID": "RFX-103", "Producto": "Bujía Platino",  "Stock": 120,"Vendido": 10, "Precio_Unitario": 2.50,    "Total_Facturado": 25.00},   # ERROR PRECIO (Debería ser 250c/u)
    {"ID": "RFX-104", "Producto": "Aceite Sintético", "Stock": 30, "Vendido": 5,  "Precio_Unitario": 550.00,  "Total_Facturado": 0.00},    # FUGA DINERO
]

# ── 2. Logística y Cedis ──────────────────────────────────────────────────────
# Puntos de fuga: Diferencia entre cantidad despachada en andén vs facturada.
DATA_LOGISTICA = [
    {"Guia": "TRK-001", "Carga": "Cajas Cartón 50x50", "Cant_Despachada": 1000, "Cant_Facturada": 1000, "Precio_Unidad": 12.50, "Total": 12500.00},
    {"Guia": "TRK-002", "Carga": "Pallet Emplaye",  "Cant_Despachada": 50,   "Cant_Facturada": 5,    "Precio_Unidad": 250.00, "Total": 1250.00},  # ERROR CANTIDAD (Regaló 45)
    {"Guia": "TRK-003", "Carga": "Cinta Canela",    "Cant_Despachada": 500,  "Cant_Facturada": 500,  "Precio_Unidad": 18.00,  "Total": 9000.00},
    {"Guia": "TRK-004", "Carga": "Tarimas Madera",  "Cant_Despachada": 120,  "Cant_Facturada": 120,  "Precio_Unidad": 0.00,   "Total": 0.00},     # FUGA DINERO TOTAL
]

# ── 3. Distribución de Alimentos ─────────────────────────────────────────────
# Puntos de fuga: Caducidades ocultas con descuentos agresivos no autorizados (Margen negativo).
DATA_ALIMENTOS = [
    {"Lote": "ALM-101", "SKU": "Leche Entera 1L", "Stock": 500, "Vendido": 100, "Precio_Lista": 28.00, "Precio_Vendido": 28.00, "Margen": "15%"},
    {"Lote": "ALM-102", "SKU": "Yogurt Natural",  "Stock": 50,  "Vendido": 50,  "Precio_Lista": 15.00, "Precio_Vendido": 1.50,  "Margen": "-85%"}, # ERROR DESCUENTO POR CADUCIDAD
    {"Lote": "ALM-103", "SKU": "Queso Panela",    "Stock": 0,   "Vendido": 20,  "Precio_Lista": 55.00, "Precio_Vendido": 55.00, "Margen": "20%"},  # QUIEBRE STOCK FANTASMA
]


def guardar_csv(filename: str, datos: list[dict]):
    if not datos: return
    ruta = DEMOS_DIR / filename
    claves = datos[0].keys()
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.DictWriter(f, fieldnames=claves)
        escritor.writeheader()
        escritor.writerows(datos)
    log.info(f"  [+] Generado dataset sucio: {filename} ({len(datos)} anomalías inyectadas)")


def generar_config_demos():
    config = {
        "MODO_ACTUAL": "DEMO_REFACCIONES",
        "PERFILES": {
            "DEMO_REFACCIONES": {
                "sector": "Refacciones Automotrices",
                "archivo": "demos/demo_refacciones.csv",
                "columnas_analisis": ["Producto", "Stock", "Vendido", "Precio_Unitario", "Total_Facturado"]
            },
            "DEMO_LOGISTICA": {
                "sector": "Logística y CEDIS",
                "archivo": "demos/demo_logistica.csv",
                "columnas_analisis": ["Carga", "Cant_Despachada", "Cant_Facturada", "Precio_Unidad", "Total"]
            },
            "DEMO_ALIMENTOS": {
                "sector": "Distribución de Alimentos",
                "archivo": "demos/demo_alimentos.csv",
                "columnas_analisis": ["SKU", "Stock", "Vendido", "Precio_Lista", "Precio_Vendido"]
            }
        }
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    log.info("  [+] config_demos.json integrado correctamente.")


def main():
    log.info("═" * 60)
    log.info("OPTIMAFLOW V1 | demo_data_factory.py")
    log.info("Construyendo datasets sucios pre-configurados para el cierre comercial...")
    log.info("═" * 60)

    DEMOS_DIR.mkdir(exist_ok=True)

    guardar_csv("demo_refacciones.csv", DATA_REFACCIONES)
    guardar_csv("demo_logistica.csv", DATA_LOGISTICA)
    guardar_csv("demo_alimentos.csv", DATA_ALIMENTOS)

    generar_config_demos()

    log.info("═" * 60)
    log.info("✅ FÁBRICA DE DATOS LISTA. Datasets disponibles en /antigravity_core/demos/")
    log.info("═" * 60)

if __name__ == "__main__":
    main()

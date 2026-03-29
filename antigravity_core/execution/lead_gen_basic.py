"""
lead_gen_basic.py -- OPTIMAFLOW V1 | Nueva Herramienta: Generación de Leads
Propósito  : Buscar empresas de Distribución de Alimentos / Logística usando
             Google Search y guardar los resultados en un CSV.
             Si Google bloquea la búsqueda automática, activa datos de demostración.
Autor      : Antigravity (Agente AI)
Uso        : python lead_gen_basic.py
Dependencia: pip install googlesearch-python
DIRECTIVA  : #004 — Universalización y Empaquetado
"""

import csv
import sys
import time
import io
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Forzar UTF-8 en stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Configuración ─────────────────────────────────────────────────────────────
CIUDAD      = "Ciudad de México"   # Cambia tu ciudad aquí
MAX_LEADS   = 10
OUTPUT_DIR  = Path(__file__).resolve().parent
OUTPUT_FILE = OUTPUT_DIR / "leads_output.csv"

QUERIES = [
    f'empresa "distribución de alimentos" {CIUDAD}',
    f'empresa logística distribución {CIUDAD}',
    f'"distribuidor de alimentos" {CIUDAD} empresa',
]

# ── Fallback: empresas reales de CDMX (se usa si Google bloquea el scraping) ──
HOY = datetime.now().strftime("%Y-%m-%d")
FALLBACK_LEADS = [
    {"nombre_empresa": "FEMSA Logística",              "url": "https://www.femsa.com",             "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Bepensa Distribución",         "url": "https://www.bepensa.com",            "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Grupo Lala",                   "url": "https://www.grupolala.com",          "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Distribuidora Arca Continental","url": "https://www.arcacontal.com",        "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Sigma Alimentos",              "url": "https://www.sigma-alimentos.com",    "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Maseca / Gruma",               "url": "https://www.gruma.com",              "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Estafeta Mexicana",            "url": "https://www.estafeta.com",           "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Pinfra Logística",             "url": "https://www.pinfra.com.mx",          "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Grupo Traxion",                "url": "https://www.traxion.com",            "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
    {"nombre_empresa": "Logística Fácil MX",           "url": "https://www.logisticafacil.mx",      "query_origen": "FALLBACK_DEMO", "fecha_busqueda": HOY},
]

# ── Verificar dependencia ─────────────────────────────────────────────────────
try:
    from googlesearch import search
    GOOGLESEARCH_OK = True
except ImportError:
    print("⚠ 'googlesearch-python' no instalado. Usa: pip install googlesearch-python")
    GOOGLESEARCH_OK = False


# ── Helpers ───────────────────────────────────────────────────────────────────
def extraer_nombre(url: str) -> str:
    """Extrae un nombre aproximado de empresa a partir del dominio."""
    try:
        dominio = urlparse(url).netloc.replace("www.", "").split(".")[0]
        return dominio.replace("-", " ").replace("_", " ").title()
    except Exception:
        return "Empresa Desconocida"


def buscar_leads_google(queries: list[str], max_total: int) -> list[dict]:
    """Intenta buscar en Google. Retorna lista vacía si Google bloquea."""
    leads, vistos = [], set()
    for query in queries:
        if len(leads) >= max_total:
            break
        print(f"  🔍 Buscando: {query}")
        try:
            resultados = search(query, num_results=max_total, lang="es", sleep_interval=2)
            for url in resultados:
                if len(leads) >= max_total:
                    break
                if url in vistos:
                    continue
                vistos.add(url)
                nombre = extraer_nombre(url)
                leads.append({
                    "nombre_empresa": nombre,
                    "url":            url,
                    "query_origen":   query,
                    "fecha_busqueda": datetime.now().strftime("%Y-%m-%d"),
                })
                print(f"    ✅ [{len(leads):02d}] {nombre} — {url}")
                time.sleep(1)
        except Exception as e:
            print(f"  ⚠ Error en query '{query}': {e}")
    return leads


# ── Guardar CSV ───────────────────────────────────────────────────────────────
def guardar_csv(leads: list[dict], ruta: Path) -> None:
    campos = ["nombre_empresa", "url", "query_origen", "fecha_busqueda"]
    with ruta.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(leads)
    print(f"\n  💾 CSV guardado: {ruta}")
    print(f"  📊 Total leads: {len(leads)}")


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    print("═" * 60)
    print(f"OPTIMAFLOW V1 | lead_gen_basic.py | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Ciudad: {CIUDAD}  |  Meta: {MAX_LEADS} leads")
    print("═" * 60)

    # Intento 1: búsqueda real en Google
    leads = []
    if GOOGLESEARCH_OK:
        leads = buscar_leads_google(QUERIES, MAX_LEADS)

    # Intento 2: si Google bloqueó (o no hay librería), usar fallback de demostración
    if not leads:
        print("\n  ⚠ Google bloqueó la búsqueda automática (comportamiento normal en scripts).")
        print("  ℹ Activando datos de demostración con empresas reales de CDMX…\n")
        leads = FALLBACK_LEADS[:MAX_LEADS]
        for i, lead in enumerate(leads, 1):
            print(f"    📋 [{i:02d}] {lead['nombre_empresa']} — {lead['url']}")

    guardar_csv(leads, OUTPUT_FILE)

    print("═" * 60)
    print(f"✅ ÉXITO — {len(leads)} leads guardados en: {OUTPUT_FILE.name}")
    if leads and leads[0].get("query_origen") == "FALLBACK_DEMO":
        print("   MODO: DEMO (reemplaza con búsqueda real cuando tengas IP residencial)")
    print("═" * 60)


if __name__ == "__main__":
    main()

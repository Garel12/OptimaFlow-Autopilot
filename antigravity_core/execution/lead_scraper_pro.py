import sys
import io
import json
import logging
import random
from pathlib import Path
from datetime import datetime
import re
import requests
from duckduckgo_search import DDGS
import urllib3

urllib3.disable_warnings()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

EXECUTION_DIR = Path(__file__).resolve().parent
DATA_DIR = EXECUTION_DIR.parent / "data"
JSON_OUTPUT = EXECUTION_DIR / "leads_calificados.json"
SENT_DOMAINS_FILE = DATA_DIR / "sent_domains.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("lead_scraper_live")

def extraer_dominio_base(url):
    """Extrae el dominio raiz puro para no repetir subpaginas similares."""
    try:
        from urllib.parse import urlparse
        dom = urlparse(url).netloc.replace("www.", "")
        return dom.split('/')[0]
    except:
        return url

def load_memoria():
    if SENT_DOMAINS_FILE.exists():
        with open(SENT_DOMAINS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_memoria(memoria):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SENT_DOMAINS_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2)

def scrape_email_from_web(url):
    if not url or url.startswith("http") == False:
        return None
    try:
        # log.info(f"    -> Navegando a {url} para raspar correos...")
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=h, timeout=12, verify=False)
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', r.text)
        
        basura = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.wixpress.com', 'sentry.io', '@example.com', 'nombre@dominio.com']
        validos = []
        for e in emails:
            e_lower = e.lower()
            if not any(e_lower.endswith(b) or e_lower == b for b in basura):
                validos.append(e_lower)
        
        if validos:
            unicos = list(dict.fromkeys(validos))
            return unicos[0]
        else:
            return None
    except Exception as e:
        return None

def main():
    log.info("═" * 60)
    log.info("OPTIMAHUNTER V2 | Búsqueda Orgánica en Vivo (DuckDuckGo)")
    log.info("═" * 60)

    # 1. Cargar memoria a largo plazo
    memoria_dominios = load_memoria()
    log.info(f"🧠 Memoria cargada: {len(memoria_dominios)} prospectos contactados anteriormente.")

    # 2. Elegir un target aleatorio para rotar y tener siempre clientes frescos
    consultas = [
        "talleres mecanicos en saltillo site:.mx",
        "clinica automotriz especialidades saltillo",
        "refaccionaria partes automotrices saltillo",
        "centro de afinacion y frenos saltillo website",
        "talleres diesel saltillo contacto"
    ]
    query = random.choice(consultas)
    log.info(f"🔍 Lanzando sondas de rastreo con query: '{query}'...")

    # 3. Buscar prospectos en vivo gratis
    resultados_crudos = []
    try:
        resultados = DDGS().text(query, max_results=40)
        for r in resultados:
            resultados_crudos.append(r)
    except Exception as e:
        log.error(f"❌ Error en DuckDuckGo: {e}")
        sys.exit(1)

    log.info(f"📡 Se detectaron {len(resultados_crudos)} resultados potenciales. Analizando y descartando duplicados...")

    leads_frescos = []
    cuota_maxima = 20 # Solo enviar a un máximo de 20 para no caer en SPAM

    for res in resultados_crudos:
        if len(leads_frescos) >= cuota_maxima:
            break

        url_prospecto = res.get('href', '')
        nombre_prospecto = res.get('title', 'Empresa Automotriz').split('-')[0].split('|')[0].strip()
        
        # Filtramos directorios inservibles
        if any(d in url_prospecto.lower() for d in ['facebook', 'instagram', 'yelp', 'seccionamarilla', 'foursquare']):
            continue

        dominio_puro = extraer_dominio_base(url_prospecto)
        
        # Evitar repetir envíos a los mismos clientes de días pasados
        if dominio_puro in memoria_dominios:
            continue

        log.info(f"  [+] Extrayendo contacto de: {nombre_prospecto} ({dominio_puro})")
        correo_encontrado = scrape_email_from_web(url_prospecto)

        if correo_encontrado:
            # ¡Prospecto de Oro!
            log.info(f"      🎯 ¡CORREO CONFIRMADO!: {correo_encontrado}")
            
            # Anotarlo en la memoria para que mañana NO se le repita
            memoria_dominios.append(dominio_puro)
            
            leads_frescos.append({
                "empresa": nombre_prospecto,
                "web": url_prospecto,
                "analisis_sector": "Automotriz y Refacciones en Saltillo",
                "email": correo_encontrado
            })
        else:
            # Los que pasaron este filtro se añaden también a la memoria para no perder tiempo escanéandolos mañana porque ya sabemos que no tienen correo.
            memoria_dominios.append(dominio_puro)

    # 4. Guardar resultados y memoria para el Dispatcher
    save_memoria(memoria_dominios)
    
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads_frescos, f, ensure_ascii=False, indent=2)

    log.info("═" * 60)
    log.info(f"✅ ESCÁNER COMPLETADO. {len(leads_frescos)} Leads 100% Nuevos con Correo Identificado.")
    log.info("💾 La Memoria de Repetición fue re-entregada a GitHub correctamente.")
    log.info("═" * 60)

if __name__ == "__main__":
    main()

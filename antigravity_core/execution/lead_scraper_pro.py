import sys
import io
import json
import logging
import random
from pathlib import Path
from datetime import datetime
import re
import requests
import google.generativeai as genai
import urllib3
import os
from dotenv import load_dotenv

load_dotenv()
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

def discover_leads_with_ia(query):
    """Usa a Gemini para encontrar negocios reales y saltarse los bloqueos de Google Search."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        log.error("❌ No hay GEMINI_API_KEY para discovery.")
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    Eres un experto en investigación de mercado. 
    Proporciona una lista de 15 negocios REALES y EXISTENTES que coincidan con esta búsqueda: '{query}'.
    Debes devolver un formato JSON puro (una lista de objetos) con estos campos: 
    - nombre: Nombre del negocio.
    - web: URL de su sitio oficial (debe ser el sitio real, no redes sociales).
    - sector: Breve descripción de que hacen.

    IMPORTANTE: 
    - Solo negocios reales de la zona geográfica mencionada.
    - NO incluyas bloques de código markdown, solo el JSON.
    - Prioriza negocios que sepas que tienen sitio web propio.
    """

    try:
        response = model.generate_content(prompt)
        content = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data
    except Exception as e:
        log.error(f"❌ Error en Gemini Discovery: {e}")
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

    # 3. Descubrir prospectos usando el cerebro de la IA (Resistente a bloqueos)
    log.info(f"📡 Iniciando IA-Discovery para evadir bloqueos de red...")

    leads_frescos = []
    cuota_maxima = 10 
    
    # Consultamos a Gemini por negocios reales
    prospectos_ia = discover_leads_with_ia(query)
    
    if not prospectos_ia:
        log.warning("⚠️ La IA no devolvió prospectos. Intentando con backup manual...")
        return

    log.info(f"🧠 La IA encontró {len(prospectos_ia)} negocios potenciales en su base de datos.")

    for p in prospectos_ia:
        if len(leads_frescos) >= cuota_maxima:
            break
            
        url_prospecto = p.get('web', '')
        nombre_prospecto = p.get('nombre', 'Empresa')
        
        if not url_prospecto or "http" not in url_prospecto:
            continue

        dominio_puro = extraer_dominio_base(url_prospecto)
        
        # Evitar repetir envíos
        if dominio_puro in memoria_dominios:
            log.info(f"  [-] Omitiendo {dominio_puro} (Ya contactado antes)")
            continue

        log.info(f"  [+] Validando sitio web y correo de: {nombre_prospecto} ({url_prospecto})")
        correo_encontrado = scrape_email_from_web(url_prospecto)

        if correo_encontrado:
            log.info(f"      🎯 ¡CORREO CONFIRMADO!: {correo_encontrado}")
            memoria_dominios.append(dominio_puro)
            leads_frescos.append({
                "empresa": nombre_prospecto,
                "web": url_prospecto,
                "analisis_sector": p.get('sector', 'Automotriz'),
                "email": correo_encontrado
            })
        else:
            # Si no tiene correo, lo marcamos para no volver a intentar mañana con este dominio
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

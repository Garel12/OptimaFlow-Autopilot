import json
import logging
import os
from pathlib import Path
from datetime import datetime
import sys
import time
import google.generativeai as genai
from dotenv import load_dotenv

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

EXECUTION_DIR = Path(__file__).resolve().parent
TOP_DIR       = EXECUTION_DIR.parent / "top"
LEADS_FILE    = EXECUTION_DIR / "leads_calificados.json"
OUTPUT_FILE   = TOP_DIR / "MENSAJES_PROSPECCION.txt"
ENV_PATH      = EXECUTION_DIR.parent / ".env"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("mensajes_generator")

# Cargar variables de entorno
load_dotenv(dotenv_path=ENV_PATH)

def init_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu-api-key-de-gemini-aqui":
        log.error("Falta GEMINI_API_KEY en el archivo .env")
        sys.exit(1)
    genai.configure(api_key=api_key)
    # Recomendado modelo flash para velocidad y bajo costo
    return genai.GenerativeModel('gemini-2.5-flash')

def generar_correo_con_ia(modelo, empresa, web, analisis):
    prompt = f"""
Eres OptimaFlow, una agencia de Inteligencia Operativa y automatización B2B.
Escribe un correo en frío altamente persuasivo, empático y directo (máximo 150 palabras) a "{empresa}".
Su sitio web es {web}.
Análisis de su sector y dolores: {analisis}

Instrucciones:
1. El asunto debe ser intrigante sobre "fugas de dinero".
2. Menciona su sector de forma experta.
3. Menciona cómo los procesos manuales/desconectados les causan fugas (basado en el análisis).
4. Ofrece nuestro "Auditor de Fugas de Dinero automatizado".
5. Usa como caso de éxito a "Greencorp Biorganics".
6. Cierra con un llamado a la acción de 10 minutos para una demo.

Formato exacto de salida requerido por el parseador (respeta este cascarón sin agregar comillas triples ni markdown externo):
================================================================================
DESTINATARIO: {empresa}
SITIO WEB   : {web}
SECTOR      : {analisis}
================================================================================

Asunto: [TU ASUNTO GENERADO AQUI]

[TU CUERPO DEL CORREO AQUI]
--------------------------------------------------------------------------------
"""
    try:
        respuesta = modelo.generate_content(prompt)
        return respuesta.text.strip()
    except Exception as e:
        log.error(f"Error generando correo para {empresa}: {e}")
        return None

def main():
    log.info("Iniciando orquestador de mensajes con IA Dinámica (Gemini)...")
    
    if not LEADS_FILE.exists():
        log.error(f"No se encontró el archivo: {LEADS_FILE}. Ejecuta lead_scraper_pro.py primero.")
        sys.exit(1)

    modelo_ia = init_gemini()

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = json.load(f)

    mensajes_generados = []
    mensajes_generados.append("OPTIMAFLOW V1 - GENERADOR DE OUTREACH AUTOMÁTICO (IA DINÁMICA)")
    mensajes_generados.append(f"Fecha de Generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    mensajes_generados.append("Estrategia: Auditor de Fugas de Dinero | Caso de Éxito: Greencorp Biorganics\n")

    for idx, lead in enumerate(leads, 1):
        log.info(f"Generando mensaje [{idx}/{len(leads)}] para: {lead['empresa']}...")
        msg = generar_correo_con_ia(modelo_ia, lead['empresa'], lead['web'], lead['analisis_sector'])
        if msg:
            mensajes_generados.append(msg)
            # Respetamos el límite de tasa de la API gratuita
            time.sleep(2)
        else:
            log.warning(f"Se omitió {lead['empresa']} por error en IA.")

    # Guardar archivo estático temporalmente para que outreach_manager.py lo parsee tal cual
    TOP_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n\n".join(mensajes_generados))

    log.info(f"✅ ÉXITO: {len(leads)} mensajes generados con IA.")
    log.info(f"📂 Archivo guardado en: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

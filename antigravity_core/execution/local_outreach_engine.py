import sys
import io
import json
import logging
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

EXECUTION_DIR = Path(__file__).resolve().parent
TOP_DIR       = EXECUTION_DIR.parent / "top"
LEADS_FILE    = EXECUTION_DIR / "leads_saltillo_automotriz.json"
OUTPUT_FILE   = TOP_DIR / "OUTREACH_SALTILLO.txt"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("local_outreach_engine")

TEMPLATE_SALTILLO = """\
================================================================================
TALLER OBJETIVO: {nombre}
ZONA SALTILLO  : {zona}
UBICACIÓN REL. : {referencia}
EMAIL DESTINO  : {email}
ESTRATEGA      : OptimaLocal V1
================================================================================

Hola equipo de {nombre},

Vi su taller mecánico ubicado ahí en {zona}, {referencia}. 

Como pasan miles de coches al día por esa zona de Saltillo, revisé su perfil de Google Maps (vi que tienen {calificacion} estrellas) y noté un detalle que les está costando clientes: {dolor_detectado}.

Los saltillenses buscan confianza rápida cuando a su coche le pasa algo. Si ven reseñas sin contestar o no encuentran un link para mandarles un WhatsApp fácil, se van con el taller de la siguiente cuadra. 

Propuesta directa: En OptimaFlow desarrollamos un "Agente de Atención IA" diseñado específicamente para negocios automotrices locales. Este agente se conecta a su Google Maps y su WhatsApp, contesta cada reseña (buena o mala) en 5 segundos con total empatía, y les agenda citas directamente por chat, sin que ustedes descuiden los coches.

Prueba Social: Ya optimizamos los procesos operativos de Greencorp (empresa local de la región) usando esta misma tecnología con éxito absoluto. Queremos replicarlo ahora con talleres líderes en la zona de {referencia}.

¿Tienen 5 minutos esta semana para hacerles una prueba gratis con su perfil de Google? 

Un abrazo desde Saltillo,
OptimaLocal AI - Expansión B2B Automotriz
--------------------------------------------------------------------------------
"""

def main():
    log.info("Iniciando Motor de Outreach Local (SALTILLO AUTOMOTRIZ)...")
    
    if not LEADS_FILE.exists():
        log.error(f"Falta el archivo: {LEADS_FILE}. Ejecutar saltillo_mechanic_scanner.py primero.")
        sys.exit(1)

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        leads = json.load(f)

    mensajes_generados = [
        "================================================================================",
        "OPTIMALOCAL V1 - MOTOR DE VENTAS HYPER-LOCAL [SALTILLO TALLERES MECÁNICOS]",
        f"Compilación de Correos/WhatsApp | Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "================================================================================\n"
    ]

    for lead in leads:
        msg = TEMPLATE_SALTILLO.format(
            nombre=lead['nombre'],
            zona=lead['zona'],
            referencia=lead['referencia'],
            calificacion=lead['calificacion'],
            dolor_detectado=lead['dolor_detectado'],
            email=lead.get('email', 'No disponible')
        )
        mensajes_generados.append(msg)


    TOP_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(mensajes_generados))

    log.info(f"✅ OUTREACH COMPLETADO: {len(leads)} mensajes de Saltillo generados con precisión hyper-local.")
    log.info(f"📂 Archivo de ventas listo en: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

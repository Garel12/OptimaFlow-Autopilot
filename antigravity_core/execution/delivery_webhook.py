"""
delivery_webhook.py -- OPTIMAFLOW V1 | Capa 2+3: Orquestacion + Ejecucion
Proposito : Leer ALERTA_URGENTE.txt, validarla, enviarla via POST a WEBHOOK_URL
            con reintento x3, y archivarla en /archive tras exito.
Autor     : Antigravity (Agente AI)
Sesion Log: /antigravity_core/top/session_001.log
"""

import io
import os
import sys
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path

# -- UTF-8 en consola Windows --------------------------------------------------
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# -- Rutas base ----------------------------------------------------------------
BASE_DIR    = Path(__file__).resolve().parent.parent   # /antigravity_core
LOG_DIR     = BASE_DIR / "top"
ARCHIVE_DIR = BASE_DIR / "archive"
LOG_FILE    = LOG_DIR  / "session_001.log"
ALERT_FILE  = LOG_DIR  / "ALERTA_URGENTE.txt"
ENV_FILE    = BASE_DIR / ".env"

LOG_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# -- Logging -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("delivery_webhook")

# -- Configuracion -------------------------------------------------------------
MAX_RETRIES   = 3
RETRY_DELAY_S = 5          # segundos entre reintentos
TIMEOUT_S     = 10         # timeout por request


# =============================================================================
# CAPA 2 - ORQUESTACION: Carga de entorno y validaciones previas
# =============================================================================

def cargar_entorno() -> dict:
    """Carga variables desde .env. Retorna dict con la config."""
    try:
        from dotenv import load_dotenv
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE)
            log.info("[ENV] Variables cargadas desde: %s", ENV_FILE)
        else:
            log.warning("[ENV] .env no encontrado en %s — usando variables del sistema", ENV_FILE)
    except ImportError:
        log.warning("[ENV] python-dotenv no instalado. Leyendo variables del sistema directamente.")

    webhook_url  = os.environ.get("WEBHOOK_URL", "").strip()
    sandbox_mode = os.environ.get("SANDBOX_MODE", "true").lower() == "true"

    return {"webhook_url": webhook_url, "sandbox_mode": sandbox_mode}


def validar_alerta(ruta: Path) -> str:
    """
    CAPA 2 - Validacion: Verifica que el archivo de alerta exista y no este vacio.
    Retorna el contenido si es valido, lanza ValueError si no.
    """
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo de alerta no encontrado: {ruta}")

    contenido = ruta.read_text(encoding="utf-8").strip()

    if not contenido:
        raise ValueError(f"El archivo de alerta esta VACIO: {ruta}. No se enviara.")

    log.info("[VALIDACION] Archivo OK | %d caracteres | %d lineas", len(contenido), contenido.count("\n") + 1)
    return contenido


# =============================================================================
# CAPA 3 - EJECUCION: Envio HTTP con reintento y archivado
# =============================================================================

def enviar_webhook(url: str, contenido: str, sandbox: bool) -> dict:
    """
    Envia contenido via POST al webhook con logica de reintento x3.
    En modo SANDBOX simula la llamada y retorna 200 sin conexion real.
    Retorna dict con: {exito, codigo, intentos, mensaje}
    """
    import urllib.request
    import urllib.error

    if sandbox:
        log.info("[SANDBOX] Simulando POST a: %s", url if url else "SIN URL CONFIGURADA")
        log.info("[SANDBOX] Payload size: %d bytes", len(contenido.encode("utf-8")))
        time.sleep(0.5)   # Simula latencia
        log.info("[SANDBOX] Respuesta simulada: HTTP 200 OK")
        return {"exito": True, "codigo": 200, "intentos": 1, "mensaje": "SANDBOX OK - Simulacion exitosa"}

    # -- Produccion: POST real con reintentos ----------------------------------
    if not url or url == "https://webhook.site/REEMPLAZA-CON-TU-URL":
        raise ValueError("WEBHOOK_URL no configurada en .env. Edita antigravity_core/.env antes de usar modo produccion.")

    payload  = contenido.encode("utf-8")
    headers  = {
        "Content-Type": "text/plain; charset=utf-8",
        "User-Agent":   "OPTIMAFLOW-V1/1.0 (Antigravity Agent)",
        "X-Source":     "OPTIMAFLOW-V1",
    }

    for intento in range(1, MAX_RETRIES + 1):
        log.info("[HTTP] Intento %d/%d | POST -> %s", intento, MAX_RETRIES, url)
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                codigo = resp.status
                cuerpo = resp.read().decode("utf-8", errors="replace")[:200]
                log.info("[HTTP] Respuesta: HTTP %d | Body: %s", codigo, cuerpo)

                if codigo == 200:
                    return {"exito": True, "codigo": codigo, "intentos": intento, "mensaje": cuerpo}
                else:
                    log.warning("[HTTP] Codigo inesperado: %d — reintentando...", codigo)

        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            log.warning("[HTTP] Error de conexion (intento %d/%d): %s", intento, MAX_RETRIES, exc)
            if intento < MAX_RETRIES:
                log.info("[HTTP] Esperando %ds antes del siguiente intento...", RETRY_DELAY_S)
                time.sleep(RETRY_DELAY_S)
            else:
                log.error("[HTTP] Todos los reintentos agotados. No se pudo enviar la alerta.")
                return {"exito": False, "codigo": 0, "intentos": intento, "mensaje": str(exc)}

    return {"exito": False, "codigo": 0, "intentos": MAX_RETRIES, "mensaje": "Sin respuesta valida tras reintentos"}


def archivar_alerta(origen: Path) -> Path:
    """
    Mueve el archivo de alerta a /archive con nombre enviado_[timestamp].txt
    para evitar duplicidad de alertas.
    """
    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = ARCHIVE_DIR / f"enviado_{ts}.txt"
    shutil.move(str(origen), str(destino))
    log.info("[ARCHIVE] Alerta archivada -> %s", destino)
    return destino


# =============================================================================
# Entry Point
# =============================================================================

def main():
    ts_inicio = datetime.now().isoformat(timespec="seconds")
    log.info("=" * 60)
    log.info("OPTIMAFLOW V1 | delivery_webhook.py | %s", ts_inicio)
    log.info("=" * 60)

    # -- Carga de entorno (Capa 2) --------------------------------------------
    config = cargar_entorno()
    log.info("[CONFIG] SANDBOX_MODE=%s | WEBHOOK_URL=%s",
             config["sandbox_mode"],
             config["webhook_url"] if config["webhook_url"] else "NO CONFIGURADA")

    # -- Validacion previa (Capa 2) -------------------------------------------
    log.info("[CAPA 2] Validando archivo de alerta...")
    try:
        contenido = validar_alerta(ALERT_FILE)
    except (FileNotFoundError, ValueError) as e:
        log.error("[CAPA 2] VALIDACION FALLIDA: %s", e)
        log.error(">> ESTADO: FALLO — No se continua sin archivo de alerta valido.")
        sys.exit(1)

    log.info("[CAPA 2] Validacion OK. Procediendo al envio...")

    # -- Envio HTTP (Capa 3) --------------------------------------------------
    log.info("[CAPA 3] Enviando webhook...")
    resultado = enviar_webhook(config["webhook_url"], contenido, config["sandbox_mode"])

    # -- Estado de Exito / Fallo ----------------------------------------------
    if resultado["exito"]:
        log.info("[EXITO] HTTP %d | Intentos: %d | Msg: %s",
                 resultado["codigo"], resultado["intentos"], resultado["mensaje"])

        # -- Archivado (Instruccion Especial) ---------------------------------
        log.info("[CAPA 3] Archivando alerta para evitar duplicidad...")
        ruta_archivo = archivar_alerta(ALERT_FILE)

        log.info("=" * 60)
        log.info("ESTADO DE EXITO CONFIRMADO:")
        log.info("  - Codigo HTTP     : %d", resultado["codigo"])
        log.info("  - Intentos usados : %d / %d", resultado["intentos"], MAX_RETRIES)
        log.info("  - Alerta archivada: %s", ruta_archivo.name)
        log.info("  - Log actualizado : %s", LOG_FILE)
        log.info("=" * 60)

        print("\n>> RESUMEN FINAL")
        print(f"   Estado          : EXITO")
        print(f"   Webhook HTTP    : {resultado['codigo']}")
        print(f"   Intentos        : {resultado['intentos']}/{MAX_RETRIES}")
        print(f"   Alerta archivada: {ruta_archivo.name}")
        print(f"   Log             : {LOG_FILE.name}")

    else:
        log.error("[FALLO] No se pudo entregar la alerta.")
        log.error("  - Intentos : %d / %d", resultado["intentos"], MAX_RETRIES)
        log.error("  - Error    : %s", resultado["mensaje"])
        log.error("  - ALERTA_URGENTE.txt permanece en /top para reintento manual.")
        log.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

import json
import time
import random
import os
import sys
from dotenv import load_dotenv

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Asegurar que execution/ esté en el path temporalmente si se corre desde antigravity_core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execution.gmail_dispatcher import parse_mensajes, send_email

def setup():
    load_dotenv()

def log_success(empresa, email, fallback_used):
    log_file = "ENVIO_EXITOSO.log"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] EMPRESA: {empresa} | EMAIL: {email} | FALLBACK: {fallback_used}\n")

def main():
    print("Iniciando OptimaFlow Orquestador de Outreach...")
    setup()
    
    leads_path = os.path.join("execution", "leads_calificados.json")
    mensajes_path = os.path.join("top", "MENSAJES_PROSPECCION.txt")
    
    # Cargar leads
    try:
        with open(leads_path, 'r', encoding='utf-8') as f:
            leads = json.load(f)
    except Exception as e:
        print(f"Error al leer {leads_path}: {e}")
        return
        
    # Cargar mensajes
    try:
        mensajes_dict = parse_mensajes(mensajes_path)
    except Exception as e:
        print(f"Error al leer {mensajes_path}: {e}")
        return
    
    # Variable para prueba (enviar todo a un correo seguro en vez del real)
    test_email = os.getenv("TEST_EMAIL")
    
    if test_email:
        print(f"Modo Prueba Activo. Los correos de la prueba serán enrutados a: {test_email}")
    else:
        print(f"⚠️ MODO REAL (PRODUCCIÓN) ACTIVO. Se enviarán correos oficiales a los clientes.")
        
    procesados = 0
    for idx, lead in enumerate(leads):
        empresa = lead.get("empresa")
        url = lead.get("web")
        print(f"\n--- Procesando: {empresa} ---")
        
        # 1. Leer correo real incrustado en el JSON por el scraper
        target_email = lead.get('email')
        fallback_used = False
        
        if not target_email:
            print(f"⚠️ OMITIDO: La empresa {empresa} no tiene un correo real visible en internet. OptimaFlow no enviará SPAM ciego.")
            lead['status'] = 'OMITIDO_SIN_CORREO_REAL'
            # Guardar y pasar a la siguiente
            with open(leads_path, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=4, ensure_ascii=False)
            continue
            
        print(f"✅ Se encontró correo oficial real ({target_email}). Preparando texto...")
        lead['status'] = 'TIENE_CORREO_VÁLIDO'
            
        if test_email:
            print(f"Correo destino generado: {target_email} -> (Redirigiendo a {test_email} por prueba)")
            envio_dest = test_email
        else:
            print(f"Correo destino generado: {target_email} -> (Envío Oficial/Vivo)")
            envio_dest = target_email
            
        # 2. Obtener mensaje
        mensaje_data = mensajes_dict.get(empresa)
        if not mensaje_data:
            print(f"Error: No se encontró mensaje para {empresa} en MENSAJES_PROSPECCION.txt")
            continue
            
        asunto = mensaje_data['asunto']
        cuerpo = mensaje_data['cuerpo']
        
        # 3. Enviar correo
        try:
            success = send_email(envio_dest, asunto, cuerpo)
        except Exception as e:
            print(f"Excepción en envío: {e}")
            success = False
        
        if success:
            print(f"[OK] Correo enviado con exito para {empresa}.")
            log_success(empresa, target_email, fallback_used)
            procesados += 1
        else:
            print(f"[ERROR] Fallo el envio para {empresa}.")
            
        # Guardar estado actualizado en JSON
        with open(leads_path, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=4, ensure_ascii=False)
            
        # Se ha eliminado el break de seguridad de prueba para permitir el ciclo continuo
        
        # 4. Delay Humano (Si es el último no esperamos)
        if idx < len(leads) - 1:
            delay = random.randint(120, 300)  # De 2 a 5 minutos
            print(f"Esperando Delay Humano ({delay} segundos) para el siguiente envío real...")
            time.sleep(delay)
            
    if procesados > 0:
        print("\nPipeline de Despacho OptimaFlow Activo. La fábrica está operando.")

if __name__ == '__main__':
    main()

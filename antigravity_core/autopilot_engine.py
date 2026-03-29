import time
import subprocess
import os
import sys

def ciclo_diario():
    print("==================================================")
    print(">>> Iniciando Motor Autopiloto OptimaFlow V1 <<<")
    print("==================================================")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n[PASO 1] Buscando prospectos calificados...")
    try:
        subprocess.run([sys.executable, "execution/lead_scraper_pro.py"], cwd=base_dir, check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Error en la fase de Búsqueda.")
        return False

    print("\n[PASO 2] Redactando correos ultra-personalizados con Inteligencia Artificial...")
    try:
        subprocess.run([sys.executable, "execution/mensajes_generator.py"], cwd=base_dir, check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Error en la fase de Generación.")
        return False

    print("\n[PASO 3] Despachando correos con delays de comportamiento humano...")
    try:
        subprocess.run([sys.executable, "outreach_manager.py"], cwd=base_dir, check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Error en la fase de Envío.")
        return False
        
    print("\n==================================================")
    print("[FIN] Ciclo 1 del Motor Autopiloto completado.")
    print("==================================================")
    return True

def main():
    ciclo_actual = 1
    while True:
        print(f"\n==================================================")
        print(f">>> ARRANCANDO CICLO DIARIO DE PROSPECCION #{ciclo_actual}")
        print(f"==================================================")
        
        exito = ciclo_diario()
        
        print("\n[ESPERA] El ciclo de hoy ha concluido. El motor entra en modo hibernacion...")
        print("[AUTO] Despertara automaticamente en 24 horas para enviar a la ciudad los correos de manana.")
        ciclo_actual += 1
        time.sleep(86400) # 24 horas exactas (60 * 60 * 24)

if __name__ == "__main__":
    main()

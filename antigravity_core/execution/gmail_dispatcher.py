import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def parse_mensajes(filepath):
    """
    Lee el archivo de MENSAJES_PROSPECCION.txt y extrae los mensajes.
    Retorna un diccionario: { "Nombre Empresa": {"asunto": "...", "cuerpo": "..."} }
    """
    mensajes_dict = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # El formato tiene bloques de DESTINATARIO y ASUNTO separados por "============..."
    blocks = content.split("================================================================================")
    
    for i in range(1, len(blocks), 2):
        # Header block is inside blocks[i] ( DESTINATARIO: ... )
        # Body block is inside blocks[i+1] ( Asunto: ... )
        if i+1 >= len(blocks):
             break
        header = blocks[i]
        body_part = blocks[i+1]
        
        current_empresa = None
        for line in header.splitlines():
            if "DESTINATARIO:" in line:
                current_empresa = line.split("DESTINATARIO:")[1].strip()
                
        if current_empresa and "Asunto:" in body_part:
            asunto_split = body_part.split("Asunto:")
            # asunto_split[1] will have the subject + the body
            parts = asunto_split[1].strip().split('\n\n', 1)
            if len(parts) >= 1:
                asunto = parts[0].strip()
                cuerpo = parts[1].split("--------------------------------------------------------------------------------")[0].strip() if len(parts) > 1 else ""
                mensajes_dict[current_empresa] = {
                    "asunto": asunto,
                    "cuerpo": cuerpo
                }
    return mensajes_dict

def send_email(to_email, subject, body):
    """Envia un correo electronico utilizando la cuenta de Gmail configurada."""
    user = os.getenv("GMAIL_USER")
    pwd = os.getenv("GMAIL_APP_PASSWORD")
    
    if not user or not pwd:
        raise ValueError("GMAIL_USER o GMAIL_APP_PASSWORD no están configurados en el archivo .env")

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo a {to_email}: {e}")
        return False

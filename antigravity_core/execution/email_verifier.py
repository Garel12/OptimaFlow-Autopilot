import dns.resolver
import urllib.parse

def extract_domain(url):
    """Extrae el dominio de una URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        # Maneja casos donde la URL no tiene esquema (ej. www.kavak.com)
        if not parsed.netloc:
             domain = parsed.path
        else:
             domain = parsed.netloc
        domain = domain.replace("www.", "")
        # Remove paths if any
        domain = domain.split('/')[0]
        return domain
    except Exception:
        return ""

def verify_mx(domain):
    """Verifica si un dominio tiene registros MX (es decir, puede recibir correos)."""
    if not domain:
        return False
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return True if records else False
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, Exception):
        return False

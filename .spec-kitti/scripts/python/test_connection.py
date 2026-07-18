#!/usr/bin/env python3
"""
Test de conexión a Jira y Confluence
Verifica que las credenciales funcionen antes de ejecutar sync
"""

import os
import sys
import requests
from pathlib import Path

# Colores para terminal
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def load_env_file(env_path: Path):
    """Carga variables desde archivo .env"""
    if not env_path.exists():
        return False
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                if value:  # Solo setear si no está vacío
                    os.environ[key.strip()] = value
    return True


def test_jira_connection(base_url: str, email: str, api_token: str) -> bool:
    """Prueba conexión a Jira"""
    try:
        print(f"{BLUE}📡 Probando conexión a Jira...{NC}")
        print(f"   URL: {base_url}")
        print(f"   Email: {email}")
        
        # Test endpoint: /rest/api/2/myself
        url = f"{base_url}/rest/api/2/myself"
        response = requests.get(
            url,
            auth=(email, api_token),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Conexión a Jira exitosa{NC}")
            print(f"   Usuario: {data.get('displayName', 'Unknown')}")
            print(f"   Email: {data.get('emailAddress', email)}")
            return True
        elif response.status_code == 401:
            print(f"{RED}❌ Error de autenticación (401){NC}")
            print(f"   Credenciales inválidas. Verifica:")
            print(f"   - JIRA_EMAIL es correcto")
            print(f"   - JIRA_API_TOKEN es válido")
            return False
        elif response.status_code == 403:
            print(f"{RED}❌ Acceso denegado (403){NC}")
            print(f"   El usuario no tiene permisos suficientes")
            return False
        else:
            print(f"{RED}❌ Error {response.status_code}{NC}")
            print(f"   {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ No se puede conectar{NC}")
        print(f"   Verifica que JIRA_BASE_URL sea correcto")
        print(f"   Verifica tu conexión a internet")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{NC}")
        return False


def test_confluence_connection(base_url: str, email: str, api_token: str, space_key: str) -> bool:
    """Prueba conexión a Confluence"""
    try:
        print(f"\n{BLUE}📡 Probando conexión a Confluence...{NC}")
        print(f"   URL: {base_url}/wiki")
        print(f"   Space: {space_key}")
        
        # Test endpoint: /wiki/rest/api/space/{spaceKey}
        url = f"{base_url}/wiki/rest/api/space/{space_key}"
        response = requests.get(
            url,
            auth=(email, api_token),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Conexión a Confluence exitosa{NC}")
            print(f"   Space: {data.get('name', space_key)}")
            print(f"   Tipo: {data.get('type', 'unknown')}")
            return True
        elif response.status_code == 401:
            print(f"{RED}❌ Error de autenticación (401){NC}")
            print(f"   Credenciales inválidas")
            return False
        elif response.status_code == 404:
            print(f"{YELLOW}⚠️  Space '{space_key}' no encontrado{NC}")
            print(f"   Verifica que CONFLUENCE_SPACE_KEY sea correcto")
            return False
        else:
            print(f"{RED}❌ Error {response.status_code}{NC}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{RED}❌ No se puede conectar a Confluence{NC}")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{NC}")
        return False


def main():
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  Spec-Kitti - Test de Conexión a Atlassian{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    # Cargar .env
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env"
    
    if env_file.exists():
        load_env_file(env_file)
        print(f"{GREEN}✓{NC} Archivo .env cargado desde: {env_file}\n")
    else:
        print(f"{YELLOW}⚠️  Archivo .env no encontrado en: {env_file}{NC}")
        print(f"   Usando variables de entorno del sistema\n")
    
    # Obtener credenciales
    email = os.getenv('JIRA_EMAIL', '').strip()
    api_token = os.getenv('JIRA_API_TOKEN', '').strip()
    base_url = os.getenv('JIRA_BASE_URL', '').strip().rstrip('/')
    space_key = os.getenv('CONFLUENCE_SPACE_KEY', '').strip()
    
    # Validar
    missing = []
    if not email:
        missing.append('JIRA_EMAIL')
    if not api_token:
        missing.append('JIRA_API_TOKEN')
    if not base_url:
        missing.append('JIRA_BASE_URL')
    
    if missing:
        print(f"{RED}❌ Faltan configuraciones requeridas:{NC}")
        for var in missing:
            print(f"   - {var}")
        print(f"\n{YELLOW}Edita el archivo .env y completa los valores{NC}\n")
        return 1
    
    # Test Jira
    jira_ok = test_jira_connection(base_url, email, api_token)
    
    # Test Confluence (solo si space_key está configurado)
    confluence_ok = True
    if space_key:
        confluence_ok = test_confluence_connection(base_url, email, api_token, space_key)
    else:
        print(f"\n{YELLOW}ℹ️  CONFLUENCE_SPACE_KEY no configurado - saltando test de Confluence{NC}")
    
    # Resumen
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  Resumen{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    if jira_ok and confluence_ok:
        print(f"{GREEN}✅ Todas las conexiones exitosas{NC}")
        print(f"\n{GREEN}🚀 Puedes ejecutar:{NC}")
        print(f"   ./scripts/bash/spec-kitti-sync.sh --epic-key TU-EPIC-KEY\n")
        return 0
    else:
        print(f"{RED}❌ Algunas conexiones fallaron{NC}")
        if not jira_ok:
            print(f"   - Jira: {RED}FALLÓ{NC}")
        if not confluence_ok:
            print(f"   - Confluence: {RED}FALLÓ{NC}")
        print(f"\n{YELLOW}Revisa las credenciales en .env y vuelve a intentar{NC}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())



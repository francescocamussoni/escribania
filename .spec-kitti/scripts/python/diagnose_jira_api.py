#!/usr/bin/env python3
"""
Diagnóstico completo de acceso a APIs de Jira
Identifica qué endpoints están disponibles y cuáles están bloqueados
"""

import os
import sys
import requests
from pathlib import Path

# Colores
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


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
                if value:
                    os.environ[key.strip()] = value
    return True


def test_endpoint(name, url, auth, method='GET', params=None, expected_codes=[200]):
    """Prueba un endpoint de la API"""
    try:
        if method == 'GET':
            response = requests.get(url, auth=auth, params=params, timeout=10)
        else:
            response = requests.post(url, auth=auth, json=params, timeout=10)
        
        status = response.status_code
        
        if status in expected_codes:
            print(f"{GREEN}✅ {name}{NC}")
            print(f"   Status: {status}")
            return True
        elif status == 401:
            print(f"{RED}❌ {name}{NC}")
            print(f"   Status: {status} - Credenciales inválidas")
            return False
        elif status == 403:
            print(f"{YELLOW}⚠️  {name}{NC}")
            print(f"   Status: {status} - Acceso denegado (permisos insuficientes)")
            return False
        elif status == 404:
            print(f"{YELLOW}⚠️  {name}{NC}")
            print(f"   Status: {status} - Endpoint no encontrado")
            return False
        elif status == 410:
            print(f"{RED}❌ {name}{NC}")
            print(f"   Status: {status} - Endpoint DESHABILITADO/DEPRECADO")
            return False
        else:
            print(f"{YELLOW}⚠️  {name}{NC}")
            print(f"   Status: {status}")
            return False
    
    except Exception as e:
        print(f"{RED}❌ {name}{NC}")
        print(f"   Error: {e}")
        return False


def main():
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  Diagnóstico de APIs de Jira{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    # Cargar .env
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env"
    
    if env_file.exists():
        load_env_file(env_file)
        print(f"{GREEN}✓{NC} Archivo .env cargado\n")
    
    # Obtener credenciales
    email = os.getenv('JIRA_EMAIL', '').strip()
    api_token = os.getenv('JIRA_API_TOKEN', '').strip()
    base_url = os.getenv('JIRA_BASE_URL', '').strip().rstrip('/')
    
    if not all([email, api_token, base_url]):
        print(f"{RED}❌ Faltan credenciales en .env{NC}\n")
        return 1
    
    print(f"URL Base: {base_url}")
    print(f"Email: {email}\n")
    
    auth = (email, api_token)
    results = {}
    
    # ========== TESTS DE API ==========
    
    print(f"{BLUE}--- Autenticación Básica ---{NC}")
    results['auth'] = test_endpoint(
        "GET /rest/api/2/myself",
        f"{base_url}/rest/api/2/myself",
        auth
    )
    print()
    
    print(f"{BLUE}--- API de Búsqueda (Search) ---{NC}")
    results['search_v2'] = test_endpoint(
        "GET /rest/api/2/search",
        f"{base_url}/rest/api/2/search",
        auth,
        params={'jql': 'project = PIANAR', 'maxResults': 1}
    )
    
    results['search_v3'] = test_endpoint(
        "GET /rest/api/3/search",
        f"{base_url}/rest/api/3/search",
        auth,
        params={'jql': 'project = PIANAR', 'maxResults': 1}
    )
    print()
    
    print(f"{BLUE}--- API Agile ---{NC}")
    results['agile_boards'] = test_endpoint(
        "GET /rest/agile/1.0/board",
        f"{base_url}/rest/agile/1.0/board",
        auth
    )
    print()
    
    print(f"{BLUE}--- API de Issues ---{NC}")
    results['get_issue'] = test_endpoint(
        "GET /rest/api/2/issue/{key}",
        f"{base_url}/rest/api/2/issue/PIANAR-2248",
        auth
    )
    
    results['get_issue_v3'] = test_endpoint(
        "GET /rest/api/3/issue/{key}",
        f"{base_url}/rest/api/3/issue/PIANAR-2248",
        auth
    )
    print()
    
    print(f"{BLUE}--- API de Proyectos ---{NC}")
    results['get_project'] = test_endpoint(
        "GET /rest/api/2/project",
        f"{base_url}/rest/api/2/project",
        auth
    )
    print()
    
    # ========== RESUMEN ==========
    
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  Resumen del Diagnóstico{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    working = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"Endpoints funcionando: {working}/{total}\n")
    
    # Diagnóstico específico
    if not results.get('search_v2') and not results.get('search_v3'):
        print(f"{RED}⚠️  PROBLEMA CRÍTICO: API de búsqueda deshabilitada{NC}")
        print(f"\n{YELLOW}Causas posibles:{NC}")
        print(f"  1. Tu instancia de Jira tiene la API de búsqueda deshabilitada")
        print(f"  2. El proyecto es 'Team-Managed' (simplified)")
        print(f"  3. Tu usuario no tiene permisos de 'Browse Projects'")
        print(f"\n{YELLOW}Soluciones:{NC}")
        print(f"  1. Contacta al administrador de Jira para habilitar la API")
        print(f"  2. Migra el proyecto a 'Company-Managed'")
        print(f"  3. Pide permisos de administrador en el proyecto")
        print(f"  4. Usa --issue-keys como workaround temporal:\n")
        print(f"     {GREEN}./scripts/bash/spec-kitti-sync.sh --epic-key PIANAR-2248 \\{NC}")
        print(f"     {GREEN}  --issue-keys \"PIANAR-2260,PIANAR-2334\"{NC}\n")
    
    if not results.get('agile_boards'):
        print(f"{YELLOW}⚠️  API Agile no disponible{NC}")
        print(f"  No es crítico, pero limita algunas funcionalidades\n")
    
    if results.get('auth') and results.get('get_issue'):
        print(f"{GREEN}✅ API básica funciona correctamente{NC}")
        print(f"  Puedes descargar issues individuales\n")
    
    # Recomendación final
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{BLUE}  Recomendación{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    if working < 3:
        print(f"{YELLOW}Tu instancia de Jira tiene restricciones importantes.{NC}")
        print(f"\n📧 Email para enviar al administrador de Jira:\n")
        print(f"---")
        print(f"Asunto: Solicitud de habilitación de APIs de Jira")
        print(f"\nHola,")
        print(f"\nNecesito acceso a las siguientes APIs REST de Jira para integración")
        print(f"con herramientas de desarrollo:")
        print(f"\n- /rest/api/2/search (o /rest/api/3/search)")
        print(f"- /rest/agile/1.0/* endpoints")
        print(f"\nActualmente estos endpoints retornan error 410 (Gone) lo que indica")
        print(f"que están deshabilitados. ¿Podrían habilitarlos o indicarme cómo")
        print(f"obtener los permisos necesarios?")
        print(f"\nProyecto: PIANAR")
        print(f"Usuario: {email}")
        print(f"\nGracias!")
        print(f"---\n")
    else:
        print(f"{GREEN}¡Tu configuración se ve bien!{NC}")
        print(f"Deberías poder usar spec-kitti sin problemas.\n")
    
    return 0 if working >= 3 else 1


if __name__ == '__main__':
    sys.exit(main())



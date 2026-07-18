#!/usr/bin/env python3
"""
analyze_test_failure.py
Analizador inteligente de fallos de pruebas para Itti-Kit

Parsea logs de frameworks de testing y extrae información accionable
para el Agente Executor, facilitando la auto-corrección.

Soporta:
- pytest
- unittest
- jest
- go test

Uso:
    python analyze_test_failure.py <log_file>
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# PATRONES DE DETECCIÓN DE ERRORES
# ============================================================================

ERROR_PATTERNS = {
    "AssertionError": r"AssertionError:?\s*(.+)",
    "AttributeError": r"AttributeError:?\s*(.+)",
    "TypeError": r"TypeError:?\s*(.+)",
    "ValueError": r"ValueError:?\s*(.+)",
    "KeyError": r"KeyError:?\s*(.+)",
    "ImportError": r"ImportError:?\s*(.+)",
    "ModuleNotFoundError": r"ModuleNotFoundError:?\s*(.+)",
    "NameError": r"NameError:?\s*(.+)",
    "IndexError": r"IndexError:?\s*(.+)",
}

ASSERTION_PATTERNS = [
    r"assert\s+(.+)",
    r"self\.assert\w+\((.+)\)",
    r"expect\((.+)\)\.to",
]

FUNCTION_PATTERN = r"in\s+(\w+)\s*\("
FILE_LINE_PATTERN = r'File\s+"([^"]+)",\s+line\s+(\d+)'


# ============================================================================
# FUNCIONES DE ANÁLISIS
# ============================================================================

def extract_error_type(content: str) -> str:
    """Identifica el tipo de error principal."""
    for error_type, pattern in ERROR_PATTERNS.items():
        if re.search(pattern, content, re.MULTILINE):
            return error_type
    return "Unknown"


def extract_error_message(content: str, error_type: str) -> str:
    """Extrae el mensaje de error completo."""
    if error_type == "Unknown":
        return "No error message found"
    
    pattern = ERROR_PATTERNS.get(error_type)
    match = re.search(pattern, content, re.MULTILINE)
    
    if match:
        return match.group(1).strip()
    return "Could not extract error message"


def extract_assertion(content: str) -> Optional[str]:
    """Extrae la aserción que falló."""
    for pattern in ASSERTION_PATTERNS:
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def extract_function_name(content: str) -> str:
    """Identifica la función que causó el error."""
    match = re.search(FUNCTION_PATTERN, content)
    if match:
        return match.group(1)
    return "N/A"


def extract_file_and_line(content: str) -> Tuple[Optional[str], Optional[int]]:
    """Extrae el archivo y línea del error."""
    match = re.search(FILE_LINE_PATTERN, content)
    if match:
        return match.group(1), int(match.group(2))
    return None, None


def extract_stack_trace(content: str) -> List[str]:
    """Extrae las líneas relevantes del stack trace."""
    lines = content.split('\n')
    trace_lines = []
    
    in_trace = False
    for line in lines:
        if 'Traceback' in line or 'File "' in line:
            in_trace = True
        
        if in_trace:
            trace_lines.append(line)
            
            # Detenerse en el mensaje de error
            if any(error in line for error in ERROR_PATTERNS.keys()):
                break
    
    return trace_lines[:10]  # Limitar a 10 líneas


# ============================================================================
# GENERACIÓN DE SUGERENCIAS
# ============================================================================

def generate_suggestion(error_type: str, error_message: str, assertion: Optional[str]) -> str:
    """Genera una sugerencia de corrección basada en el tipo de error."""
    suggestions = []
    
    # Sugerencias por tipo de error
    if error_type == "AssertionError":
        suggestions.append("❌ **Aserción fallida**: La expresión evaluó a False.")
        
        if assertion:
            suggestions.append(f"   Aserción: `{assertion}`")
        
        if "==" in error_message or "!=" in error_message:
            suggestions.append("   💡 **Sugerencia**: Compara el valor retornado con el esperado. Usa `print()` o `logging` para debug.")
        
        if "None" in error_message:
            suggestions.append("   💡 **Sugerencia**: La función retorna `None`. Verifica que el `return` esté presente y correcto.")
    
    elif error_type == "AttributeError":
        suggestions.append("❌ **Atributo no encontrado**: Objeto no tiene el atributo/método esperado.")
        
        if "NoneType" in error_message:
            suggestions.append("   💡 **Sugerencia**: El objeto es `None`. Verifica que la inicialización sea correcta.")
        else:
            suggestions.append("   💡 **Sugerencia**: Revisa typos en nombres de atributos/métodos o verifica que estén definidos.")
    
    elif error_type == "TypeError":
        suggestions.append("❌ **Error de tipo**: Operación con tipo de dato incorrecto.")
        
        if "argument" in error_message.lower():
            suggestions.append("   💡 **Sugerencia**: Argumentos de función incorrectos. Verifica firma del método y tipos de parámetros.")
        elif "unsupported operand" in error_message.lower():
            suggestions.append("   💡 **Sugerencia**: Operación no soportada para estos tipos. Convierte tipos antes de operar.")
        else:
            suggestions.append("   💡 **Sugerencia**: Usa `type()` para verificar tipos y añade conversiones si es necesario.")
    
    elif error_type == "ValueError":
        suggestions.append("❌ **Valor incorrecto**: Valor fuera de rango o formato inválido.")
        suggestions.append("   💡 **Sugerencia**: Valida inputs antes de procesar. Usa try-except para manejar conversiones.")
    
    elif error_type == "KeyError":
        suggestions.append("❌ **Clave no existe**: Acceso a clave inexistente en diccionario.")
        suggestions.append("   💡 **Sugerencia**: Usa `.get(key, default)` en lugar de `[key]` o verifica con `if key in dict`.")
    
    elif error_type == "ImportError" or error_type == "ModuleNotFoundError":
        suggestions.append("❌ **Módulo no encontrado**: Import falló.")
        suggestions.append("   💡 **Sugerencia**: Verifica que el paquete esté instalado (`pip list`) y el path sea correcto.")
    
    elif error_type == "NameError":
        suggestions.append("❌ **Nombre no definido**: Variable o función usada sin definir.")
        suggestions.append("   💡 **Sugerencia**: Verifica typos o que la variable esté definida antes de usarse.")
    
    elif error_type == "IndexError":
        suggestions.append("❌ **Índice fuera de rango**: Acceso a índice que no existe en lista/array.")
        suggestions.append("   💡 **Sugerencia**: Verifica el tamaño de la lista antes de acceder o usa try-except.")
    
    else:
        suggestions.append("❌ **Error desconocido**: Revisa el stack trace para más detalles.")
    
    return "\n".join(suggestions)


def analyze_common_patterns(content: str) -> List[str]:
    """Detecta patrones comunes de errores."""
    patterns = []
    
    # Comparación de None
    if re.search(r"None.*==", content) or re.search(r"==.*None", content):
        patterns.append("⚠️  **Patrón detectado**: Comparación con None. Usa `is None` en lugar de `== None`.")
    
    # Uso de mutable default
    if "mutable default argument" in content.lower():
        patterns.append("⚠️  **Patrón detectado**: Argumento mutable por defecto. Usa `None` y crea dentro de función.")
    
    # División por cero
    if "division by zero" in content.lower():
        patterns.append("⚠️  **Patrón detectado**: División por cero. Agrega validación antes de dividir.")
    
    # Encoding issues
    if "codec" in content.lower() or "encoding" in content.lower():
        patterns.append("⚠️  **Patrón detectado**: Problema de encoding. Especifica `encoding='utf-8'` al leer/escribir.")
    
    return patterns


# ============================================================================
# ANÁLISIS PRINCIPAL
# ============================================================================

def analyze_pytest_log(log_file: str) -> Dict:
    """
    Analiza un log de pytest y extrae información estructurada del error.
    """
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        return {
            "error": f"Log file not found: {log_file}",
            "error_type": "FileNotFound",
        }
    
    error_type = extract_error_type(content)
    error_message = extract_error_message(content, error_type)
    assertion = extract_assertion(content)
    function_name = extract_function_name(content)
    file_path, line_number = extract_file_and_line(content)
    stack_trace = extract_stack_trace(content)
    suggestion = generate_suggestion(error_type, error_message, assertion)
    common_patterns = analyze_common_patterns(content)
    
    return {
        "error_type": error_type,
        "error_message": error_message,
        "assertion_failure": assertion or "N/A",
        "affected_function": function_name,
        "file": file_path or "N/A",
        "line": line_number or "N/A",
        "suggestion": suggestion,
        "common_patterns": common_patterns,
        "stack_trace": stack_trace,
    }


def format_analysis(analysis: Dict) -> str:
    """Formatea el análisis para ser legible por humanos y LLMs."""
    output = []
    
    # Header
    output.append("\n" + "="*60)
    output.append(f"🔍 ANÁLISIS DE FALLO DE PRUEBA")
    output.append("="*60 + "\n")
    
    # Información básica
    output.append(f"- **Tipo de Error**: {analysis['error_type']}")
    output.append(f"- **Mensaje**: {analysis['error_message']}")
    output.append(f"- **Archivo**: {analysis['file']} (línea {analysis['line']})")
    output.append(f"- **Función**: `{analysis['affected_function']}`")
    
    if analysis['assertion_failure'] != "N/A":
        output.append(f"- **Aserción Fallida**: `{analysis['assertion_failure']}`")
    
    output.append("")
    
    # Sugerencias
    output.append("## 💡 Sugerencias de Corrección\n")
    output.append(analysis['suggestion'])
    output.append("")
    
    # Patrones comunes
    if analysis['common_patterns']:
        output.append("## ⚠️  Patrones Comunes Detectados\n")
        for pattern in analysis['common_patterns']:
            output.append(pattern)
        output.append("")
    
    # Stack trace (opcional, para referencia)
    if analysis['stack_trace']:
        output.append("## 📚 Stack Trace Relevante\n")
        output.append("```")
        for line in analysis['stack_trace']:
            output.append(line)
        output.append("```")
        output.append("")
    
    output.append("="*60)
    
    return "\n".join(output)


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_test_failure.py <log_file>", file=sys.stderr)
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    # Analizar
    analysis = analyze_pytest_log(log_file)
    
    # Formatear y mostrar
    formatted = format_analysis(analysis)
    print(formatted)


if __name__ == "__main__":
    main()


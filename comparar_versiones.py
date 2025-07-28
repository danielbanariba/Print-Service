def mostrar_diferencias():
    print("=== COMPARACIÓN DE VERSIONES ===\n")
    
    print("1. VERSIÓN ORIGINAL DE PRODUCCIÓN:")
    print("-" * 50)
    print('cadena=cadena.replace("<BARCODE_CODE39>","\\u001d\\u0068\\u0064\\u001d\\u0077\\u0002\\u001d\\u0048\\u0002\\u001d\\u0066\\u0000\\u001d\\u006b\\u0004")')
    print("\nPROBLEMA:")
    print("- Solo reemplaza el tag <BARCODE_CODE39>")
    print("- NO incluye los datos del código (ej: *123456789*)")
    print("- NO incluye el terminador NUL (\\u0000)")
    print("- NO maneja el <NL> después de los datos")
    print("\nRESULTADO: El texto '<BARCODE_CODE39>*123456789*' se imprime literalmente")
    
    print("\n\n2. VERSIÓN CORREGIDA:")
    print("-" * 50)
    print("""
import re

# Procesar CODE39 ANTES de reemplazar <NL>
if '<BARCODE_CODE39>' in cadena:
    pattern = r'<BARCODE_CODE39>(.*?)<NL>'
    
    def replace_code39(match):
        barcode_data = match.group(1)  # Extrae *123456789*
        
        commands = ""
        commands += "\\u001d\\u0068\\u0064"  # GS h 100 - Altura
        commands += "\\u001d\\u0077\\u0002"  # GS w 2 - Ancho
        commands += "\\u001d\\u0048\\u0002"  # GS H 2 - HRI abajo
        commands += "\\u001d\\u0066\\u0000"  # GS f 0 - Fuente A
        commands += "\\u001d\\u006b\\u0004"  # GS k 4 - CODE39
        commands += barcode_data          # INCLUYE LOS DATOS
        commands += "\\u0000"              # INCLUYE TERMINADOR NUL
        commands += "\\n"                  # Nueva línea
        
        return commands
    
    cadena = re.sub(pattern, replace_code39, cadena)
""")
    
    print("\nVENTAJAS:")
    print("- Procesa códigos ANTES de reemplazar <NL>")
    print("- Extrae los datos del código de barras")
    print("- Incluye el terminador NUL requerido")
    print("- Maneja correctamente el patrón completo")
    print("\nRESULTADO: Imprime el código de barras correctamente")
    
    print("\n\n3. EJEMPLO DE PROCESAMIENTO:")
    print("-" * 50)
    print("Entrada: <BARCODE_CODE39>*123456789*<NL>")
    print("\nVersión original produce:")
    print("  [comandos]*123456789*")
    print("  (Los datos se imprimen como texto)")
    print("\nVersión corregida produce:")
    print("  [comandos + *123456789* + NUL + LF]")
    print("  (Se genera el código de barras)")


def ejemplo_hex():
    print("\n\n4. COMPARACIÓN EN HEXADECIMAL:")
    print("-" * 50)
    
    # Lo que genera la versión original (incompleto)
    original = "\u001d\u0068\u0064\u001d\u0077\u0002\u001d\u0048\u0002\u001d\u0066\u0000\u001d\u006b\u0004"
    print("Versión original (solo comandos):")
    print(' '.join(f'{ord(c):02x}' for c in original))
    print(f"Total: {len(original)} bytes")
    
    # Lo que debe generar (completo)
    correcto = "\u001d\u0068\u0064\u001d\u0077\u0002\u001d\u0048\u0002\u001d\u0066\u0000\u001d\u006b\u0004*123456789*\u0000\n"
    print("\nVersión corregida (comandos + datos + NUL + LF):")
    print(' '.join(f'{ord(c):02x}' for c in correcto))
    print(f"Total: {len(correcto)} bytes")
    
    print("\nDiferencia:")
    print("Faltan en la original: datos + NUL + LF")
    print(f"Bytes faltantes: {len(correcto) - len(original)}")


if __name__ == "__main__":
    mostrar_diferencias()
    ejemplo_hex()
    
    print("\n\n=== RECOMENDACIÓN ===")
    print("Usa TSSPrint_standalone_mejorado.py para producción")
    print("Esta versión es compatible con el formato actual pero")
    print("procesa correctamente los códigos de barras.")
import win32print
import time

def test_basico_te200():
    """Test súper básico para TSC TE200"""
    
    impresora = "ETIQUETA"  # Cambiar si es necesario
    
    print("\n" + "="*60)
    print("TEST BÁSICO TSC TE200")
    print("="*60)
    
    # Comando más básico posible
    comandos = "CLS\r\nTEXT 10,10,\"1\",0,1,1,\"TEST\"\r\nPRINT 1\r\n"
    
    print("\nEnviando comando más básico:")
    print(comandos.replace('\r\n', '\\r\\n'))
    
    try:
        # Abrir impresora
        p = win32print.OpenPrinter(impresora)
        
        # Obtener info
        info = win32print.GetPrinter(p, 2)
        print(f"\nImpresora: {info['pPrinterName']}")
        print(f"Puerto: {info['pPortName']}")
        print(f"Driver: {info['pDriverName']}")
        print(f"Estado: {info['Status']}")
        
        # Enviar comando
        win32print.StartDocPrinter(p, 1, ("TestBasico", None, "RAW"))
        win32print.StartPagePrinter(p)
        win32print.WritePrinter(p, bytes(comandos, 'latin-1'))  # Probar con latin-1
        win32print.EndPagePrinter(p)
        win32print.EndDocPrinter(p)
        win32print.ClosePrinter(p)
        
        print("\n✓ Comando enviado")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    respuesta = input("\n¿Se imprimió algo? (s/n): ")
    return respuesta.lower() == 's'

def test_formato_alternativo():
    """Prueba formato alternativo para TE200"""
    
    impresora = "ETIQUETA"
    
    print("\n" + "="*60)
    print("TEST FORMATO ALTERNATIVO")
    print("="*60)
    
    # Algunos TE200 necesitan inicialización diferente
    tests = [
        # Test 1: Con comillas diferentes
        "CLS\nTEXT 10,10,1,0,1,1,TEST1\nPRINT 1\n",
        
        # Test 2: Con SIZE mínimo
        "SIZE 30,20\nCLS\nTEXT 10,10,\"1\",0,1,1,\"TEST2\"\nPRINT 1\n",
        
        # Test 3: Formato EPL2
        "N\nA10,10,0,1,1,1,N,\"TEST3\"\nP1\n",
        
        # Test 4: Con inicialización CODEPAGE
        "CODEPAGE 850\nCLS\nTEXT 10,10,\"1\",0,1,1,\"TEST4\"\nPRINT 1\n"
    ]
    
    for i, cmd in enumerate(tests, 1):
        print(f"\n--- Test {i} ---")
        print(f"Comando: {cmd.replace(chr(10), '\\n')}")
        
        try:
            p = win32print.OpenPrinter(impresora)
            win32print.StartDocPrinter(p, 1, (f"Test{i}", None, "RAW"))
            win32print.StartPagePrinter(p)
            win32print.WritePrinter(p, bytes(cmd, 'utf-8'))
            win32print.EndPagePrinter(p)
            win32print.EndDocPrinter(p)
            win32print.ClosePrinter(p)
            
            time.sleep(2)  # Esperar 2 segundos
            
            resp = input(f"¿Test {i} imprimió algo? (s/n): ")
            if resp.lower() == 's':
                print(f"\n✅ FORMATO ENCONTRADO: Test {i}")
                with open("formato_te200_ok.txt", "w") as f:
                    f.write(f"Formato que funciona:\n{cmd}")
                return True
                
        except Exception as e:
            print(f"Error: {e}")
    
    return False

# Ejecutar tests
if __name__ == "__main__":
    print("DIAGNÓSTICO RÁPIDO TSC TE200\n")
    
    # Primero el test básico
    if test_basico_te200():
        print("\n✅ La impresora responde a comandos básicos")
    else:
        print("\n❌ La impresora no responde")
        print("\nPosibles soluciones:")
        print("1. Verificar que la impresora esté encendida y lista")
        print("2. Verificar el cable USB")
        print("3. En la impresora, mantener presionado FEED por 5 segundos para calibrar")
        print("4. Reinstalar el driver TSC")
        
        # Intentar formato alternativo
        print("\n¿Quieres probar formatos alternativos? (s/n): ", end="")
        if input().lower() == 's':
            test_formato_alternativo()
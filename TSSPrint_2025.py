from websocket_server import WebsocketServer
import os, sys
import win32print
import json
import re

#FUNCIONES IMPRESION

def reemplazar(cadena):
    print("\n=== PROCESANDO CONTENIDO ===")
    
    # IMPORTANTE: Procesar códigos de barras ANTES de reemplazar <NL>
    if '<BARCODE_CODE39>' in cadena:
        print(f"Códigos de barras encontrados: {cadena.count('<BARCODE_CODE39>')}")
        
        # Patrón que busca <BARCODE_CODE39>datos<NL>
        pattern = r'<BARCODE_CODE39>(.*?)<NL>'
        
        def replace_barcode(match):
            barcode_data = match.group(1)
            print(f"  Procesando código: '{barcode_data}'")
            
            # Crear comandos ESC/POS
            commands = ""
            commands += "\u001d\u0068\u0064"  # GS h 100 - Altura
            commands += "\u001d\u0077\u0002"  # GS w 2 - Ancho
            commands += "\u001d\u0048\u0002"  # GS H 2 - HRI abajo
            commands += "\u001d\u006b\u0004"  # GS k 4 - CODE39
            commands += barcode_data          # Datos
            commands += "\u0000"              # NUL terminator
            commands += "\n"                  # Nueva línea
            
            return commands
        
        # Reemplazar todos los códigos de barras
        cadena = re.sub(pattern, replace_barcode, cadena)
        print(f"Códigos procesados correctamente")
    
    # Ahora procesar el resto de etiquetas
    cadena = cadena.replace("<ESC>", "\u001b@")
    cadena = cadena.replace("<NL>", "\n")
    cadena = cadena.replace("<TITULO>", "\u0038")
    cadena = cadena.replace("<FUENTE>", "\u0000")
    cadena = cadena.replace("<DOBLE>", "\u0018")
    cadena = cadena.replace("<TXT_NORMAL>", "\u001b\u0021\u0000")
    cadena = cadena.replace("<TXT_2HEIGHT>", "\u001b\u0021\u0010")
    cadena = cadena.replace("<TTXT_2WIDTH>", "\u001b\u0021\u0020")
    cadena = cadena.replace("<TXT_4SQUARE>", "\u001b\u0021\u0030")
    cadena = cadena.replace("<TXT_UNDERL_OFF>", "\u001b\u002d\u0000")
    cadena = cadena.replace("<TXT_UNDERL_ON>", "\u001b\u002d\u0001")
    cadena = cadena.replace("<TXT_UNDERL2_ON>", "\u001b\u002d\u0002")
    cadena = cadena.replace("<TXT_BOLD_OFF>", "\u001b\u0045\u0000")
    cadena = cadena.replace("<NEGRITA>", "\u001b\u0045\u0001")
    cadena = cadena.replace("<NO_NEGRITA>", "\u001b\u0045\u0000")
    cadena = cadena.replace("<TXT_FONT_A>", "\u001b\u004d\u0048")
    cadena = cadena.replace("<TXT_FONT_B>", "\u001b\u004d\u0001")
    cadena = cadena.replace("<TXT_ALIGN_LT>", "\u001b\u0061\u0000")
    cadena = cadena.replace("<TXT_ALIGN_CT>", "\u001b\u0061\u0001")
    cadena = cadena.replace("<TXT_ALIGN_RT>", "\u001b\u0061\u0002")
    cadena = cadena.replace("<BEEPER>", "\u001b\u0042\u0005\u0009")
    cadena = cadena.replace("<LINE_SPACE_24>", "\u001b\u0033\u0018")
    cadena = cadena.replace("<LINE_SPACE_30>", "\u001b\u0033\u001E")
    cadena = cadena.replace("<CD_KICK_2>", "\u001b\u0070\u0000")
    cadena = cadena.replace("<CD_KICK_5>", "\u001b\u0070\u0001")
    cadena = cadena.replace("<PAPER_FULL_CUT>", "\u001d\u0056\u0000")
    cadena = cadena.replace("<PAPER_PART_CUT>", "\u001d\u0056\u0001")
    
    # Procesar códigos de caracteres
    cadena = cadena.replace("<CHARCODE_PC437>", "\u001b\u0074\u0000")
    cadena = cadena.replace("<CHARCODE_JIS>", "\u001b\u0074\u0001")
    cadena = cadena.replace("<CHARCODE_PC850>", "\u001b\u0074\u0002")
    cadena = cadena.replace("<CHARCODE_PC860>", "\u001b\u0074\u0003")
    cadena = cadena.replace("<CHARCODE_PC863>", "\u001b\u0074\u0004")
    cadena = cadena.replace("<CHARCODE_PC865>", "\u001b\u0074\u0005")
    cadena = cadena.replace("<CHARCODE_WEU>", "\u001b\u0074\u0006")
    cadena = cadena.replace("<CHARCODE_GREEK>", "\u001b\u0074\u0007")
    cadena = cadena.replace("<CHARCODE_HEBREW>", "\u001b\u0074\u0008")
    cadena = cadena.replace("<CHARCODE_PC1252>", "\u001b\u0074\u0010")
    cadena = cadena.replace("<CHARCODE_PC866>", "\u001b\u0074\u0012")
    cadena = cadena.replace("<CHARCODE_PC852>", "\u001b\u0074\u0013")
    cadena = cadena.replace("<CHARCODE_PC858>", "\u001b\u0074\u0014")
    
    # Otros formatos de código de barras
    cadena = cadena.replace("<BARCODE_TXT_OFF>", "\u001d\u0048\u0000")
    cadena = cadena.replace("<BARCODE_TXT_ABV>", "\u001d\u0048\u0001")
    cadena = cadena.replace("<BARCODE_TXT_BLW>", "\u001d\u0048\u0002")
    cadena = cadena.replace("<BARCODE_TXT_BTH>", "\u001d\u0048\u0003")
    cadena = cadena.replace("<BARCODE_FONT_A>", "\u001d\u0066\u0000")
    cadena = cadena.replace("<BARCODE_FONT_B>", "\u001d\u0066\u0001")
    cadena = cadena.replace("<BARCODE_HEIGHT>", "\u001d\u0068\u0064")
    cadena = cadena.replace("<BARCODE_WIDTH>", "\u001d\u0077\u0003")
    
    # Densidad de impresión
    cadena = cadena.replace("<PD_N50>", "\u001d\u007c\u0000")
    cadena = cadena.replace("<PD_N37>", "\u001d\u007c\u0001")
    cadena = cadena.replace("<PD_N25>", "\u001d\u007c\u0002")
    cadena = cadena.replace("<PD_N12>", "\u001d\u007c\u0003")
    cadena = cadena.replace("<PD_0>", "\u001d\u007c\u0004")
    cadena = cadena.replace("<PD_P50>", "\u001d\u007c\u0008")
    cadena = cadena.replace("<PD_P37>", "\u001d\u007c\u0007")
    cadena = cadena.replace("<PD_P25>", "\u001d\u007c\u0006")
    cadena = cadena.replace("<PD_P12>", "\u001d\u007c\u0005")
    
    # Inicializar impresora al principio
    cadena = "\u001b@" + cadena
    
    return cadena


def imprimir(contenido, impresora):
    p = win32print.OpenPrinter(impresora)
    new_contenido = reemplazar(contenido)
    
    print(f"Imprimiendo en: {impresora}")
    
    job = win32print.StartDocPrinter(p, 1, ("printer job", None, "RAW"))
    win32print.StartPagePrinter(p)
    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
    win32print.EndPagePrinter(p)
    win32print.EndDocPrinter(p)
    win32print.ClosePrinter(p)


def message_received(client, server, message):
    JSON = json.loads(message)
    contenido = JSON['contenido']
    impresora = JSON['impresora']
    
    if isinstance(contenido, list):
        processed_contenido = []
        for item in contenido:
            if isinstance(item, dict) and 'text' in item:
                processed_contenido.append(item['text'])
            elif isinstance(item, dict) and 'barcode' in item:
                barcode_type = item.get('type', '<BARCODE_CODE39>')
                barcode_data = item.get('barcode', '')
                if barcode_data:
                    processed_contenido.append(f"{barcode_type}{barcode_data}")
                else:
                    print("Warning: Barcode data is empty!")
            else:
                processed_contenido.append(str(item))
        contenido = ''.join(processed_contenido)
    
    imprimir(contenido, impresora)


PORT = 9000
HOST = "0.0.0.0"
server = WebsocketServer(host=HOST, port=PORT)
server.set_fn_message_received(message_received)

print("Servidor de impresión térmica iniciado")
print(f"Escuchando en {HOST}:{PORT}")
print("Versión corregida - Procesa códigos de barras ANTES de otras etiquetas")

server.run_forever()
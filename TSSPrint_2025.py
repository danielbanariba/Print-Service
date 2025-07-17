
from websocket_server import WebsocketServer
import os, sys
import win32print
import json


#INSTALAR PAQUETES
#pip install pywin32

#FUNCIONES IMPRESION

def reemplazar(cadena):

    # Secuencias de Control de Alimentacion
    cadena=cadena.replace("<ESC>", "\u001b@")
    cadena=cadena.replace("<NL>",'\n')

    # Formato de texto
    cadena=cadena.replace("<TITULO>","\u0038") # Texto titulo
    cadena=cadena.replace("<FUENTE>","\u0000") # Fuente de Texto
    cadena=cadena.replace("<DOBLE>","\u0018") # Tamano Doble de Texto
    cadena=cadena.replace("<TXT_NORMAL>","\u001b\u0021\u0000") # Texto Normal
    cadena=cadena.replace("<TXT_2HEIGHT>","\u001b\u0021\u0010") # Texto Doble Altura
    cadena=cadena.replace("<TTXT_2WIDTH>","\u001b\u0021\u0020") # Texto Ancho Doble
    cadena=cadena.replace("<TXT_4SQUARE>","\u001b\u0021\u0030") # Texto Area Cuadrado
    cadena=cadena.replace("<TXT_UNDERL_OFF>","\u001b\u002d\u0000") # Subrayado font OFF
    cadena=cadena.replace("<TXT_UNDERL_ON>","\u001b\u002d\u0001") # Subrayado font 1-dot ON
    cadena=cadena.replace("<TXT_UNDERL2_ON>","\u001b\u002d\u0002") # Subrayado font 2-dot ON
    cadena=cadena.replace("<TXT_BOLD_OFF>","\u001b\u0045\u0000") # Desactivar Negrita
    cadena=cadena.replace("<NEGRITA>","\u001b\u0045\u0001") # Activar Negrita
    cadena=cadena.replace("<NO_NEGRITA>", "\u001b\u0045\u0000")  # Deactivate bold formatting
    cadena=cadena.replace("<TXT_FONT_A>","\u001b\u004d\u0048") # Fuente tipo A
    cadena=cadena.replace("<TXT_FONT_B>","\u001b\u004d\u0001") # Fuente tipo B
    cadena=cadena.replace("<TXT_ALIGN_LT>","\u001b\u0061\u0000") # Justificacion Izquierda
    cadena=cadena.replace("<TXT_ALIGN_CT>","\u001b\u0061\u0001") # Texto Centrado
    cadena=cadena.replace("<TXT_ALIGN_RT>","\u001b\u0061\u0002") # Justificaion derecha

    # Beeper
    cadena=cadena.replace("<BEEPER>","\u001b\u0042\u0005\u0009") # Beeps 5 veces por cada 9*50ms

    # Lineas de Espacion
    cadena=cadena.replace("<LINE_SPACE_24>","\u001b\u0033, 24") # Establecer espaciado de linea en 24
    cadena=cadena.replace("<LINE_SPACE_30>","\u001b\u0033, 30") # Establecer espaciado de
    # Imagen
    cadena=cadena.replace("<SELECT_BIT_IMAGE_MODE>","\u001B\u002A, 33")

    # # Printer hardware
    # cadena=cadena.replace("<HW_INIT>","\u001b\u0040") # Limpiar Bufer y resetear modos

    # Caja Registradora linea en 30

    cadena=cadena.replace("<CD_KICK_2>","\u001b\u0070\u0000") # Enviar un pulse al pin 2 []
    cadena=cadena.replace("<CD_KICK_5>","\u001b\u0070\u0001") # Enviar un pulse al pin 5 []

    # Papel
    cadena=cadena.replace("<PAPER_FULL_CUT>","\u001d\u0056\u0000") # Corte total del papel
    cadena=cadena.replace("<PAPER_PART_CUT>","\u001d\u0056\u0001") # Corte parcial del papel

    # Tabla de Codigos de Caracteres
    cadena=cadena.replace("<CHARCODE_PC437>","\u001b\u0074\u0000") # USA){ Standard Europe
    cadena=cadena.replace("<CHARCODE_JIS>","\u001b\u0074\u0001") # Japones Katakana
    cadena=cadena.replace("<CHARCODE_PC850>","\u001b\u0074\u0002") # Multilingual
    cadena=cadena.replace("<CHARCODE_PC860>","\u001b\u0074\u0003") # Portugues
    cadena=cadena.replace("<CHARCODE_PC863>","\u001b\u0074\u0004") # Franco - Canadiense
    cadena=cadena.replace("<CHARCODE_PC865>","\u001b\u0074\u0005") # Nordic
    cadena=cadena.replace("CHARCODE_WEU>","\u001b\u0074\u0006") # Kanji Simplificado, Hirakana
    cadena=cadena.replace("<CHARCODE_GREEK>","\u001b\u0074\u0007") # Simplificado Kanji
    cadena=cadena.replace("<CHARCODE_HEBREW>","\u001b\u0074\u0008") # Simplified Kanji
    cadena=cadena.replace("<CHARCODE_PC1252>","\u001b\u0074\u0010") # Western European Windows Code Set
    cadena=cadena.replace("<CHARCODE_PC866>","\u001b\u0074\u0012") #  Cirillic //2
    cadena=cadena.replace("<CHARCODE_PC852>","\u001b\u0074\u0013") # Latin 2
    cadena=cadena.replace("<CHARCODE_PC858>","\u001b\u0074\u0014") # Euro
    cadena=cadena.replace("<CHARCODE_THAI42>","\u001b\u0074\u0015") # Thai character code 42
    cadena=cadena.replace("<CHARCODE_THAI11>","\u001b\u0074\u0016") # Thai character code 11
    cadena=cadena.replace("<CHARCODE_THAI13>","\u001b\u0074\u0017") # Thai character code 13
    cadena=cadena.replace("<CHARCODE_THAI14>","\u001b\u0074\u0018") # Thai character code 14
    cadena=cadena.replace("<CHARCODE_THAI16>","\u001b\u0074\u00119") # Thai character code 16
    cadena=cadena.replace("<CHARCODE_THAI17>", "\u001b\u0074\u001a") # Thai character code 17
    cadena=cadena.replace("CHARCODE_THAI18>","\u001b\u0074\u001b") # Thai character code 18

    # Formato de Codigo de Barra
    cadena=cadena.replace("<BARCODE_TXT_OFF>","\u001d\u0048\u0000") # HRI ImprimirCodigoBarra chars OFF
    cadena=cadena.replace("<BARCODE_TXT_ABV>","\u001d\u0048\u0001") # HRI ImprimirCodigoBarra chars arriba
    cadena=cadena.replace("<BARCODE_TXT_BLW>","\u001d\u0048\u0002") # HRI ImprimirCodigoBarra chars abajo
    cadena=cadena.replace("<BARCODE_TXT_BTH>","\u001d\u0048\u0003") # HRI ImprimirCodigoBarra chars ambos arriba y abajo
    cadena=cadena.replace("<BARCODE_FONT_A>","\u001d\u0066\u0000") # Font tipo A para HRI ImprimirCodigoBarra chars
    cadena=cadena.replace("<BARCODE_FONT_B>","\u001d\u0066\u0001") # Font tipo B para HRI ImprimirCodigoBarra chars
    cadena=cadena.replace("<BARCODE_HEIGHT>","\u001d\u0068\u0064") # CodigoBarra Alto [1-255]
    cadena=cadena.replace("<BARCODE_WIDTH>","\u001d\u0077\u0003") # CodigoBarra Ancho  [2-6]
    cadena=cadena.replace("<BARCODE_UPC_A>","\u001d\u006b\u0000") # CodigoBarra Tipo UPC-A
    cadena=cadena.replace("<BARCODE_UPC_E>","\u001d\u006b\u0001") # CodigoBarra Tipo UPC-E
    cadena=cadena.replace("<BARCODE_EAN13>","\u001d\u006b\u0002") # CodigoBarra Tipo EAN13
    cadena=cadena.replace("<BARCODE_EAN8>","\u001d\u006b\u0003") # CodigoBarra Tipo EAN8
    cadena=cadena.replace("<BARCODE_CODE39>","\u001d\u006b\u0004") # CodigoBarra Tipo CODE39
    cadena=cadena.replace("<BARCODE_ITF>","\u001d\u006b\u0005") # CodigoBarra Tipo ITF
    cadena=cadena.replace("<BARCODE_NW7>","\u001d\u006b\u0006") # CodigoBarra Tipo NW7

    if "<BARCODE_CODE39>" in cadena:
        barcode_data = "0001562622178"  # Replace with actual barcode data
        # Configure barcode height, width, and text position
        barcode_config = (
            "\u001d\u0068\u0064"  # Set barcode height to 100 (default: 64)
            "\u001d\u0077\u0003"  # Set barcode width to 3 (default: 2)
            "\u001d\u0048\u0002"  # Set HRI (Human Readable Interpretation) position to below the barcode
        )
        barcode_command = f"\u001d\u006b\u0004{barcode_data}\n"  # CODE39 command with data
        cadena = cadena.replace("<BARCODE_CODE39>", barcode_config + barcode_command)

    # Desindad de Impresion
    cadena=cadena.replace("<PD_N50>","\u001d\u007c\u0000") # Densidad Impresion -50%
    cadena=cadena.replace("<PD_N37>","\u001d\u007c\u0001") # Densidad Impresion -37.5%
    cadena=cadena.replace("<PD_N25>","\u001d\u007c\u0002") # Densidad Impresion -25%
    cadena=cadena.replace("<PD_N12>","\u001d\u007c\u0003") # Densidad Impresion -12.5%
    cadena=cadena.replace("<PD_0>","\u001d\u007c\u0004") # Densidad Impresion  0%
    cadena=cadena.replace("<PD_P50>","\u001d\u007c\u0008") # Densidad Impresion +50%
    cadena=cadena.replace("<PD_P37>","\u001d\u007c\u0007") # Densidad Impresion +37.5%
    cadena=cadena.replace("<PD_P25>","\u001d\u007c\u0006") # Densidad Impresion +25%
    cadena=cadena.replace("<PD_P12>","\u001d\u007c\u0005") # Densidad Impresion +12.5%


    # Add printer initialization at the start
    cadena = "\u001b@" + cadena  # Reset printer

    return cadena


def imprimir(contenido, impresora):
    # Indicar nombre de impresora
    p = win32print.OpenPrinter(impresora)
    new_contenido = reemplazar(contenido)
    
    # Print the content to the console for debugging
    print(f"Printing to {impresora}:")
    print("Formatted Content:")
    print(new_contenido)
    print("Raw Bytes Sent to Printer:")
    print(bytes(new_contenido, 'utf-8'))
    
    # Send the content to the printer
    job = win32print.StartDocPrinter(p, 1, ("printer job", None, "RAW"))
    win32print.StartPagePrinter(p)
    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
    win32print.EndPagePrinter(p)
    win32print.ClosePrinter(p)

# Llamar cuando el Cliente envia el mensaje
# def message_received(client, server, message):
#     # Descomponer JSON
#     JSON=json.loads(message)
#     contenido=JSON['contenido']
#     impresora=JSON['impresora']
#     # Llamar a la función imprimir 
#     imprimir(contenido,impresora)


# def message_received(client, server, message):
#     # Descomponer JSON
#     JSON = json.loads(message)
#     contenido = JSON['contenido']
#     impresora = JSON['impresora']

#     # Ensure contenido is a string
#     if isinstance(contenido, list):
#         # Extract strings from dictionaries and join them
#         contenido = ''.join(item.get('text', '') if isinstance(item, dict) else str(item) for item in contenido)

#     # Llamar a la función imprimir 
#     imprimir(contenido, impresora)


def message_received(client, server, message):
    # Parse the incoming JSON message
    JSON = json.loads(message)
    contenido = JSON['contenido']
    impresora = JSON['impresora']

    # Ensure contenido is a string
    if isinstance(contenido, list):
        # Process the list to maintain the order and include barcode data dynamically
        processed_contenido = []
        for item in contenido:
            if isinstance(item, dict) and 'text' in item:
                # Add text from dictionaries
                processed_contenido.append(item['text'])
            elif isinstance(item, dict) and 'barcode' in item:
                # Add barcode control sequence and data
                barcode_type = item.get('type', '<BARCODE_CODE39>')  # Default to CODE39 if not specified
                barcode_data = item.get('barcode', '')
                if barcode_data:  # Ensure barcode data is not empty
                    processed_contenido.append(f"{barcode_type}{barcode_data}")
                else:
                    print("Warning: Barcode data is empty!")
            else:
                # Add non-dictionary items as strings
                processed_contenido.append(str(item))
        contenido = ''.join(processed_contenido)

    # Call the print function
    imprimir(contenido, impresora)






PORT=9000
HOST = "0.0.0.0"  # Or "localhost" if only local connections are allowed
# server = WebsocketServer(PORT)
server = WebsocketServer(host=HOST, port=PORT)
server.set_fn_message_received(message_received)

# Print a message indicating the server is ready
print("Listening for outgoing printing")

server.run_forever()

# rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)

# PORTS = [9000, 9001]
# HOST = "0.0.0.0"  # Or "localhost" if only local connections are allowed

# servers = []
# for port in PORTS:
#     server = WebsocketServer(host=HOST, port=port)
#     server.set_fn_message_received(message_received)
#     servers.append(server)

# # Run all servers in separate threads
# import threading
# threads = []
# for server in servers:
#     thread = threading.Thread(target=server.run_forever)
#     thread.daemon = True
#     thread.start()
#     threads.append(thread)

# rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
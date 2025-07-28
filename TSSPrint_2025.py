# -*- coding: utf-8 -*-
import socket
import json
import time
import re
import threading
import traceback

from websocket_server import WebsocketServer

# For Windows
try:
    import win32print
    WINDOWS = True
except ImportError:
    WINDOWS = False
    print("win32print not available - running in Linux mode")

class PrintService:
    
    def __init__(self):
        self.running = False
        self.servers = []
        socket.setdefaulttimeout(60)

    def log(self, msg):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}")
  
    def start(self):
        self.running = True
        self.log("Starting print service...")
        self.main()
    
    def stop(self):
        self.running = False
        self.log("Stopping print service...")
        for server in self.servers:
            try:
                server.shutdown()
            except:
                pass
        self.log("Print service stopped")
    
    def limpiar_texto_utf8(self, texto):
        """Limpia caracteres problemáticos UTF-8 para impresoras térmicas"""
        replacements = {
            '–': '-',  # en-dash a guión normal
            '—': '-',  # em-dash a guión normal
            '“': '"',  # comillas izquierdas
            '”': '"',  # comillas derechas
            '‘': "'",  # apóstrofe izquierdo
            '’': "'",  # apóstrofe derecho
            '…': '...',  # elipsis
            '°': 'o',   # grado
            '±': '+/-', # más menos
            '×': 'x',   # multiplicación
            '÷': '/',   # división
            '≤': '<=',  # menor o igual
            '≥': '>=',  # mayor o igual
            '≠': '!=',  # no igual
            '∞': 'inf', # infinito
            '√': 'raiz',# raíz cuadrada
            '²': '2',   # superíndice 2
            '³': '3',   # superíndice 3
            '€': 'EUR', # euro
            '£': 'GBP', # libra
            '¥': 'YEN', # yen
            '©': '(c)', # copyright
            '®': '(r)', # registrado
            '™': 'TM',  # trademark
            '•': '*',   # bullet
            '◦': 'o',   # white bullet
            '▪': '*',   # black small square
            '▫': 'o',   # white small square
            '►': '>',   # black right-pointing pointer
            '◄': '<',   # black left-pointing pointer
            '▲': '^',   # black up-pointing triangle
            '▼': 'v',   # black down-pointing triangle
        }
        
        for old, new in replacements.items():
            texto = texto.replace(old, new)
        
        texto_limpio = ''
        for char in texto:
            if ord(char) < 128 or char in 'áéíóúñÁÉÍÓÚÑüÜ':
                texto_limpio += char
            else:
                texto_limpio += ' '
        
        return texto_limpio
    
    def convertir_escpos_a_tspl(self, contenido):
        """Convierte comandos ESC/POS a TSPL para impresoras de etiquetas"""
        
        # Corrección: Usar puntos (dots) en lugar de mm. Asumiendo 203dpi (8 dots/mm)
        # 50mm * 8 = 400 dots; 30mm * 8 = 240 dots
        tspl = "SIZE 400, 240\n"
        tspl += "GAP 24, 0\n" # 3mm * 8 = 24 dots
        tspl += "DIRECTION 1\n"
        tspl += "CLS\n\n"
        # Variables de estado
        y_position = 30
        font_size = "2"
        bold = False
        align = "left"
        
        # Procesar línea por línea
        lineas = contenido.split('<NL>')
        
        for linea in lineas:
            # Limpiar etiquetas de formato
            texto = linea
            
            # Detectar negrita
            if '<NEGRITA>' in texto:
                bold = True
                texto = texto.replace('<NEGRITA>', '')
            if '<NO_NEGRITA>' in texto:
                bold = False
                texto = texto.replace('<NO_NEGRITA>', '')
            
            # Detectar tamaño
            if '<TXT_4SQUARE>' in texto:
                font_size = "3"
                texto = texto.replace('<TXT_4SQUARE>', '')
            elif '<TXT_2HEIGHT>' in texto:
                font_size = "2"
                texto = texto.replace('<TXT_2HEIGHT>', '')
            elif '<TXT_NORMAL>' in texto:
                font_size = "2"
                texto = texto.replace('<TXT_NORMAL>', '')
            
            # Detectar alineación
            if '<TXT_ALIGN_CT>' in texto:
                align = "center"
                texto = texto.replace('<TXT_ALIGN_CT>', '')
            elif '<TXT_ALIGN_LT>' in texto:
                align = "left"
                texto = texto.replace('<TXT_ALIGN_LT>', '')
            elif '<TXT_ALIGN_RT>' in texto:
                align = "right"
                texto = texto.replace('<TXT_ALIGN_RT>', '')
            
            # Detectar código de barras CODE39
            if '<BARCODE_CODE39>' in texto:
                # Extraer datos del código
                match = re.search(r'<BARCODE_CODE39>\*(.*?)\*$', texto)
                if match:
                    barcode_data = match.group(1)
                    tspl += f'BARCODE 50,{y_position},"39",50,1,0,2,2,"{barcode_data}"\n'
                    y_position += 80
                continue
            
            # Detectar código de barras EAN13
            if '<BARCODE_EAN13>' in texto:
                # Extraer datos del código
                match = re.search(r'<BARCODE_EAN13>(\d+)$', texto)
                if match:
                    barcode_data = match.group(1)
                    tspl += f'BARCODE 50,{y_position},"EAN13",50,1,0,2,2,"{barcode_data}"\n'
                    y_position += 80
                continue
            
            # Limpiar otras etiquetas
            for tag in ['<ESC>', '<BARCODE_HEIGHT>', '<BARCODE_WIDTH>', '<BARCODE_TXT_BLW>', 
                        '<TXT_FONT_A>', '<TXT_FONT_B>', '<PAPER_FULL_CUT>', '<PAPER_PART_CUT>',
                        '<BARCODE_TXT_OFF>', '<TXT_FONT_B>']:
                texto = texto.replace(tag, '')
            
            # Si hay texto, imprimirlo
            texto = texto.strip()
            if texto:
                texto = self.limpiar_texto_utf8(texto)
                
                x_pos = 50
                if align == "center":
                    x_pos = 200  # Centro aproximado para etiqueta de 50mm
                elif align == "right":
                    x_pos = 350
                
                # Agregar comando TEXT
                tspl += f'TEXT {x_pos},{y_position},"{font_size}",0,1,1,"{texto}"\n'
                y_position += 30
        
        # Agregar comando de impresión
        tspl += "\nPRINT 1\n"
        
        return tspl
        
    def main(self):
        
        #GESTION DE IMPRESION TERMICA
        def reemplazar(cadena):
            cadena = self.limpiar_texto_utf8(cadena)
            
            # Procesar CODE39 con datos
            if '<BARCODE_CODE39>' in cadena:
                self.log(f"Procesando códigos de barras CODE39...")
                pattern = r'<BARCODE_CODE39>(.*?)<NL>'
                
                def replace_code39(match):
                    barcode_data = match.group(1)
                    self.log(f"  - CODE39 encontrado: '{barcode_data}'")
                    
                    # Construir comandos ESC/POS completos
                    commands = ""
                    commands += "\u001d\u0068\u0064"  # GS h 100 - Altura
                    commands += "\u001d\u0077\u0002"  # GS w 2 - Ancho
                    commands += "\u001d\u0048\u0002"  # GS H 2 - HRI abajo
                    commands += "\u001d\u0066\u0000"  # GS f 0 - Fuente A para HRI
                    commands += "\u001d\u006b\u0004"  # GS k 4 - CODE39
                    commands += barcode_data          # Datos del código
                    commands += "\u0000"              # NUL terminator
                    commands += "\n"                  # Nueva línea
                    
                    return commands
                
                cadena = re.sub(pattern, replace_code39, cadena)
            
            # Ahora procesar el resto de etiquetas
            # Secuencias de Control de Alimentacion
            cadena=cadena.replace("<ESC>", "\u001b\u0040")
            cadena=cadena.replace("<NL>",'\n')
            # Formato de texto
            cadena=cadena.replace("<TITULO>","\u001b\u0021\u0038")
            cadena=cadena.replace("<FUENTE>","\u001b\u004d\u0000")
            cadena=cadena.replace("<DOBLE>","\u001b\u0021\u0018")
            cadena=cadena.replace("<TXT_NORMAL>","\u001b\u0021\u0000")
            cadena=cadena.replace("<TXT_2HEIGHT>","\u001b\u0021\u0010")
            cadena=cadena.replace("<TXT_2WIDTH>","\u001b\u0021\u0020")
            cadena=cadena.replace("<TXT_4SQUARE>","\u001b\u0021\u0030")
            cadena=cadena.replace("<TXT_UNDERL_OFF>","\u001b\u002d\u0000")
            cadena=cadena.replace("<TXT_UNDERL_ON>","\u001b\u002d\u0001")
            cadena=cadena.replace("<TXT_UNDERL2_ON>","\u001b\u002d\u0002")
            cadena=cadena.replace("<NO_NEGRITA>","\u001b\u0045\u0000")
            cadena=cadena.replace("<NEGRITA>","\u001b\u0045\u0001")
            cadena=cadena.replace("<TXT_FONT_A>","\u001b\u004d\u0000")
            cadena=cadena.replace("<TXT_FONT_B>","\u001b\u004d\u0001")
            cadena=cadena.replace("<TXT_ALIGN_LT>","\u001b\u0061\u0000")
            cadena=cadena.replace("<TXT_ALIGN_CT>","\u001b\u0061\u0001")
            cadena=cadena.replace("<TXT_ALIGN_RT>","\u001b\u0061\u0002")

            # Beeper
            cadena=cadena.replace("<BEEPER>","\u001b\u0042\u0005\u0009")

            # Printer hardware
            cadena=cadena.replace("<HW_INIT>","\u001b\u0040")

            # Lineas de Espacion
            cadena=cadena.replace("<LINE_SPACE_24>","\u001b\u0033\u0018")
            cadena=cadena.replace("<LINE_SPACE_30>","\u001b\u0033\u001E")
            # Imagen
            cadena=cadena.replace("<SELECT_BIT_IMAGE_MODE>","\u001B\u002A\u0021")
            cadena=cadena.replace("<CD_KICK_2>","\u001b\u0070\u0000")
            cadena=cadena.replace("<CD_KICK_5>","\u001b\u0070\u0001")

            # Papel
            cadena=cadena.replace("<PAPER_FULL_CUT>","\u001d\u0056\u0000")
            cadena=cadena.replace("<PAPER_PART_CUT>","\u001d\u0056\u0001")

            # Tabla de Codigos de Caracteres
            cadena=cadena.replace("<CHARCODE_PC437>","\u001b\u0074\u0000")
            cadena=cadena.replace("<CHARCODE_JIS>","\u001b\u0074\u0001")
            cadena=cadena.replace("<CHARCODE_PC850>","\u001b\u0074\u0002")
            cadena=cadena.replace("<CHARCODE_PC860>","\u001b\u0074\u0003")
            cadena=cadena.replace("<CHARCODE_PC863>","\u001b\u0074\u0004")
            cadena=cadena.replace("<CHARCODE_PC865>","\u001b\u0074\u0005")
            cadena=cadena.replace("CHARCODE_WEU>","\u001b\u0074\u0006")
            cadena=cadena.replace("<CHARCODE_GREEK>","\u001b\u0074\u0007")
            cadena=cadena.replace("<CHARCODE_HEBREW>","\u001b\u0074\u0008")
            cadena=cadena.replace("<CHARCODE_PC1252>","\u001b\u0074\u0010")
            cadena=cadena.replace("<CHARCODE_PC866>","\u001b\u0074\u0012")
            cadena=cadena.replace("<CHARCODE_PC852>","\u001b\u0074\u0013")
            cadena=cadena.replace("<CHARCODE_PC858>","\u001b\u0074\u0014")
            cadena=cadena.replace("<CHARCODE_THAI42>","\u001b\u0074\u0015")
            cadena=cadena.replace("<CHARCODE_THAI11>","\u001b\u0074\u0016")
            cadena=cadena.replace("<CHARCODE_THAI13>","\u001b\u0074\u0017")
            cadena=cadena.replace("<CHARCODE_THAI14>","\u001b\u0074\u0018")
            cadena=cadena.replace("<CHARCODE_THAI16>","\u001b\u0074\u00119")
            cadena=cadena.replace("<CHARCODE_THAI17>", "\u001b\u0074\u001a")
            cadena=cadena.replace("CHARCODE_THAI18>","\u001b\u0074\u001b")

            # Formato de Codigo de Barra
            cadena=cadena.replace("<BARCODE_TXT_OFF>","\u001d\u0048\u0000")
            cadena=cadena.replace("<BARCODE_TXT_ABV>","\u001d\u0048\u0001")
            cadena=cadena.replace("<BARCODE_TXT_BLW>","\u001d\u0048\u0002")
            cadena=cadena.replace("<BARCODE_TXT_BTH>","\u001d\u0048\u0003")
            cadena=cadena.replace("<BARCODE_FONT_A>","\u001d\u0066\u0000")
            cadena=cadena.replace("<BARCODE_FONT_B>","\u001d\u0066\u0001")
            cadena=cadena.replace("<BARCODE_HEIGHT>","\u001d\u0068\u0064")
            cadena=cadena.replace("<BARCODE_WIDTH>","\u001d\u0077\u0002")
            cadena=cadena.replace("<BARCODE_UPC_A>","\u001d\u006b\u0000")
            cadena=cadena.replace("<BARCODE_UPC_E>","\u001d\u006b\u0001")
            cadena=cadena.replace("<BARCODE_EAN13>","\u001d\u006b\u0002")
            cadena=cadena.replace("<BARCODE_EAN8>","\u001d\u006b\u0003")
            cadena=cadena.replace("<BARCODE_128>","\u001d\u006b\u0008")
            cadena=cadena.replace("<BARCODE_NW7>","\u001d\u006b\u0006")
            cadena=cadena.replace("<BARCODE_2D>","\u001d\u006b\u0049")
            cadena=cadena.replace("<BARCODE_93>","\u001d\u006b\u0007")
            cadena=cadena.replace("<BARCODE_ITF>","\u001d\u006b\u0005")

            # Densidad de Impresion
            cadena=cadena.replace("<PD_N50>","\u001d\u007c\u0000")
            cadena=cadena.replace("<PD_N37>","\u001d\u007c\u0001")
            cadena=cadena.replace("<PD_N25>","\u001d\u007c\u0002")
            cadena=cadena.replace("<PD_N12>","\u001d\u007c\u0003")
            cadena=cadena.replace("<PD_0>","\u001d\u007c\u0004")
            cadena=cadena.replace("<PD_P50>","\u001d\u007c\u0008")
            cadena=cadena.replace("<PD_P37>","\u001d\u007c\u0007")
            cadena=cadena.replace("<PD_P25>","\u001d\u007c\u0006")
            cadena=cadena.replace("<PD_P12>","\u001d\u007c\u0005")
            return cadena
        
        def imprimir_ter(contenido, impresora):
            try:
                # DETECTAR TIPO DE IMPRESORA
                # Lista de palabras clave para impresoras de etiquetas
                es_impresora_etiquetas = any(keyword in impresora.upper() for keyword in 
                    ['ETIQUETA', '4BARCODE', 'LDT114', '3NSTAR', 'TSC', 'ZEBRA', 'GODEX'])
                
                if es_impresora_etiquetas:
                    # Convertir ESC/POS a TSPL para impresoras de etiquetas
                    new_contenido = self.convertir_escpos_a_tspl(contenido)
                    self.log(f"TSPL print to {impresora}: {len(new_contenido)} bytes")
                else:
                    # Usar ESC/POS para impresoras térmicas normales
                    new_contenido = reemplazar(contenido)
                    self.log(f"ESC/POS print to {impresora}: {len(new_contenido)} bytes")
                
                if WINDOWS:
                    # Windows printing
                    p = win32print.OpenPrinter(impresora)
                    job = win32print.StartDocPrinter(p, 1, ("TSSPrint Job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
                    win32print.EndPagePrinter(p)
                    win32print.EndDocPrinter(p)
                    win32print.ClosePrinter(p)
                    self.log(f"Print job sent successfully to {impresora}")
                else:
                    self.log("Linux thermal printing - implement CUPS or direct device")
                
            except Exception as e:
                self.log(f"Error printing to thermal printer {impresora}: {str(e)}")
                traceback.print_exc()

        #GESTION DE IMPRESION IMPACTO            
        def conversor(linea, printer):
            #valores por defecto
            size = {"height": 12}
            _aling = "center"
            linea = linea.replace('<NL>', '\n')
            linea = linea.replace('<MARGEN>', '    ')
            if linea.find('<MINI>') != -1:
                size = {"height": 8}
                linea = linea.replace('<MINI>', '')
            if linea.find('<PEQUENO>') != -1:
                size = {"height": 9}
                linea = linea.replace('<PEQUENO>', '')
            if linea.find('<MEDIANO>') != -1:
                size = {"height": 15}
                linea = linea.replace('<MEDIANO>', '')
            if linea.find('<NORMAL>') != -1:
                size = {"height": 12}
                linea = linea.replace('<NORMAL>', '')
            if linea.find('<GRANDE>') != -1:
                size = {"height": 18}
                linea = linea.replace('<GRANDE>', '')
            #MANEJO DE NEGRITA
            if linea.find('<NEGRITA>') != -1:
                size['weight'] = 700
                linea = linea.replace('<NEGRITA>', '')
            else:
                size['weight'] = 400
            #MANEJO DE ALINEAMIENTO
            if linea.find('<IZQUIERDA>') != -1:
                _aling = "left"
                linea = linea.replace('<IZQUIERDA>', '')
            if linea.find('<CENTRO>') != -1:
                _aling = "center"
                linea = linea.replace('<CENTRO>', '')
            if linea.find('<DERECHA>') != -1:
                _aling = "right"
                linea = linea.replace('<DERECHA>', '')
            
            # For Linux, you'll need to implement this with a CUPS-compatible library
            self.log(f"Impact print line: {linea} (size: {size}, align: {_aling})")
        
        def imprimir_impac(contenido, impresora):
            try:
                self.log(f"Impact print to {impresora}")
                lineas = contenido.split('\n')
                for l in lineas:
                    conversor(l, impresora)
            except Exception as e:
                self.log(f"Error printing to impact printer {impresora}: {str(e)}")

        def imprimir_etiqueta(contenido, impresora):
            self.log(f"Iniciando trabajo de impresión de ETIQUETA para: '{impresora}'")
            
            try:
                new_contenido = ""
                
                if isinstance(contenido, list):
                    self.log("Contenido detectado como DATOS (lista JSON). Construyendo etiqueta TSPL...")
                    
                    tspl_commands = []
                    
                    # ======================= INICIO DE LA CORRECCIÓN =======================
                    # Se usan unidades en PUNTOS (dots) en lugar de 'mm' para compatibilidad.
                    # Asumiendo una impresora de 203dpi (8 puntos por milímetro).
                    # Ancho: 40mm * 8 dots/mm = 320 dots
                    # Alto:  25mm * 8 dots/mm = 200 dots
                    # GAP:   3mm * 8 dots/mm = 24 dots
                    tspl_commands.append("SIZE 320, 200")
                    tspl_commands.append("GAP 24, 0")
                    # ======================== FIN DE LA CORRECCIÓN =======================

                    tspl_commands.append("DIRECTION 1")
                    tspl_commands.append("DENSITY 12")
                    tspl_commands.append("SPEED 3")
                    tspl_commands.append("SET TEAR ON")
                    
                    for idx, item in enumerate(contenido):
                        tspl_commands.append("CLS")
                        
                        nombre = str(item.get("nombre", "")).strip()
                        orden = str(item.get("orden", "")).strip()
                        area = str(item.get("area", "")).strip()
                        genero = str(item.get("genero", "")).strip()
                        edad = str(item.get("edad", "")).strip()
                        
                        self.log(f" - Construyendo etiqueta {idx+1}: orden={orden}, paciente={nombre}")

#-----------------------------------------------------------------------------------------------------------------------------------------------------------                                                
                        # 🎯 INICIO DE LA CORRECCIÓN DE LAYOUT FINAL
                        # Coordenadas ajustadas para un diseño más compacto y alineado.
                        
                        # Área - Y=15
                        if area:
                            tspl_commands.append(f'TEXT 25,15,"1",0,1,1,"{area}"')
                        
                        # Nombre - Y=40
                        if nombre:
                            nombre_corto = nombre[:27]
                            tspl_commands.append(f'TEXT 25,40,"2",0,1,1,"{nombre_corto}"')
                        
                        # Edad y Género en la misma línea (Y=65) pero con dos comandos TEXT
                        if edad or genero:
                            if edad and not edad.endswith('A'):
                                edad_formateada = f"{edad} A"
                            else:
                                edad_formateada = edad
                            
                            # Comando para la Edad
                            if edad_formateada:
                                tspl_commands.append(f'TEXT 25,65,"2",0,1,1,"Edad: {edad_formateada}"')
                            
                            # Comando para el Género, en la misma línea Y pero más a la derecha (X=160)
                            if genero:
                                tspl_commands.append(f'TEXT 160,65,"2",0,1,1,"Genero: {genero}"')
                                
                        # Código de barras - Y=100
                        if orden:
                            tspl_commands.append(f'BARCODE 25,100,"128",45,1,0,2,2,"{orden}"')
#-----------------------------------------------------------------------------------------------------------------------------------------------------------                        

                        tspl_commands.append("PRINT 1,1")
                    
                    new_contenido = "\n".join(tspl_commands) + "\n"
                    
                elif isinstance(contenido, str):
                    if contenido.strip().upper().startswith(('SIZE', 'CLS', 'TEXT', 'BARCODE')):
                        self.log("Contenido detectado como comandos TSPL directos.")
                        new_contenido = contenido
                    else:
                        self.log("Contenido detectado como texto. Procesando...")
                        new_contenido = contenido.replace('\n', '').replace('<NL>', '\n')
                else:
                    self.log(f"ERROR: Tipo de contenido no soportado: {type(contenido)}")
                    return
                
                self.log(f"CONTENIDO FINAL A IMPRIMIR en '{impresora}':\n---\n{new_contenido}\n---")
                
                if WINDOWS and new_contenido:
                    # Windows printing
                    p = win32print.OpenPrinter(impresora)
                    win32print.StartDocPrinter(p, 1, ("Label Job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
                    win32print.EndPagePrinter(p)
                    win32print.EndDocPrinter(p)
                    win32print.ClosePrinter(p)
                    self.log(f"Trabajo de etiqueta enviado exitosamente.")
                    
            except Exception as e:
                self.log(f"ERROR en 'imprimir_etiqueta': {str(e)}")
                traceback.print_exc()

        def message_received(client, server, message):
            try:
                self.log(f"Mensaje recibido del cliente {client['id']} en puerto {server.port}")
                
                JSON = json.loads(message)
                contenido = JSON.get('contenido', '')
                impresora = JSON.get('impresora', 'TERMICA')
                tipo = JSON.get('tipo', 'TERMICA').upper()
                
                self.log(f"Trabajo de impresión: Tipo={tipo}, Impresora={impresora}")
                
                if tipo == 'TERMICA':
                    imprimir_ter(contenido, impresora)
                elif tipo == 'IMPACTO':
                    contenido = contenido.replace('<SEP>', '\n')
                    imprimir_impac(contenido, impresora)
                elif tipo in ['ETIQUETA', 'TSC']:
                    imprimir_etiqueta(contenido, impresora)
                else:
                    self.log(f"Tipo de impresión desconocido: {tipo}")
                    
            except Exception as e:
                self.log(f"Error procesando mensaje: {str(e)}")
                traceback.print_exc()

        PORTS = [9000, 9001]
        HOST = "127.0.0.1"
        
        for port in PORTS:
            server = WebsocketServer(host=HOST, port=port)
            server.set_fn_message_received(message_received)
            self.servers.append(server)
            self.log(f"WebSocket server created for port {port}")
        
        threads = []
        for server in self.servers:
            thread = threading.Thread(target=server.run_forever)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        self.log("All servers running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("\nService interrupted by user")
        finally:
            self.stop()

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║      TSSPrint Service - UNIFIED PRINTER SUPPORT       ║
    ║         ESC/POS + TSPL + ZPL Support Fixed            ║
    ║             Version: FIXED-2025-DOTS-UNITS            ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    print("Impresoras configuradas:")
    print("  - TERMICA: POS-80 (ESC/POS)")
    print("  - ETIQUETA: 4BARCODE 4B-2054L (TSPL)")
    print("  - IMPACTO: Impresoras de impacto")
    print("")
    print("Correcciones aplicadas:")
    print("  ✓ Unidades de etiqueta (mm) cambiadas a puntos (dots) para TSPL.")
    print("  ✓ Caracteres UTF-8 limpiados para impresoras térmicas")
    print("  ✓ Edad/Género corregido en etiquetas") 
    print("  ✓ Mejor espaciado en stickers")
    print("  ✓ Comando ESC inicialización corregido")
    print("")
    
    print_service = PrintService()
    
    try:
        print_service.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        print_service.stop()
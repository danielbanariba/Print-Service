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
        self.main()

    def stop(self):
        self.running = False
        for server in self.servers:
            try:
                server.shutdown()
            except:
                pass
    
    def limpiar_texto_utf8(self, texto):
        """Limpia caracteres problemáticos UTF-8 para impresoras térmicas"""
        replacements = {
            '–': '-', '—': '-', '"': '"', '"': '"', ''': "'", ''': "'",
            '…': '...', '°': 'o', '±': '+/-', '×': 'x', '÷': '/',
            '€': 'EUR', '£': 'GBP', '¥': 'YEN', '©': '(c)', '®': '(r)',
            '™': 'TM', '•': '*', '►': '>', '◄': '<', '▲': '^', '▼': 'v'
        }
        
        for old, new in replacements.items():
            texto = texto.replace(old, new)
        
        # Mantener solo ASCII y caracteres españoles básicos
        texto_limpio = ''
        for char in texto:
            if ord(char) < 128 or char in 'áéíóúñÁÉÍÓÚÑüÜ':
                texto_limpio += char
            else:
                texto_limpio += ' '
        
        return texto_limpio
    
    def convertir_escpos_a_tspl(self, contenido):
        """Convierte comandos ESC/POS a TSPL para impresoras de etiquetas"""
        tspl = "SIZE 320, 200\n"
        tspl += "GAP 24, 0\n"
        tspl += "DIRECTION 1\n"
        tspl += "CLS\n\n"
        
        font_size = "2"
        align = "left"
        
        lineas = contenido.split('<NL>')
        
        for linea in lineas:
            texto = linea
            
            # Detectar formatos
            if '<NEGRITA>' in texto:
                texto = texto.replace('<NEGRITA>', '')
            if '<NO_NEGRITA>' in texto:
                texto = texto.replace('<NO_NEGRITA>', '')
            
            if '<TXT_4SQUARE>' in texto:
                font_size = "3"
                texto = texto.replace('<TXT_4SQUARE>', '')
            elif '<TXT_2HEIGHT>' in texto or '<TXT_NORMAL>' in texto:
                font_size = "2"
                texto = texto.replace('<TXT_2HEIGHT>', '').replace('<TXT_NORMAL>', '')
            
            # Detectar alineación
            if '<TXT_ALIGN_CT>' in texto:
                align = "center"
                texto = texto.replace('<TXT_ALIGN_CT>', '')
            elif '<TXT_ALIGN_RT>' in texto:
                align = "right"
                texto = texto.replace('<TXT_ALIGN_RT>', '')
            elif '<TXT_ALIGN_LT>' in texto:
                align = "left"
                texto = texto.replace('<TXT_ALIGN_LT>', '')
            
            # Detectar código de barras CODE39
            if '<BARCODE_CODE39>' in texto:
                match = re.search(r'<BARCODE_CODE39>\*(.*?)\*$', texto)
                if match:
                    barcode_data = match.group(1)
                    # 120 es la posición del código de barras
                    tspl += f'BARCODE 120,"39",50,1,0,2,2,"{barcode_data}"\n'
                continue
            
            # Detectar código de barras EAN13
            if '<BARCODE_EAN13>' in texto:
                match = re.search(r'<BARCODE_EAN13>(\d+)$', texto)
                if match:
                    barcode_data = match.group(1)
                    # 120 es la posición del código de barras
                    tspl += f'BARCODE 120,"EAN13",50,1,0,2,2,"{barcode_data}"\n'
                continue
            
            # Limpiar etiquetas restantes
            for tag in ['<ESC>', '<BARCODE_HEIGHT>', '<BARCODE_WIDTH>', '<BARCODE_TXT_BLW>', 
                        '<TXT_FONT_A>', '<TXT_FONT_B>', '<PAPER_FULL_CUT>', '<PAPER_PART_CUT>',
                        '<BARCODE_TXT_OFF>']:
                texto = texto.replace(tag, '')
            
            # Imprimir texto si existe
            texto = texto.strip()
            if texto:
                texto = self.limpiar_texto_utf8(texto)
                
                # left_align: 120, center_align: 160, right_align: 240
                x_pos = 120
                if align == "center":
                    x_pos = 160
                elif align == "right":
                    x_pos = 240
                
                tspl += f'TEXT {x_pos},"{font_size}",0,1,1,"{texto}"\n'
        
        tspl += "\nPRINT 1\n"
        return tspl
        
    def main(self):
        
        def reemplazar(cadena):
            """Convierte etiquetas a comandos ESC/POS para impresoras térmicas"""
            cadena = self.limpiar_texto_utf8(cadena)
            
            # Procesar CODE39 con datos
            if '<BARCODE_CODE39>' in cadena:
                self.log(f"Procesando códigos de barras CODE39...")
                pattern = r'<BARCODE_CODE39>(.*?)<NL>'
                
                def replace_code39(match):
                    barcode_data = match.group(1)
                    self.log(f"  - CODE39 encontrado: '{barcode_data}'")
                    
                    commands = ""
                    commands += "\u001d\u0068\u0064"  # GS h 100 - Altura
                    commands += "\u001d\u0077\u0002"  # GS w 2 - Ancho
                    commands += "\u001d\u0048\u0002"  # GS H 2 - HRI abajo
                    commands += "\u001d\u0066\u0000"  # GS f 0 - Fuente A para HRI
                    commands += "\u001d\u006b\u0004"  # GS k 4 - CODE39
                    commands += barcode_data
                    commands += "\u0000"              # NUL terminator
                    commands += "\n"
                    
                    return commands
                
                cadena = re.sub(pattern, replace_code39, cadena)
            
            # Comandos básicos ESC/POS que sí se usan
            cadena = cadena.replace("<ESC>", "\u001b\u0040")  # Inicializar impresora
            cadena = cadena.replace("<NL>", '\n')
            
            # Formato de texto
            cadena = cadena.replace("<TXT_NORMAL>", "\u001b\u0021\u0000")
            cadena = cadena.replace("<TXT_2HEIGHT>", "\u001b\u0021\u0010")
            cadena = cadena.replace("<TXT_2WIDTH>", "\u001b\u0021\u0020")
            cadena = cadena.replace("<TXT_4SQUARE>", "\u001b\u0021\u0030")
            cadena = cadena.replace("<NO_NEGRITA>", "\u001b\u0045\u0000")
            cadena = cadena.replace("<NEGRITA>", "\u001b\u0045\u0001")
            cadena = cadena.replace("<TXT_FONT_A>", "\u001b\u004d\u0000")
            cadena = cadena.replace("<TXT_FONT_B>", "\u001b\u004d\u0001")
            cadena = cadena.replace("<TXT_ALIGN_LT>", "\u001b\u0061\u0000")
            cadena = cadena.replace("<TXT_ALIGN_CT>", "\u001b\u0061\u0001")
            cadena = cadena.replace("<TXT_ALIGN_RT>", "\u001b\u0061\u0002")
            
            # Papel
            cadena = cadena.replace("<PAPER_FULL_CUT>", "\u001d\u0056\u0000")
            cadena = cadena.replace("<PAPER_PART_CUT>", "\u001d\u0056\u0001")
            
            # Códigos de barras básicos
            cadena = cadena.replace("<BARCODE_TXT_OFF>", "\u001d\u0048\u0000")
            cadena = cadena.replace("<BARCODE_TXT_BLW>", "\u001d\u0048\u0002")
            cadena = cadena.replace("<BARCODE_HEIGHT>", "\u001d\u0068\u0064")
            cadena = cadena.replace("<BARCODE_WIDTH>", "\u001d\u0077\u0002")
            cadena = cadena.replace("<BARCODE_EAN13>", "\u001d\u006b\u0002")
            
            return cadena
        
        def imprimir_ter(contenido, impresora):
            """Imprime en impresoras térmicas"""
            try:
                # Detectar tipo de impresora
                es_impresora_etiquetas = any(keyword in impresora.upper() for keyword in 
                    ['ETIQUETA', '4BARCODE', 'LDT114', '3NSTAR', 'TSC', 'ZEBRA', 'GODEX'])
                
                if es_impresora_etiquetas:
                    new_contenido = self.convertir_escpos_a_tspl(contenido)
                    self.log(f"TSPL print to {impresora} (POSICIÓN CORREGIDA): {len(new_contenido)} bytes")
                else:
                    new_contenido = reemplazar(contenido)
                    self.log(f"ESC/POS print to {impresora}: {len(new_contenido)} bytes")
                
                if WINDOWS:
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
        
        def imprimir_etiqueta(contenido, impresora):
            """Imprime etiquetas en formato TSPL con posicionamiento y estructura corregidos"""
            self.log(f"Iniciando trabajo de impresión de ETIQUETA para: '{impresora}'")
            
            try:
                new_contenido = ""
                
                if isinstance(contenido, list):
                    self.log("Contenido detectado como DATOS (lista JSON). Construyendo etiqueta TSPL...")
                    
                    # SOLUCIÓN CLAVE #1: Configuración FUERA del bucle para evitar reinicios
                    tspl_commands = []
                    
                    # Usar tamaño en mm para mejor compatibilidad
                    tspl_commands.append("SIZE 40 mm, 25 mm")
                    tspl_commands.append("GAP 3 mm, 0 mm")
                    tspl_commands.append("REFERENCE 0,0")  # Punto de referencia en esquina superior izquierda
                    tspl_commands.append("DIRECTION 1")
                    tspl_commands.append("DENSITY 12")
                    tspl_commands.append("SPEED 3")
                    tspl_commands.append("SET TEAR ON")
                    
                    # SOLUCIÓN CLAVE #2: CLS solo una vez antes del bucle
                    tspl_commands.append("CLS")
                    
                    for idx, item in enumerate(contenido):
                        # Si hay múltiples etiquetas, agregar comando de nueva etiqueta
                        if idx > 0:
                            tspl_commands.append("PRINT 1")  # Imprimir etiqueta anterior
                            tspl_commands.append("CLS")      # Limpiar para siguiente
                        
                        nombre = str(item.get("nombre", "")).strip()
                        orden = str(item.get("orden", "")).strip()
                        area = str(item.get("area", "")).strip()
                        genero = str(item.get("genero", "")).strip()
                        edad = str(item.get("edad", "")).strip()
                        
                        self.log(f" - Construyendo etiqueta {idx+1}: orden={orden}, paciente={nombre}")
                        
                        # Posiciones Y optimizadas para mejor aprovechamiento del espacio
                        y_base = 10  # Margen superior
                        
                        # Margen izquierdo
                        x_base = 1
                        
                        # Área - Primera línea
                        if area:
                            area_corta = area[:30]
                            tspl_commands.append(f'TEXT {x_base},{y_base},"2",0,1,1,"{area_corta}"')
                        
                        # Nombre - Segunda línea
                        if nombre:
                            nombre_corto = nombre[:30]
                            tspl_commands.append(f'TEXT {x_base},{y_base + 25},"2",0,1,1,"{nombre_corto}"')
                        
                        # EDAD Y GÉNERO EN UNA SOLA LÍNEA
                        linea_edad_genero = ""
                        if edad:
                            if not edad.endswith(' A'):
                                edad_formateada = f"{edad} A"
                            else:
                                edad_formateada = edad
                            linea_edad_genero = f"Edad:{edad_formateada}"
                        
                        if genero:
                            # Agregar espacios para separar
                            if linea_edad_genero:
                                linea_edad_genero += f"     Genero: {genero}"
                            else:
                                linea_edad_genero = f"Genero: {genero}"
                        
                        if linea_edad_genero:
                            tspl_commands.append(f'TEXT {x_base},{y_base + 50},"2",0,1,1,"{linea_edad_genero}"')
                        
                        # Código de barras
                        if orden:
                            # Formatear la cadena para incluir paréntesis
                            orden_formateado = f"({orden[:2]}){orden[2:]}"
                            
                            # Código de barras con altura apropiada
                            tspl_commands.append(f'BARCODE {x_base},{y_base + 75},"128",45,1,0,2,2,"{orden_formateado}"')
                    
                    # SOLUCIÓN CLAVE #5: Un solo PRINT al final
                    tspl_commands.append("PRINT 1")
                    
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
                
                self.log(f"CONTENIDO FINAL A IMPRIMIR en '{impresora}':")
                self.log(f"---INICIO CONTENIDO---")
                self.log(new_contenido[:500] + "..." if len(new_contenido) > 500 else new_contenido)
                self.log(f"---FIN CONTENIDO---")
                
                if WINDOWS and new_contenido:
                    # SOLUCIÓN CLAVE #6: Enviar todo como un único trabajo de impresión
                    p = win32print.OpenPrinter(impresora)
                    win32print.StartDocPrinter(p, 1, ("Label Job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
                    win32print.EndPagePrinter(p)
                    win32print.EndDocPrinter(p)
                    win32print.ClosePrinter(p)
                    self.log(f"✅ Trabajo de etiqueta enviado exitosamente.")
                    
            except Exception as e:
                self.log(f"ERROR en 'imprimir_etiqueta': {str(e)}")
                traceback.print_exc()
                
        def message_received(client, server, message):
            """Maneja mensajes WebSocket recibidos"""
            try:
                self.log(f"Mensaje recibido del cliente {client['id']} en puerto {server.port}")
                
                JSON = json.loads(message)
                contenido = JSON.get('contenido', '')
                impresora = JSON.get('impresora', 'TERMICA')
                tipo = JSON.get('tipo', 'TERMICA').upper()
                
                self.log(f"Trabajo de impresión: Tipo={tipo}, Impresora={impresora}")
                
                if tipo == 'TERMICA':
                    imprimir_ter(contenido, impresora)
                elif tipo in ['ETIQUETA', 'TSC']:
                    imprimir_etiqueta(contenido, impresora)
                else:
                    self.log(f"Tipo de impresión no soportado: {tipo}")
                    
            except Exception as e:
                self.log(f"Error procesando mensaje: {str(e)}")
                traceback.print_exc()

        # Configuración de servidores WebSocket
        PORTS = [9000, 9001]
        HOST = "127.0.0.1"
        
        for port in PORTS:
            server = WebsocketServer(host=HOST, port=port)
            server.set_fn_message_received(message_received)
            self.servers.append(server)
            self.log(f"WebSocket server created for port {port}")
        
        # Iniciar servidores en threads separados
        threads = []
        for server in self.servers:
            thread = threading.Thread(target=server.run_forever)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
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
    ║            ESC/POS + TSPL Support FIXED               ║
    ║             Version: 2025-POSITION-FIXED              ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    print_service = PrintService()
    
    print_service.start()
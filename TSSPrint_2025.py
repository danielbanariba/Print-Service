import socket
import json
import time
import re
import threading
import traceback
import platform

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
        # Detectar versión de Windows
        self.windows_version = None
        if WINDOWS:
            try:
                version = platform.version()
                if '10.0.22' in version or '11.' in version:
                    self.windows_version = 11
                else:
                    self.windows_version = 10
            except:
                self.windows_version = 10
        
        self.log(f"Sistema detectado: Windows {self.windows_version if WINDOWS else 'No detectado'}")

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
    
    def es_impresora_tsc(self, nombre_impresora):
        """Detecta si es una impresora TSC específicamente"""
        tsc_keywords = ['TSC', 'TE200', 'TE210', 'TTP', 'TDP', 'DA200', 'DA210']
        return any(keyword in nombre_impresora.upper() for keyword in tsc_keywords)
    
    def es_impresora_3nstar(self, nombre_impresora):
        """Detecta si es una impresora 3nStar"""
        nstar_keywords = ['3NSTAR', 'LDT114', 'LDT-114', '3N-STAR']
        return any(keyword in nombre_impresora.upper() for keyword in nstar_keywords)
    
    def generar_tspl_tsc_windows11(self, contenido):
        """Genera TSPL específico para TSC en Windows 11"""
        tspl_commands = []
        
        # Comandos específicos para TSC en Windows 11
        tspl_commands.append("! 0 200 200 0 1")  # Comando de inicialización TSC
        tspl_commands.append("WIDTH 320")        # Ancho en dots
        tspl_commands.append("HEIGHT 200")       # Alto en dots
        tspl_commands.append("GAP-SENSE")        # Auto-detección de gap
        tspl_commands.append("SPEED 4")
        tspl_commands.append("DENSITY 8")
        tspl_commands.append("DIRECTION 0")      # 0 para TSC
        tspl_commands.append("REFERENCE 0,0")
        tspl_commands.append("OFFSET 0")         # Sin offset
        tspl_commands.append("SHIFT 0")          # Sin desplazamiento
        tspl_commands.append("CLS")
        
        if isinstance(contenido, list):
            for idx, item in enumerate(contenido):
                if idx > 0:
                    tspl_commands.append("PRINT 1,1")
                    tspl_commands.append("CLS")
                
                nombre = str(item.get("nombre", "")).strip()[:30]
                orden = str(item.get("orden", "")).strip()
                area = str(item.get("area", "")).strip()[:30]
                genero = str(item.get("genero", "")).strip()
                edad = str(item.get("edad", "")).strip()
                
                # Coordenadas ajustadas para TSC en Windows 11
                # TSC usa origen en esquina superior izquierda con offset
                x_offset = 5  # Offset horizontal para TSC (menos negativo que genérico)
                
                # Área
                if area:
                    tspl_commands.append(f'TEXT {x_offset},10,"2",0,1,1,"{area}"')
                
                # Nombre
                if nombre:
                    tspl_commands.append(f'TEXT {x_offset},35,"2",0,1,1,"{nombre}"')
                
                # Edad y género
                linea_edad_genero = ""
                if edad:
                    edad_formateada = f"{edad} A" if not edad.endswith(' A') else edad
                    linea_edad_genero = f"Edad:{edad_formateada}"
                
                if genero:
                    if linea_edad_genero:
                        linea_edad_genero += f"     Genero: {genero}"
                    else:
                        linea_edad_genero = f"Genero: {genero}"
                
                if linea_edad_genero:
                    tspl_commands.append(f'TEXT {x_offset},60,"2",0,1,1,"{linea_edad_genero}"')
                
                # Código de barras
                if orden:
                    orden_formateado = f"({orden[:2]}){orden[2:]}"
                    tspl_commands.append(f'BARCODE {x_offset},85,"128",45,1,0,2,2,"{orden_formateado}"')
            
            tspl_commands.append("PRINT 1,1")
            
        return "\n".join(tspl_commands) + "\n"
    
    def generar_tspl_generico(self, contenido, impresora):
        """Genera TSPL genérico para otras impresoras de etiquetas"""
        tspl_commands = []
        
        # Configuración estándar para impresoras genéricas
        tspl_commands.append("SIZE 59 mm, 25 mm")
        tspl_commands.append("GAP 3 mm, 0 mm")
        tspl_commands.append("DIRECTION 1")
        tspl_commands.append("DENSITY 12")
        tspl_commands.append("SPEED 3")
        tspl_commands.append("CLS")
        
        if isinstance(contenido, list):
            for idx, item in enumerate(contenido):
                if idx > 0:
                    tspl_commands.append("PRINT 1")
                    tspl_commands.append("CLS")
                
                nombre = str(item.get("nombre", "")).strip()[:30]
                orden = str(item.get("orden", "")).strip()
                area = str(item.get("area", "")).strip()[:30]
                genero = str(item.get("genero", "")).strip()
                edad = str(item.get("edad", "")).strip()
                
                # Posición X para centrar el contenido
                x_base = 60  # Posición centrada para etiqueta de 40mm
                
                if area:
                    tspl_commands.append(f'TEXT {x_base},10,"2",0,1,1,"{area}"')
                
                if nombre:
                    tspl_commands.append(f'TEXT {x_base},35,"2",0,1,1,"{nombre}"')
                
                linea_edad_genero = ""
                if edad:
                    edad_formateada = f"{edad} A" if not edad.endswith(' A') else edad
                    linea_edad_genero = f"Edad:{edad_formateada}"
                
                if genero:
                    if linea_edad_genero:
                        linea_edad_genero += f"     Genero: {genero}"
                    else:
                        linea_edad_genero = f"Genero: {genero}"
                
                if linea_edad_genero:
                    tspl_commands.append(f'TEXT {x_base},60,"2",0,1,1,"{linea_edad_genero}"')
                
                if orden:
                    orden_formateado = f"({orden[:2]}){orden[2:]}"
                    tspl_commands.append(f'BARCODE {x_base},85,"128",45,1,0,2,2,"{orden_formateado}"')
            
            tspl_commands.append("PRINT 1")
            
        return "\n".join(tspl_commands) + "\n"
        
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
                    tspl += f'BARCODE 120,"39",50,1,0,2,2,"{barcode_data}"\n'
                continue
            
            # Detectar código de barras EAN13
            if '<BARCODE_EAN13>' in texto:
                match = re.search(r'<BARCODE_EAN13>(\d+)$', texto)
                if match:
                    barcode_data = match.group(1)
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
            
            # Comandos básicos ESC/POS
            cadena = cadena.replace("<ESC>", "\u001b\u0040")
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
            
            # Códigos de barras
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
                    self.log(f"TSPL print to {impresora}: {len(new_contenido)} bytes")
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
            """Imprime etiquetas con detección específica para TSC"""
            self.log(f"Iniciando trabajo de impresión de ETIQUETA para: '{impresora}'")
            
            try:
                new_contenido = ""
                
                # Detectar si es TSC y está en Windows 11
                es_tsc = self.es_impresora_tsc(impresora)
                usar_modo_tsc_win11 = es_tsc and self.windows_version == 11
                
                if usar_modo_tsc_win11:
                    self.log(f"Modo TSC Windows 11 activado para: {impresora}")
                elif self.es_impresora_3nstar(impresora):
                    self.log(f"Impresora 3nStar detectada: {impresora}")
                else:
                    self.log(f"Impresora genérica/TSC detectada: {impresora}")
                
                if isinstance(contenido, list):
                    self.log("Contenido detectado como DATOS (lista JSON). Construyendo etiqueta TSPL...")
                    
                    if usar_modo_tsc_win11:
                        new_contenido = self.generar_tspl_tsc_windows11(contenido)
                    else:
                        new_contenido = self.generar_tspl_generico(contenido, impresora)  # Pasar nombre de impresora
                    
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
                
                self.log(f"Usando modo: {'TSC Windows 11' if usar_modo_tsc_win11 else 'Genérico'}")
                self.log(f"CONTENIDO FINAL A IMPRIMIR en '{impresora}':")
                self.log(f"---INICIO CONTENIDO---")
                self.log(new_contenido[:500] + "..." if len(new_contenido) > 500 else new_contenido)
                self.log(f"---FIN CONTENIDO---")
                
                if WINDOWS and new_contenido:
                    # Para TSC en Windows 11, enviar con configuración especial
                    if usar_modo_tsc_win11:
                        # Agregar pausa antes de imprimir para TSC
                        time.sleep(0.1)
                    
                    p = win32print.OpenPrinter(impresora)
                    win32print.StartDocPrinter(p, 1, ("TSC Label Job" if es_tsc else "Label Job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    
                    # Para TSC, enviar en chunks más pequeños si es Windows 11
                    if usar_modo_tsc_win11:
                        # Enviar línea por línea para mejor compatibilidad
                        for line in new_contenido.split('\n'):
                            if line:
                                win32print.WritePrinter(p, bytes(line + '\n', 'utf-8'))
                                time.sleep(0.01)  # Pequeña pausa entre líneas
                    else:
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
    ║         TSC Windows 11 Fix - Print Service            ║
    ║           Version: 2025-TSC-WIN11-FIX                 ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    print_service = PrintService()
    
    print_service.start()
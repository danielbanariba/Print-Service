import socket
import json
import time
import re
import threading
import traceback
import platform
import sys

from websocket_server import WebsocketServer

# Para Windows
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

        # Detectar versión de Windows de forma robusta (build >= 22000 => Windows 11)
        self.windows_version = None
        if WINDOWS:
            try:
                build = sys.getwindowsversion().build  # p.ej. 22621, 26100
                self.windows_version = 11 if build >= 22000 else 10
            except Exception:
                try:
                    version_str = platform.version()  # p.ej. "10.0.26100"
                    parts = version_str.split('.')
                    build = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                    self.windows_version = 11 if build >= 22000 else 10
                except Exception:
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
        """Limpia caracteres problemáticos UTF-8 para impresoras térmicas/etiquetas."""
        replacements = {
            '–': '-', '—': '-',
            '"': '"', '"': '"',
            ''': "'", ''': "'",
            '…': '...', '°': 'o', '±': '+/-', '×': 'x', '÷': '/',
            '€': 'EUR', '£': 'GBP', '¥': 'YEN', '©': '(c)', '®': '(r)', '™': 'TM',
            '•': '*', '►': '>', '◄': '<', '▲': '^', '▼': 'v'
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

    def es_impresora_tsc(self, nombre_impresora):
        """Detecta si es una impresora TSC específicamente."""
        tsc_keywords = ['TSC', 'TE200', 'TE210', 'TTP', 'TDP', 'DA200', 'DA210']
        return any(keyword in nombre_impresora.upper() for keyword in tsc_keywords)

    def es_impresora_3nstar(self, nombre_impresora):
        """Detecta si es una impresora 3nStar."""
        nstar_keywords = ['3NSTAR', 'LDT114', 'LDT-114', '3N-STAR']
        return any(keyword in nombre_impresora.upper() for keyword in nstar_keywords)



    def convertir_escpos_a_tspl(self, contenido):
        """
        Convierte comandos ESC/POS a un TSPL mínimo (sin forzar SIZE/GAP),
        preservando alineación aproximada mediante posiciones X fijas.
        """
        tspl_lines = ["CLS"]
        font_size = "2"  # "2" TSPL (tamaño estándar)
        align = "left"

        # Normalizar líneas
        temp = contenido.replace('\r\n', '\n').replace('<NL>', '\n')
        lineas = []
        for linea in temp.split('\n'):
            if linea is None:
                continue
            lineas.append(linea)

        current_y = 20
        y_step = 24

        for linea in lineas:
            texto = linea

            # Formatos (se omiten en TSPL mínimo, se conserva tamaño base)
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

            # Alineación
            if '<TXT_ALIGN_CT>' in texto:
                align = "center"
                texto = texto.replace('<TXT_ALIGN_CT>', '')
            elif '<TXT_ALIGN_RT>' in texto:
                align = "right"
                texto = texto.replace('<TXT_ALIGN_RT>', '')
            elif '<TXT_ALIGN_LT>' in texto:
                align = "left"
                texto = texto.replace('<TXT_ALIGN_LT>', '')

            # Código de barras CODE39
            if '<BARCODE_CODE39>' in texto:
                # Se espera: <BARCODE_CODE39>*DATA*
                match = re.search(r'<BARCODE_CODE39>\*(.*?)\*', texto)
                if match:
                    barcode_data = match.group(1)
                    x_pos = 120
                    tspl_lines.append(f'BARCODE {x_pos},{current_y},"39",50,1,0,2,2,"{self.limpiar_texto_utf8(barcode_data)}"')
                    current_y += (50 + 10)
                continue

            # Código de barras EAN13
            if '<BARCODE_EAN13>' in texto:
                match = re.search(r'<BARCODE_EAN13>(\d+)', texto)
                if match:
                    barcode_data = match.group(1)
                    x_pos = 120
                    tspl_lines.append(f'BARCODE {x_pos},{current_y},"EAN13",50,1,0,2,2,"{self.limpiar_texto_utf8(barcode_data)}"')
                    current_y += (50 + 10)
                continue

            # Limpiar etiquetas restantes no soportadas en TSPL mínimo
            for tag in ['<ESC>', '<BARCODE_HEIGHT>', '<BARCODE_WIDTH>', '<BARCODE_TXT_BLW>',
                        '<TXT_FONT_A>', '<TXT_FONT_B>', '<PAPER_FULL_CUT>', '<PAPER_PART_CUT>',
                        '<BARCODE_TXT_OFF>']:
                texto = texto.replace(tag, '')

            # Imprimir texto si existe
            texto = texto.strip()
            if texto:
                texto = self.limpiar_texto_utf8(texto)
                # Posiciones X aproximadas (sin conocer SIZE real)
                if align == "center":
                    x_pos = 160
                elif align == "right":
                    x_pos = 300
                else:
                    x_pos = 10

                tspl_lines.append(f'TEXT {x_pos},{current_y},"{font_size}",0,1,1,"{texto}"')
                current_y += y_step

        tspl_lines.append("PRINT 1")
        return "\n".join(tspl_lines) + "\n"

    def main(self):

        def reemplazar(cadena):
            """Convierte etiquetas a comandos ESC/POS para impresoras térmicas."""
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
            """Imprime en impresoras térmicas (ESC/POS) o convierte a TSPL si es impresora de etiqueta."""
            try:
                # Detectar tipo de impresora
                es_impresora_etiquetas = any(keyword in impresora.upper() for keyword in
                    ['ETIQUETA', 'LABEL', '4BARCODE', 'LDT114', '3NSTAR', 'TSC', 'ZEBRA', 'GODEX'])

                if es_impresora_etiquetas:
                    # Convertir ESC/POS recibido a TSPL mínimo
                    new_contenido = self.convertir_escpos_a_tspl(contenido)
                    self.log(f"TSPL (convertido) -> {impresora}: {len(new_contenido)} bytes")
                else:
                    new_contenido = reemplazar(contenido)
                    self.log(f"ESC/POS -> {impresora}: {len(new_contenido)} bytes")

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
            """
            Como imprimir_ZPL del código de producción - simple y directo.
            """
            try:
                new_contenido = ""
                
                if isinstance(contenido, str):
                    # EXACTO como el código de producción
                    new_contenido = contenido.replace('\n', '')
                    new_contenido = new_contenido.replace('<NL>', '\n')
                    
                elif isinstance(contenido, list):
                    # Si viene JSON, generar comandos SIMPLES
                    # SIN valores hardcodeados, dejar que la impresora use sus defaults
                    comandos = []
                    for item in contenido:
                        comandos.append("CLS")
                        
                        # Solo los campos básicos
                        if item.get("area"):
                            comandos.append(f'TEXT 10,10,"0",0,1,1,"{item.get("area")[:30]}"')
                        if item.get("nombre"):
                            comandos.append(f'TEXT 10,30,"0",0,1,1,"{item.get("nombre")[:30]}"')
                        
                        # Edad y género en una línea
                        edad = item.get("edad", "")
                        genero = item.get("genero", "")
                        if edad or genero:
                            linea = f"Edad:{edad} A     Genero:{genero}" if edad and genero else f"Edad:{edad} A" if edad else f"Genero:{genero}"
                            comandos.append(f'TEXT 10,50,"0",0,1,1,"{linea}"')
                        
                        # Código de barras
                        orden = item.get("orden", "")
                        if orden:
                            codigo = re.sub(r'[^0-9]', '', str(orden))
                            if not codigo.endswith('01'):
                                codigo = codigo + '01'
                            
                            # Código de barras sin especificar altura/ancho - usar defaults
                            comandos.append(f'BARCODE 10,70,"128",50,1,0,2,2,"{codigo}"')
                            # HRI manual
                            hri = f"(00) {codigo[2:]}" if len(codigo) > 2 else codigo
                            comandos.append(f'TEXT 10,125,"0",0,1,1,"{hri}"')
                        
                        comandos.append("PRINT 1")
                    
                    new_contenido = "\n".join(comandos)
                else:
                    self.log(f"Tipo no soportado: {type(contenido)}")
                    return

                # Enviar a imprimir - EXACTO como el código de producción
                if WINDOWS and new_contenido:
                    p = win32print.OpenPrinter(impresora)
                    win32print.SetDefaultPrinter(impresora)
                    imp = win32print.GetPrinter(p, 2)
                    job = win32print.StartDocPrinter(p, 1, ("printer job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
                    win32print.EndPagePrinter(p)
                    win32print.EndDocPrinter(p)
                    win32print.ClosePrinter(p)

            except Exception as e:
                self.log(f"Error: {str(e)}")

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

        # Configuración de servidores WebSocket - AHORA SOPORTA AMBOS PUERTOS
        PORTS = [9000, 9001]  # Windows 10 usa 9000, Windows 11 usa 9001
        HOST = "127.0.0.1"

        for port in PORTS:
            try:
                server = WebsocketServer(host=HOST, port=port)
            except Exception as e:
                self.log(f"No se pudo abrir puerto {port}: {e}. Se omite este puerto.")
                continue
            server.set_fn_message_received(message_received)
            self.servers.append(server)
            self.log(f"WebSocket server creado en {HOST}:{port}")

        if not self.servers:
            self.log("No hay servidores WebSocket inicializados. Verifique que los puertos 9000/9001 estén libres.")
            return

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


# Soporte para servicio Windows
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import pywintypes

    class TSSPrintService(win32serviceutil.ServiceFramework):
        _svc_name_ = "TSSPrintService"
        _svc_display_name_ = "TSSPrint_CRM2_V2"
        _svc_description_ = "Servicio de impresión para Windows 10 y 11, compatible con TSC, 3nStar y Zebra"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.print_service = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            if self.print_service:
                self.print_service.stop()

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.print_service = PrintService()
            self.print_service.start()

    # Si se ejecuta como servicio Windows o en modo consola
    if __name__ == '__main__':
        # Comandos de servicio conocidos -> delegar a pywin32
        service_cmds = {'install', 'remove', 'start', 'stop', 'restart', 'update', 'status'}
        # Comandos explícitos de consola
        console_cmds = {'debug', 'console', 'run'}

        if len(sys.argv) > 1 and sys.argv[1].lower() in service_cmds:
            win32serviceutil.HandleCommandLine(TSSPrintService)
        elif len(sys.argv) > 1 and sys.argv[1].lower() in console_cmds:
            print("""
        ╔════════════════════════════════════════════════════╗
        ║         TSC Windows 11 Fix - Print Service            ║
        ║           Version: 2025-TSC-WIN11-FIX                 ║
        ╚════════════════════════════════════════════════════╝
            """)
            print_service = PrintService()
            print_service.start()
        else:
            # Si fue lanzado por el Service Manager, esto funcionará.
            # Si fue lanzado desde consola sin argumentos, capturamos el 1063 y corremos en modo consola.
            try:
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(TSSPrintService)
                servicemanager.StartServiceCtrlDispatcher()
            except pywintypes.error as e:
                # 1063: The service process could not connect to the service controller
                if getattr(e, 'winerror', None) == 1063 or (hasattr(e, 'args') and e.args and e.args[0] == 1063):
                    print("""
        ╔════════════════════════════════════════════════════╗
        ║      Ejecutando en modo consola (no SCM detectado)    ║
        ║           Version: 2025-TSC-WIN11-FIX                 ║
        ╚════════════════════════════════════════════════════╝
                    """)
                    print_service = PrintService()
                    print_service.start()
                else:
                    raise
            except Exception:
                # Cualquier otro problema al iniciar como servicio -> consola como fallback seguro
                print("""
        ╔════════════════════════════════════════════════════╗
        ║      Ejecutando en modo consola (fallback general)    ║
        ║           Version: 2025-TSC-WIN11-FIX                 ║
        ╚════════════════════════════════════════════════════╝
                """)
                print_service = PrintService()
                print_service.start()

except ImportError:
    # Si no está disponible win32service, ejecutar como aplicación normal
    if __name__ == '__main__':
        print("""
        ╔════════════════════════════════════════════════════╗
        ║         TSC Windows 11 Fix - Print Service            ║
        ║           Version: 2025-TSC-WIN11-FIX                 ║
        ╚════════════════════════════════════════════════════╝
        """)

        print_service = PrintService()
        print_service.start()
# -*- coding: utf-8 -*-
import servicemanager
import socket
import sys
import win32service
import win32serviceutil
import win32event
import json
import time
import re
import threading
import traceback
import platform
import pywintypes
import win32print

from websocket_server import WebsocketServer

# INSTALAR PAQUETES NECESARIOS ARRIBA IMPORTADOS
# pip install pywin32 websocket-server pyinstaller

try:
    WINDOWS = True
except ImportError:
    WINDOWS = False
    print("win32print not available - running in Linux mode")

class PrintService:

    def __init__(self):
        self.running = False
        self.servers = []
        socket.setdefaulttimeout(60)
        
        # Detectar versión de Windows de forma robusta
        self.windows_version = None
        if WINDOWS:
            try:
                build = sys.getwindowsversion().build
                self.windows_version = 11 if build >= 22000 else 10
            except Exception:
                try:
                    version_str = platform.version()
                    parts = version_str.split('.')
                    build = int(parts[-1]) if parts and parts[-1].isdigit() else 0
                    self.windows_version = 11 if build >= 22000 else 10
                except Exception:
                    self.windows_version = 10

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {str(msg)}")

    def start(self):
        self.running = True
        try:
            self.main()
        except Exception as e:
            self.log(f"Error en start(): {str(e)}")
            raise

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
    
    def calcular_posicion_centrada(self, texto, ancho_etiqueta=180):
        """Calcula la posición X para centrar el texto basándose en su longitud"""
        # Estimación: cada carácter ocupa aproximadamente 4-5 puntos en fuente tamaño 2
        ancho_texto = len(texto) * 4
        x_centrado = max(0, (ancho_etiqueta - ancho_texto) // 2)
        return x_centrado
    
    def generar_tspl_generico(self, contenido, impresora):
        """Genera TSPL con centrado dinámico y código de barras CORREGIDO"""
        tspl_commands = []
        
        # Detectar tipo de impresora para ajustar configuración
        es_tsc = self.es_impresora_tsc(impresora)
        es_3nstar = self.es_impresora_3nstar(impresora)
        
        # Configuración según tipo de impresora
        if es_tsc and self.windows_version == 11:
            # TSC en Windows 11
            tspl_commands.append("SIZE 40 mm, 25 mm")
            tspl_commands.append("GAP 3 mm, 0 mm")
            tspl_commands.append("DIRECTION 1")
            tspl_commands.append("DENSITY 12")
            tspl_commands.append("SPEED 3")
            ancho_etiqueta = 150  # 40mm en puntos
        elif es_3nstar:
            # 3nStar
            tspl_commands.append("SIZE 59 mm, 25 mm")
            tspl_commands.append("GAP 3 mm, 0 mm")
            tspl_commands.append("DIRECTION 1")
            tspl_commands.append("DENSITY 12")
            tspl_commands.append("SPEED 3")
            ancho_etiqueta = 220  # 59mm en puntos
        else:
            # Genérico - usar configuración para 3nStar por defecto
            tspl_commands.append("SIZE 59 mm, 25 mm")
            tspl_commands.append("GAP 3 mm, 0 mm")
            tspl_commands.append("DIRECTION 1")
            tspl_commands.append("DENSITY 12")
            tspl_commands.append("SPEED 3")
            ancho_etiqueta = 220
        
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
                
                y_pos = 10  # Posición Y inicial
                
                if area:
                    x_area = self.calcular_posicion_centrada(area, ancho_etiqueta)
                    tspl_commands.append(f'TEXT {x_area},{y_pos},"2",0,1,1,"{self.limpiar_texto_utf8(area)}"')
                    y_pos += 25
                
                if nombre:
                    x_nombre = self.calcular_posicion_centrada(nombre, ancho_etiqueta)
                    tspl_commands.append(f'TEXT {x_nombre},{y_pos},"2",0,1,1,"{self.limpiar_texto_utf8(nombre)}"')
                    y_pos += 25
                
                linea_edad_genero = ""
                if edad:
                    # Verificar si ya tiene 'A' al final
                    edad_formateada = f"{edad} A" if not edad.endswith(' A') and not edad.endswith('A') else edad
                    linea_edad_genero = f"Edad:{edad_formateada}"
                
                if genero:
                    if linea_edad_genero:
                        linea_edad_genero += f"     Genero: {genero}"
                    else:
                        linea_edad_genero = f"Genero: {genero}"
                
                if linea_edad_genero:
                    x_edad_genero = self.calcular_posicion_centrada(linea_edad_genero, ancho_etiqueta)
                    tspl_commands.append(f'TEXT {x_edad_genero},{y_pos},"2",0,1,1,"{self.limpiar_texto_utf8(linea_edad_genero)}"')
                    y_pos += 30  # Un poco más de espacio antes del código
                
                if orden:
                    # Extraer solo dígitos
                    order_digits = re.sub(r'[^0-9]', '', str(orden))
                    
                    # Si el orden no termina en 01, agregarlo
                    if not order_digits.endswith('01'):
                        codigo_barras = order_digits + '01'
                    else:
                        codigo_barras = order_digits
                    
                    # Los paréntesis NO van en el código, solo en el texto visible
                    x_barcode = ancho_etiqueta // 2 - 40  # Centro menos offset para código de barras
                    barcode_height = 45
                    
                    # IMPORTANTE: readable=0 para que no muestre texto automático
                    tspl_commands.append(
                        f'BARCODE {x_barcode},{y_pos},"128",{barcode_height},0,0,2,2,"{codigo_barras}"'
                    )
                    
                    # Texto HRI manual debajo - aquí SÍ van los paréntesis
                    y_hri = y_pos + barcode_height + 10
                    if len(codigo_barras) > 2:
                        hri_text = f"(00) {codigo_barras[2:]}"
                    else:
                        hri_text = codigo_barras
                    
                    x_hri = self.calcular_posicion_centrada(hri_text, ancho_etiqueta)
                    tspl_commands.append(
                        f'TEXT {x_hri},{y_hri},"2",0,1,1,"{self.limpiar_texto_utf8(hri_text)}"'
                    )
            
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
                    x_barcode = 160 - (len(barcode_data) * 2)
                    tspl += f'BARCODE {x_barcode},120,"39",50,1,0,2,2,"{barcode_data}"\n'
                continue
            
            # Detectar código de barras EAN13
            if '<BARCODE_EAN13>' in texto:
                match = re.search(r'<BARCODE_EAN13>(\d+)$', texto)
                if match:
                    barcode_data = match.group(1)
                    tspl += f'BARCODE 120,120,"EAN13",50,1,0,2,2,"{barcode_data}"\n'
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
                
                # Calcular posición X basada en alineación y longitud del texto
                if align == "center":
                    x_pos = self.calcular_posicion_centrada(texto, 320)
                elif align == "right":
                    x_pos = 320 - (len(texto) * 4)
                else:  # left
                    x_pos = 20
                
                tspl += f'TEXT {x_pos},120,"{font_size}",0,1,1,"{texto}"\n'
        
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
                
            except Exception as e:
                self.log(f"Error printing to thermal printer {impresora}: {str(e)}")
                traceback.print_exc()
        
        def imprimir_etiqueta(contenido, impresora):
            try:
                new_contenido = ""
                
                # Detectar tipo de impresora
                es_tsc = self.es_impresora_tsc(impresora)
                es_3nstar = self.es_impresora_3nstar(impresora)
                usar_modo_tsc_win11 = es_tsc and self.windows_version == 11
                
                if isinstance(contenido, list):
                    new_contenido = self.generar_tspl_generico(contenido, impresora)
                    
                elif isinstance(contenido, str):
                    if contenido.strip().upper().startswith(('SIZE', 'CLS', 'TEXT', 'BARCODE')):
                        new_contenido = contenido
                    else:
                        new_contenido = contenido.replace('\n', '').replace('<NL>', '\n')
                else:
                    self.log(f"ERROR: Tipo de contenido no soportado: {type(contenido)}")
                    return
                
                if WINDOWS and new_contenido:
                    
                    p = win32print.OpenPrinter(impresora)
                    win32print.StartDocPrinter(p, 1, ("TSC Label Job" if es_tsc else "Label Job", None, "RAW"))
                    win32print.StartPagePrinter(p)
                    
                    # Para TSC en Windows 11, enviar línea por línea
                    if usar_modo_tsc_win11:
                        for line in new_contenido.split('\n'):
                            if line:
                                win32print.WritePrinter(p, bytes(line + '\n', 'utf-8'))
                    else:
                        win32print.WritePrinter(p, bytes(new_contenido, 'utf-8'))
                    
                    win32print.EndPagePrinter(p)
                    win32print.EndDocPrinter(p)
                    win32print.ClosePrinter(p)
                    
            except Exception as e:
                self.log(f"ERROR en 'imprimir_etiqueta': {str(e)}")
                traceback.print_exc()
                
        def message_received(client, server, message):
            # Descomponer JSON
            try:                
                JSON=json.loads(message)
                contenido=JSON['contenido']
                impresora=JSON['impresora']
                tipo = JSON.get('tipo', 'TERMICA').upper()                
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
            try:
                server = WebsocketServer(host=HOST, port=port)
            except Exception as e:
                self.log(f"No se pudo abrir puerto {port}: {e}")
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
        finally:
            self.stop()
        
# Soporte para servicio Windows
try:
    class TSSPrintService(win32serviceutil.ServiceFramework):
        _svc_name_ = "TSSPrintService"
        _svc_display_name_ = "TSSPrint_CRM2_V2"
        _svc_description_ = "Servicio de impresión para Windows 10 y 11, compatible con TSC, 3nStar y zebra"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.print_service = None

        def SvcStop(self):
            # Decir a la SCM cuando detener el servicio
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            # Detener el evento
            win32event.SetEvent(self.hWaitStop)
            if self.print_service:
                self.print_service.stop()

        def SvcDoRun(self):
            try:
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, '')
                )
                
                # Crear e inicializar el servicio de impresión
                self.print_service = PrintService()
                self.print_service.log("Servicio TSSPrint iniciado correctamente")
                
                # Iniciar el servicio
                self.print_service.start()
                
                # Esperar hasta que se solicite parar
                win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
                
            except Exception as e:
                servicemanager.LogErrorMsg(f"Error en SvcDoRun: {str(e)}")
                self.SvcStop()

    # Si se ejecuta como servicio Windows o en modo consola
    if __name__ == '__main__':
        # Comandos de servicio conocidos
        service_cmds = {'install', 'remove', 'start', 'stop', 'restart', 'update', 'status'}
        # Comandos explícitos de consola
        console_cmds = {'debug', 'console', 'run'}

        if len(sys.argv) > 1 and sys.argv[1].lower() in service_cmds:
            # Ejecutar comandos de servicio
            try:
                win32serviceutil.HandleCommandLine(TSSPrintService)
            except Exception as e:
                print(f"Error en comando de servicio: {e}")
                sys.exit(1)
        elif len(sys.argv) > 1 and sys.argv[1].lower() in console_cmds:
            # Ejecutar en modo consola
            print("Ejecutando en modo consola...")
            print_service = PrintService()
            try:
                print_service.start()
            except KeyboardInterrupt:
                print("Deteniendo servicio...")
                print_service.stop()
        else:
            # Intento de ejecutar como servicio
            try:
                # Verificar si estamos corriendo como servicio
                servicemanager.Initialize()
                servicemanager.PrepareToHostSingle(TSSPrintService)
                servicemanager.StartServiceCtrlDispatcher()
            except pywintypes.error as e:
                error_code = getattr(e, 'winerror', None) or (e.args[0] if e.args else None)
                if error_code == 1063:
                    # Error 1063: El servicio no está siendo ejecutado por Service Control Manager
                    # Ejecutar en modo consola
                    print("Ejecutando en modo consola (no iniciado como servicio)...")
                    print_service = PrintService()
                    try:
                        print_service.start()
                    except KeyboardInterrupt:
                        print("Deteniendo servicio...")
                        print_service.stop()
                else:
                    print(f"Error del servicio: {e}")
                    raise
            except Exception as e:
                print(f"Error general: {e}")
                # Como último recurso, ejecutar en modo consola
                print_service = PrintService()
                try:
                    print_service.start()
                except KeyboardInterrupt:
                    print("Deteniendo servicio...")
                    print_service.stop()

except ImportError:
    # Si no está disponible win32service, ejecutar como aplicación normal
    if __name__ == '__main__':
        print_service = PrintService()
        print_service.start()
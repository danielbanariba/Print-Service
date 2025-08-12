# -*- coding: utf-8 -*-
import servicemanager
import socket
import sys
import win32service
import win32serviceutil
import win32event
import pythoncom

from websocket_server import WebsocketServer
import os, sys
import win32print
import pywintypes
import json
from win32printing import Printer

# INSTALAR PAQUETES NECESARIOS ARRIBA IMPORTADOS
# pip install pywin32
# pip install websocket-server

class PySvc(win32serviceutil.ServiceFramework):    
    # Puede Iniciar y Detener el servicio con el siguiente nombre en la SCM
    _svc_name_ = "TSSPrint_Analiza"
    # Muestra el nombre que aparece en en listado de servicios de SCM
    # Control Manager (SCM)
    _svc_display_name_ = "TSSPrint Analiza V1.0"
    # La Descripcion del servicio en cuestion en la  SCM
    _svc_description_ = "Este Servicio Administra Cliente de Impresion Lab Analiza"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        # crear un evento para escuchar solicitudes de detención
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))
    
    #  LOGICA CENTRAL DEL SERVICIO
    def SvcDoRun(self):
        
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.main()
   
    # #  FUNCIONES IMPRESION
    def main(self):        

        rc = None
        while rc != win32event.WAIT_OBJECT_0:
            
            #GESTION DE IMPRESION TERMICA
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
                cadena=cadena.replace("<NO_NEGRITA>","\u001b\u0045\u0000") # Desactivar Negrita
                cadena=cadena.replace("<NEGRITA>","\u001b\u0045\u0001") # Activar Negrita
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
                cadena=cadena.replace("<BARCODE_WIDTH>","\u001d\u0077\u0002") # CodigoBarra Ancho  [2-6]
                cadena=cadena.replace("<BARCODE_UPC_A>","\u001d\u006b\u0000") # CodigoBarra Tipo UPC-A
                cadena=cadena.replace("<BARCODE_UPC_E>","\u001d\u006b\u0001") # CodigoBarra Tipo UPC-E
                cadena=cadena.replace("<BARCODE_EAN13>","\u001d\u006b\u0003") # CodigoBarra Tipo EAN13
                cadena=cadena.replace("<BARCODE_EAN8>","\u001d\u006b\u0003") # CodigoBarra Tipo EAN8                
                cadena=cadena.replace("<BARCODE_128>","\u001d\u006b\u0008") # CodigoBarra Tipo ITF
                cadena=cadena.replace("<BARCODE_NW7>","\u001d\u006b\u0006") # CodigoBarra Tipo NW7
                cadena=cadena.replace("<BARCODE_2D>","\u001d\u006b\u0006") # CodigoBarra Tipo NW7
                cadena=cadena.replace("<BARCODE_93>","\u001d\u006b\u0007") # CodigoBarra Tipo CODE39
                #codigo de barra code39
                cadena=cadena.replace("<BARCODE_CODE39>","\u001d\u0068\u0064\u001d\u0077\u0002\u001d\u0048\u0002\u001d\u0066\u0000\u001d\u006b\u0004")

                cadena=cadena.replace("<BARCODE_ITF>","\u001d\u006b\u0005") # CodigoBarra Tipo ITF
             
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

                return cadena
            def imprimir_ter(contenido,impresora):
                # Indicar nombre de impresora
                new_contenido=reemplazar(contenido)
                p = win32print.OpenPrinter(impresora)
                win32print.SetDefaultPrinter(impresora)
                imp=win32print.GetPrinter(p,2)
                job = win32print.StartDocPrinter (p, 1, ("printer job", None, "RAW"))
                win32print.StartPagePrinter(p)
                win32print.WritePrinter(p, bytes(new_contenido,'utf-8'))
                win32print.EndPagePrinter (p)
     
          
            #GESTION DE IMPRESION IMPACTO            
            def conversor(linea,printer):
                            #valores por defecto
                            size={"height": 12}
                            _aling="center"
                            linea=linea.replace('<NL>','\n')
                            linea=linea.replace('<MARGEN>','    ')
                            if linea.find('<MINI>')!=-1:
                                size={"height": 8}
                                linea=linea.replace('<MINI>','')
                            if linea.find('<PEQUENO>')!=-1:
                                size={"height": 9}
                                linea=linea.replace('<PEQUENO>','')
                            if linea.find('<MEDIANO>')!=-1:
                                size={"height": 15}
                                linea=linea.replace('<MEDIANO>','')
                            if linea.find('<NORMAL>')!=-1:
                                size={"height": 12}
                                linea=linea.replace('<NORMAL>','')
                            if linea.find('<GRANDE>')!=-1:
                                size={"height": 18}
                                linea=linea.replace('<GRANDE>','')
                            #MANEJO DE NEGRITA
                            if linea.find('<NEGRITA>')!=-1:
                                size['weight']=700
                                linea=linea.replace('<NEGRITA>','')
                            else:
                                size['weight']=400
                            #MANEJO DE ALINEAMIENTO
                            if linea.find('<IZQUIERDA>')!=-1:
                                _aling="left"
                                linea=linea.replace('<IZQUIERDA>','')
                            if linea.find('<CENTRO>')!=-1:
                                _aling="center"
                                linea=linea.replace('<CENTRO>','')
                            if linea.find('<DERECHA>')!=-1:
                                _aling="right"
                                linea=linea.replace('<DERECHA>','')
                            printer.text(linea, font_config=size , align=_aling )
            def imprimir_impac(contenido,impresora):
                #contenido=contenido.replace('<NL>','\n')
                with Printer(linegap=1, printer_name=impresora) as printer:
                    lineas=contenido.split('\n')
                    for l in lineas:
                        conversor(l,printer)

            #GESTION DE IMPRESION ETIQUETA
            def reemplazarZPL(cadena):
                cadena=cadena.replace('\n','')
                cadena=cadena.replace('<NL>','\n')
                return cadena
            def imprimir_ZPL(contenido,impresora):
                            # Indicar nombre de impresora
                            new_contenido=reemplazarZPL(contenido)
                            p = win32print.OpenPrinter(impresora)
                            win32print.SetDefaultPrinter(impresora)
                            imp=win32print.GetPrinter(p,2)
                            job = win32print.StartDocPrinter (p, 1, ("printer job", None, "RAW"))
                            win32print.StartPagePrinter(p)
                            win32print.WritePrinter(p, bytes(new_contenido,'utf-8'))
                            win32print.EndPagePrinter (p)    

            # Llamar cuando el Cliente envia el mensaje
            def message_received(client, server, message):
                # Descomponer JSON
                JSON=json.loads(message)
                contenido=JSON['contenido']
                impresora=JSON['impresora']
                if JSON['tipo']=='TERMICA':
                    imprimir_ter(contenido,impresora)
                if JSON['tipo']=='IMPACTO':
                    contenido=contenido.replace('<SEP>','\n')
                    imprimir_impac(contenido,impresora)
                if JSON['tipo']=='ETIQUETA':
                    imprimir_ZPL(contenido,impresora)                

            PORT=9000
            server = WebsocketServer(PORT)
            server.set_fn_message_received(message_received)
            server.run_forever()
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)                        
        
    
    # Llamar para detener el servicio  
    def SvcStop(self):
        # Decir a la SCM cuando detener el servicio
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        # Detener el evento
        win32event.SetEvent(self.hWaitStop)
        sys.exit (0)

    # a sobre-escribir
    def start(self): pass

    # a sobre-escribir
    def stop(self): pass
    
        
if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PySvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PySvc)
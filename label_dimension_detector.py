# -*- coding: utf-8 -*-
"""
Detector Automático de Dimensiones de Etiquetas
Prueba diferentes tamaños y posiciones para determinar el área imprimible real
"""
import win32print
import time
import json

class LabelDimensionDetector:
    
    def __init__(self):
        self.printer_name = None
        self.results = {}
    
    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    
    def get_available_printers(self):
        """Lista todas las impresoras disponibles"""
        printers = []
        for printer in win32print.EnumPrinters(2):
            printers.append(printer[2])
        return printers
    
    def select_printer(self):
        """Permite seleccionar la impresora de etiquetas"""
        printers = self.get_available_printers()
        
        print("\n🖨️  IMPRESORAS DISPONIBLES:")
        for i, printer in enumerate(printers, 1):
            print(f"  {i}. {printer}")
        
        while True:
            try:
                choice = int(input(f"\nSelecciona tu impresora de etiquetas (1-{len(printers)}): "))
                if 1 <= choice <= len(printers):
                    self.printer_name = printers[choice-1]
                    self.log(f"Impresora seleccionada: {self.printer_name}")
                    break
                else:
                    print("❌ Número inválido")
            except ValueError:
                print("❌ Ingresa un número válido")
    
    def print_tspl(self, tspl_commands):
        """Envía comandos TSPL a la impresora"""
        try:
            p = win32print.OpenPrinter(self.printer_name)
            win32print.StartDocPrinter(p, 1, ("Dimension Test", None, "RAW"))
            win32print.StartPagePrinter(p)
            win32print.WritePrinter(p, bytes(tspl_commands, 'utf-8'))
            win32print.EndPagePrinter(p)
            win32print.EndDocPrinter(p)
            win32print.ClosePrinter(p)
            return True
        except Exception as e:
            self.log(f"❌ Error imprimiendo: {e}")
            return False
    
    def test_label_sizes(self):
        """Prueba diferentes tamaños de etiqueta comunes"""
        
        # Tamaños comunes de etiquetas en dots (203dpi)
        common_sizes = [
            {"name": "25x15mm", "width": 200, "height": 120, "gap": 16},
            {"name": "30x20mm", "width": 240, "height": 160, "gap": 16}, 
            {"name": "40x25mm", "width": 320, "height": 200, "gap": 24},
            {"name": "50x30mm", "width": 400, "height": 240, "gap": 24},
            {"name": "60x40mm", "width": 480, "height": 320, "gap": 32},
            {"name": "70x50mm", "width": 560, "height": 400, "gap": 32},
        ]
        
        print(f"\n🧪 PROBANDO TAMAÑOS DE ETIQUETA...")
        print("Se imprimirán etiquetas de prueba con marcos CENTRADOS.")
        print("Observa cuál se imprime completamente dentro del papel.\n")
        
        for i, size in enumerate(common_sizes, 1):
            self.log(f"Probando tamaño {i}/6: {size['name']} ({size['width']}x{size['height']} dots)")
            
            # Calcular posiciones más centradas (empezar más hacia la derecha)
            left_margin = max(40, size['width'] // 8)  # Al menos 40 dots del borde
            right_pos = size['width'] - left_margin - 20
            top_margin = 20
            bottom_pos = size['height'] - 40
            center_x = size['width'] // 2
            center_y = size['height'] // 2
            
            tspl = f"""SIZE {size['width']}, {size['height']}
GAP {size['gap']}, 0
DIRECTION 1
DENSITY 12
SPEED 3
CLS

REM === MARCO CENTRADO PARA {size['name']} ===
TEXT {left_margin},{top_margin},"1",0,1,1,"TL"
TEXT {right_pos},{top_margin},"1",0,1,1,"TR"
TEXT {left_margin},{bottom_pos},"1",0,1,1,"BL"
TEXT {right_pos},{bottom_pos},"1",0,1,1,"BR"

TEXT {center_x-30},{center_y-15},"2",0,1,1,"{size['name']}"
TEXT {center_x-50},{center_y+10},"1",0,1,1,"{size['width']}x{size['height']} dots"

BOX {left_margin-10},{top_margin-10},{right_pos+20},{bottom_pos+20},2

PRINT 1
"""
            
            if self.print_tspl(tspl):
                input(f"  ✅ Etiqueta {size['name']} enviada. Presiona ENTER para continuar...")
            else:
                print(f"  ❌ Error enviando etiqueta {size['name']}")
            
            time.sleep(1)
        
        print(f"\n📏 ¿Cuál de las etiquetas se imprimió COMPLETAMENTE dentro del papel?")
        print("(Debe verse el marco completo y todo el texto legible)\n")
        
        for i, size in enumerate(common_sizes, 1):
            print(f"  {i}. {size['name']} - {size['width']}x{size['height']} dots")
        
        while True:
            try:
                choice = int(input(f"\nElige el tamaño correcto (1-6): "))
                if 1 <= choice <= 6:
                    selected_size = common_sizes[choice-1]
                    self.results['detected_size'] = selected_size
                    self.log(f"✅ Tamaño detectado: {selected_size['name']}")
                    return selected_size
                else:
                    print("❌ Número inválido")
            except ValueError:
                print("❌ Ingresa un número válido")
    
    def test_printable_area(self, label_size):
        """Detecta el área imprimible real probando posiciones extremas"""
        
        print(f"\n🎯 DETECTANDO ÁREA IMPRIMIBLE REAL...")
        print("Se probarán diferentes posiciones X para encontrar los límites.\n")
        
        width = label_size['width']
        height = label_size['height']
        gap = label_size['gap']
        
        # Probar posiciones X más centradas (empezar más hacia la derecha)
        test_positions_x = [40, 50, 60, 70, 80, 90, 100, 120]
        
        print("Probando posiciones X (empezando más centrado):")
        
        min_x = 60  # Valor por defecto más centrado
        
        for x in test_positions_x:
            self.log(f"Probando posición X={x}")
            
            tspl = f"""SIZE {width}, {height}
GAP {gap}, 0
DIRECTION 1
CLS

TEXT {x},30,"2",0,1,1,"X={x}"
TEXT {x},60,"1",0,1,1,"¿Se ve completo?"
TEXT {x},80,"1",0,1,1,"Todo el texto aqui"
BOX {x},20,{x+120},100,1

PRINT 1
"""
            
            if self.print_tspl(tspl):
                response = input(f"  ✅ ¿Se ve TODO el contenido completo en X={x}? (s/n): ").lower()
                if response == 's':
                    min_x = x
                    self.log(f"✅ Posición X={x} confirmada como válida")
                    break
                else:
                    self.log(f"❌ Posición X={x} se corta o no se ve bien")
            time.sleep(0.5)
        
        # Probar área de centrado con posiciones más realistas
        print(f"\nProbando área central para alineación óptima:")
        
        center_x = width // 2
        # Usar posiciones más centradas basadas en el min_x encontrado
        test_centers = [center_x - 30, center_x, center_x + 30]
        
        optimal_center = center_x  # Valor por defecto
        
        for cx in test_centers:
            if cx < min_x:  # No probar posiciones que sabemos que no funcionan
                continue
                
            self.log(f"Probando centro en X={cx}")
            
            tspl = f"""SIZE {width}, {height}
GAP {gap}, 0
DIRECTION 1
CLS

TEXT {cx-40},35,"2",0,1,1,"CENTRO"
TEXT {cx-30},60,"1",0,1,1,"X={cx}"
TEXT {cx-50},80,"1",0,1,1,"Texto centrado aqui"
BOX {cx-45,25,cx+45,95,1}

PRINT 1
"""
            
            if self.print_tspl(tspl):
                response = input(f"  ✅ ¿Está bien centrado en X={cx}? (s/n): ").lower()
                if response == 's':
                    optimal_center = cx
                    self.log(f"✅ Centro óptimo encontrado en X={cx}")
                    break
            time.sleep(0.5)
        
        # Calcular posiciones óptimas con base en los resultados
        optimal_left = min_x
        optimal_center = optimal_center
        optimal_right = min(width - 60, optimal_center + (width - optimal_center) // 2)  # Más conservador
        
        area_info = {
            'left_margin': optimal_left,
            'center_position': optimal_center, 
            'right_position': optimal_right,
            'usable_width': optimal_right - optimal_left,
            'total_width': width,
            'total_height': height
        }
        
        self.log(f"📊 Área imprimible detectada:")
        self.log(f"   - Izquierda: X={optimal_left}")
        self.log(f"   - Centro: X={optimal_center}")  
        self.log(f"   - Derecha: X={optimal_right}")
        self.log(f"   - Ancho útil: {area_info['usable_width']} dots")
        
        self.results['printable_area'] = area_info
        return area_info
    
    def generate_config(self):
        """Genera la configuración automática detectada"""
        
        if 'detected_size' not in self.results or 'printable_area' not in self.results:
            print("❌ Faltan datos de detección")
            return None
        
        size = self.results['detected_size']
        area = self.results['printable_area']
        
        config = {
            'printer_name': self.printer_name,
            'label_dimensions': {
                'width_dots': size['width'],
                'height_dots': size['height'], 
                'gap_dots': size['gap'],
                'name': size['name']
            },
            'optimal_positions': {
                'left_align': area['left_margin'],
                'center_align': area['center_position'],
                'right_align': area['right_position']
            },
            'tspl_config': {
                'SIZE': f"{size['width']}, {size['height']}",
                'GAP': f"{size['gap']}, 0",
                'DIRECTION': "1",
                'DENSITY': "12",
                'SPEED': "3"
            }
        }
        
        return config
    
    def save_config(self, config):
        """Guarda la configuración detectada"""
        filename = f"label_config_{self.printer_name.replace(' ', '_')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Configuración guardada en: {filename}")
            return filename
        except Exception as e:
            self.log(f"❌ Error guardando configuración: {e}")
            return None
    
    def print_summary(self, config):
        """Muestra resumen de la detección"""
        print(f"\n" + "="*60)
        print(f"🎉 DETECCIÓN COMPLETADA - RESUMEN")
        print(f"="*60)
        print(f"📏 Tamaño detectado: {config['label_dimensions']['name']}")
        print(f"📐 Dimensiones: {config['label_dimensions']['width_dots']}x{config['label_dimensions']['height_dots']} dots")
        print(f"📍 Posición izquierda óptima: X={config['optimal_positions']['left_align']}")
        print(f"📍 Posición central óptima: X={config['optimal_positions']['center_align']}")
        print(f"📍 Posición derecha óptima: X={config['optimal_positions']['right_align']}")
        print(f"🖨️  Impresora: {config['printer_name']}")
        print(f"="*60)
    
    def quick_position_test(self):
        """Prueba rápida de posiciones para ajuste fino"""
        print(f"\n⚡ PRUEBA RÁPIDA DE POSICIONAMIENTO")
        print("Vamos a probar varias posiciones X rápidamente.\n")
        
        # Usar un tamaño estándar para pruebas rápidas
        width, height = 320, 200  # 40x25mm común
        gap = 24
        
        # Posiciones de prueba más centradas
        positions_to_test = [60, 80, 100, 120, 140]
        
        for pos in positions_to_test:
            self.log(f"Probando posición rápida X={pos}")
            
            tspl = f"""SIZE {width}, {height}
GAP {gap}, 0
DIRECTION 1
CLS

TEXT {pos},25,"2",0,1,1,"Posicion X={pos}"
TEXT {pos},50,"1",0,1,1,"Orlin Ariel Corea Garcia"
TEXT {pos},75,"1",0,1,1,"Edad: 39 A    Genero: M"
BARCODE {pos},100,"128",40,1,0,2,2,"123456789"

PRINT 1
"""
            
            if self.print_tspl(tspl):
                response = input(f"  ✅ ¿Posición X={pos} se ve bien? (s/n/q para salir): ").lower()
                if response == 's':
                    return pos
                elif response == 'q':
                    break
            time.sleep(0.5)
        
        return None
    
    def run_detection(self):
        """Ejecuta el proceso completo de detección"""
        print("🔍 DETECTOR AUTOMÁTICO DE DIMENSIONES DE ETIQUETAS")
        print("="*55)
        
        # Opción de prueba rápida
        quick_test = input("\n¿Quieres hacer una prueba rápida de posicionamiento? (s/n): ").lower()
        
        if quick_test == 's':
            self.select_printer()
            optimal_x = self.quick_position_test()
            if optimal_x:
                print(f"\n🎉 Posición óptima encontrada: X={optimal_x}")
                print(f"💡 Usa este valor en tu código: TEXT {optimal_x},Y,...")
                return
        
        # Proceso completo
        # Paso 1: Seleccionar impresora
        self.select_printer()
        
        # Paso 2: Detectar tamaño de etiqueta
        detected_size = self.test_label_sizes()
        
        # Paso 3: Detectar área imprimible
        printable_area = self.test_printable_area(detected_size)
        
        # Paso 4: Generar configuración
        config = self.generate_config()
        
        if config:
            # Paso 5: Mostrar resumen
            self.print_summary(config)
            
            # Paso 6: Guardar configuración
            config_file = self.save_config(config)
            
            print(f"\n💡 PRÓXIMOS PASOS:")
            print(f"1. Usa estos valores en tu código de impresión:")
            print(f"   - SIZE {config['tspl_config']['SIZE']}")
            print(f"   - Posición izquierda: X={config['optimal_positions']['left_align']}")
            print(f"   - Posición central: X={config['optimal_positions']['center_align']}")
            print(f"2. El archivo {config_file} contiene toda la configuración")
            
            return config
        else:
            print("❌ Error generando configuración")
            return None

def main():
    detector = LabelDimensionDetector()
    
    try:
        config = detector.run_detection()
        
        if config:
            print(f"\n✅ Detección exitosa! Usa esta configuración en tu servicio de impresión.")
        else:
            print(f"\n❌ Detección fallida. Intenta nuevamente.")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Detección cancelada por el usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")

if __name__ == '__main__':
    main()
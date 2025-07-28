import json
import asyncio
import websockets

async def detect_port():
    """Detecta automáticamente qué puerto usar"""
    ports = [9000, 9001]
    
    for port in ports:
        uri = f"ws://localhost:{port}"
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=2.0
            )
            await websocket.close()
            return port
        except:
            continue
    
    return None

async def send_order():
    """Envía una orden de prueba al servicio de impresión"""
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║              IMPRESIÓN DE ORDEN - PRUEBA              ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Contenido de la orden (formato similar a la factura pero más simple)
    order_content = """<ESC><TXT_NORMAL>
<TXT_ALIGN_CT><NEGRITA>LABORATORIOS ANALIZA<NO_NEGRITA><NL>
<TXT_ALIGN_CT>ORDEN DE LABORATORIO<NL>
<NL>
======================================<NL>
<NL>
<TXT_ALIGN_LT><NEGRITA>No. Orden:<NO_NEGRITA> 0001562622178<NL>
<TXT_ALIGN_LT><NEGRITA>Fecha:<NO_NEGRITA> 18/07/2025 10:30 AM<NL>
<TXT_ALIGN_LT><NEGRITA>Sucursal:<NO_NEGRITA> Hospital Escuela<NL>
<NL>
<NEGRITA>DATOS DEL PACIENTE<NO_NEGRITA><NL>
<TXT_ALIGN_LT>Nombre: Juan Pérez García<NL>
<TXT_ALIGN_LT>Identidad: 0801-1990-12345<NL>
<TXT_ALIGN_LT>Edad: 35 años<NL>
<TXT_ALIGN_LT>Sexo: Masculino<NL>
<NL>
<NEGRITA>EXAMENES SOLICITADOS<NO_NEGRITA><NL>
--------------------------------------<NL>
1. Hemograma Completo<NL>
2. Glucosa en Ayunas<NL>
3. Creatinina<NL>
4. Colesterol Total<NL>
5. Triglicéridos<NL>
--------------------------------------<NL>
<NL>
<NEGRITA>MUESTRAS REQUERIDAS<NO_NEGRITA><NL>
- Tubo Rojo (01): Química<NL>
- Tubo Lila (02): Hematología<NL>
<NL>
<TXT_ALIGN_CT><NEGRITA>CÓDIGO DE BARRAS<NO_NEGRITA><NL>
<BARCODE_CODE39>*0001562622178*<NL>
<NL>
<TXT_ALIGN_CT>** URGENTE **<NL>
<NL>
<TXT_ALIGN_LT>Recepcionista: María López<NL>
<TXT_ALIGN_LT>Médico: Dr. Carlos Mendoza<NL>
<NL>
======================================<NL>
<TXT_ALIGN_CT>Conservar esta orden<NL>
<TXT_ALIGN_CT>para retirar resultados<NL>
<NL>
<PAPER_PART_CUT>"""

    # Detectar puerto
    port = await detect_port()
    if port is None:
        print("✗ ERROR: No se pudo detectar el servicio de impresión")
        print("Asegúrate de que TSSPrint_multiport.py esté ejecutándose")
        return
    
    print(f"✓ Puerto detectado: {port}")
    
    # Crear estructura de datos
    data_to_send = {
        'contenido': order_content,
        'impresora': 'TERMICA',
        'tipo': 'TERMICA'
    }
    
    # Enviar orden
    uri = f"ws://localhost:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            print("\nEnviando orden de laboratorio...")
            json_payload = json.dumps(data_to_send)
            await websocket.send(json_payload)
            print("✓ Orden enviada exitosamente")
            
    except Exception as e:
        print(f"✗ Error al enviar: {e}")

async def send_multiple_orders():
    """Envía múltiples órdenes de prueba"""
    
    print("\n=== ENVIANDO MÚLTIPLES ÓRDENES ===\n")
    
    port = await detect_port()
    if port is None:
        print("✗ No se pudo detectar el servicio")
        return
    
    orders = [
        {"numero": "0001562622178", "paciente": "Juan Pérez", "examenes": 5},
        {"numero": "0001562622179", "paciente": "María García", "examenes": 3},
        {"numero": "0001562622180", "paciente": "Carlos López", "examenes": 7}
    ]
    
    uri = f"ws://localhost:{port}"
    
    for order in orders:
        order_content = f"""<ESC><TXT_NORMAL>
<TXT_ALIGN_CT><NEGRITA>LABORATORIOS ANALIZA<NO_NEGRITA><NL>
<TXT_ALIGN_CT>ORDEN #{order['numero']}<NL>
<NL>
<TXT_ALIGN_LT>Paciente: {order['paciente']}<NL>
<TXT_ALIGN_LT>Exámenes: {order['examenes']}<NL>
<NL>
<TXT_ALIGN_CT><BARCODE_CODE39>*{order['numero']}*<NL>
<NL>
<PAPER_PART_CUT>"""

        data = {
            'contenido': order_content,
            'impresora': 'TERMICA',
            'tipo': 'TERMICA'
        }
        
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(data))
                print(f"✓ Orden {order['numero']} enviada")
                await asyncio.sleep(2)  # Pausa entre órdenes
        except Exception as e:
            print(f"✗ Error con orden {order['numero']}: {e}")

async def main():
    print("""
    Opciones:
    1. Enviar una orden de prueba
    2. Enviar múltiples órdenes
    3. Salir
    """)
    
    opcion = input("Selecciona una opción (1-3): ")
    
    if opcion == "1":
        await send_order()
    elif opcion == "2":
        await send_multiple_orders()
    elif opcion == "3":
        print("Saliendo...")
    else:
        print("Opción no válida")

if __name__ == "__main__":
    asyncio.run(main())
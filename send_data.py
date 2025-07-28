from jinja2 import Environment, FileSystemLoader
import json
import asyncio
import websockets
import platform

async def detect_port():
    """Detecta automáticamente qué puerto usar"""
    ports = [9000, 9001]
    
    for port in ports:
        uri = f"ws://localhost:{port}"
        try:
            # Intentar conectar brevemente
            websocket = await asyncio.wait_for(
                websockets.connect(uri),
                timeout=2.0
            )
            await websocket.close()
            print(f"✓ Puerto {port} disponible")
            return port
        except:
            continue
    
    print("✗ No se encontró ningún puerto disponible")
    return None

async def send_to_printer(data, port=None):
    """Envía datos al servicio de impresión"""
    if port is None:
        port = await detect_port()
        if port is None:
            raise Exception("No se pudo conectar al servicio de impresión")
    
    uri = f"ws://localhost:{port}"
    async with websockets.connect(uri) as websocket:
        json_payload = json.dumps(data)
        await websocket.send(json_payload)
        return True

async def main():
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║           ENVÍO DE FACTURAS - MULTI-PUERTO            ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Detectar sistema operativo
    os_info = platform.system() + " " + platform.release()
    print(f"Sistema operativo: {os_info}")
    
    # Load JSON data
    with open('data.json', encoding='utf-8') as f:
        data = json.load(f)

    # Extract the payload
    payload = data['payload']

    # Ensure numeric values are floats
    for key in ['subtotal', 'credito_aseguradora', 'total_cliente', 'descuento']:
        if key in payload:
            payload[key] = float(payload[key])

    # Set up the Jinja2 environment
    env = Environment(loader=FileSystemLoader('.'))

    # Render the template
    template = env.get_template('planitlla_final.html')
    rendered_html = template.render(dat=payload)

    print("\n=== FACTURA ORIGINAL ===")
    print(f"Número de orden: {payload.get('orden', 'N/A')}")
    print(f"Cliente: {payload.get('cliente_nombre', 'N/A')}")
    print(f"Total: ${payload.get('total', 0)}")

    # Save the rendered HTML to a file
    with open('output.html', 'w', encoding='utf-8') as f:
        f.write(rendered_html)

    # Create the data structure to be sent
    data_to_send = {
        'contenido': rendered_html,
        'impresora': 'TERMICA',
        'tipo': 'TERMICA'
    }

    # Load JSON data for the copy
    with open('data_2.json', encoding='utf-8') as f:
        data_copy = json.load(f)

    # Extract the payload for the copy
    payload_copy = data_copy['payload']

    # Ensure numeric values are floats for copy
    for key in ['subtotal', 'credito_aseguradora', 'total_cliente', 'descuento']:
        if key in payload_copy:
            payload_copy[key] = float(payload_copy[key])

    # Render the copy
    rendered_html_copy = template.render(dat=payload_copy)

    print("\n=== FACTURA COPIA ===")
    print(f"Número de orden: {payload_copy.get('orden', 'N/A')}")
    print(f"Cliente: {payload_copy.get('cliente_nombre', 'N/A')}")
    print(f"Total: ${payload_copy.get('total', 0)}")

    # Save the rendered HTML copy to a file
    with open('output_copy.html', 'w', encoding='utf-8') as f:
        f.write(rendered_html_copy)

    # Create the data structure for the copy
    data_to_send_copy = {
        'contenido': rendered_html_copy,
        'impresora': 'TERMICA',
        'tipo': 'TERMICA'
    }

    print("\n" + "="*50)
    print("INICIANDO ENVÍO DE IMPRESIÓN")
    print("="*50)
    
    try:
        # Detectar puerto disponible
        port = await detect_port()
        if port is None:
            raise Exception("No se pudo detectar el puerto")
        
        print(f"\nUsando puerto: {port}")
        
        # Enviar primera factura
        print("\nEnviando factura original...")
        await send_to_printer(data_to_send, port)
        print("✓ Factura original enviada")
        
        # Pequeña pausa entre impresiones
        await asyncio.sleep(2)
        
        # Enviar copia
        print("\nEnviando copia de factura...")
        await send_to_printer(data_to_send_copy, port)
        print("✓ Copia de factura enviada")
        
        print("\n✓ Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nVerifica que TSSPrint_multiport.py esté ejecutándose")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
import json
import asyncio
import websockets
import time

async def test_factura():
    print("\n1. PROBANDO FACTURA")
    from jinja2 import Environment, FileSystemLoader
    
    with open('data.json', encoding='utf-8') as f:
        data = json.load(f)
    
    payload = data['payload']
    for key in ['subtotal', 'credito_aseguradora', 'total_cliente', 'descuento']:
        if key in payload:
            payload[key] = float(payload[key])
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('planitlla_final.html')
    rendered_html = template.render(dat=payload)
    
    data_to_send = {
        'contenido': rendered_html,
        'impresora': 'TERMICA',
        'tipo': 'TERMICA'
    }
    
    for port in [9000, 9001]:
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(data_to_send))
                print(f"   Factura enviada al puerto {port}")
                return
        except:
            continue
    print("   ERROR: No se pudo enviar factura")

async def test_orden():
    print("\n2. PROBANDO ORDEN")
    order_content = """<ESC><TXT_NORMAL>
<TXT_ALIGN_CT>LABORATORIOS ANALIZA<NL>
<TXT_ALIGN_CT>ORDEN DE LABORATORIO<NL>
<NL>
<TXT_ALIGN_LT>No. Orden: 0001562622178<NL>
<TXT_ALIGN_LT>Paciente: Juan Perez<NL>
<NL>
<TXT_ALIGN_CT><BARCODE_CODE39>*0001562622178*<NL>
<NL>
<PAPER_PART_CUT>"""

    data_to_send = {
        'contenido': order_content,
        'impresora': 'TERMICA',
        'tipo': 'TERMICA'
    }
    
    for port in [9000, 9001]:
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(data_to_send))
                print(f"   Orden enviada al puerto {port}")
                return
        except:
            continue
    print("   ERROR: No se pudo enviar orden")

async def test_sticker():
    print("\n3. PROBANDO STICKER")
    sticker_content = """<ESC><TXT_NORMAL>
<TXT_ALIGN_CT>LAB ANALIZA<NL>
<TXT_ALIGN_LT>Orden: 0001802603985<NL>
<TXT_ALIGN_LT>Tubo: 01<NL>
<BARCODE_HEIGHT><BARCODE_WIDTH>
<BARCODE_TXT_BLW><BARCODE_EAN13>000180260398501<NL>
<TXT_ALIGN_CT>18/07/2025<NL>
<PAPER_FULL_CUT>"""

    data_to_send = {
        'contenido': sticker_content,
        'impresora': 'ETIQUETA',  # Nombre correcto de tu impresora
        'tipo': 'TERMICA'  # IMPORTANTE: Usar TERMICA, no ETIQUETA
    }
    
    for port in [9000, 9001]:
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(data_to_send))
                print(f"   Sticker enviado al puerto {port}")
                return
        except:
            continue
    print("   ERROR: No se pudo enviar sticker")

async def main():
    print("INICIANDO PRUEBAS")
    print("-" * 40)
    
    await test_factura()
    await asyncio.sleep(2)
    
    await test_orden()
    await asyncio.sleep(2)
    
    await test_sticker()
    
    print("\nPRUEBAS COMPLETADAS")

if __name__ == "__main__":
    asyncio.run(main())
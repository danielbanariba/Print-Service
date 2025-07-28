import json
import asyncio
import websockets

# Basado en la imagen que mostraste:
# p = Usb(0x04b8, 0x0202)
# p.barcode('000180260398501', 'EAN13', 64, 2, '', '')

async def send_tubo_barcode():
    # Contenido para el sticker del tubo
    tubo_content = """<ESC><TXT_NORMAL>
<TXT_ALIGN_CT>LABORATORIOS ANALIZA<NL>
<NL>
<TXT_ALIGN_LT>Orden: 0001802603985<NL>
<TXT_ALIGN_LT>Tubo: 01<NL>
<NL>
<BARCODE_HEIGHT><BARCODE_WIDTH>
<BARCODE_TXT_BLW><BARCODE_EAN13>000180260398501<NL>
<NL>
<TXT_ALIGN_CT>Fecha: 18/07/2025<NL>
<PAPER_FULL_CUT>"""

    data = {
        'contenido': tubo_content,
        'impresora': 'ETIQUETA',  # Nombre de tu impresora de stickers
        'tipo': 'TERMICA'  # IMPORTANTE: Usar TERMICA, no ETIQUETA
    }
    
    # Probar ambos puertos
    for port in [9000, 9001]:
        try:
            uri = f"ws://localhost:{port}"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(data))
                print(f"Enviado al puerto {port}")
                break
        except Exception as e:
            print(f"Puerto {port} fallo: {e}")

if __name__ == "__main__":
    asyncio.run(send_tubo_barcode())
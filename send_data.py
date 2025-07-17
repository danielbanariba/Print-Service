from jinja2 import Environment, FileSystemLoader
import json
import asyncio
import websockets

# Load JSON data
with open('data.json', encoding='utf-8') as f:
    data = json.load(f)

# Extract the payload
payload = data['payload']

# Ensure 'subtotal' is a float
if 'subtotal' in payload:
    payload['subtotal'] = float(payload['subtotal'])

# Ensure 'credito_aseguradora' is a float
if 'credito_aseguradora' in payload:
    payload['credito_aseguradora'] = float(payload['credito_aseguradora'])

# Ensure 'total_cliente' is a float
if 'total_cliente' in payload:
    payload['total_cliente'] = float(payload['total_cliente'])

# Ensure 'descuento' is a float
if 'descuento' in payload:
    payload['descuento'] = float(payload['descuento'])

# Set up the Jinja2 environment
env = Environment(loader=FileSystemLoader('.'))

# Render the template with the JSON data using 'plantila_impresion.html'
# template_copy = env.get_template('plantila_impresion_copy.html')y
template = env.get_template('planitlla_final.html')
rendered_html = template.render(dat=payload)

# Print the rendered HTML
print(rendered_html)

# Save the rendered HTML to a file
with open('output.html', 'w') as f:
    f.write(rendered_html)

# Create the data structure to be sent
data_to_send = {
    'contenido': rendered_html,  # Include the rendered HTML content
    'impresora': 'TERMICA'  # Replace 'TERMICA' with the name of your printer if needed
}

# Load JSON data for the copy
with open('data_2.json', encoding='utf-8') as f:
    data_copy = json.load(f)

# Extract the payload for the copy
payload_copy = data_copy['payload']

# Ensure 'subtotal' is a float
if 'subtotal' in payload_copy:
    payload_copy['subtotal'] = float(payload_copy['subtotal'])

# Ensure 'credito_aseguradora' is a float
if 'credito_aseguradora' in payload_copy:
    payload_copy['credito_aseguradora'] = float(payload_copy['credito_aseguradora'])

# Ensure 'total_cliente' is a float
if 'total_cliente' in payload_copy:
    payload_copy['total_cliente'] = float(payload_copy['total_cliente'])

# Ensure 'descuento' is a float
if 'descuento' in payload_copy:
    payload_copy['descuento'] = float(payload_copy['descuento'])

# Render the template with the JSON data using 'planitlla_final.html'
# template_copy = env.get_template('plantila_impresion_copy.html')
template_copy = env.get_template('planitlla_final.html')
rendered_html_copy = template_copy.render(dat=payload_copy)

# Print the rendered HTML copy
# print salto de linea
print("\n")
print("###########################################################################")
print("\n")
print(rendered_html_copy)

# Save the rendered HTML copy to a file
with open('output_copy.html', 'w') as f:
    f.write(rendered_html_copy)

# Create the data structure to be sent for the copy
data_to_send_copy = {
    'contenido': rendered_html_copy,  # Include the rendered HTML content
    'impresora': 'TERMICA'  # Replace 'TERMICA' with the name of your printer if needed
}

# Send the JSON payload to the WebSocket server
async def send_data():
    uri = "ws://localhost:9000"
    async with websockets.connect(uri) as websocket:
        json_payload = json.dumps(data_to_send)  # Convert the data structure to a JSON string
        await websocket.send(json_payload)
        # print("Data sent to WebSocket server:", json_payload)

        json_payload_copy = json.dumps(data_to_send_copy)  # Convert the data structure to a JSON string
        await websocket.send(json_payload_copy)
        # print("Data sent to WebSocket server:", json_payload_copy)

# Run the async function
asyncio.get_event_loop().run_until_complete(send_data())
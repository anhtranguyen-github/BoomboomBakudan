import websocket
import json
import avro.schema
import avro.io
import io
import time
from datetime import datetime

# Load Avro schema
schema_path = "./schemas/assets.avsc"
with open(schema_path, 'r') as f:
    schema = avro.schema.parse(f.read())

# Binance WebSocket URL for a specific trading pair (e.g., BTC/USDT)
ws_url = "wss://stream.binance.com:9443/ws/btcusdt@ticker"

def on_message(ws, message):
    # Parse incoming WebSocket message
    data = json.loads(message)
    
    # Extract relevant fields
    asset_id = "BTCUSDT"  # Example: trading pair as ID
    asset_name = "Bitcoin"  # Example: human-readable name
    asset_price = data.get('c')  # Current price from Binance ticker
    collected_at = datetime.utcnow().isoformat()  # Current timestamp in ISO format

    # Create Avro record
    record = {
        "id": asset_id,
        "asset_name": asset_name,
        "asset_price": asset_price,
        "collected_at": collected_at
    }

    # Serialize to Avro
    writer = avro.io.DatumWriter(schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(record, encoder)
    raw_bytes = bytes_writer.getvalue()

    # For demonstration, print the record and Avro bytes
    print(f"Record: {record}")
    print(f"Avro serialized bytes: {raw_bytes.hex()}")

    # Optionally, save to a file or send to a downstream system
    with open("assets_data.avro", "ab") as f:
        f.write(raw_bytes)

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Connected to Binance WebSocket")

def main():
    # Initialize WebSocket
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    
    # Run WebSocket
    ws.run_forever()

if __name__ == "__main__":
    main()
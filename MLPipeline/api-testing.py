import websocket
import json
from datetime import datetime

def on_message(ws, message):
    print("\nReceived OHLCV data:")
    data = json.loads(message)
    kline = data['data']['k']
    
    # Format the OHLCV data
    ohlcv = {
        "timestamp": datetime.fromtimestamp(kline['t'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        "open": float(kline['o']),
        "high": float(kline['h']),
        "low": float(kline['l']),
        "close": float(kline['c']),
        "volume": float(kline['v']),
        "close_time": datetime.fromtimestamp(kline['T'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
        "quote_volume": float(kline['q']),
        "trades": kline['n'],
        "is_closed": kline['x']
    }
    
    print(json.dumps(ohlcv, indent=2))
    ws.close()

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("\nWebSocket connection closed")

def on_open(ws):
    print("WebSocket connection opened - waiting for OHLCV data...")

if __name__ == "__main__":
    # Create WebSocket connection for 1-minute candles
    ws = websocket.WebSocketApp(
        "wss://stream.binance.com:9443/stream?streams=btcusdt@kline_1m",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    
    # Start WebSocket connection
    ws.run_forever()
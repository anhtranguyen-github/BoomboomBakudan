import websocket
import datetime as dt
import json
import avro.schema
import avro.io
import io
import os
from kafka import KafkaProducer, errors
import uuid
import logging
from logging.handlers import RotatingFileHandler

# Configure logger
logger = logging.getLogger('BinanceProducer')
logger.setLevel(logging.DEBUG)  # Capture all levels, filter at handler level

# Console handler (INFO and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# File handler (DEBUG and above, with rotation)
file_handler = RotatingFileHandler(
    'binance_producer.log', maxBytes=10*1024*1024, backupCount=5
)  # 10MB per file, keep 5 backups
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class BinanceProducer:
    def __init__(self) -> None:
        self.asset_avro_schema = self.load_schema('./schemas/assets.avsc')
        self.asset_topic = os.environ.get('ASSET_PRICES_TOPIC', 'data.asset_prices')

        config = {
            'bootstrap_servers': os.environ.get('REDPANDA_BROKERS', 'localhost:9092').split(',')
        }

        try:
            self.producer = KafkaProducer(**config)
            logger.info('Kafka producer initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize Kafka producer: {str(e)}')
            raise

        # Map Binance trading pairs to human-readable asset names
        self.asset_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'BNBUSDT': 'binance-coin'
        }

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            'wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/ethusdt@ticker/bnbusdt@ticker',
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        logger.info('Starting WebSocket connection')
        self.ws.run_forever(reconnect=5)

    def on_open(self, ws) -> None:
        logger.info('Opened Connection to Binance WebSocket!')

    def on_close(self, ws, close_status_code, close_msg) -> None:
        logger.info(f'WebSocket connection closed: status={close_status_code}, message={close_msg}')

    def on_error(self, ws, error) -> None:
        logger.error(f'WebSocket error: {str(error)}')

    def on_message(self, ws, message) -> None:
        logger.debug('Received WebSocket message')
        try:
            message_data = json.loads(message)
            logger.debug(f'Message data: {message_data}')
        except json.JSONDecodeError as e:
            logger.error(f'Failed to parse message: {str(e)}')
            return

        if 'data' in message_data:
            data = message_data['data']
            symbol = data.get('s')
            price = data.get('c')
            asset_name = self.asset_map.get(symbol, symbol.lower())

            payload = {
                'id': str(uuid.uuid4()),
                'asset_name': asset_name,
                'asset_price': price,
                'collected_at': dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            logger.debug(f'Created payload: {payload}')

            encoded_data = self.encode_message(payload, self.asset_avro_schema)
            self.publish_asset_prices(encoded_data)

    def load_schema(self, schema_path):
        try:
            schema = avro.schema.parse(open(schema_path).read())
            logger.info(f'Loaded Avro schema from {schema_path}')
            return schema
        except Exception as e:
            logger.error(f'Failed to load Avro schema: {str(e)}')
            raise

    def encode_message(self, data, schema):
        try:
            writer = avro.io.DatumWriter(schema)
            buffer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(buffer)
            writer.write(data, encoder)
            encoded = buffer.getvalue()
            logger.debug(f'Encoded message to Avro: {encoded.hex()}')
            return encoded
        except Exception as e:
            logger.error(f'Failed to encode message to Avro: {str(e)}')
            raise

    def publish_asset_prices(self, value):
        try:
            self.producer.send(topic=self.asset_topic, value=value)
            logger.debug(f'Published message to Kafka topic {self.asset_topic}')
        except errors.KafkaTimeoutError as e:
            logger.error(f'Kafka timeout error: {str(e)}')
        except Exception as e:
            logger.error(f'Error publishing to Kafka: {str(e)}')

if __name__ == "__main__":
    BinanceProducer()
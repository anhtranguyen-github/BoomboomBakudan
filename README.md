# BoomboomBakudan: Real-Time Crypto Data Stream

A robust data streaming pipeline that captures real-time cryptocurrency price data from Binance, processes it through a scalable stream processing architecture, and makes it available for analysis and visualization.

## Features

- **Real-time Data Collection**: Live streaming of cryptocurrency price data from Binance WebSocket API
- **Scalable Stream Processing**: Apache Spark-based stream processing with worker nodes
- **Avro Schema Serialization**: Structured data serialization using Apache Avro
- **Message Queueing**: Redpanda (Kafka API compatible) message broker for reliable data streaming
- **Persistent Storage**: Cassandra NoSQL database for storing processed data
- **Real-time Visualization**: Grafana dashboards for monitoring cryptocurrency prices
- **Containerized Architecture**: Docker-based deployment for easy setup and scaling
- **Fault Tolerance**: Resilient system design with automatic reconnection and error handling

## Architecture Overview

```
┌─────────────────┐    ┌────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Binance        │    │            │    │ Spark Streaming │    │             │
│  WebSocket API  │───▶│  Redpanda  │───▶│ (Consumer with  │───▶│  Cassandra  │
│  (Producer)     │    │  (Kafka)   │    │  workers)       │    │  Database   │
└─────────────────┘    └────────────┘    └─────────────────┘    └──────┬──────┘
                                                                       │
                                                                       ▼
                                                               ┌─────────────────┐
                                                               │    Grafana      │
                                                               │  Visualization  │
                                                               └─────────────────┘
```

The system uses:
- **Python** for data collection and processing
- **Apache Spark** for stream processing
- **Redpanda** (Kafka API compatible) for message queuing
- **Apache Avro** for data serialization
- **Cassandra** for data storage
- **Grafana** for visualization

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/BoomboomBakudan.git
   cd BoomboomBakudan
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. Verify all services are running:
   ```bash
   docker-compose ps
   ```

## Usage

### Accessing Services

- **Redpanda Console**: http://localhost:1003 - For monitoring Kafka topics and messages
- **Grafana**: http://localhost:3000 - For data visualization (default credentials: admin/admin)
- **Spark UI**: http://localhost:4010 - For monitoring Spark jobs and performance

### Monitoring Data Flow

1. Check the Redpanda Console to verify messages are flowing through the `data.asset_prices` topic.
2. View live data processing in the Spark UI.
3. Monitor cryptocurrency prices and trends in Grafana dashboards.

### Adding New Cryptocurrency Pairs

To monitor additional cryptocurrency pairs, update the `asset_map` in `BinanceProducer/BinanceProducer.py`:

```python
self.asset_map = {
    'BTCUSDT': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'BNBUSDT': 'binance-coin',
    'NEWPAIRUSDT': 'new-coin-name'  # Add your new pair here
}
```

And update the WebSocket connection URL to include the new pair.

## Configuration

### Environment Variables

The system uses the following environment variables (already configured in docker-compose.yaml):

| Variable | Description | Default |
|----------|-------------|---------|
| REDPANDA_BROKERS | Redpanda broker addresses | binance-redpanda:29092 |
| ASSET_PRICES_TOPIC | Kafka topic for asset prices | data.asset_prices |
| SPARK_MASTER | Spark master URL | local[*] |
| ASSET_CASSANDRA_HOST | Cassandra host | binance-cassandra |
| ASSET_CASSANDRA_PORT | Cassandra port | 9042 |
| ASSET_CASSANDRA_KEYSPACE | Cassandra keyspace | assets |
| ASSET_CASSANDRA_TABLE | Cassandra table | assets |

### Scaling

To scale the Spark workers:
```bash
docker-compose up -d --scale binance-consumer-worker=3
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT License](LICENSE)


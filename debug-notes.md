# Debug Notes for BoomboomBakudan

## System Overview
This document contains commands and procedures to debug the entire data pipeline:
- BinanceProducer: Connects to Binance WebSocket API and sends data to Redpanda
- Redpanda: Kafka-compatible message broker
- BinanceConsumer: Processes messages with Apache Spark and stores in Cassandra
- Cassandra: Database for storing cryptocurrency data

## Redpanda/Kafka Debugging

### Check if Redpanda is running
```bash
docker ps | grep redpanda
```

### List all topics
```bash
docker exec -it binance-redpanda rpk topic list
```

### Create a topic manually (if needed)
```bash
docker exec -it binance-redpanda rpk topic create data.asset_prices
```

### Consume messages from a topic (see raw data)
```bash
docker exec -it binance-redpanda rpk topic consume data.asset_prices --brokers=localhost:9092 -n 1
```

### View topic details
```bash
docker exec -it binance-redpanda rpk topic describe data.asset_prices
```

## Producer Debugging

### Check if producer container is running
```bash
docker ps | grep producer
```

### View producer logs
```bash
docker logs binance-producer -f
```

### Rebuild producer after code changes
```bash
docker build -t boomboombakudan-binance-producer:latest ./BinanceProducer
```

### Delete and recreate producer container
```bash
docker stop binance-producer && docker rm binance-producer
docker run -d --name binance-producer --network boomboombakudan_default -e REDPANDA_BROKERS="binance-redpanda:29092" -e ASSET_PRICES_TOPIC="data.asset_prices" boomboombakudan-binance-producer:latest
```

### Check WebSocket connections
```bash
docker exec binance-producer sh -c "ps aux | grep websocket"
```

## Consumer Debugging

### Check if consumer is running
```bash
docker ps | grep consumer
```

### View consumer logs
```bash
docker logs binance-consumer -f
```

### Rebuild consumer after code changes
```bash
docker build -t boomboombakudan-binance-consumer:latest ./BinanceConsumer
```

### Delete and recreate consumer
```bash
docker stop binance-consumer && docker rm binance-consumer
docker run -d --name binance-consumer --network boomboombakudan_default -e SPARK_MASTER="local[*]" -e REDPANDA_BROKERS="binance-redpanda:29092" -e ASSET_PRICES_TOPIC="data.asset_prices" -e ASSET_SCHEMA_LOCATION="/src/schemas/assets.avsc" -e ASSET_CASSANDRA_HOST="binance-cassandra" -e ASSET_CASSANDRA_PORT=9042 -e ASSET_CASSANDRA_USERNAME="adminadmin" -e ASSET_CASSANDRA_PASSWORD="adminadmin" -e ASSET_CASSANDRA_KEYSPACE="assets" -e ASSET_CASSANDRA_TABLE="assets" -p 9090:8080 -p 7014:7077 -p 4010:4040 boomboombakudan-binance-consumer:latest
```

### Check Spark checkpoints
```bash
docker exec binance-consumer sh -c "cat /tmp/checkpoint/metadata | grep 'Batch'"
```

## Cassandra Debugging

### Check if Cassandra is running
```bash
docker ps | grep cassandra
```

### View table schema
```bash
docker exec -i binance-cassandra cqlsh -e "USE assets; DESCRIBE TABLE assets;"
```

### Query table data (use cass script)
```bash
./cass
```

### Manual query with limit
```bash
docker exec -i binance-cassandra cqlsh -e "USE assets; SELECT id, asset_name, open, high, low, close FROM assets LIMIT 5;"
```

### Drop and recreate table (CAUTION: destroys data)
```bash
docker exec -i binance-cassandra cqlsh -e "USE assets; DROP TABLE assets;"
```

### View Cassandra logs
```bash
docker logs binance-cassandra
```

## Common Issues & Solutions

### 1. Schema mismatch between producer and consumer
If you see Avro serialization errors, check that schemas match exactly between:
- BinanceProducer/schemas/assets.avsc 
- BinanceConsumer/schemas/assets.avsc

### 2. Type conversion errors
For fields like 'trades', ensure proper string conversion in the producer:
```python
'trades': str(kline.get('n')),  # Convert to string before sending
```

### 3. Missing topics in Redpanda console
- Ensure producer is running and connected
- Check producer logs for connection errors
- Verify network connectivity between containers

### 4. Container restart after schema changes
After changing Avro schemas or database schemas, you typically need to:
1. Rebuild the container images
2. Remove old containers
3. Create new containers

### 5. Complete system restart
If you need to start fresh:
```bash
docker-compose down
docker-compose up -d
```

## Testing Data Flow
This sequence verifies data is flowing through the entire pipeline:
```bash
# 1. Check producer is connecting to Binance
docker logs binance-producer | grep "WebSocket"

# 2. Verify messages in Redpanda
docker exec -it binance-redpanda rpk topic consume data.asset_prices --brokers=localhost:9092 -n 1

# 3. Check consumer is processing
docker logs binance-consumer | grep "Processing"

# 4. Verify data in Cassandra
docker exec -i binance-cassandra cqlsh -e "
USE assets;
SELECT id, asset_name, open, high, low, close, volume, quote_volume, trades, is_closed, timestamp, close_time, collected_at, consumed_at FROM assets LIMIT 10;
"
```
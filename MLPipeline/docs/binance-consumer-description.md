# BinanceConsumer

The BinanceConsumer is a critical component in the data pipeline designed to consume cryptocurrency market data from Binance exchange. It's built using Apache Spark for high-throughput data processing, and connects to Kafka/Redpanda for streaming data ingestion.

## Architecture

BinanceConsumer is developed as a containerized service that:

1. Reads cryptocurrency OHLCV (Open-High-Low-Close-Volume) data from a Kafka topic
2. Processes and transforms the data using Apache Spark Structured Streaming
3. Stores the processed data in a Cassandra database for analytical workloads

## Features

- **Real-time processing**: Consumes cryptocurrency data from Kafka in real-time
- **Avro deserialization**: Decodes binary Avro messages into structured data
- **Data transformation**: Transforms string data types into appropriate numeric types
- **Dual output streams**: Supports both console output (for debugging) and Cassandra persistence
- **Scalable design**: Can be deployed with multiple Spark workers for horizontal scaling

## Technical Implementation

The BinanceConsumer leverages several key technologies:

- **Spark Structured Streaming**: Provides fault-tolerant stream processing with exactly-once semantics
- **Avro Message Decoding**: Uses custom UDF (User Defined Function) to decode binary Avro messages
- **Spark DataFrame API**: Processes data in a structured columnar format optimized for analytics
- **Type Conversions**: Automatically casts string values to appropriate numeric types (float/int)
- **Timestamp Processing**: Parses string timestamps into proper timestamp objects for time-series analysis
- **Checkpoint Management**: Maintains processing state for fault tolerance and recovery

## Data Processing Workflow

1. **Data Ingestion**: Reads raw binary messages from Kafka
2. **Deserialization**: Converts Avro binary format to structured records
3. **Schema Application**: Applies a predefined schema to validate data structure
4. **Type Conversion**: Transforms string representations to appropriate data types
5. **Timestamp Processing**: Handles timestamp conversions for time-based analysis
6. **Streaming Output**: Writes transformed data to Cassandra in micro-batches

## Configuration

The BinanceConsumer is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| SPARK_MASTER | Spark master URL | local[*] |
| REDPANDA_BROKERS | Kafka/Redpanda broker addresses | localhost:9092 |
| ASSET_PRICES_TOPIC | Kafka topic for asset prices | data.asset_prices |
| ASSET_SCHEMA_LOCATION | Location of Avro schema file | ./schemas/assets.avsc |
| ASSET_CASSANDRA_HOST | Cassandra host | localhost |
| ASSET_CASSANDRA_PORT | Cassandra port | 9042 |
| ASSET_CASSANDRA_USERNAME | Cassandra username | |
| ASSET_CASSANDRA_PASSWORD | Cassandra password | |
| ASSET_CASSANDRA_KEYSPACE | Cassandra keyspace | assets |
| ASSET_CASSANDRA_TABLE | Cassandra table | assets |

## Data Schema

### Avro Schema

The BinanceConsumer uses Avro schema for data serialization and deserialization. Below is the complete schema definition:

```json
{
    "namespace":  "io.binance",
    "type": "record",
    "name": "assets",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "asset_name", "type": "string"},
        {"name": "open", "type": "string"},
        {"name": "high", "type": "string"},
        {"name": "low", "type": "string"},
        {"name": "close", "type": "string"},
        {"name": "volume", "type": "string"},
        {"name": "quote_volume", "type": "string"},
        {"name": "trades", "type": "string"},
        {"name": "is_closed", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "close_time", "type": "string"},
        {"name": "collected_at", "type": "string"}
    ]
}
```

### Spark Schema

The data is transformed into the following PySpark schema during processing:

```python
schema = StructType([
    StructField("id", StringType(), True),
    StructField("asset_name", StringType(), True),
    StructField("open", StringType(), True),
    StructField("high", StringType(), True),
    StructField("low", StringType(), True),
    StructField("close", StringType(), True),
    StructField("volume", StringType(), True),
    StructField("quote_volume", StringType(), True),
    StructField("trades", StringType(), True),
    StructField("is_closed", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("close_time", StringType(), True),
    StructField("collected_at", StringType(), True)
])
```

### Cassandra Schema

The processed data is stored in Cassandra with the following schema:

```cql
CREATE TABLE IF NOT EXISTS assets.assets (
    id UUID,
    asset_name text,
    open float,
    high float,
    low float,
    close float,
    volume float,
    quote_volume float,
    trades int,
    is_closed boolean,
    timestamp timestamp,
    close_time timestamp,
    collected_at timestamp,
    consumed_at timestamp,
    PRIMARY KEY (asset_name, timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC)
   AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_size': '1', 'compaction_window_unit': 'DAYS'};
```

### Data Fields

The BinanceConsumer processes the following data schema:

| Field | Description | Type | Notes |
|-------|-------------|------|-------|
| id | Unique identifier | String | UUID generated per record |
| asset_name | Cryptocurrency name | String | Examples: bitcoin, ethereum, binance-coin |
| open | Opening price in the period | Float | First price in the period |
| high | Highest price in the period | Float | Maximum price reached |
| low | Lowest price in the period | Float | Minimum price reached |
| close | Closing price in the period | Float | Last price in the period |
| volume | Trading volume in base asset | Float | Amount of cryptocurrency traded |
| quote_volume | Trading volume in quote asset | Float | Amount traded in quote currency (usually USDT) |
| trades | Number of trades in the period | Integer | Count of individual trades executed |
| is_closed | Whether the candlestick is closed | Boolean | True if the time period is complete |
| timestamp | Start time of the period | Timestamp | Beginning of the candlestick period |
| close_time | End time of the period | Timestamp | End of the candlestick period |
| collected_at | Time when data was collected | Timestamp | When BinanceProducer received the data |
| consumed_at | Time when data was processed | Timestamp | When BinanceConsumer processed the data |

## Docker Compose Configuration

The BinanceConsumer can be deployed using Docker Compose. Below is a sample configuration:

```yaml
version: '3.8'

services:
  binance-consumer:
    build:
      context: ./BinanceConsumer
      dockerfile: Dockerfile
    container_name: binance-consumer
    ports:
      - 9090:8080  # Spark UI
      - 7014:7077  # Spark Master
      - 4010:4040  # Spark Application UI
    environment:
      SPARK_MASTER: "local[*]"
      REDPANDA_BROKERS: "binance-redpanda:29092"
      ASSET_PRICES_TOPIC: "data.asset_prices"
      ASSET_SCHEMA_LOCATION: "/src/schemas/assets.avsc"
      ASSET_CASSANDRA_HOST: "binance-cassandra"
      ASSET_CASSANDRA_PORT: 9042
      ASSET_CASSANDRA_USERNAME: "adminadmin"
      ASSET_CASSANDRA_PASSWORD: "adminadmin"
      ASSET_CASSANDRA_KEYSPACE: 'assets'
      ASSET_CASSANDRA_TABLE: 'assets'
    volumes:
      - ./checkpoint:/tmp/checkpoint  # Persist checkpoint data
    depends_on:
      binance-redpanda:
        condition: service_healthy
      binance-cassandra:
        condition: service_healthy

  # Optional: Scalable worker nodes
  binance-consumer-worker-1:
    build:
      context: ./BinanceConsumer
      dockerfile: SparkWorker.DockerFile
    container_name: binance-consumer-worker-1
    ports:
      - 8041:8081
    depends_on:
      - binance-consumer
    environment:
      SPARK_MODE: worker
      SPARK_WORKER_CORES: 2
      SPARK_WORKER_MEMORY: 1g
      SPARK_MASTER_URL: spark://binance-consumer:7077

  # Related services (for reference)
  binance-cassandra:
    image: cassandra:4.1
    container_name: binance-cassandra
    ports:
      - 9042:9042
    environment:
      - MAX_HEAP_SIZE=512M
      - HEAP_NEWSIZE=100M
      - CASSANDRA_USERNAME=adminadmin
      - CASSANDRA_PASSWORD=adminadmin
    volumes:
      - cassandra_data:/var/lib/cassandra
    healthcheck:
      test: ["CMD", "cqlsh", "-u", "adminadmin", "-p", "adminadmin", "-e", "describe keyspaces"]
      interval: 15s
      timeout: 10s
      retries: 10

volumes:
  cassandra_data:
```

### Docker Image Configuration

The Dockerfile for BinanceConsumer:

```dockerfile
FROM bitnami/spark:latest

USER root

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

COPY . .

RUN pip install -r requirements.txt
RUN curl https://repo1.maven.org/maven2/org/apache/ivy/ivy/2.5.2/ivy-2.5.2.jar -o ivy.jar
RUN java -jar ivy.jar -ivy ivy.xml -retrieve "/opt/bitnami/spark/jars/[conf]-[artifact]-[type]-[revision].[ext]"

CMD ["python", "BinanceConsumer.py"]
```

## Usage

The BinanceConsumer is designed to run as a containerized service in a Docker environment, typically launched using docker-compose. It's configured to start automatically and begin consuming data once the Kafka/Redpanda service is available.

## Dependencies

- Apache Spark (3.5.x)
- Spark SQL Kafka Connector
- Spark Avro Library
- Spark Cassandra Connector
- Python Avro Library

## ML Pipeline Integration Points

The BinanceConsumer provides several key integration points for machine learning pipelines:

### 1. Direct Cassandra Connection

ML pipelines can directly query the Cassandra database where the processed data is stored:

```python
from pyspark.sql import SparkSession

# ML pipeline connection example
spark = SparkSession.builder \
    .appName("ml-pipeline") \
    .config("spark.cassandra.connection.host", "binance-cassandra") \
    .config("spark.cassandra.connection.port", 9042) \
    .config("spark.cassandra.auth.username", "adminadmin") \
    .config("spark.cassandra.auth.password", "adminadmin") \
    .getOrCreate()

# Load data from Cassandra
df = spark.read \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="assets", keyspace="assets") \
    .load()
```

### 2. Feature Engineering

The data schema is optimized for time series ML applications with features ready for analysis:

- Price movement features (OHLC)
- Volume indicators
- Timestamp data for temporal patterns
- Trading activity metrics

### 3. Time Window Processing

The data structure supports common time-based feature creation:

```python
# Example time window aggregations
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Define time window
window_spec = Window.partitionBy("asset_name").orderBy("timestamp").rowsBetween(-5, 0)

# Calculate moving averages
df_features = df \
    .withColumn("price_5min_avg", F.avg("close").over(window_spec)) \
    .withColumn("volume_5min_avg", F.avg("volume").over(window_spec)) \
    .withColumn("price_volatility", F.stddev("close").over(window_spec))
```

### 4. Data Sampling Results

Sample of transformed data as it appears in Cassandra:

```
+------+-------------+--------+--------+-------+--------+----------+-------------+------+---------+-------------------+-------------------+-------------------+-------------------+
|id    |asset_name   |open    |high    |low    |close   |volume    |quote_volume |trades|is_closed|timestamp          |close_time         |collected_at       |consumed_at        |
+------+-------------+--------+--------+-------+--------+----------+-------------+------+---------+-------------------+-------------------+-------------------+-------------------+
|uuid-1|bitcoin      |55432.21|55987.65|55102.3|55876.32|1324.56784|73687542.87  |8764  |true     |2023-05-15 10:00:00|2023-05-15 10:59:59|2023-05-15 11:00:01|2023-05-15 11:00:05|
|uuid-2|ethereum     |3214.43 |3287.65 |3198.76|3245.87 |5432.6578 |17654321.43  |5432  |true     |2023-05-15 10:00:00|2023-05-15 10:59:59|2023-05-15 11:00:02|2023-05-15 11:00:06|
|uuid-3|binance-coin |312.45  |318.76  |309.87 |315.65  |45678.765 |14324567.87  |3245  |true     |2023-05-15 10:00:00|2023-05-15 10:59:59|2023-05-15 11:00:03|2023-05-15 11:00:07|
+------+-------------+--------+--------+-------+--------+----------+-------------+------+---------+-------------------+-------------------+-------------------+-------------------+
```

### 5. ML Model Deployment Strategies

The BinanceConsumer architecture supports several ML model deployment patterns:

- **Batch Processing**: Load historical data for training and backtesting
- **Online Inference**: Connect to near real-time data for prediction
- **Stream Processing**: Extend the consumer to include model inference directly in the pipeline

## Performance Characteristics

- **Throughput**: ~5,000-10,000 records/second (depending on hardware)
- **Latency**: 1-3 seconds from Kafka ingestion to Cassandra storage
- **Scalability**: Linear scaling with additional Spark workers
- **Recovery Time**: <30 seconds after failure (with proper checkpointing)

## Common Use Cases for ML

- Price prediction models
- Anomaly detection in trading patterns
- Market volatility forecasting
- Trading volume analysis
- Trend identification algorithms
- Arbitrage opportunity detection 
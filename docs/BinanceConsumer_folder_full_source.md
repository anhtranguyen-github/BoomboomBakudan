# BinanceConsumer Folder - Full Source

---

## BinanceConsumer.py

```python
import io
import os
import avro.io
import avro.schema
import pyspark.sql.types as T
#from elasticsearch import Elasticsearch
from pyspark.sql import SparkSession, functions as func

# Define the schema structure explicitly
schema = T.StructType([
    T.StructField("id", T.StringType(), True),
    T.StructField("asset_name", T.StringType(), True),
    T.StructField("open", T.StringType(), True),
    T.StructField("high", T.StringType(), True),
    T.StructField("low", T.StringType(), True),
    T.StructField("close", T.StringType(), True),
    T.StructField("volume", T.StringType(), True),
    T.StructField("quote_volume", T.StringType(), True),
    T.StructField("trades", T.StringType(), True),
    T.StructField("is_closed", T.StringType(), True),
    T.StructField("timestamp", T.StringType(), True),
    T.StructField("close_time", T.StringType(), True),
    T.StructField("collected_at", T.StringType(), True)
])

asset_schema_location = os.environ.get('ASSET_SCHEMA_LOCATION', './schemas/assets.avsc') 

def load_schema(schema_path):
    return avro.schema.parse(open(schema_path).read())

def decode_asset_avro_message(data):
    try:
        asset_avro_schema = load_schema(asset_schema_location)
        bytes_reader = io.BytesIO(data)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(asset_avro_schema)
        decoded = reader.read(decoder)
        # Print is_closed value for debugging
        if 'is_closed' in decoded:
            print(f"Decoded is_closed value: '{decoded['is_closed']}' (type: {type(decoded['is_closed'])})")
        return decoded
    except Exception as e:
        print(f"Error decoding message: {str(e)}")
        return None

class BinanceConsumer:
    def __init__(self) -> None:
        self.spark = SparkSession.builder \
            .appName('binance-consumer') \
            .master(os.environ.get('SPARK_MASTER', 'local[*]')) \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
            .config("spark.cassandra.connection.host", os.environ.get('ASSET_CASSANDRA_HOST', 'localhost')) \
            .config("spark.cassandra.connection.port", os.environ.get('ASSET_CASSANDRA_PORT', 9042)) \
            .config("spark.cassandra.auth.username", os.environ.get('ASSET_CASSANDRA_USERNAME')) \
            .config("spark.cassandra.auth.password", os.environ.get('ASSET_CASSANDRA_PASSWORD')) \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .getOrCreate()

        self.spark.sparkContext.setLogLevel('INFO')  # Changed to INFO for better debugging
        print("SparkSession created successfully")

    def read_from_kafka(self, topic: str):
        self.df_raw_stream = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", os.environ.get('REDPANDA_BROKERS', 'localhost:9092')) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .load()
        
        print(f"Created Kafka stream for topic: {topic}")

    def parse_avro_message_4rm_kafka(self):
        decode_asset_avro_message_udf = func.udf(decode_asset_avro_message, returnType=schema)
        df_value_stream = self.df_raw_stream.selectExpr('value')

        self.df_pure_stream = df_value_stream \
            .select(decode_asset_avro_message_udf(func.col('value')).alias('decoded_data')) \
            .select(
                func.col('decoded_data.id'),
                func.col('decoded_data.asset_name'),
                func.col('decoded_data.open').cast('float').alias('open'),
                func.col('decoded_data.high').cast('float').alias('high'),
                func.col('decoded_data.low').cast('float').alias('low'),
                func.col('decoded_data.close').cast('float').alias('close'),
                func.col('decoded_data.volume').cast('float').alias('volume'),
                func.col('decoded_data.quote_volume').cast('float').alias('quote_volume'),
                func.col('decoded_data.trades').cast('int').alias('trades'),
                func.when(func.lower(func.col('decoded_data.is_closed')) == 'true', True)
                    .when(func.lower(func.col('decoded_data.is_closed')) == 'false', False)
                    .otherwise(None).alias('is_closed'),
                func.to_timestamp(func.col('decoded_data.timestamp')).alias('timestamp'),
                func.to_timestamp(func.col('decoded_data.close_time')).alias('close_time'),
                func.to_timestamp(func.col('decoded_data.collected_at')).alias('collected_at'),
                func.date_format(func.current_timestamp(), "yyyy-MM-dd HH:mm:ss").alias('consumed_at')
            )
        
        print("Created streaming DataFrame with schema")

    def sink_console(self, output_mode: str = 'append', processing_time: str = '10 seconds'):
        print("Starting console sink...")
        query = self.df_pure_stream.writeStream \
            .outputMode(output_mode) \
            .trigger(processingTime=processing_time) \
            .format("console") \
            .option("truncate", False) \
            .start()
        print("Console sink started")
        return query

    def sink_into_cassandra(self, output_mode: str = 'append'):
        print("Starting Cassandra sink...")
        query = self.df_pure_stream.writeStream \
            .format("org.apache.spark.sql.cassandra") \
            .outputMode(output_mode) \
            .option("checkpointLocation", "/tmp/checkpoint/cassandra") \
            .options(
                table=os.environ.get('ASSET_CASSANDRA_TABLE'), 
                keyspace=os.environ.get('ASSET_CASSANDRA_KEYSPACE')
            ) \
            .start()
        print("Cassandra sink started")
        return query
    
    def waitingForTermination(self):
        print("Waiting for stream termination...")
        self.spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    try:
        print("Starting BinanceConsumer...")
        consumer = BinanceConsumer()

        topic = os.environ.get('ASSET_PRICES_TOPIC', 'data.asset_prices')
        print(f"Reading from topic: {topic}")
        consumer.read_from_kafka(topic=topic)
        
        print("Parsing Avro messages...")
        consumer.parse_avro_message_4rm_kafka()

        # Start both sinks
        console_query = consumer.sink_console(output_mode='append')
        cassandra_query = consumer.sink_into_cassandra(output_mode='append')

        print("All sinks started, waiting for termination...")
        consumer.waitingForTermination()
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

    
```

---

## ivy.xml

```xml
<ivy-module version="2.0">
  <info organisation="org.apache.spark" module="coincap-consumer" />

  <configurations>
    <conf name="default"/>
    <conf name="sources" visibility="private"/>
    <conf name="javadoc" visibility="private"/>
  </configurations>

  <dependencies>
    <dependency org="org.apache.spark" name="spark-sql-kafka-0-10_2.12" rev="3.5.1" conf="default"/>
    <dependency org="org.apache.spark" name="spark-avro_2.12" rev="3.5.1" conf="default"/>
    <dependency org="org.apache.spark" name="spark-sql_2.12" rev="3.5.1" conf="default->master"/>
    <dependency org="com.datastax.spark" name="spark-cassandra-connector_2.12" rev="3.5.0" conf="default"/>
  </dependencies>
</ivy-module>
```

---

## docker-compose.yaml

```yaml
services:
  binance-consumer:
    build:
      context: .
      dockerfile: SparkMaster.DockerFile
    container_name: binance-consumer
    ports:
      - 9090:8080
      - 7014:7077
      - 4010:4040
    environment:
      REDPANDA_BROKERS: "binance-redpanda:29092"
      ASSET_PRICES_TOPIC: "data.asset_prices"
      ASSET_SCHEMA_LOCATION: "/src/schemas/assets.avsc"
    depends_on:
      binance-redpanda:
        condition: service_healthy

  binance-consumer-worker-1:
    build:
      context: .
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

  binance-consumer-worker-2:
    build:
      context: .
      dockerfile: SparkWorker.DockerFile
    container_name: binance-consumer-worker-2
    ports:
      - 8042:8081
    depends_on:
      - binance-consumer
    environment:
      SPARK_MODE: worker
      SPARK_WORKER_CORES: 2
      SPARK_WORKER_MEMORY: 1g
      SPARK_MASTER_URL: spark://binance-consumer:7077
```

---

## Dockerfile

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

# Run the consumer application instead of Spark master
CMD ["python", "BinanceConsumer.py"]
```

---

## SparkMaster.DockerFile

```dockerfile
FROM bitnami/spark:latest

USER root

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

USER 1001

WORKDIR /src

COPY . .

RUN pip install -r requirements.txt
RUN curl https://repo1.maven.org/maven2/org/apache/ivy/ivy/2.5.2/ivy-2.5.2.jar -o ivy.jar
RUN java -jar ivy.jar -ivy ivy.xml -retrieve "/opt/bitnami/spark/jars/[conf]-[artifact]-[type]-[revision].[ext]"

CMD ["/opt/bitnami/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]
```

---

## SparkWorker.DockerFile

```dockerfile
FROM bitnami/spark:latest

USER root

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

USER 1001

WORKDIR /src

COPY . .

RUN pip install -r requirements.txt

RUN curl https://repo1.maven.org/maven2/org/apache/ivy/ivy/2.5.2/ivy-2.5.2.jar -o ivy.jar
RUN java -jar ivy.jar -ivy ivy.xml -retrieve "/opt/bitnami/spark/jars/[conf]-[artifact]-[type]-[revision].[ext]"

CMD ["/opt/bitnami/spark/bin/spark-class", "org.apache.spark.deploy.worker.Worker", "spark://binance-consumer:7077"]
```

---

## requirements.txt

```text
avro==1.11.3
avro-python3==1.10.2
py4j==0.10.9.7
pyspark==3.5.1
websockets==12.0

```

---

## schemas/assets.avsc

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

</rewritten_file>
# Cassandra Folder - Full Source

## `init.cql`
```sql
-- Create keyspace
CREATE KEYSPACE IF NOT EXISTS assets
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE assets;

CREATE TABLE IF NOT EXISTS assets (
    id TIMEUUID PRIMARY KEY DEFAULT now(),
    asset_name varchar,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT, 
    volume FLOAT,
    quote_volume FLOAT,
    trades INT,
    is_closed BOOLEAN,
    timestamp timestamp,
    close_time timestamp,
    collected_at timestamp,
    consumed_at timestamp
);

CREATE INDEX IF NOT EXISTS asset_name_idx ON assets (asset_name);
```

---

## `docker-compose.yaml`
```yaml
version: "3.6"
services:
  coincap-cassandra:
    build:
      context: .
      dockerfile: Dockerfile
    image: cassandra:latest
    container_name: coincap-cassandra
    ports:
      - 9042:9042
    environment:
      - CASSANDRA_CLUSTER_NAME=conincap_cluster
      - CASSANDRA_USER=adminadmin
      - CASSANDRA_PASSWORD=adminadmin
      - CASSANDRA_DC=dc1
      - CASSANDRA_RACK=rack1
    healthcheck:
      test: ["CMD-SHELL", "cqlsh -e 'DESC KEYSPACES'"]
      interval: 30s
      timeout: 10s
      retries: 5
    volumes:
      - cassandra_data:/var/lib/cassandra
  
  coincap-cassandra-init:
    image: cassandra:latest
    container_name: binance-cassandra-init
    depends_on:
      coincap-cassandra:
        condition: service_healthy
    command: /bin/bash -c "cqlsh coincap-cassandra -u adminadmin -p adminadmin -f /init.cql"
```

---

## `Dockerfile`
```dockerfile
FROM cassandra:latest


COPY init.cql init.cql
``` 
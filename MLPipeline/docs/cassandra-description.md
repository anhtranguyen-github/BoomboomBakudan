Binance Cassandra Setup
This file documents the setup for a Cassandra service and its initialization using Docker and a shell script.

📦 Docker Services
binance-cassandra
yaml
Copy
Edit
binance-cassandra:
  image: cassandra:4.1.3
  container_name: binance-cassandra
  ports:
    - 9042:9042
  healthcheck:
    test: ["CMD-SHELL", "[ $$(nodetool statusgossip) = running ]"]
    interval: 30s
    timeout: 10s
    retries: 5
binance-cassandra-init
yaml
Copy
Edit
binance-cassandra-init:
  image: cassandra:4.1.3
  container_name: binance-cassandra-init
  depends_on:
    binance-cassandra:
      condition: service_healthy
  volumes:
    - ./init-cassandra.sh:/init-cassandra.sh
  command: ["/init-cassandra.sh"]
🛠️ Initialization Script
init-cassandra.sh
bash
Copy
Edit
#!/bin/bash

# Wait for Cassandra to be ready
echo "Waiting for Cassandra to start..."
until cqlsh binance-cassandra -u cassandra -p cassandra -e "describe keyspaces"; do
  echo "Cassandra is unavailable - sleeping"
  sleep 5
done

echo "Creating keyspace and table..."
# Create keyspace and table
cqlsh binance-cassandra -u cassandra -p cassandra -e "
CREATE KEYSPACE IF NOT EXISTS assets WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE assets;
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  asset_name TEXT,
  open FLOAT,
  high FLOAT,
  low FLOAT,
  close FLOAT, 
  volume FLOAT,
  quote_volume FLOAT,
  trades INT,
  is_closed BOOLEAN,
  timestamp TEXT,
  close_time TEXT,
  collected_at TEXT,
  consumed_at TEXT
);
"

echo "Creating admin user..."
# Create admin user
cqlsh binance-cassandra -u cassandra -p cassandra -e "
CREATE USER IF NOT EXISTS adminadmin WITH PASSWORD 'adminadmin' SUPERUSER;
"

echo "Cassandra initialization completed."
✅ Summary
binance-cassandra: Runs a Cassandra container with healthcheck.

binance-cassandra-init: Waits for Cassandra to be healthy and runs an init script.

init-cassandra.sh: Initializes keyspace, table, and admin user in Cassandra.

Use this setup to reliably provision a local Cassandra database with custom schema and user.
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
  asset_price FLOAT,
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
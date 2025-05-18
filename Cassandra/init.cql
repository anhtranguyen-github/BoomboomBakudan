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
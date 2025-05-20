# Bitcoin Price Prediction Model Service

This service provides real-time price predictions for Bitcoin using machine learning models.

## Overview

The Model Service connects to the Bitcoin data pipeline and:

1. Loads trained machine learning models from the `trained_models` directory
2. Consumes the latest Bitcoin price data from either:
   - Direct Kafka stream (same as BinanceConsumer)
   - Reading from Cassandra where BinanceConsumer stores data
3. Calculates required technical indicators for model inputs
4. Generates predictions using multiple ML models (LDA, GBM, XGB, CAT)
5. Saves predictions to Cassandra for visualization and analysis

## Architecture

```
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Binance API   │───▶│ Redpanda      │───▶│ BinanceConsumer│
└───────────────┘    └───────────────┘    └───────────────┘
                            │                      │
                            │                      ▼
                            │               ┌───────────────┐
                            │               │   Cassandra   │
                            │               └───────────────┘
                            │                      ▲
                            ▼                      │
                     ┌───────────────┐      ┌───────────────┐
                     │ Model Service │──────│ Visualization │
                     └───────────────┘      └───────────────┘
```

## Models

The service uses trained machine learning models:

- **LDA (Linear Discriminant Analysis)** - Linear classifier
- **GBM (Gradient Boosting Machine)** - Ensemble method
- **XGB (XGBoost)** - Optimized gradient boosting
- **CAT (CatBoost)** - Gradient boosting with categorical features support

All models produce binary classification outputs:
- `0` = Price is expected to decrease
- `1` = Price is expected to increase

## Configuration

The service can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `SPARK_MASTER` | Spark master URL | `local[*]` |
| `REDPANDA_BROKERS` | Kafka brokers | `localhost:9092` |
| `ASSET_PRICES_TOPIC` | Kafka topic for price data | `data.asset_prices` |
| `ASSET_CASSANDRA_HOST` | Cassandra host | `localhost` |
| `ASSET_CASSANDRA_PORT` | Cassandra port | `9042` |
| `ASSET_CASSANDRA_USERNAME` | Cassandra username | - |
| `ASSET_CASSANDRA_PASSWORD` | Cassandra password | - |
| `ASSET_CASSANDRA_KEYSPACE` | Cassandra keyspace | `assets` |
| `ASSET_CASSANDRA_TABLE` | Cassandra table for price data | `assets` |
| `MODEL_PREDICTIONS_TABLE` | Cassandra table for predictions | `model_predictions` |
| `MODEL_SERVICE_STREAM_MODE` | Run in streaming mode | `true` |
| `MODELS_DIR` | Directory containing trained models | `trained_models` |

## Running the Service

### Docker Compose

The easiest way to run the service is with Docker Compose:

```bash
docker-compose up -d
```

### Manual Execution

To run the service directly:

```bash
python ModelService.py
```

## Prediction Data Schema

The service saves predictions to Cassandra with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Same ID as the original price data |
| asset_name | TEXT | Asset name (e.g., BTCUSDT) |
| timestamp | TIMESTAMP | Timestamp of the original data point |
| model_name | TEXT | Name of the model making the prediction |
| prediction | INT | Binary prediction (0=decrease, 1=increase) |
| probability | FLOAT | Probability of the prediction (confidence) |
| predicted_at | TIMESTAMP | When the prediction was made 
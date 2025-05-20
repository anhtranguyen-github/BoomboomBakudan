FROM python:3.9-slim

WORKDIR /app

# Install Java (required for PySpark)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
ENV PYTHONPATH=${PYTHONPATH}:/app
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model service code
COPY ModelService.py .
COPY trained_models/ ./trained_models/

# Copy bitcoin trading package
COPY bitcoin_trading/ ./bitcoin_trading/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_SERVICE_STREAM_MODE=true
ENV MODELS_DIR=/app/trained_models
ENV ASSET_CASSANDRA_TABLE=assets
ENV ASSET_CASSANDRA_KEYSPACE=assets
ENV MODEL_PREDICTIONS_TABLE=model_predictions

# Run model service
CMD ["python", "ModelService.py"] 
import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import FloatType, IntegerType, StringType, BooleanType, TimestampType, StructType, StructField
from bitcoin_trading.features.technical_indicators import TechnicalIndicators

class ModelService:
    def __init__(self):
        """Initialize the model service with Spark session and load the ML models"""
        self.spark = SparkSession.builder \
            .appName('bitcoin-model-service') \
            .master(os.environ.get('SPARK_MASTER', 'local[*]')) \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
            .config("spark.cassandra.connection.host", os.environ.get('ASSET_CASSANDRA_HOST', 'localhost')) \
            .config("spark.cassandra.connection.port", os.environ.get('ASSET_CASSANDRA_PORT', 9042)) \
            .config("spark.cassandra.auth.username", os.environ.get('ASSET_CASSANDRA_USERNAME')) \
            .config("spark.cassandra.auth.password", os.environ.get('ASSET_CASSANDRA_PASSWORD')) \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint/models") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel('INFO')
        print("Model service SparkSession created successfully")
        
        # Load models and metadata
        self.models_dir = Path(os.environ.get('MODELS_DIR', 'MLPipeline/trained_models'))
        self.load_models()
        
        # Initialize technical indicators calculator
        self.indicators = TechnicalIndicators()
        
        # Define prediction schema
        self.prediction_schema = StructType([
            StructField("id", StringType(), True),
            StructField("asset_name", StringType(), True),
            StructField("timestamp", TimestampType(), True),
            StructField("model_name", StringType(), True),
            StructField("prediction", IntegerType(), True),
            StructField("probability", FloatType(), True),
            StructField("predicted_at", TimestampType(), True)
        ])

    def load_models(self):
        """Load trained models and their metadata"""
        # Find the latest metadata file
        metadata_files = list(self.models_dir.glob("model_metadata_*.json"))
        if not metadata_files:
            raise ValueError("No model metadata files found")
        
        latest_metadata_file = max(metadata_files, key=lambda x: x.name)
        print(f"Loading models from metadata: {latest_metadata_file}")
        
        # Load metadata
        with open(latest_metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        # Extract date from metadata filename
        model_date = latest_metadata_file.name.replace('model_metadata_', '').replace('.json', '')
        
        # Load all models
        self.models = {}
        for model_name in self.metadata['saved_models']:
            model_path = self.models_dir / f"{model_name}_full_{model_date}.joblib"
            if model_path.exists():
                self.models[model_name] = joblib.load(model_path)
                print(f"Loaded model: {model_name}")
            else:
                print(f"Warning: Model file not found: {model_path}")
        
        if not self.models:
            raise ValueError("No models could be loaded")
        
        # Store input features
        self.input_features = self.metadata['model_types']['full_features']['input_features']
        print(f"Model service ready with {len(self.models)} models")

    def read_from_cassandra(self):
        """Read the latest Bitcoin data from Cassandra"""
        # Read from Cassandra
        df = self.spark.read \
            .format("org.apache.spark.sql.cassandra") \
            .options(table=os.environ.get('ASSET_CASSANDRA_TABLE', 'assets'), 
                     keyspace=os.environ.get('ASSET_CASSANDRA_KEYSPACE', 'assets')) \
            .load() \
            .filter(F.col('asset_name') == 'BTCUSDT') \
            .orderBy(F.col('timestamp').desc()) \
            .limit(300)  # Get enough history to calculate indicators
        
        return df

    def calculate_features(self, df):
        """Calculate technical indicators needed for model input"""
        # Convert to pandas for easier indicator calculation
        pdf = df.toPandas()
        
        # Ensure data is sorted by timestamp
        pdf = pdf.sort_values('timestamp')
        
        # Prepare OHLCV data
        feature_df = pd.DataFrame({
            'Open': pdf['open'],
            'High': pdf['high'],
            'Low': pdf['low'],
            'Close': pdf['close'],
            'Volume': pdf['volume'],
            'timestamp': pdf['timestamp']
        })
        
        # Calculate all technical indicators
        feature_df = self.indicators.add_all_indicators(feature_df)

        # Add SMA1 and SMA2 for model input if required
        feature_df['SMA1'] = feature_df['Close'].rolling(window=10, min_periods=1).mean()
        feature_df['SMA2'] = feature_df['Close'].rolling(window=60, min_periods=1).mean()

        # Drop NaN values
        feature_df = feature_df.dropna()
        
        # Keep only the needed features
        model_features = feature_df[self.input_features]
        # Ensure all features are float type for model compatibility
        model_features = model_features.astype(float)

        # Add original data for reference
        result_df = model_features.copy()
        result_df['id'] = pdf.iloc[-len(model_features):]['id'].values
        result_df['asset_name'] = pdf.iloc[-len(model_features):]['asset_name'].values
        result_df['timestamp'] = pdf.iloc[-len(model_features):]['timestamp'].values
        
        return result_df

    def make_predictions(self, feature_df):
        """Generate predictions from all loaded models"""
        predictions = []
        
        # Get features for model input
        X = feature_df[self.input_features]
        # Ensure all features are float type for model compatibility
        X = X.astype(float)
        
        # Current timestamp for prediction records
        prediction_time = datetime.now()
        
        # Generate predictions from each model
        for model_name, model in self.models.items():
            try:
                # Get prediction and probability
                pred = model.predict(X)
                prob = model.predict_proba(X)[:, 1]  # Probability of class 1
                
                # Create prediction records
                for i in range(len(X)):
                    predictions.append({
                        'id': feature_df['id'].iloc[i],
                        'asset_name': feature_df['asset_name'].iloc[i],
                        'timestamp': feature_df['timestamp'].iloc[i],
                        'model_name': model_name,
                        'prediction': int(pred[i]),
                        'probability': float(prob[i]),
                        'predicted_at': prediction_time
                    })
            except Exception as e:
                print(f"Error making prediction with model {model_name}: {str(e)}")
        
        # Convert to DataFrame
        predictions_df = pd.DataFrame(predictions)
        return predictions_df

    def save_predictions_to_cassandra(self, predictions_df):
        """Save model predictions to Cassandra"""
        if predictions_df is None or len(predictions_df) == 0:
            print("No predictions to save to Cassandra.")
            return
        # Convert pandas DataFrame to Spark DataFrame
        spark_predictions = self.spark.createDataFrame(predictions_df, schema=self.prediction_schema)
        # Write to Cassandra
        spark_predictions.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=os.environ.get('MODEL_PREDICTIONS_TABLE', 'model_predictions'), 
                     keyspace=os.environ.get('ASSET_CASSANDRA_KEYSPACE', 'assets')) \
            .save()
        print(f"Saved {len(predictions_df)} predictions to Cassandra")

    def run(self):
        """Main method to run the prediction service"""
        try:
            # Read data from Cassandra
            print("Reading data from Cassandra...")
            data_df = self.read_from_cassandra()
            
            if data_df.count() == 0:
                print("No data found in Cassandra")
                return
            
            # Calculate features
            print("Calculating technical indicators...")
            feature_df = self.calculate_features(data_df)
            
            if len(feature_df) == 0:
                print("No valid features could be calculated")
                return
            
            # Make predictions
            print("Generating predictions...")
            predictions_df = self.make_predictions(feature_df)
            
            # Save predictions
            print("Saving predictions to Cassandra...")
            self.save_predictions_to_cassandra(predictions_df)
            
            print("Prediction cycle completed successfully")
            
        except Exception as e:
            print(f"Error in model service: {str(e)}")
            raise

    def run_stream(self):
        """Run as a streaming service that processes data continuously"""
        try:
            # Read streaming data from Cassandra
            print("Setting up streaming prediction service...")
            
            # Read from Kafka topic directly (same as BinanceConsumer)
            df_raw_stream = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", os.environ.get('REDPANDA_BROKERS', 'localhost:9092')) \
                .option("subscribe", os.environ.get('ASSET_PRICES_TOPIC', 'data.asset_prices')) \
                .option("startingOffsets", "latest") \
                .load()
            
            # Process each micro-batch
            def process_batch(batch_df, batch_id):
                if batch_df.count() > 0:
                    print(f"Processing batch {batch_id} with {batch_df.count()} records")
                    # Read current state from Cassandra to get historical data for indicators
                    cassandra_df = self.read_from_cassandra()
                    # Calculate features
                    feature_df = self.calculate_features(cassandra_df)
                    # Make predictions
                    predictions_df = self.make_predictions(feature_df)
                    # Save predictions
                    self.save_predictions_to_cassandra(predictions_df)
                    print(f"Batch {batch_id} processed successfully")
            
            # Start the streaming query
            query = df_raw_stream.writeStream \
                .foreachBatch(process_batch) \
                .outputMode("update") \
                .trigger(processingTime="1 minute") \
                .start()
            
            print("Streaming prediction service started")
            query.awaitTermination()
            
        except Exception as e:
            print(f"Error in streaming service: {str(e)}")
            raise

if __name__ == "__main__":
    # Create Cassandra prediction table if it doesn't exist
    # This is typically done in the initialization script, but we'll ensure it exists
    
    service = ModelService()
    
    # Choose running mode
    stream_mode = os.environ.get('MODEL_SERVICE_STREAM_MODE', 'true').lower() == 'true'
    
    if stream_mode:
        print("Starting model service in streaming mode")
        service.run_stream()
    else:
        print("Starting model service in batch mode")
        service.run() 
from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators
from bitcoin_trading.model_core.model_factory import ModelFactory
from bitcoin_trading.model_core.model_evaluator import ModelEvaluator
import time

# Script to load data, apply technical indicators, and evaluate models

def main():
    # Path to the CSV file
    data_path = 'btcusd_1-min_data.csv'
    
    # Initialize the data loader
    loader = BitcoinDataLoader(data_path)
    
    # Load the data
    df = loader.load_data()
    
    # Define the period for training and testing
    data_period = slice('2025-03-01', '2025-05-01')
    
    # Split the data into training and testing sets
    df_train, df_test = loader.split_timeseries(df, test_size=0.2, cut_period=data_period)
    
    # Clean the data
    df_train = loader.clean_data(df_train)
    df_test = loader.clean_data(df_test)
    
    # Initialize the technical indicators generator
    indicators = TechnicalIndicators()
    
    # Add technical indicators to training and testing data
    df_train = indicators.add_all_indicators(df_train)
    df_test = indicators.add_all_indicators(df_test)
    
    # Create target signal manually since it's missing from the data
    df_train = indicators.create_target_signal(df_train)
    df_test = indicators.create_target_signal(df_test)
    
    # Drop rows with NaN values (critical fix for model training)
    print(f"\nBefore dropping NaN values: {len(df_train)} rows")
    df_train = df_train.dropna()
    df_test = df_test.dropna()
    print(f"After dropping NaN values: {len(df_train)} rows")
    
    # Track training process
    print("\nStarting training process...")
    start_time = time.time()

    # Evaluate baseline model
    print("\nEvaluating baseline model...")
    baseline_features = ['Open', 'High', 'Low', 'Close', 'Volume', 'signal']
    df_baseline = df_train[baseline_features]
    
    # Ensure baseline dataset doesn't have NaN values
    df_baseline = df_baseline.dropna()
    
    models = ModelFactory.create_models(n_estimators=25)
    evaluator = ModelEvaluator(models, n_fold=5, scoring='accuracy')
    baseline_results, baseline_times, _ = evaluator.evaluate(df_baseline, plot=False)
    
    # Record baseline model training time
    baseline_training_time = time.time() - start_time
    print(f"Baseline model training time: {baseline_training_time:.2f} seconds")
    
    # Evaluate model with all indicators
    print("\nEvaluating model with all indicators...")
    start_time = time.time()
    all_results, all_times, _ = evaluator.evaluate(df_train, plot=False)
    
    # Record all indicators model training time
    all_training_time = time.time() - start_time
    print(f"Model with all indicators training time: {all_training_time:.2f} seconds")
    
    # Compare results
    print("\nModel Performance Comparison:")
    print("Baseline Model:")
    print(baseline_results)
    print("\nModel with All Indicators:")
    print(all_results)

if __name__ == "__main__":
    main()
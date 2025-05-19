from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators
from bitcoin_trading.models.model_factory import ModelFactory
from bitcoin_trading.models.model_evaluator import ModelEvaluator
from bitcoin_trading.models.model_pipeline import ModelPipeline
import time
import pandas as pd

# Script to demonstrate training with pipelines

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
    
    # Get the models
    models_list = ModelFactory.create_models(n_estimators=25)
    
    # Initialize the evaluator
    evaluator = ModelEvaluator([], n_fold=5, scoring='accuracy')
    
    # Preprocessing strategies to test
    preprocess_strategies = ['standard', 'minmax', 'robust', 'impute']
    
    # Results storage
    results = []
    
    print("\nStarting pipeline experiments...")
    start_time = time.time()
    
    # Loop through preprocessing strategies
    for strategy in preprocess_strategies:
        print(f"\nTesting preprocessing strategy: {strategy}")
        
        # Create pipelines for each model
        pipeline_models = []
        for model_name, model_instance in models_list:
            pipeline = ModelPipeline.create_pipeline(
                model_instance,
                preprocess_strategy=strategy
            )
            pipeline_models.append((f"{model_name}_{strategy}", pipeline))
        
        # Set new models for evaluator
        evaluator.models = pipeline_models
        
        # Evaluate pipeline models
        strategy_results, strategy_times, _ = evaluator.evaluate(df_train, plot=False)
        strategy_results['strategy'] = strategy
        results.append(strategy_results)
    
    # Combine and display all results
    all_results = pd.concat(results)
    print("\nAll Pipeline Results:")
    print(all_results)
    
    print(f"\nTotal experiment time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main() 
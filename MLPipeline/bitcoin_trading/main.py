# File: bitcoin_trading/main.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytz

from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators
from bitcoin_trading.model_core.model_factory import ModelFactory
from bitcoin_trading.model_core.model_evaluator import ModelEvaluator
from bitcoin_trading.features.feature_importance import FeatureImportanceAnalyzer
from bitcoin_trading.dim_reduction.feature_reducer import FeatureReducer

def main():
    # Config
    data_path = 'bitstampUSD_1-min_data_2012-01-01_to_2021-03-31.csv'
    data_period = slice('2025-03-01', '2025-05-01')
    test_size = 0.2
    
    # Load and prepare data
    print("Loading data...")
    loader = BitcoinDataLoader(data_path)
    df = loader.load_data()
    df_train, df_test = loader.split_timeseries(df, test_size=test_size, cut_period=data_period)
    df_train = loader.clean_data(df_train)
    df_test = loader.clean_data(df_test)
    
    # Add technical indicators
    print("Creating technical indicators...")
    indicator_generator = TechnicalIndicators()
    df_train = indicator_generator.create_target_signal(df_train)
    df_train = indicator_generator.add_all_indicators(df_train)
    df_test = indicator_generator.create_target_signal(df_test)
    df_test = indicator_generator.add_all_indicators(df_test)
    
    # Clean the enhanced dataframes
    df_train = df_train.dropna()
    df_test = df_test.dropna()
    
    # Evaluate baseline model
    print("\nEvaluating baseline model...")
    baseline_features = ['Open', 'High', 'Low', 'Close', 'Volume_(BTC)', 'Volume_(Currency)', 'Weighted_Price', 'signal']
    df_baseline = df_train[baseline_features]
    
    models = ModelFactory.create_models(n_estimators=25)
    evaluator = ModelEvaluator(models, n_fold=5, scoring='accuracy')
    baseline_results, baseline_times, _ = evaluator.evaluate(df_baseline, plot=True)
    
    # Analyze feature importance
    print("\nAnalyzing feature importance...")
    importance_analyzer = FeatureImportanceAnalyzer(df_train)
    importance_df = importance_analyzer.analyze()
    importance_analyzer.plot_importance(importance_df)
    
    # Filter to important features based on importance analysis
    print("\nRemoving less important features...")
    features_to_drop = ['Open', 'High', 'Low', 'Close', 'Volume_(BTC)', 'Volume_(Currency)', 
                        'Weighted_Price', 'MA63', 'EMA10', '%K10']
    df_optimized = df_train.drop(columns=features_to_drop)
    
    # Evaluate optimized model
    print("\nEvaluating feature-optimized model...")
    optimized_results, optimized_times, _ = evaluator.evaluate(df_optimized, plot=True)
    
    # Apply dimensionality reduction
    print("\nApplying dimensionality reduction...")
    reducer = FeatureReducer(method='fastica', n_components=5)
    df_reduced = reducer.reduce_features(df_train, scaler='standard')
    
    # Evaluate reduced model
    print("\nEvaluating dimension-reduced model...")
    reduced_results, reduced_times, _ = evaluator.evaluate(df_reduced, plot=True)
    
    # Compare results
    print("\nComparing model results:")
    comparison = pd.DataFrame({
        'baseline': baseline_results['cv_average'],
        'optimized': optimized_results['cv_average'],
        'reduced': reduced_results['cv_average']
    })
    
    plt.figure(figsize=(12, 6))
    comparison.plot(kind='bar')
    plt.title('Model Performance Comparison')
    plt.ylabel('CV Average Accuracy')
    plt.tight_layout()
    plt.show()
    
    # Print timing comparison
    print("\nExecution time comparison (seconds):")
    timing = pd.DataFrame({
        'baseline': baseline_times,
        'optimized': optimized_times,
        'reduced': reduced_times
    })
    print(timing)

if __name__ == "__main__":
    main()
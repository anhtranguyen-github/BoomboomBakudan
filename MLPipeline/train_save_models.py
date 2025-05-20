from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators
from bitcoin_trading.model_core.model_factory import ModelFactory
from bitcoin_trading.model_core.model_evaluator import ModelEvaluator
import time
import datetime
import pandas as pd
import numpy as np
import os
import joblib
from pathlib import Path
import json

# Script to load data, train, evaluate and save models from 2025-03-01 to today

def get_feature_names(df_train, is_baseline=False):
    """Get feature names for model input."""
    if is_baseline:
        return ['Open', 'High', 'Low', 'Close', 'Volume']
    else:
        return [col for col in df_train.columns if col != 'signal']

def save_model_metadata(models_dir, baseline_features, all_features, end_date, saved_models):
    """Save metadata about models for serving."""
    metadata = {
        "training_date": end_date,
        "model_types": {
            "baseline": {
                "description": "Models trained on basic OHLCV data only",
                "input_features": baseline_features,
                "output": "Binary classification (0 or 1)",
                "output_meaning": {
                    "0": "Price is expected to decrease",
                    "1": "Price is expected to increase"
                },
                "file_pattern": "*_baseline_*.joblib"
            },
            "full_features": {
                "description": "Models trained on all technical indicators",
                "input_features": all_features,
                "output": "Binary classification (0 or 1)",
                "output_meaning": {
                    "0": "Price is expected to decrease",
                    "1": "Price is expected to increase"
                },
                "file_pattern": "*_full_*.joblib"
            }
        },
        "serving_instructions": {
            "preprocessing": [
                "Ensure all input features match the expected feature names",
                "Handle missing values by forward-filling or using last valid values",
                "No need for additional scaling as it's handled in model pipelines"
            ],
            "prediction": [
                "Load model using joblib.load('model_file.joblib')",
                "Ensure input DataFrame has the correct features in the right order",
                "Get prediction using model.predict(X)"
            ]
        }
    }
    
    # Save metadata to JSON
    with open(models_dir / f"model_metadata_{end_date}.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    # Also create a README file in the models directory - use triple braces to escape code examples
    readme_content = f"""# Model Serving Guide

## Models Overview
This directory contains trained machine learning models for Bitcoin price prediction.
Training date: {end_date}

## Model Types

### Baseline Models (`*_baseline_{end_date}.joblib`)
- **Description**: Models trained on basic OHLCV data only
- **Input features**: {", ".join(baseline_features)}
- **Output**: Binary classification (0 or 1)
  - 0: Price is expected to decrease
  - 1: Price is expected to increase

### Full-Feature Models (`*_full_{end_date}.joblib`)
- **Description**: Models trained on all technical indicators
- **Input features**: (see model_metadata_{end_date}.json - too many to list here)
- **Output**: Binary classification (0 or 1)
  - 0: Price is expected to decrease
  - 1: Price is expected to increase

## Saved Models
{", ".join(saved_models if saved_models else ["No models saved"])}

## Serving Instructions

### Preprocessing Requirements
1. Ensure all input features match the expected feature names
2. Handle missing values by forward-filling or using last valid values
3. No need for additional scaling as it's handled in model pipelines

### Prediction Code Example
```python
import joblib
import pandas as pd

# Load the model
model = joblib.load('trained_models/RF_full_{end_date}.joblib')

# Prepare input data (example)
data = {{...}}  # Your input data with all required features
X = pd.DataFrame([data])

# Get prediction
prediction = model.predict(X)[0]
probability = model.predict_proba(X)[0][1]  # Probability of class 1

print(f"Prediction: {{'Increase' if prediction == 1 else 'Decrease'}}")
print(f"Confidence: {{probability:.4f}}")
```

See `model_metadata_{end_date}.json` for complete feature lists and details.
"""
    
    with open(models_dir / "README.md", "w") as f:
        f.write(readme_content)

def print_report(results, start_date, end_date, start_time, initial_train_size, final_train_size, baseline_features, all_features):
    """
    Print a detailed report of model training and performance.
    
    Parameters:
    -----------
    results : pandas.DataFrame
        DataFrame with model results
    start_date : str
        Start date of data used for training
    end_date : str
        End date of data used for training
    start_time : float
        Start time of training process
    initial_train_size : int
        Number of samples before preprocessing
    final_train_size : int
        Number of samples after preprocessing
    baseline_features : list
        List of baseline feature names
    all_features : list
        List of all feature names
    """
    total_time = time.time() - start_time
    model_count = len(results)
    
    print("\n" + "="*80)
    print(f"MODEL TRAINING REPORT ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*80)
    
    print(f"\nTRAINING SUMMARY:")
    print(f"  Data period: {start_date} to {end_date}")
    print(f"  Total models trained: {model_count}")
    print(f"  Training samples: {final_train_size} (from initial {initial_train_size})")
    print(f"  Total training time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"  Average time per model: {total_time/model_count:.2f} seconds")
    
    # Check what columns are available in the results DataFrame
    print("\nAvailable columns in results:", results.columns.tolist())
    
    # Handle sorting based on available columns
    accuracy_col = next((col for col in results.columns if col.lower() in ['accuracy', 'cv_average', 'test', 'all']), 'cv_average')
    print(f"Using column '{accuracy_col}' for sorting performance")
    
    print("\nMODEL PERFORMANCE (TOP 5):")
    top_models = results.sort_values(accuracy_col, ascending=False).head(5)
    for i, (idx, row) in enumerate(top_models.iterrows()):
        model_name = idx if isinstance(idx, str) else row.get('model', str(idx))
        accuracy_value = row[accuracy_col]
        if isinstance(accuracy_value, (pd.Series, np.ndarray)):
            accuracy_value = accuracy_value.iloc[0] if len(accuracy_value) > 0 else 0.0
        print(f"  {i+1}. {model_name}: {accuracy_value:.4f}")
    
    print("\nMODEL PERFORMANCE (BOTTOM 5):")
    bottom_models = results.sort_values(accuracy_col, ascending=True).head(5)
    for i, (idx, row) in enumerate(bottom_models.iterrows()):
        model_name = idx if isinstance(idx, str) else row.get('model', str(idx))
        accuracy_value = row[accuracy_col]
        if isinstance(accuracy_value, (pd.Series, np.ndarray)):
            accuracy_value = accuracy_value.iloc[0] if len(accuracy_value) > 0 else 0.0
        print(f"  {i+1}. {model_name}: {accuracy_value:.4f}")
    
    # Group by algorithm type
    if isinstance(results.index, pd.Index) and not isinstance(results.index, pd.RangeIndex):
        results['algorithm'] = results.index.str.split('_').str[0]
    elif 'model' in results.columns:
        results['algorithm'] = results['model'].str.split('_').str[0]
    else:
        results['algorithm'] = 'Unknown'
    
    algo_perf = results.groupby('algorithm')[accuracy_col].agg(['mean', 'max', 'min', 'std'])
    algo_perf = algo_perf.sort_values('mean', ascending=False)
    
    print("\nALGORITHM PERFORMANCE:")
    for algo, metrics in algo_perf.iterrows():
        print(f"  {algo}: Avg={metrics['mean']:.4f}, Max={metrics['max']:.4f}, " +
              f"Min={metrics['min']:.4f}, Std={metrics['std']:.4f}")
    
    # Best model details
    best_idx = results[accuracy_col].idxmax()
    best_model_name = best_idx if isinstance(best_idx, str) else results.loc[best_idx].get('model', str(best_idx))
    
    # Get accuracy value safely
    accuracy_value = results.loc[best_idx, accuracy_col]
    if isinstance(accuracy_value, (pd.Series, np.ndarray)):
        accuracy_value = accuracy_value.iloc[0] if len(accuracy_value) > 0 else 0.0
    
    print("\nBEST MODEL DETAILS:")
    print(f"  Name: {best_model_name}")
    print(f"  {accuracy_col}: {accuracy_value:.4f}")
    
    print("\nSAVED ARTIFACTS:")
    print(f"  - Model files: trained_models/*.joblib")
    print(f"  - Results CSV: trained_models/model_results_{end_date}.csv")
    print(f"  - Metadata: trained_models/model_metadata_{end_date}.json")
    print(f"  - Serving guide: trained_models/README.md")
    
    print("\nMODEL INPUT/OUTPUT SPECIFICATIONS:")
    print("  Baseline Models:")
    print(f"  - Input features ({len(baseline_features)}): {', '.join(baseline_features[:3])}..." if len(baseline_features) > 3 else f"  - Input features: {', '.join(baseline_features)}")
    print("  - Output: Binary classification (0=Price decrease, 1=Price increase)")
    print("")
    print("  Full-Feature Models:")
    print(f"  - Input features ({len(all_features)}): {', '.join(all_features[:3])}..." if len(all_features) > 3 else f"  - Input features: {', '.join(all_features)}")
    print("  - Output: Binary classification (0=Price decrease, 1=Price increase)")
    print("")
    print("  For complete feature lists and serving instructions, see:")
    print(f"  - trained_models/model_metadata_{end_date}.json")
    print("  - trained_models/README.md")
    
    print("\n" + "="*80)

def main():
    # Configure start date and today's date
    start_date = '2025-03-01'
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    print(f"Training models from {start_date} to {end_date}")
    
    # Create directory for saving models if it doesn't exist
    models_dir = Path("trained_models")
    models_dir.mkdir(exist_ok=True)
    
    # Path to the CSV file
    data_path = 'btcusd_1-min_data.csv'
    
    # Initialize the data loader
    loader = BitcoinDataLoader(data_path)
    
    # Load the data
    print("Loading data...")
    df = loader.load_data()
    
    # Define the period for training and testing
    data_period = slice(start_date, end_date)
    
    # Split the data into training and testing sets
    df_train, df_test = loader.split_timeseries(df, test_size=0.2, cut_period=data_period)
    
    # Clean the data
    df_train = loader.clean_data(df_train)
    df_test = loader.clean_data(df_test)
    
    # Initialize the technical indicators generator
    indicators = TechnicalIndicators()
    
    # Add technical indicators to training and testing data
    print("Generating technical indicators...")
    df_train = indicators.add_all_indicators(df_train)
    df_test = indicators.add_all_indicators(df_test)
    
    # Create target signal manually since it's missing from the data
    df_train = indicators.create_target_signal(df_train)
    df_test = indicators.create_target_signal(df_test)
    
    # Track initial size
    initial_train_size = len(df_train)
    
    # Drop rows with NaN values (critical fix for model training)
    print(f"\nBefore dropping NaN values: {len(df_train)} rows")
    df_train = df_train.dropna()
    df_test = df_test.dropna()
    print(f"After dropping NaN values: {len(df_train)} rows")
    
    # Track final size after cleaning
    final_train_size = len(df_train)
    
    # Get feature lists
    baseline_features = ['Open', 'High', 'Low', 'Close', 'Volume']
    all_features = [col for col in df_train.columns if col != 'signal']
    
    # Models to save (only these will be saved for production)
    models_to_save = ['XGB', 'CAT', 'LDA', 'GBM']
    print(f"\nOnly saving selected models for production: {', '.join(models_to_save)}")
    
    # Track training process
    print("\nStarting training process...")
    start_time = time.time()

    # Evaluate baseline model
    print("\nEvaluating baseline model...")
    baseline_features_with_signal = baseline_features + ['signal']
    df_baseline = df_train[baseline_features_with_signal]
    
    # Ensure baseline dataset doesn't have NaN values
    df_baseline = df_baseline.dropna()
    
    models = ModelFactory.create_models(n_estimators=100)  # Increased from 25 for better accuracy
    evaluator = ModelEvaluator(models, n_fold=5, scoring='accuracy')
    baseline_results, baseline_times, _ = evaluator.evaluate(df_baseline, plot=False)
    
    # Print baseline_results columns to debug
    print("\nBaseline results columns:", baseline_results.columns.tolist())
    
    # We'll evaluate all models but not save baseline models to save space
    print("\nSkipping saving baseline models (evaluating only)")
    
    # Evaluate model with all indicators
    print("\nEvaluating model with all indicators...")
    all_results, all_times, _ = evaluator.evaluate(df_train, plot=False)
    
    # Print all_results columns to debug
    print("\nAll results columns:", all_results.columns.tolist())
    
    # Save only selected full-feature models
    print("\nSaving selected full-feature models only...")
    saved_models = []
    
    for model_name in all_results.index:
        if any(selected_model in model_name for selected_model in models_to_save):
            # Recreate the model
            model_instance = next((m for n, m in models if n == model_name), None)
            if model_instance:
                # Train on all features
                X = df_train.drop(columns=['signal'])
                y = df_train['signal']
                model_instance.fit(X, y)
                
                # Save the model
                model_filename = f"{model_name}_full_{end_date}.joblib"
                model_path = models_dir / model_filename
                joblib.dump(model_instance, model_path)
                saved_models.append(model_name)
                print(f"Saved {model_name} full-feature model to {model_path}")
        else:
            print(f"Skipping {model_name} (not in selected models list)")
    
    print(f"\nSaved models: {', '.join(saved_models)}")
    
    # Combine results for reporting
    baseline_results['model_type'] = 'baseline'
    all_results['model_type'] = 'full_features'
    
    # Add to comprehensive results dataframe
    combined_results = pd.concat([baseline_results, all_results])
    
    # Save results to CSV
    results_filename = f"model_results_{end_date}.csv"
    results_path = models_dir / results_filename
    combined_results.to_csv(results_path)
    print(f"\nSaved model results to {results_path}")
    
    # Update metadata to only include saved models
    metadata = {
        "training_date": end_date,
        "saved_models": saved_models,
        "model_types": {
            "full_features": {
                "description": "Models trained on all technical indicators",
                "input_features": all_features,
                "output": "Binary classification (0 or 1)",
                "output_meaning": {
                    "0": "Price is expected to decrease",
                    "1": "Price is expected to increase"
                },
                "file_pattern": "*_full_*.joblib"
            }
        },
        "serving_instructions": {
            "preprocessing": [
                "Ensure all input features match the expected feature names",
                "Handle missing values by forward-filling or using last valid values",
                "No need for additional scaling as it's handled in model pipelines"
            ],
            "prediction": [
                "Load model using joblib.load('model_file.joblib')",
                "Ensure input DataFrame has the correct features in the right order",
                "Get prediction using model.predict(X)"
            ]
        }
    }
    
    # Save metadata to JSON
    with open(models_dir / f"model_metadata_{end_date}.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    # Create a more focused README
    readme_content = f"""# Bitcoin Price Prediction Models

## Models Overview
This directory contains selected machine learning models for Bitcoin price prediction.
Training date: {end_date}

## Saved Models
{", ".join(saved_models)}

## Model Details
- **Description**: Models trained on all technical indicators
- **Input features**: (see model_metadata_{end_date}.json for complete list)
- **Output**: Binary classification (0 or 1)
  - 0: Price is expected to decrease
  - 1: Price is expected to increase

## Serving Instructions

### Preprocessing Requirements
1. Ensure all input features match the expected feature names
2. Handle missing values by forward-filling or using last valid values
3. No need for additional scaling as it's handled in model pipelines

### Prediction Code Example
```python
import joblib
import pandas as pd

# Load the model (use one of: {", ".join([f"{model}_full_{end_date}.joblib" for model in saved_models])})
model = joblib.load('trained_models/{saved_models[0] if saved_models else "RF"}_full_{end_date}.joblib')

# Prepare input data (example)
data = {{...}}  # Your input data with all required features
X = pd.DataFrame([data])

# Get prediction
prediction = model.predict(X)[0]
probability = model.predict_proba(X)[0][1]  # Probability of class 1

print(f"Prediction: {{'Increase' if prediction == 1 else 'Decrease'}}")
print(f"Confidence: {{probability:.4f}}")
```

See `model_metadata_{end_date}.json` for complete feature lists and details.
"""
    
    with open(models_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"\nSaved model metadata and serving guide to trained_models directory")
    
    # Record all indicators model training time
    total_training_time = time.time() - start_time
    print(f"Total training time: {total_training_time:.2f} seconds")
    
    # Compare results
    print("\nModel Performance Comparison:")
    print("Baseline Model:")
    print(baseline_results)
    print("\nModel with All Indicators:")
    print(all_results)
    
    # Print detailed report
    print_report(combined_results, start_date, end_date, start_time, initial_train_size, 
                final_train_size, baseline_features, all_features)
    
    print("\nModel serving documentation has been generated in the trained_models directory.")
    print(f"IMPORTANT: Only {len(saved_models)} models have been saved: {', '.join(saved_models)}")
    print("Use the README.md and model_metadata JSON files for guidance on using these models in production.")

if __name__ == "__main__":
    main() 
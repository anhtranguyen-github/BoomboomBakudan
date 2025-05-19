from bitcoin_trading.dim_reduction.feature_reducer import FeatureReducer
from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators

# Example usage of FeatureReducer

def main():
    # Path to the CSV file
    data_path = 'btcusd_1-min_data.csv'
    
    # Initialize the data loader
    loader = BitcoinDataLoader(data_path)
    
    # Load the data
    df = loader.load_data()
    
    # Define the period for analysis
    data_period = slice('2025-03-01', '2025-05-01')
    df = df.loc[data_period]
    
    # Initialize the technical indicators generator
    indicators = TechnicalIndicators()
    
    # Create the target signal
    df = indicators.create_target_signal(df)
    
    # Initialize the feature reducer
    reducer = FeatureReducer(method='pca', n_components=2)
    
    # Reduce features
    df_reduced = reducer.reduce_features(df, target_col='signal', scaler='standard', plot=True)
    
    # Print the reduced dataframe
    print(df_reduced.head())

if __name__ == "__main__":
    main() 
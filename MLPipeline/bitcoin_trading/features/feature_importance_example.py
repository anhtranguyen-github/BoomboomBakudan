from bitcoin_trading.features.feature_importance import FeatureImportanceAnalyzer
from bitcoin_trading.data.data_loader import BitcoinDataLoader
from bitcoin_trading.features.technical_indicators import TechnicalIndicators

# Example usage of FeatureImportanceAnalyzer

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
    
    # Initialize the feature importance analyzer
    analyzer = FeatureImportanceAnalyzer(df, target_col='signal')
    
    # Analyze feature importance
    importance_df = analyzer.analyze()
    
    # Plot feature importance
    analyzer.plot_importance(importance_df)

if __name__ == "__main__":
    main() 
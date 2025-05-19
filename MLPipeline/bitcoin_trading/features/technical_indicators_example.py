from bitcoin_trading.features.technical_indicators import TechnicalIndicators
from bitcoin_trading.data.data_loader import BitcoinDataLoader

# Example usage of TechnicalIndicators

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
    
    # Add all indicators
    df_with_indicators = indicators.add_all_indicators(df)
    
    # Print the resulting dataframe
    print(df_with_indicators.head(40))

if __name__ == "__main__":
    main() 
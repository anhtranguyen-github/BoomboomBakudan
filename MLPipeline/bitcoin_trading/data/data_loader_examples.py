from bitcoin_trading.data.data_loader import BitcoinDataLoader

# Example usage of BitcoinDataLoader

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
    
    # Print the results
    print("Training Data:")
    print(df_train.head())
    print("\nTesting Data:")
    print(df_test.head())
    
    # Display basic information about the dataset
    print("\nData Information:")
    print(df_test.info())
    
    # Display summary statistics
    print("\nSummary Statistics:")
    print(df_test.describe())
    
    # Display the first few rows of the dataset
    print("\nFirst few rows of the dataset:")
    print(df_test.head())
    
    # Display the last few rows of the dataset
    print("\nLast few rows of the dataset:")
    print(df_test.tail())
    
    # Display the number of rows in the dataset
    print("\nNumber of rows in the dataset:")
    print(len(df_test))

if __name__ == "__main__":
    main()

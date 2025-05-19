# File: bitcoin_trading/data/data_loader.py
import pandas as pd
import datetime
import pytz
import numpy as np

class BitcoinDataLoader:
    """Loads and preprocesses Bitcoin price data."""
    
    def __init__(self, path, date_parser=None):
        self.path = path
        self.date_parser = date_parser or self._default_date_parser
    
    def _default_date_parser(self, time_in_secs):
        return pytz.utc.localize(datetime.datetime.fromtimestamp(float(time_in_secs)))
    
    def load_data(self):
        """Load data from CSV file."""
        return pd.read_csv(self.path, 
                          parse_dates=[0],
                          date_parser=self.date_parser,
                          index_col='Timestamp')
    
    def reduce_memory(self, df):
        """Reduce memory usage of dataframe."""
        numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
        start_mem = df.memory_usage().sum() / 1024**2
        for col in df.columns:
            col_type = df[col].dtypes
            if col_type in numerics:
                c_min = df[col].min()
                c_max = df[col].max()
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                    elif c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
                        df[col] = df[col].astype(np.int64)
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        df[col] = df[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
                    else:
                        df[col] = df[col].astype(np.float64)
        end_mem = df.memory_usage().sum() / 1024**2
        print(f'Memory usage after optimization is: {end_mem:.2f} MB')
        print(f'Decreased by {100 * (start_mem - end_mem) / start_mem:.1f}%')
        return df

    def split_timeseries(self, df, test_size=0.2, cut_period=None):
        """Split the dataframe into training and testing sets."""
        if cut_period:
            if isinstance(cut_period, int):
                df = df.iloc[-cut_period:]
            else:
                df = df[cut_period]
            t1 = df.index.max()
            t0 = df.index.min()
            print(f'Dataset Min.Index: {t0} | Max.Index: {t1}')
        
        train_df, test_df = pd.DataFrame(), pd.DataFrame()
        if test_size:
            # Non-shuffled split for time series
            split_idx = int(len(df) * (1 - test_size))
            train_df = df.iloc[:split_idx]
            test_df = df.iloc[split_idx:]
        
        return train_df, test_df
    
    def clean_data(self, df):
        """Clean missing data in the dataframe."""
        df['Open'] = df['Open'].ffill()
        df['High'] = df['High'].ffill()
        df['Low'] = df['Low'].ffill()
        df['Close'] = df['Close'].ffill()
        return df.dropna()
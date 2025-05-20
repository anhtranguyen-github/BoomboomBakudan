# File: bitcoin_trading/features/technical_indicators.py
import pandas as pd
import numpy as np

class TechnicalIndicators:
    """Class for generating technical indicators from price data."""
    
    @staticmethod
    def create_target_signal(df):
        """Create target variable based on SMA crossover."""
        df = df.copy()
        df['SMA1'] = df['Close'].rolling(window=10, min_periods=1, center=False).mean()
        df['SMA2'] = df['Close'].rolling(window=60, min_periods=1, center=False).mean()
        df['signal'] = np.where(df['SMA1'] > df['SMA2'], 1.0, 0.0)
        return df
    
    @staticmethod
    def add_moving_averages(df):
        """Add moving averages to dataframe."""
        df['MA21'] = TechnicalIndicators.ma(df, 10)
        df['MA63'] = TechnicalIndicators.ma(df, 30)
        df['MA252'] = TechnicalIndicators.ma(df, 200)
        return df
    
    @staticmethod
    def add_ema(df):
        """Add exponential moving averages to dataframe."""
        df['EMA10'] = TechnicalIndicators.ema(df, 10)
        df['EMA30'] = TechnicalIndicators.ema(df, 30)
        df['EMA200'] = TechnicalIndicators.ema(df, 200)
        return df
    
    @staticmethod
    def add_momentum(df):
        """Add momentum indicators to dataframe."""
        df['MOM10'] = TechnicalIndicators.mom(df['Close'], 10)
        df['MOM30'] = TechnicalIndicators.mom(df['Close'], 30)
        return df
    
    @staticmethod
    def add_rsi(df):
        """Add relative strength index to dataframe."""
        df['RSI10'] = TechnicalIndicators.rsi(df['Close'], 10)
        df['RSI30'] = TechnicalIndicators.rsi(df['Close'], 30)
        df['RSI200'] = TechnicalIndicators.rsi(df['Close'], 200)
        return df
    
    @staticmethod
    def add_stochastic(df):
        """Add stochastic oscillators to dataframe."""
        # Slow oscillators
        df['%K10'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 5, 0)
        df['%K30'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 10, 0)
        df['%K200'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 20, 0)
        
        # Fast oscillators
        df['%D10'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 10, 1)
        df['%D30'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 30, 1)
        df['%D200'] = TechnicalIndicators.sto(df['Close'], df['Low'], df['High'], 200, 1)
        return df
    
    @staticmethod
    def add_all_indicators(df):
        """Add all technical indicators to dataframe."""
        df = TechnicalIndicators.add_moving_averages(df)
        df = TechnicalIndicators.add_ema(df)
        df = TechnicalIndicators.add_momentum(df)
        df = TechnicalIndicators.add_rsi(df)
        df = TechnicalIndicators.add_stochastic(df)
        return df
    
    # Technical indicator calculations
    @staticmethod
    def ma(df, n):
        """Calculate moving average."""
        if len(df) < n:
            return pd.Series([np.nan] * len(df), index=df.index, name=f'MA_{n}')
        return pd.Series(df['Close'].rolling(n, min_periods=n).mean(), name=f'MA_{n}')
    
    @staticmethod
    def ema(df, n):
        """Calculate exponentially weighted moving average."""
        if len(df) < n:
            return pd.Series([np.nan] * len(df), index=df.index, name=f'EMA_{n}')
        return pd.Series(df['Close'].ewm(span=n, min_periods=n).mean(), name=f'EMA_{n}')
    
    @staticmethod
    def mom(df, n):
        """Calculate price momentum."""
        if len(df) < n:
            return pd.Series([np.nan] * len(df), index=df.index, name=f'Momentum_{n}')
        return pd.Series(df.diff(n), name=f'Momentum_{n}')
    
    @staticmethod
    def roc(df, n):
        """Calculate rate of change."""
        if len(df) < n:
            return pd.Series([np.nan] * len(df), index=df.index, name=f'ROC_{n}')
        M = df.diff(n - 1)
        N = df.shift(n - 1)
        return pd.Series(((M / N) * 100), name=f'ROC_{n}')
    
    @staticmethod
    def rsi(df, period):
        """Calculate relative strength index."""
        if len(df) < period:
            return pd.Series([np.nan] * len(df), index=df.index)
        delta = df.diff().dropna()
        u = delta * 0
        d = u.copy()
        u[delta > 0] = delta[delta > 0]
        d[delta < 0] = -delta[delta < 0]
        u[u.index[period-1]] = np.mean(u[:period])
        u = u.drop(u.index[:(period-1)])
        d[d.index[period-1]] = np.mean(d[:period])
        d = d.drop(d.index[:(period-1)])
        rs = u.ewm(com=period-1, adjust=False).mean() / d.ewm(com=period-1, adjust=False).mean()
        rsi = 100 - 100 / (1 + rs)
        # Pad the beginning with NaN to match the original index length
        pad = [np.nan] * (len(df) - len(rsi))
        return pd.Series(pad + list(rsi), index=df.index)
    
    @staticmethod
    def sto(close, low, high, n, id):
        """Calculate stochastic oscillators."""
        if len(close) < n or len(low) < n or len(high) < n:
            return pd.Series([np.nan] * len(close), index=close.index)
        stok = ((close - low.rolling(n).min()) / (high.rolling(n).max() - low.rolling(n).min())) * 100
        if id == 0:
            return stok
        else:
            return stok.rolling(3).mean()
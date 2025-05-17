import pandas as pd
import numpy as np
import ta
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import config

class TechnicalAnalyzer:
    def __init__(self):
        self.rsi_period = config.RSI_PERIOD
        self.rsi_overbought = config.RSI_OVERBOUGHT
        self.rsi_oversold = config.RSI_OVERSOLD
        self.macd_fast = config.MACD_FAST
        self.macd_slow = config.MACD_SLOW
        self.macd_signal = config.MACD_SIGNAL

    def calculate_indicators(self, df):
        """Calculate technical indicators for the given price data"""
        # RSI
        rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
        df['rsi'] = rsi.rsi()

        # MACD
        macd = MACD(
            close=df['close'],
            window_slow=self.macd_slow,
            window_fast=self.macd_fast,
            window_sign=self.macd_signal
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        # Bollinger Bands
        bollinger = BollingerBands(close=df['close'])
        df['bb_high'] = bollinger.bollinger_hband()
        df['bb_low'] = bollinger.bollinger_lband()
        df['bb_mid'] = bollinger.bollinger_mavg()

        return df

    def generate_signals(self, df):
        """Generate trading signals based on technical indicators"""
        signals = pd.DataFrame(index=df.index)
        signals['signal'] = 0.0

        # RSI signals
        signals.loc[df['rsi'] < self.rsi_oversold, 'signal'] += 0.3
        signals.loc[df['rsi'] > self.rsi_overbought, 'signal'] -= 0.3

        # MACD signals
        signals.loc[df['macd'] > df['macd_signal'], 'signal'] += 0.3
        signals.loc[df['macd'] < df['macd_signal'], 'signal'] -= 0.3

        # Bollinger Bands signals
        signals.loc[df['close'] < df['bb_low'], 'signal'] += 0.4
        signals.loc[df['close'] > df['bb_high'], 'signal'] -= 0.4

        # Normalize signals to range [-1, 1]
        signals['signal'] = signals['signal'].clip(-1, 1)

        return signals

    def get_buy_recommendation(self, df):
        """Get a buy recommendation based on technical analysis"""
        df = self.calculate_indicators(df)
        signals = self.generate_signals(df)
        
        # Get the latest signal
        latest_signal = signals['signal'].iloc[-1]
        
        # Calculate confidence score (0 to 1)
        confidence = (latest_signal + 1) / 2
        
        recommendation = {
            'confidence': confidence,
            'signal': latest_signal,
            'indicators': {
                'rsi': df['rsi'].iloc[-1],
                'macd': df['macd'].iloc[-1],
                'macd_signal': df['macd_signal'].iloc[-1],
                'bb_position': (df['close'].iloc[-1] - df['bb_low'].iloc[-1]) / 
                             (df['bb_high'].iloc[-1] - df['bb_low'].iloc[-1])
            }
        }
        
        return recommendation 
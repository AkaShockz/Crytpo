import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'YOUR_NEWS_API_KEY')
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', 'YOUR_TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', 'YOUR_TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', 'YOUR_TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET', 'YOUR_TWITTER_ACCESS_TOKEN_SECRET')

# Trading Parameters
SYMBOLS = [
    'BTCUSDT',  # Bitcoin
    'ETHUSDT',  # Ethereum
    'XRPUSDT',  # Ripple
    'HBARUSDT', # Hedera
    'BNBUSDT',  # Binance Coin
    'ADAUSDT',  # Cardano
    'DOGEUSDT', # Dogecoin
    'SOLUSDT',  # Solana
    'DOTUSDT',  # Polkadot
    'MATICUSDT' # Polygon
]

TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']
SIGNAL_THRESHOLD = 0.7  # Minimum confidence score for buy signals

# Technical Analysis Parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# News Analysis Parameters
NEWS_LOOKBACK_HOURS = 24
SENTIMENT_THRESHOLD = 0.6  # Minimum sentiment score to consider news positive
SIGNAL_INTERVAL = 300  # 5 minutes in seconds

# Risk Management
MAX_POSITION_SIZE = 0.1  # Maximum 10% of portfolio per position
STOP_LOSS_PERCENTAGE = 0.05  # 5% stop loss
TAKE_PROFIT_PERCENTAGE = 0.15  # 15% take profit

# Database
DATABASE_FILE = 'trading_signals.db' 
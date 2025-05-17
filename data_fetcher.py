import pandas as pd
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import config
import requests
import time
import json
from functools import lru_cache

class DataFetcher:
    def __init__(self):
        # Initialize clients with error handling
        self.news_client = None
        self.twitter_client = None
        
        # CoinGecko API base URL
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.last_request_time = 0
        self.min_request_interval = 6.0  # Increased to 6 seconds between requests
        self.price_cache = {}
        self.price_cache_time = {}
        self.cache_duration = 60  # Cache prices for 60 seconds
        
        # Try to initialize News API client
        try:
            if config.NEWS_API_KEY != "YOUR_NEWS_API_KEY":
                self.news_client = NewsApiClient(api_key=config.NEWS_API_KEY)
                print("Successfully connected to News API")
            else:
                print("News API key not configured. Continuing without news data.")
        except Exception as e:
            print(f"Warning: Could not connect to News API: {str(e)}")
            print("The application will continue with limited functionality")
        
        # Try to initialize Twitter client
        try:
            import tweepy
            auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.TWITTER_API_SECRET)
            auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET)
            self.twitter_client = tweepy.API(auth)
            print("Successfully connected to Twitter API")
        except Exception as e:
            print("Twitter integration is not available. Continuing without Twitter data.")

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            print(f"Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _get_coin_id(self, symbol):
        """Convert trading symbol to CoinGecko coin ID"""
        symbol_map = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum',
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'DOGEUSDT': 'dogecoin'
        }
        return symbol_map.get(symbol, symbol.lower().replace('usdt', ''))

    @lru_cache(maxsize=32)
    def get_historical_klines(self, symbol, interval, lookback_days=30):
        """Fetch historical price data from CoinGecko with caching"""
        try:
            self._rate_limit()
            coin_id = self._get_coin_id(symbol)
            end_time = int(time.time())
            start_time = end_time - (lookback_days * 24 * 60 * 60)
            
            url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': start_time,
                'to': end_time
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 429:
                print("Rate limit hit. Waiting 60 seconds before retrying...")
                time.sleep(60)
                return self.get_historical_klines(symbol, interval, lookback_days)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Add other required columns
            df['open'] = df['close'].shift(1)
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0  # CoinGecko doesn't provide volume data in this endpoint
            
            # Forward fill missing values
            df.ffill(inplace=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {str(e)}")
            raise

    def get_crypto_news(self, symbol):
        """Fetch recent news articles about a cryptocurrency"""
        if not self.news_client:
            print("News API is not available")
            return []
            
        try:
            query = symbol.replace('USDT', '')  # Remove USDT from symbol
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=config.NEWS_LOOKBACK_HOURS)
            
            news = self.news_client.get_everything(
                q=query,
                from_param=start_date.strftime('%Y-%m-%d'),
                to=end_date.strftime('%Y-%m-%d'),
                language='en',
                sort_by='relevancy'
            )
            
            return news['articles']
        except Exception as e:
            print(f"Error fetching news for {symbol}: {str(e)}")
            return []

    def get_twitter_sentiment(self, symbol):
        """Fetch recent tweets about a cryptocurrency"""
        if not self.twitter_client:
            return []
            
        try:
            query = symbol.replace('USDT', '')  # Remove USDT from symbol
            tweets = self.twitter_client.search_tweets(
                q=query,
                lang='en',
                count=100,
                tweet_mode='extended'
            )
            return [tweet.full_text for tweet in tweets]
        except Exception as e:
            print(f"Error fetching tweets: {str(e)}")
            return []

    def get_current_price(self, symbol):
        """Get current price of a cryptocurrency with caching"""
        try:
            current_time = time.time()
            
            # Check cache first
            if symbol in self.price_cache:
                cache_age = current_time - self.price_cache_time.get(symbol, 0)
                if cache_age < self.cache_duration:
                    return self.price_cache[symbol]
            
            self._rate_limit()
            coin_id = self._get_coin_id(symbol)
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 429:
                print("Rate limit hit. Waiting 60 seconds before retrying...")
                time.sleep(60)
                return self.get_current_price(symbol)
            response.raise_for_status()
            data = response.json()
            
            price = float(data[coin_id]['usd'])
            
            # Update cache
            self.price_cache[symbol] = price
            self.price_cache_time[symbol] = current_time
            
            return price
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {str(e)}")
            raise 
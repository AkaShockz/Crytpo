import time
import schedule
from data_fetcher import DataFetcher
from technical_analysis import TechnicalAnalyzer
from sentiment_analysis import SentimentAnalyzer
from signal_generator import SignalGenerator
import config
import sys

class CryptoTradingSignals:
    def __init__(self):
        print("Initializing Crypto Trading Signals...")
        self.data_fetcher = DataFetcher()
        self.technical_analyzer = TechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.signal_generator = SignalGenerator()
        print("Initialization complete!")

    def analyze_symbol(self, symbol):
        """Analyze a single cryptocurrency symbol"""
        try:
            print(f"\nAnalyzing {symbol}...")
            
            # Get current price
            try:
                current_price = self.data_fetcher.get_current_price(symbol)
                print(f"Current price: ${current_price:.2f}")
            except Exception as e:
                print(f"Could not get current price for {symbol}: {str(e)}")
                return
            
            # Get historical data
            try:
                df = self.data_fetcher.get_historical_klines(symbol, '1h', lookback_days=30)
                print("Historical data retrieved successfully")
            except Exception as e:
                print(f"Could not get historical data for {symbol}: {str(e)}")
                return
            
            # Get news and tweets
            news = self.data_fetcher.get_crypto_news(symbol)
            tweets = self.data_fetcher.get_twitter_sentiment(symbol)
            print(f"Retrieved {len(news)} news articles and {len(tweets)} tweets")
            
            # Generate technical analysis
            technical_recommendation = self.technical_analyzer.get_buy_recommendation(df)
            
            # Generate sentiment analysis
            sentiment_recommendation = self.sentiment_analyzer.get_sentiment_recommendation(news, tweets)
            
            # Generate final signal
            signal = self.signal_generator.generate_signal(
                technical_recommendation,
                sentiment_recommendation,
                current_price
            )
            
            # Print signal if it's a buy recommendation
            if signal['recommendation'] == 'BUY':
                message = self.signal_generator.format_signal_message(signal, symbol)
                print(message)
            else:
                print(f"No buy signal for {symbol} at this time")
                
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")

    def run_analysis(self):
        """Run analysis for all configured symbols"""
        print(f"\nRunning analysis at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for symbol in config.SYMBOLS:
            self.analyze_symbol(symbol)

def main():
    try:
        app = CryptoTradingSignals()
        
        # Run initial analysis
        app.run_analysis()
        
        # Schedule regular analysis
        schedule.every(1).hours.do(app.run_analysis)
        
        print("\nCrypto Trading Signals application started...")
        print("Press Ctrl+C to exit")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
# Crypto Trading Signals

A real-time cryptocurrency trading signals application that analyzes market data, technical indicators, and news sentiment to provide buy recommendations.

## Features

- Real-time cryptocurrency price monitoring
- Technical analysis using multiple indicators
- News and social media sentiment analysis
- Automated buy signals generation
- Historical performance tracking

## Setup

1. Install Python 3.8 or higher
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   NEWS_API_KEY=your_newsapi_key
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
   ```

## Usage

Run the main application:
```
python main.py
```

## Components

- `main.py`: Main application entry point
- `data_fetcher.py`: Handles fetching price data and news
- `technical_analysis.py`: Implements technical indicators
- `sentiment_analysis.py`: Analyzes news and social media sentiment
- `signal_generator.py`: Generates buy signals based on analysis
- `config.py`: Configuration and constants 
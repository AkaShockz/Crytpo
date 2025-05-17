from textblob import TextBlob
import numpy as np
from datetime import datetime, timedelta
import config

class SentimentAnalyzer:
    def __init__(self):
        self.sentiment_threshold = config.SENTIMENT_THRESHOLD

    def analyze_text(self, text):
        """Analyze sentiment of a single text"""
        analysis = TextBlob(text)
        # Convert polarity (-1 to 1) to sentiment score (0 to 1)
        sentiment_score = (analysis.sentiment.polarity + 1) / 2
        return sentiment_score

    def analyze_news(self, news_articles):
        """Analyze sentiment of news articles"""
        if not news_articles:
            return 0.5  # Neutral sentiment if no news

        sentiments = []
        for article in news_articles:
            # Combine title and description for analysis
            text = f"{article['title']} {article['description']}"
            sentiment = self.analyze_text(text)
            sentiments.append(sentiment)

        # Weight more recent articles more heavily
        weights = np.linspace(0.5, 1.0, len(sentiments))
        weighted_sentiment = np.average(sentiments, weights=weights)
        
        return weighted_sentiment

    def analyze_tweets(self, tweets):
        """Analyze sentiment of tweets"""
        if not tweets:
            return 0.5  # Neutral sentiment if no tweets

        sentiments = []
        for tweet in tweets:
            sentiment = self.analyze_text(tweet)
            sentiments.append(sentiment)

        # Weight more recent tweets more heavily
        weights = np.linspace(0.5, 1.0, len(sentiments))
        weighted_sentiment = np.average(sentiments, weights=weights)
        
        return weighted_sentiment

    def get_sentiment_recommendation(self, news_articles, tweets):
        """Get a sentiment-based recommendation"""
        news_sentiment = self.analyze_news(news_articles)
        
        # If there are no tweets, use only news sentiment
        if not tweets:
            tweet_sentiment = 0.5  # Neutral sentiment
            combined_sentiment = news_sentiment  # Use only news sentiment
        else:
            tweet_sentiment = self.analyze_tweets(tweets)
            # Combine news and tweet sentiment with equal weights
            combined_sentiment = (news_sentiment + tweet_sentiment) / 2
        
        recommendation = {
            'confidence': combined_sentiment,
            'sentiment': combined_sentiment,
            'components': {
                'news_sentiment': news_sentiment,
                'tweet_sentiment': tweet_sentiment
            }
        }
        
        return recommendation 
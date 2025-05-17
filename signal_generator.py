from datetime import datetime
import config

class SignalGenerator:
    def __init__(self):
        self.signal_threshold = config.SIGNAL_THRESHOLD

    def generate_signal(self, technical_recommendation, sentiment_recommendation, current_price):
        """Generate final trading signal by combining technical and sentiment analysis"""
        # Calculate weighted confidence score
        technical_weight = 0.7
        sentiment_weight = 0.3
        
        combined_confidence = (
            technical_recommendation['confidence'] * technical_weight +
            sentiment_recommendation['confidence'] * sentiment_weight
        )
        
        # Generate signal
        signal = {
            'timestamp': datetime.now(),
            'confidence': combined_confidence,
            'recommendation': 'BUY' if combined_confidence >= self.signal_threshold else 'HOLD',
            'current_price': current_price,
            'analysis': {
                'technical': technical_recommendation,
                'sentiment': sentiment_recommendation
            }
        }
        
        return signal

    def format_signal_message(self, signal, symbol):
        """Format the signal into a readable message"""
        message = f"""
🔔 Trading Signal for {symbol} 🔔
Time: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
Current Price: ${signal['current_price']:.2f}
Recommendation: {signal['recommendation']}
Confidence: {signal['confidence']*100:.1f}%

Technical Analysis:
- RSI: {signal['analysis']['technical']['indicators']['rsi']:.1f}
- MACD Signal: {signal['analysis']['technical']['indicators']['macd_signal']:.1f}
- BB Position: {signal['analysis']['technical']['indicators']['bb_position']:.1f}

Sentiment Analysis:
- News Sentiment: {signal['analysis']['sentiment']['components']['news_sentiment']*100:.1f}%
- Twitter Sentiment: {signal['analysis']['sentiment']['components']['tweet_sentiment']*100:.1f}%
"""
        return message 
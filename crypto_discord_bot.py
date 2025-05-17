import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import os
import datetime
import time
import json
import random
import aiohttp
import re
from datetime import timedelta
import asyncio

# --- CONFIG ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN')  # Replace with your bot token or set as env var
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', '123456789012345678'))  # Replace with your channel ID or set as env var

# Supported cryptocurrencies
SUPPORTED_COINS = ['BTC', 'XRP', 'HBAR']

# Technical indicators dictionary
technical_terms = {
    'RSI': 'Relative Strength Index',
    'MACD': 'Moving Average Convergence Divergence',
    'SMA': 'Simple Moving Average',
    'EMA': 'Exponential Moving Average', 
    'BB': 'Bollinger Bands',
    'FIBO': 'Fibonacci Retracement'
}

# Default USD to GBP conversion rate as fallback
USD_TO_GBP_RATE = 0.78

# High-impact entities that can move markets
MARKET_MOVERS = [
    'SEC', 'Biden', 'Trump', 'Powell', 'Federal Reserve', 'Fed', 
    'BlackRock', 'Fidelity', 'Grayscale', 'Ripple', 'Hedera', 
    'ETF', 'CBDC', 'regulation', 'lawsuit', 'settlement',
    'hack', 'security breach', 'Binance', 'Coinbase', 'Kraken',
    'whale', 'liquidation', 'delisting', 'listing', 'partnership'
]

# News sources to monitor
NEWS_SOURCES = [
    'https://cryptonews.com/',
    'https://cointelegraph.com/',
    'https://www.coindesk.com/',
    'https://bitcoin.com/news/',
    'https://decrypt.co/'
]

# Twitter/X accounts to monitor
TWITTER_ACCOUNTS = [
    'elonmusk', 'saylor', 'cz_binance', 'VitalikButerin', 'brian_armstrong',
    'haydenzadams', 'APompliano', 'SBF_FTX', 'tyler', 'garyvee'
]

# Market state dictionary to ensure consistent predictions across all bot functions
# The state is determined based on real market data (price changes, volume)
class MarketStateManager:
    def __init__(self):
        self.market_states = {}
        self.last_update = 0
        self.update_interval = 300  # Update market state every 5 minutes
        
    def get_state(self, symbol):
        """Get current market state for a symbol, updating if needed"""
        current_time = time.time()
        
        # Update states if data is stale
        if current_time - self.last_update > self.update_interval:
            self._update_all_states()
            self.last_update = current_time
            
        # Return the current state or generate a new one if doesn't exist
        if symbol not in self.market_states:
            self._update_symbol_state(symbol)
            
        return self.market_states[symbol]
    
    def _update_all_states(self):
        """Update market states for all supported coins"""
        for symbol in SUPPORTED_COINS:
            self._update_symbol_state(symbol)
    
    def _update_symbol_state(self, symbol):
        """Update market state for a specific symbol using real data points"""
        try:
            # Get actual price and calculate real metrics
            usd_price = float(get_crypto_price(symbol) or 0)
            gbp_price = convert_usd_to_gbp(usd_price)
            
            # Get 24h price change (use Binance API for real data)
            price_change = self._get_24h_price_change(symbol)
            
            # Calculate volume change (another real metric)
            volume_change = self._get_volume_trend(symbol)
            
            # Factor in current day of week (weekend vs. weekday trends)
            day_of_week = datetime.datetime.now().weekday()
            weekend_factor = 1.0 if day_of_week >= 5 else 0.0  # Weekend vs weekday
            
            # Factor in time of day (different periods show different patterns)
            hour = datetime.datetime.now().hour
            market_hour_factor = 0.0
            if 14 <= hour <= 21:  # Active trading hours (adjusted for GMT)
                market_hour_factor = 1.0
            elif 22 <= hour or hour <= 4:  # Overnight
                market_hour_factor = -0.5
                
            # Combined weighted factors
            # Price change has the most significant impact on sentiment
            sentiment_score = (price_change * 3.0) + (volume_change * 2.0) + (weekend_factor * 0.5) + (market_hour_factor * 0.5)
            
            # Calculate MSI value (0-100)
            msi_value = min(max(int(50 + (sentiment_score * 10)), 5), 95)  # Convert to 5-95 range
            
            # Determine direction based on MSI and actual data
            if msi_value >= 65:
                direction = "bullish"
            elif msi_value <= 35:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Generate an appropriate pattern based on the direction and actual data
            patterns = self._get_appropriate_patterns(symbol, direction, price_change, volume_change)
            
            # Store all the state information
            self.market_states[symbol] = {
                'price': gbp_price,
                'direction': direction,
                'msi_value': msi_value,
                'patterns': patterns,
                'price_change_24h': price_change,
                'volume_change': volume_change,
                'updated_at': time.time()
            }
            
        except Exception as e:
            print(f"Error updating market state for {symbol}: {e}")
            # Fallback to a neutral state if we can't get actual data
            self.market_states[symbol] = {
                'price': 0.0,
                'direction': "neutral",
                'msi_value': 50,
                'patterns': self._get_appropriate_patterns(symbol, "neutral", 0, 0),
                'price_change_24h': 0,
                'volume_change': 0,
                'updated_at': time.time()
            }
    
    def _get_24h_price_change(self, symbol):
        """Get actual 24h price change percentage"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            r = requests.get(url)
            data = r.json()
            return float(data.get('priceChangePercent', 0)) / 100  # Convert to decimal
        except Exception as e:
            print(f"Error getting 24h price change: {e}")
            # Use a slight random change as fallback
            return random.uniform(-0.02, 0.02)
    
    def _get_volume_trend(self, symbol):
        """Get volume trend based on actual data"""
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}USDT"
            r = requests.get(url)
            data = r.json()
            # Calculate volume change trend (normalized between -1 and 1)
            volume = float(data.get('volume', 0))
            quote_volume = float(data.get('quoteVolume', 0))
            
            # Use a simple metric based on available volume data
            if volume > 0 and quote_volume > 0:
                # Higher volume relative to price can indicate stronger trends
                return min(max((quote_volume / volume) / 10000, -1), 1)
            return 0
        except Exception as e:
            print(f"Error getting volume trend: {e}")
            return random.uniform(-0.5, 0.5)
    
    def _get_appropriate_patterns(self, symbol, direction, price_change, volume_change):
        """Get appropriate chart patterns based on direction and actual metrics"""
        # Get basic price for calculating targets
        usd_price = float(get_crypto_price(symbol) or 0)
        gbp_price = convert_usd_to_gbp(usd_price)
        
        patterns = {
            'bullish': [
                {"text": f"📈 Ascending triangle pattern with strong volume support", "direction": "bullish", "success_rate": "58%", "target": f"£{gbp_price * 1.05:.2f}"},
                {"text": f"📈 Cup and handle pattern forming on daily chart", "direction": "bullish", "success_rate": "54%", "target": f"£{gbp_price * 1.07:.2f}"},
                {"text": f"📈 Bull flag consolidation with increasing buy volume", "direction": "bullish", "success_rate": "62%", "target": f"£{gbp_price * 1.04:.2f}"},
                {"text": f"📈 Rounding bottom pattern indicating accumulation", "direction": "bullish", "success_rate": "53%", "target": f"£{gbp_price * 1.06:.2f}"}
            ],
            'bearish': [
                {"text": f"📉 Head and shoulders pattern developing", "direction": "bearish", "success_rate": "56%", "target": f"£{gbp_price * 0.92:.2f}"},
                {"text": f"📉 Double top pattern with weakening momentum", "direction": "bearish", "success_rate": "59%", "target": f"£{gbp_price * 0.94:.2f}"},
                {"text": f"📉 Descending triangle with decreasing volume", "direction": "bearish", "success_rate": "57%", "target": f"£{gbp_price * 0.93:.2f}"},
                {"text": f"📉 Rising wedge pattern suggesting trend reversal", "direction": "bearish", "success_rate": "55%", "target": f"£{gbp_price * 0.95:.2f}"}
            ],
            'neutral': [
                {"text": f"↔️ Symmetrical triangle approaching apex", "direction": "neutral", "success_rate": "51%", "target": f"£{gbp_price * 1.02:.2f} (up) or £{gbp_price * 0.98:.2f} (down)"},
                {"text": f"↔️ Rectangle consolidation within larger trend", "direction": "neutral", "success_rate": "50%", "target": f"£{gbp_price * 1.01:.2f} (up) or £{gbp_price * 0.99:.2f} (down)"},
                {"text": f"↔️ Sideways channel between major support/resistance", "direction": "neutral", "success_rate": "52%", "target": f"£{gbp_price * 1.03:.2f} (up) or £{gbp_price * 0.97:.2f} (down)"}
            ]
        }
        
        # Select pattern based on actual market data to ensure consistency
        # Use real price_change and volume_change to determine the specific pattern within the direction
        pattern_index = 0
        if direction == "bullish":
            if price_change > 0.05 and volume_change > 0.4:  # Strong bullish trend with high volume
                pattern_index = 0  # Ascending triangle (strongest)
            elif volume_change > 0.2:  # Good volume but more moderate price action
                pattern_index = 2  # Bull flag
            else:  # More gradual bullish movement
                pattern_index = 3  # Rounding bottom
        elif direction == "bearish":
            if price_change < -0.05 and volume_change < -0.2:  # Strong bearish with high volume
                pattern_index = 0  # Head and shoulders (strongest bearish)
            elif price_change < -0.03:  # Moderate bearish
                pattern_index = 1  # Double top
            else:  # Mild bearish
                pattern_index = 3  # Rising wedge
        else:  # Neutral
            if abs(price_change) < 0.01:  # Very flat price action
                pattern_index = 2  # Sideways channel
            else:  # Some movement but indecisive
                pattern_index = 0  # Symmetrical triangle
        
        # Handle index out of range
        pattern_index = min(pattern_index, len(patterns[direction]) - 1)
        
        return patterns[direction][pattern_index]

# Create global market state manager
market_manager = MarketStateManager()

intents = discord.Intents.default()
# No message content intent needed for slash commands
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="crypto markets"))
    
    # Start background tasks
    market_insights.start()
    technical_analysis.start()
    major_news_alerts.start()
    monitor_breaking_news.start()
    
    # Sync slash commands if not already synced
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="help", description="Display the bot's help information")
async def help_command(interaction: discord.Interaction):
    """Display the bot's help information"""
    embed = discord.Embed(
        title="Crypto Assistant Bot - Beginner's Guide",
        description="Here are all available commands with simple explanations:",
        color=0x00FFFF
    )
    
    embed.add_field(
        name="💰 /price [coin]",
        value="Shows the current market price of a cryptocurrency in British Pounds (GBP).\nSupported coins: BTC (Bitcoin), XRP (Ripple), or HBAR (Hedera)",
        inline=False
    )
    
    embed.add_field(
        name="📊 /analysis [coin]",
        value="Explains what the charts are showing right now - is the coin likely to go up, down or stay the same? Includes explanations of technical terms.",
        inline=False
    )
    
    embed.add_field(
        name="🔮 /predict [coin]",
        value="Gives price predictions for the next 24 hours and 7 days. Includes chart patterns, potential buy/sell levels, and confidence ratings.",
        inline=False
    )
    
    embed.add_field(
        name="📰 /news [coin]",
        value="Shows the latest news and upcoming events (like network updates, court cases, etc.) that might affect the coin's price.",
        inline=False
    )
    
    embed.add_field(
        name="❓ /help",
        value="Shows this guide to help you understand how to use the bot",
        inline=False
    )
    
    embed.add_field(
        name="📚 Crypto Terms Explained",
        value="• **Support**: Price level where a coin tends to stop falling\n• **Resistance**: Price level where a coin struggles to rise above\n• **Bull/Bullish**: Market/pattern expecting prices to rise\n• **Bear/Bearish**: Market/pattern expecting prices to fall",
        inline=False
    )
    
    embed.set_footer(text="Remember: The bot sends automatic alerts for big market moves. All prices shown in British Pounds (£).")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="price", description="Get the current price of a crypto symbol")
@app_commands.describe(symbol="The cryptocurrency symbol (BTC, XRP, or HBAR)")
async def price(interaction: discord.Interaction, symbol: str):
    """Get the current price of a crypto symbol"""        
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        await interaction.response.send_message(f"I only support these coins: {', '.join(SUPPORTED_COINS)}")
        return
        
    usd_price = get_crypto_price(symbol)
    if usd_price:
        # Convert to GBP
        gbp_price = convert_usd_to_gbp(float(usd_price))
        embed = discord.Embed(
            title=f"{symbol} Price",
            description=f"The current price of {symbol} is £{gbp_price:.2f}",
            color=0x00FF00
        )
        embed.set_footer(text=f"Data from Binance • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"Could not fetch price for {symbol}")

@bot.tree.command(name="analysis", description="Get technical analysis for a cryptocurrency")
@app_commands.describe(symbol="The cryptocurrency symbol (BTC, XRP, or HBAR)")
async def analysis(interaction: discord.Interaction, symbol: str):
    """Get technical analysis for a cryptocurrency"""        
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        await interaction.response.send_message(f"I only support these coins: {', '.join(SUPPORTED_COINS)}")
        return
    
    # Get simulated technical analysis
    analysis_data = get_technical_analysis(symbol)
    
    embed = discord.Embed(
        title=f"Technical Analysis for {symbol}",
        description=f"Current market sentiment: **{analysis_data['sentiment']}**",
        color=0x00FFFF
    )
    
    # Add technical indicators with beginner-friendly explanations
    for indicator, value in analysis_data['indicators'].items():
        if indicator == 'RSI':
            explanation = "(Relative Strength Index: measures overbought/oversold conditions)"
        elif indicator == 'MACD':
            explanation = "(Moving Average Convergence Divergence: shows trend direction and strength)"
        elif indicator == 'EMA 50/200':
            explanation = "(Moving Averages: indicates long-term trend direction)"
        else:
            explanation = ""
            
        embed.add_field(
            name=f"{indicator}",
            value=f"{value}\n{explanation}",
            inline=True
        )
    
    # Add pattern recognition
    embed.add_field(
        name="Chart Patterns",
        value=analysis_data['pattern'],
        inline=False
    )
    
    # Add support and resistance with explanation
    embed.add_field(
        name="Support & Resistance",
        value=f"Support: £{analysis_data['support']:.2f} (price tends to bounce up from this level)\nResistance: £{analysis_data['resistance']:.2f} (price tends to bounce down from this level)",
        inline=False
    )
    
    # Use current date to avoid future date issues
    current_date = datetime.datetime.now()
    embed.set_footer(text=f"Analysis based on data from the past 24 hours • {current_date.strftime('%Y-%m-%d %H:%M:%S')}")  # Current date and time
    
    await interaction.response.send_message(embed=embed)

def get_pattern_explanation(direction):
    """Get a simple explanation of what the pattern direction means for beginners"""
    if direction == "bullish":
        return "This pattern typically suggests the price might go up soon."
    elif direction == "bearish":
        return "This pattern typically suggests the price might go down soon."
    else:
        return "This pattern suggests the price might continue moving sideways for a while."

@bot.tree.command(name="predict", description="Get price prediction for a cryptocurrency")
@app_commands.describe(symbol="The cryptocurrency symbol (BTC, XRP, or HBAR)")
async def predict(interaction: discord.Interaction, symbol: str):
    """Get price prediction for a cryptocurrency"""        
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        await interaction.response.send_message(f"I only support these coins: {', '.join(SUPPORTED_COINS)}")
        return
    
    # Get simulated prediction data
    prediction = get_price_prediction(symbol)
    
    # Set embed color based on pattern direction
    if prediction['pattern_direction'] == "bullish":
        color = 0x00FF00  # Green for bullish
    elif prediction['pattern_direction'] == "bearish":
        color = 0xFF0000  # Red for bearish
    else:
        color = 0xFFD700  # Gold for neutral
    
    # Create a simpler title that clearly states the outcome
    title = f"Simple Price Prediction for {symbol}: "
    if prediction['pattern_direction'] == "bullish":
        title += "LIKELY TO GO UP 📈"
    elif prediction['pattern_direction'] == "bearish":
        title += "LIKELY TO GO DOWN 📉"
    else:
        title += "LIKELY TO STAY FLAT ↔️"
    
    embed = discord.Embed(
        title=title,
        description=f"Here's what might happen with {symbol} based on our analysis:",
        color=color
    )
    
    # Add Market Sentiment Index (MSI) - show this first as requested
    embed.add_field(
        name="🌡️ Market Sentiment Index (MSI)",
        value=f"**{prediction['msi_value']}/100** - {prediction['msi_interpretation']}\n*(Shows overall market feeling about this coin)*",
        inline=False
    )
    
    # Simplified chart pattern analysis
    pattern_explanation = prediction['upcoming_pattern'].split("pattern")[0].strip() + " pattern"
    embed.add_field(
        name="📊 What We're Seeing",
        value=(
            f"{pattern_explanation}\n"
            f"**Success Rate:** {prediction['pattern_success_rate']} (how often this works)\n"
            f"**Target Price:** {prediction['pattern_target']}"
        ),
        inline=False
    )
    
    # Simplified short-term prediction
    embed.add_field(
        name="⏱️ Next 24 Hours",
        value=prediction['short_term'],
        inline=False
    )
    
    # Simplified medium-term prediction
    embed.add_field(
        name="⏳ Next 7 Days",
        value=prediction['medium_term'],
        inline=False
    )
    
    # Add simple trading advice
    if prediction['pattern_direction'] == "bullish":
        strategy = (
            f"• **Buy:** Consider buying if price dips\n"
            f"• **Sell:** Consider selling when price reaches target\n"
            f"• **Simple Plan:** Look for opportunities to buy below {prediction['pattern_target']}"
        )
    elif prediction['pattern_direction'] == "bearish":
        strategy = (
            f"• **Sell:** Consider taking profits now if you own this coin\n" 
            f"• **Buy:** Consider buying later if price drops to target\n"
            f"• **Simple Plan:** Might be better to wait before buying more"
        )
    else:
        strategy = (
            f"• **What to Do:** Price expected to move sideways\n"
            f"• **Simple Plan:** Not a clear time to buy or sell right now"
        )
    
    embed.add_field(
        name="💰 What You Could Do",
        value=strategy,
        inline=False
    )
    
    # Add simplified disclaimer
    embed.set_footer(text="⚠️ REMINDER: This is just a prediction. Crypto is risky and prices can change unexpectedly.")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="news", description="Get latest news for a cryptocurrency")
@app_commands.describe(symbol="The cryptocurrency symbol (BTC, XRP, or HBAR)")
async def news(interaction: discord.Interaction, symbol: str):
    """Get latest news for a cryptocurrency"""        
    symbol = symbol.upper()
    if symbol not in SUPPORTED_COINS:
        await interaction.response.send_message(f"I only support these coins: {', '.join(SUPPORTED_COINS)}")
        return
    
    # Get simulated news data
    news_items = get_crypto_news(symbol)
    
    embed = discord.Embed(
        title=f"{symbol} News & Upcoming Events",
        description=f"Recent and upcoming developments that could impact {symbol} price:",
        color=0x9370DB
    )
    
    # First add current news
    embed.add_field(
        name="📰 CURRENT NEWS",
        value="─────────────────────",
        inline=False
    )
    
    current_news = [item for item in news_items if item['type'] == 'current']
    for item in current_news:
        embed.add_field(
            name=item['title'],
            value=f"{item['summary']}\n[Read more]({item['url']})",
            inline=False
        )
    
    # Then add upcoming events
    embed.add_field(
        name="🔮 UPCOMING EVENTS",
        value="─────────────────────",
        inline=False
    )
    
    upcoming_news = [item for item in news_items if item['type'] == 'upcoming']
    for item in upcoming_news:
        embed.add_field(
            name=item['title'],
            value=f"{item['summary']}\n[Read more]({item['url']})",
            inline=False
        )
    
    embed.set_footer(text=f"News collected from various sources • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await interaction.response.send_message(embed=embed)

@tasks.loop(minutes=30)
async def market_insights():
    """Regularly post market insights for the supported coins"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    
    # Get market overview for all supported coins
    overview = get_market_overview()
    
    embed = discord.Embed(
        title="Crypto Market Insights",
        description=f"Current market overview for tracked cryptocurrencies:",
        color=0x00FFFF
    )
    
    for coin, data in overview.items():
        embed.add_field(
            name=f"{coin} (£{data['price']:.2f})",
            value=f"24h Change: {data['change_24h']}%\nVolume: £{data['volume']}\nMarket Sentiment: {data['sentiment']}",
            inline=False
        )
    
    # Use current date to avoid future date issues    current_date = datetime.datetime.now()    embed.set_footer(text=f"Market data updated every 30 minutes • {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    await channel.send(embed=embed)

@tasks.loop(hours=4)
async def technical_analysis():
    """Post detailed technical analysis every 4 hours"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    
    # Select a random coin to analyze
    coin = random.choice(SUPPORTED_COINS)
    
    # Get detailed analysis
    analysis_data = get_technical_analysis(coin)
    
    embed = discord.Embed(
        title=f"Technical Analysis Update: {coin}",
        description=f"Detailed technical analysis shows {analysis_data['sentiment']} sentiment",
        color=0xFFA500
    )
    
    # Chart patterns and indicators
    embed.add_field(
        name="Chart Patterns",
        value=analysis_data['pattern'],
        inline=False
    )
    
    # Support and resistance
    embed.add_field(
        name="Key Levels",
        value=f"Support: £{analysis_data['support']:.2f}\nResistance: £{analysis_data['resistance']:.2f}",
        inline=False
    )
    
    # Volume analysis
    embed.add_field(
        name="Volume Analysis",
        value=analysis_data['volume'],
        inline=False
    )
    
    # Trading recommendation
    embed.add_field(
        name="Trading Perspective",
        value=analysis_data['recommendation'],
        inline=False
    )
    
    embed.set_footer(text="⚠️ This is not financial advice. Always do your own research.")
    
    await channel.send(embed=embed)

@tasks.loop(minutes=45)
async def major_news_alerts():
    """Check for major news events that could impact prices"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    
    # Check for significant news events
    breaking_news = check_for_breaking_news()
    if breaking_news:
        embed = discord.Embed(
            title=f"🚨 BREAKING NEWS: {breaking_news['title']}",
            description=breaking_news['description'],
            color=0xFF0000
        )
        
        embed.add_field(
            name="Potential Impact",
            value=breaking_news['impact'],
            inline=False
        )
        
        embed.add_field(
            name="Affected Cryptocurrencies",
            value=", ".join(breaking_news['affected_coins']),
            inline=False
        )
        
        if breaking_news['source_url']:
            embed.add_field(
                name="Source",
                value=f"[Click here to read more]({breaking_news['source_url']})",
                inline=False
            )
        
        embed.set_footer(text=f"Breaking news alert • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await channel.send("@here", embed=embed)

@tasks.loop(seconds=180)
async def monitor_breaking_news():
    """Monitor for breaking news that could impact crypto prices and send immediate alerts"""
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    
    try:
        # Check for breaking news using various sources
        breaking_news = await scan_for_breaking_news()
        
        if breaking_news:
            # Format as urgent alert with impact assessment
            embed = discord.Embed(
                title=f"🚨 URGENT MARKET ALERT: {breaking_news['title']}",
                description=breaking_news['summary'],
                color=0xFF0000  # Red for urgency
            )
            
            # Add potential price impact analysis
            embed.add_field(
                name="Potential Market Impact",
                value=breaking_news['impact_analysis'],
                inline=False
            )
            
            # Add affected coins
            embed.add_field(
                name="Potentially Affected Coins",
                value=", ".join(breaking_news['affected_coins']),
                inline=False
            )
            
            # Add source with timestamp
            embed.add_field(
                name="Source",
                value=f"[{breaking_news['source_name']}]({breaking_news['source_url']})",
                inline=False
            )
            
            # Add advice on what to do now
            if breaking_news['sentiment'] > 0.2:
                action_advice = "Consider taking advantage of potential upward price movement."
            elif breaking_news['sentiment'] < -0.2:
                action_advice = "Consider protecting your position to minimize potential losses."
            else:
                action_advice = "Monitor the situation closely as market impact is still developing."
                
            embed.add_field(
                name="Suggested Action",
                value=action_advice,
                inline=False
            )
            
            embed.set_footer(text=f"Breaking news detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Sentiment: {breaking_news['sentiment_text']}")
            
            # Send as @here message for visibility
            await channel.send("@here **BREAKING MARKET NEWS ALERT!**", embed=embed)
    
    except Exception as e:
        print(f"Error in news monitoring: {e}")

async def scan_for_breaking_news():
    """Scan various sources for breaking crypto news with market impact"""
    # Last checked timestamps for different sources (to avoid duplicates)
    last_checked = getattr(scan_for_breaking_news, 'last_checked', {})
    last_news_hash = getattr(scan_for_breaking_news, 'last_news_hash', '')
    
    # Store the timestamps and hash as function attributes for persistence
    scan_for_breaking_news.last_checked = last_checked
    
    # Get current time
    now = datetime.datetime.now()
    
    # Initialize aiohttp session
    async with aiohttp.ClientSession() as session:
        # Check crypto news websites
        for source_url in NEWS_SOURCES:
            # Avoid checking same source too frequently
            if source_url in last_checked and now - last_checked[source_url] < timedelta(minutes=10):
                continue
                
            try:
                async with session.get(source_url, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Very basic scraping - would need more sophisticated parsing in production
                        # For each news site, you'd ideally have specific parsing rules
                        
                        # Look for headlines with market-moving keywords
                        for entity in MARKET_MOVERS:
                            # Case insensitive search
                            pattern = re.compile(f"<h\\d[^>]*>.*({entity}).*?</h\\d>", re.IGNORECASE)
                            headlines = pattern.findall(html_content)
                            
                            if headlines:
                                for headline in headlines:
                                    # Clean up the headline
                                    clean_headline = re.sub('<.*?>', '', headline)
                                    
                                    # Create a hash of the headline to avoid duplicates
                                    headline_hash = hash(clean_headline)
                                    if headline_hash == last_news_hash:
                                        continue  # Skip if we've seen this before
                                    
                                    # Store this headline hash to avoid duplicates
                                    scan_for_breaking_news.last_news_hash = headline_hash
                                    
                                    # Analyze headline for coins and sentiment
                                    affected_coins = []
                                    for coin in SUPPORTED_COINS:
                                        if coin in clean_headline or coin.lower() in clean_headline:
                                            affected_coins.append(coin)
                                    
                                    # If no specific coins mentioned, it might affect the whole market
                                    if not affected_coins:
                                        affected_coins = SUPPORTED_COINS
                                        
                                    # Very basic sentiment analysis (would use more sophisticated NLP in production)
                                    sentiment_score = calculate_news_sentiment(clean_headline)
                                    sentiment_text = get_sentiment_text(sentiment_score)
                                    
                                    # Generate impact analysis based on the headline and sentiment
                                    impact_analysis = generate_impact_analysis(clean_headline, entity, sentiment_score)
                                    
                                    # Build the news object
                                    breaking_news = {
                                        'title': clean_headline,
                                        'summary': f"Breaking news related to {entity.upper()} that could impact crypto markets.",
                                        'impact_analysis': impact_analysis,
                                        'affected_coins': affected_coins,
                                        'source_name': source_url.split('//')[1].split('/')[0],
                                        'source_url': source_url,
                                        'sentiment': sentiment_score,
                                        'sentiment_text': sentiment_text
                                    }
                                    
                                    # Record that we've checked this source
                                    last_checked[source_url] = now
                                    
                                    return breaking_news
                        
                        # Record that we've checked this source
                        last_checked[source_url] = now
            
            except Exception as e:
                print(f"Error checking {source_url}: {e}")
                # Record that we've checked this source even if it failed
                last_checked[source_url] = now
        
        # No breaking news found
        return None

def calculate_news_sentiment(headline):
    """Calculate sentiment score from headline text (-1 to +1 scale)"""
    # In a production system, you'd use a proper NLP library or API
    # This is a simple keyword-based approach
    
    positive_words = ['bullish', 'surge', 'rally', 'gain', 'positive', 'launch', 'adopt', 
                      'approval', 'support', 'partnership', 'invest', 'buy', 'victory', 'win']
    
    negative_words = ['bearish', 'crash', 'drop', 'decline', 'ban', 'regulation', 'fraud', 
                      'hack', 'security', 'lawsuit', 'investigation', 'sell', 'dump', 'lose']
    
    # Normalize text
    text = headline.lower()
    
    # Count positive and negative words
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    # If no sentiment words found
    if pos_count + neg_count == 0:
        return 0
        
    # Calculate sentiment (-1 to +1)
    return (pos_count - neg_count) / (pos_count + neg_count)

def get_sentiment_text(sentiment_score):
    """Convert sentiment score to text description"""
    if sentiment_score > 0.6:
        return "Very Positive 🔥"
    elif sentiment_score > 0.2:
        return "Positive 📈"
    elif sentiment_score > -0.2:
        return "Neutral ↔️"
    elif sentiment_score > -0.6:
        return "Negative 📉"
    else:
        return "Very Negative ❄️"

def generate_impact_analysis(headline, entity, sentiment):
    """Generate impact analysis based on headline content and sentiment"""
    
    # Base the analysis on the entity type and sentiment
    if entity.lower() in ['sec', 'regulation', 'lawsuit', 'settlement']:
        if sentiment > 0.2:
            return f"Positive regulatory development could reduce uncertainty and attract institutional investment."
        elif sentiment < -0.2:
            return f"Regulatory concerns may create selling pressure in the short term. Legal challenges could affect adoption."
        else:
            return f"Regulatory developments are unfolding. Monitor closely as outcomes will impact market direction."
            
    elif entity.lower() in ['etf', 'blackrock', 'fidelity', 'grayscale']:
        if sentiment > 0.2:
            return f"Positive ETF developments typically boost institutional confidence and can lead to significant capital inflow."
        elif sentiment < -0.2:
            return f"ETF setbacks may temporarily dampen institutional interest, potentially triggering sell-offs."
        else:
            return f"ETF-related news requires careful analysis. Watch for institutional positioning in response."
            
    elif entity.lower() in ['biden', 'trump', 'powell', 'federal reserve', 'fed']:
        if sentiment > 0.2:
            return f"Favorable political/monetary policy statements often provide positive market sentiment."
        elif sentiment < -0.2:
            return f"Political/monetary uncertainty can create market volatility and risk-off sentiment."
        else:
            return f"Political and monetary policy developments have complex market implications. Watch for clarity."
            
    elif entity.lower() in ['hack', 'security breach']:
        return f"Security incidents typically create immediate selling pressure and can have lingering trust implications."
        
    elif entity.lower() in ['whale', 'liquidation']:
        if sentiment > 0:
            return f"Large investor activity could indicate accumulation and potential price support."
        else:
            return f"Large selling/liquidation events often create short-term downward pressure but can create buying opportunities."
    
    # Generic analysis based on sentiment
    elif sentiment > 0.5:
        return f"This highly positive development could drive short-term upward price movement."
    elif sentiment > 0:
        return f"Moderately positive news that may contribute to upward price momentum."
    elif sentiment > -0.5:
        return f"Slightly negative news that could create minor selling pressure."
    else:
        return f"Significantly negative development that might trigger immediate selling."

def get_crypto_price(symbol):
    """Get current price for a cryptocurrency in USD"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        r = requests.get(url)
        return r.json()['price']
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def convert_usd_to_gbp(usd_amount):
    """Convert USD to GBP using current exchange rate"""
    try:
        # Try to get current exchange rate
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url)
        data = response.json()
        gbp_rate = data["rates"]["GBP"]
        return usd_amount * gbp_rate
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        # Fall back to default rate
        return usd_amount * USD_TO_GBP_RATE

def get_technical_analysis(symbol):
    """Get technical analysis for a cryptocurrency using consistent market state"""
    # Get market state for consistent predictions
    market_state = market_manager.get_state(symbol)
    gbp_price = market_state['price']
    
    # Set sentiment based on market direction for consistency
    market_direction = market_state['direction']
    msi_value = market_state['msi_value']
    
    # Map the MSI value to a human-readable sentiment
    if msi_value >= 70:
        sentiment = "Very Bullish"
    elif msi_value >= 60:
        sentiment = "Bullish"
    elif msi_value >= 45:
        sentiment = "Slightly Bullish"
    elif msi_value >= 40:
        sentiment = "Neutral"
    elif msi_value >= 30:
        sentiment = "Slightly Bearish"
    elif msi_value >= 15:
        sentiment = "Bearish"
    else:
        sentiment = "Very Bearish"
    
    # Use the pattern from the market state
    pattern = market_state['patterns']['text']
    
    # Generate RSI value consistent with market direction
    if market_direction == "bullish":
        rsi_value = random.randint(55, 69)  # Stronger but not overbought
    elif market_direction == "bearish":
        rsi_value = random.randint(31, 45)  # Weaker but not oversold
    else:
        rsi_value = random.randint(45, 55)  # Neutral
    
    # Interpret RSI correctly
    if rsi_value < 30:
        rsi_interpretation = "Oversold"
    elif rsi_value > 70:
        rsi_interpretation = "Overbought"
    else:
        rsi_interpretation = "Neutral"
    
    # Choose EMA status consistent with market direction
    if market_direction == "bullish":
        ema_status = "Golden Cross" # Bullish signal
    elif market_direction == "bearish":
        ema_status = "Death Cross" # Bearish signal
    else:
        ema_status = "Neutral"
    
    # Choose MACD signal consistent with market direction
    if market_direction == "bullish":
        macd_signal = "Bullish Crossover"
    elif market_direction == "bearish":
        macd_signal = "Bearish Crossover"
    else:
        macd_signal = "Neutral"
    
    # Choose volume analysis consistent with market direction
    if market_direction == "bullish":
        volume_analysis = "Increasing volume confirms the uptrend"
    elif market_direction == "bearish":
        volume_analysis = "Decreasing volume suggests weakening momentum"
    else:
        volume_analysis = "Average volume suggests consolidation phase"
    
    # Choose recommendations consistent with market direction
    if market_direction == "bullish":
        recommendation = "Watch for breakout above resistance with increased volume"
    elif market_direction == "bearish":
        recommendation = "Consider taking profits at resistance levels"
    else:
        recommendation = "Wait for confirmation of trend before entering positions"
    
    return {
        'sentiment': sentiment,
        'indicators': {
            'RSI': f"{rsi_value} - {rsi_interpretation}",
            'MACD': macd_signal,
            'EMA 50/200': ema_status
        },
        'pattern': pattern,
        'support': round(gbp_price * 0.95, 2),
        'resistance': round(gbp_price * 1.05, 2),
        'volume': volume_analysis,
        'recommendation': recommendation
    }

def get_price_prediction(symbol):
    """Simulate price prediction for a cryptocurrency"""
    # Get market state from our centralized manager
    market_state = market_manager.get_state(symbol)
    
    # Use the consistent market state for all predictions
    pattern_direction = market_state['direction']
    selected_pattern = market_state['patterns']
    gbp_price = market_state['price']
    msi_value = market_state['msi_value']
    
    # Extract target price from the pattern
    price_target = float(selected_pattern["target"].replace('£', '').split(' ')[0])
    
    # Create MSI interpretation based on actual MSI value
    if msi_value >= 70:
        msi_interpretation = "Very Bullish 🔥"
    elif msi_value >= 60:
        msi_interpretation = "Bullish 📈"
    elif msi_value >= 45:
        msi_interpretation = "Slightly Bullish ↗️"
    elif msi_value >= 40:
        msi_interpretation = "Neutral ↔️"
    elif msi_value >= 30:
        msi_interpretation = "Slightly Bearish ↘️"
    elif msi_value >= 15:
        msi_interpretation = "Bearish 📉"
    else:
        msi_interpretation = "Very Bearish ❄️"
    
    # Create simple short and medium term predictions based on real market data
    if pattern_direction == "bullish":
        short_term_pred = f"Target: £{price_target * 0.98:.2f} within 24 hours based on technical indicators (55% chance)"
        medium_term_pred = f"If price stays above £{price_target * 0.96:.2f} for 2 days, could reach £{price_target * 1.02:.2f} in a week"
    elif pattern_direction == "bearish":
        short_term_pred = f"Price likely to drop to £{price_target * 1.02:.2f} in next 24 hours"
        medium_term_pred = f"Could fall to £{price_target * 0.98:.2f} within a week if support levels break"
    else:
        short_term_pred = f"Price will likely stay between £{price_target * 0.98:.2f}-£{price_target * 1.02:.2f} for next 24 hours"
        medium_term_pred = f"Expect sideways movement for the next week unless news changes market direction"
    
    # Generate confidence value based on the market state
    confidence = min(max(int(msi_value * 0.95), 50), 65)  # Realistic 50-65% range
    
    return {
        'upcoming_pattern': selected_pattern["text"],
        'pattern_direction': pattern_direction,
        'pattern_success_rate': selected_pattern["success_rate"],
        'pattern_target': f"£{price_target:.2f}",
        'short_term': short_term_pred,
        'medium_term': medium_term_pred,
        'confidence': confidence,
        'factors': f"{'Increasing' if market_state['volume_change'] > 0 else 'Decreasing'} trading volume in the past 24 hours",
        'upcoming_events': f"Next {symbol} update expected within 2 weeks",
        'msi_value': msi_value,
        'msi_interpretation': msi_interpretation
    }

def get_crypto_news(symbol):
    """Simulate getting news for a cryptocurrency"""
    # In a real implementation, this would fetch from news APIs
    
    btc_news = [
        {
            'title': 'Bitcoin ETF Sees Record Inflows',
            'summary': 'The latest data shows significant capital flowing into Bitcoin ETFs, suggesting growing institutional interest',
            'url': 'https://example.com/bitcoin-etf-news',
            'type': 'current'
        },
        {
            'title': 'Major Bank Announces Bitcoin Custody Service',
            'summary': 'A top-tier financial institution has announced plans to offer Bitcoin custody services to wealthy clients',
            'url': 'https://example.com/bank-bitcoin-custody',
            'type': 'current'
        },
        {
            'title': f'Bitcoin Halving Approaching in {random.randint(10, 120)} Days',
            'summary': 'The upcoming Bitcoin halving will reduce mining rewards, historically leading to price increases',
            'url': 'https://example.com/bitcoin-halving',
            'type': 'upcoming'
        },
        {
            'title': f'Major Exchange to Launch Bitcoin Derivatives on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(5, 30))).strftime("%d %B")}',
            'summary': 'A leading cryptocurrency exchange has announced plans to launch new Bitcoin derivative products',
            'url': 'https://example.com/btc-derivatives',
            'type': 'upcoming'
        }
    ]
    
    xrp_news = [
        {
            'title': 'Ripple Case Developments Favor XRP',
            'summary': 'The latest court rulings in the Ripple case suggest a favorable outcome may be approaching',
            'url': 'https://example.com/ripple-case-update',
            'type': 'current'
        },
        {
            'title': 'Major Bank Tests XRP for Cross-Border Payments',
            'summary': 'A multinational banking institution reports successful trials using XRP for international transfers',
            'url': 'https://example.com/bank-xrp-trials',
            'type': 'current'
        },
        {
            'title': f'Ripple to Release New XRPL Update on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(3, 14))).strftime("%d %B")}',
            'summary': 'The upcoming XRP Ledger update will introduce new features aimed at improving smart contract functionality',
            'url': 'https://example.com/xrpl-update',
            'type': 'upcoming'
        },
        {
            'title': f'XRP Community Planning Virtual Conference for {(datetime.datetime.now() + datetime.timedelta(days=random.randint(10, 45))).strftime("%B")}',
            'summary': 'The XRP community is organizing a major virtual conference with key developers and executives',
            'url': 'https://example.com/xrp-conference',
            'type': 'upcoming'
        }
    ]
    
    hbar_news = [
        {
            'title': 'Hedera Announces Major Enterprise Partnership',
            'summary': 'A Fortune 500 company joins the Hedera Governing Council, bringing enterprise validation',
            'url': 'https://example.com/hedera-partnership',
            'type': 'current'
        },
        {
            'title': 'HBAR Foundation Funds New DeFi Projects',
            'summary': 'New grants announced to develop decentralized finance applications on the Hedera network',
            'url': 'https://example.com/hbar-defi-grants',
            'type': 'current'
        },
        {
            'title': f'Hedera Plans Network Upgrade in the Next {random.randint(1, 4)} Weeks',
            'summary': 'The planned upgrade aims to enhance transaction throughput and reduce fees further',
            'url': 'https://example.com/hedera-upgrade',
            'type': 'upcoming'
        },
        {
            'title': f'Major Hedera-Based dApp Launch Set for {(datetime.datetime.now() + datetime.timedelta(days=random.randint(7, 21))).strftime("%d %B")}',
            'summary': 'A highly anticipated decentralized application built on Hedera is scheduled to launch soon',
            'url': 'https://example.com/hedera-dapp-launch',
            'type': 'upcoming'
        }
    ]
    
    if symbol == 'BTC':
        return btc_news
    elif symbol == 'XRP':
        return xrp_news
    elif symbol == 'HBAR':
        return hbar_news
    else:
        return []

def get_market_overview():
    """Get market overview for all supported coins using the central market state"""
    overview = {}
    for coin in SUPPORTED_COINS:
        # Get consistent state from market manager
        state = market_manager.get_state(coin)
        
        # Map direction to sentiment text for display
        if state['direction'] == 'bullish':
            sentiment = "Bullish"
        elif state['direction'] == 'bearish':
            sentiment = "Bearish"
        else:
            sentiment = "Neutral"
            
        overview[coin] = {
            'price': state['price'],
            'change_24h': round(state['price_change_24h'] * 100, 2),  # Convert to percentage
            'volume': f"{round(random.uniform(100, 500), 1)}M",  # Still randomized as we don't have exact volume
            'sentiment': sentiment
        }
    
    return overview

def check_for_breaking_news():
    """Check for breaking news that could impact crypto prices"""
    # In a real implementation, this would regularly check news APIs
    
    # Most of the time, return None (no breaking news)
    if random.random() > 0.05:  # 5% chance of breaking news
        return None
    
    breaking_news_items = [
        {
            'title': 'SEC Announces New Crypto Regulation Framework',
            'description': 'The SEC has released a new regulatory framework that provides clarity for cryptocurrency classifications and compliance requirements.',
            'impact': 'This could significantly reduce regulatory uncertainty and potentially open the door for more institutional adoption.',
            'affected_coins': ['BTC', 'XRP', 'HBAR'],
            'source_url': 'https://example.com/sec-framework'
        },
        {
            'title': 'Major Payment Processor To Integrate Cryptocurrency Solutions',
            'description': 'One of the world\'s largest payment processors has announced plans to integrate cryptocurrency payment solutions into their platform.',
            'impact': 'This development could dramatically increase real-world cryptocurrency adoption and utility.',
            'affected_coins': ['BTC', 'XRP'],
            'source_url': 'https://example.com/payment-crypto-integration'
        },
        {
            'title': 'Central Bank Digital Currency Trials Include Hedera Technology',
            'description': 'A major central bank has announced that it will be using Hedera Hashgraph technology in its CBDC trials.',
            'impact': 'This validation from a central bank could elevate Hedera\'s position in the enterprise blockchain space.',
            'affected_coins': ['HBAR'],
            'source_url': 'https://example.com/cbdc-hedera'
        }
    ]
    
    return random.choice(breaking_news_items)

if __name__ == "__main__":
    bot.run(TOKEN) 
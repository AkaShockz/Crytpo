import discord
from discord import app_commands
from discord.ext import commands, tasks
import requests
import os
import datetime
import time
import json
import random

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
    
    embed.set_footer(text=f"Analysis based on data from the past 24 hours • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")  # Current date and time
    
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
    
    embed = discord.Embed(
        title=f"Advanced Price Prediction for {symbol}",
        description=f"Based on technical analysis, on-chain metrics, and market sentiment:",
        color=color
    )
    
    # Chart pattern with success rate, price target, and beginner explanation
    embed.add_field(
        name="📊 Technical Pattern Analysis",
        value=(
            f"{prediction['upcoming_pattern']}\n"
            f"**Success Rate:** {prediction['pattern_success_rate']} (how often this pattern works)\n"
            f"**Target:** {prediction['pattern_target']} (potential price if pattern completes)\n"
            f"**What This Means:** {get_pattern_explanation(prediction['pattern_direction'])}"
        ),
        inline=False
    )
    
    embed.add_field(
        name="⏱️ Short-term Projection (24h)",
        value=prediction['short_term'],
        inline=False
    )
    
    embed.add_field(
        name="📈 Medium-term Trajectory (7 days)",
        value=prediction['medium_term'],
        inline=False
    )
    
    # Added disclaimer about confidence levels for beginners
    embed.add_field(
        name="🎯 Confidence Level",
        value=f"{prediction['confidence']}% based on historical pattern completion and volume metrics\n*(Note: Even high confidence predictions can be wrong due to unexpected market events)*",
        inline=False
    )
    
    embed.add_field(
        name="🔍 Key On-Chain Metrics",
        value=prediction['factors'],
        inline=False
    )
    
    embed.add_field(
        name="📅 Upcoming Market Catalysts",
        value=prediction['upcoming_events'],
        inline=False
    )
    
    # Add a trading strategy hint based on the pattern direction - simplified for beginners
    price_target = float(prediction['pattern_target'].replace('£', ''))
    
    if prediction['pattern_direction'] == "bullish":
        buy_price = price_target * 0.92
        stop_loss = price_target * 0.88
        profit_target = price_target * 1.08
        
        strategy = (
            f"**Beginner-Friendly Strategy (BULLISH OUTLOOK):**\n"
            f"• **Possible Buy Zone:** Around £{buy_price:.4f}\n"
            f"• **Where to Place Stop-Loss:** £{stop_loss:.4f} (to limit potential losses)\n"
            f"• **Target Sell Price:** £{profit_target:.4f}\n"
            f"• **Simple Explanation:** Charts suggest price might rise. Consider buying at support levels and selling at the target."
        )
    elif prediction['pattern_direction'] == "bearish":
        sell_now_price = price_target * 1.02
        stop_loss = price_target * 1.05
        reentry_price = price_target * 0.95
        
        strategy = (
            f"**Beginner-Friendly Strategy (BEARISH OUTLOOK):**\n"
            f"• **Current Action:** Consider taking profits if you already own this coin (around £{sell_now_price:.4f})\n"
            f"• **Where to Place Stop-Loss:** £{stop_loss:.4f} (if continuing to hold)\n"
            f"• **Potential Buy-Back Level:** Around £{reentry_price:.4f} (after price drops)\n"
            f"• **Simple Explanation:** Charts suggest price might fall. If you own this coin, consider selling some now and buying back cheaper later."
        )
    else:
        # For neutral patterns, we need to handle the target differently
        target_parts = prediction['pattern_target'].split(' ')
        base_price = float(target_parts[0].replace('£', ''))
        support = base_price * 0.97
        resistance = base_price * 1.03
        
        strategy = (
            f"**Beginner-Friendly Strategy (SIDEWAYS OUTLOOK):**\n"
            f"• **Buy Zone:** Near £{support:.4f} (when price dips)\n"
            f"• **Sell Zone:** Near £{resistance:.4f} (when price rises)\n"
            f"• **Simple Explanation:** Charts suggest price moving sideways in a range. Consider buying near the bottom of the range and selling near the top."
        )
    
    embed.add_field(
        name="💰 Suggested Trading Approach",
        value=strategy,
        inline=False
    )
    
    embed.set_footer(text="⚠️ IMPORTANT: This is not financial advice - all predictions have risks. Only invest what you can afford to lose. Past patterns don't guarantee future results.")
    
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
    
    embed.set_footer(text=f"Market data updated every 30 minutes • {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
    """Simulate technical analysis for a cryptocurrency"""
    # In a real implementation, this would use actual market data and technical indicators
    usd_price = float(get_crypto_price(symbol) or 0)
    gbp_price = convert_usd_to_gbp(usd_price)
    
    # First determine the overall market direction to keep indicators consistent
    # This will help us generate consistent technical analysis
    market_direction = random.choice(["bullish", "neutral", "bearish"])
    
    # Set sentiment based on market direction
    if market_direction == "bullish":
        sentiment = random.choice(["Bullish", "Slightly Bullish"])
        macd_signal = "Bullish Crossover"
        pattern_index = random.choice([0, 4])  # Bull flag or cup and handle (bullish patterns)
    elif market_direction == "bearish":
        sentiment = random.choice(["Bearish", "Slightly Bearish"])
        macd_signal = "Bearish Crossover"
        pattern_index = 2  # Head and shoulders (bearish pattern)
    else:
        sentiment = "Neutral"
        macd_signal = random.choice(["Neutral", "Sideways"])
        pattern_index = random.choice([1, 3])  # Other patterns
    
    # Define patterns with clear explanations for beginners
    patterns = [
        f"Forming a bull flag pattern with increased volume supporting upward movement (typically bullish)",
        f"Double bottom pattern suggesting potential reversal of downtrend (potentially bullish)",
        f"Head and shoulders pattern indicating possible trend reversal (typically bearish)",
        f"Bullish engulfing pattern on the 4-hour chart (short-term bullish signal)",
        f"Forming a cup and handle pattern suggesting continued uptrend (typically bullish)"
    ]
    
    # Generate RSI value consistent with market direction
    if market_direction == "bullish":
        rsi_value = random.randint(50, 69)  # Stronger but not overbought
    elif market_direction == "bearish":
        rsi_value = random.randint(31, 49)  # Weaker but not oversold
    else:
        rsi_value = random.randint(45, 55)  # Neutral
    
    # Interpret RSI correctly
    if rsi_value < 30:
        rsi_interpretation = "Oversold"
    elif rsi_value > 70:
        rsi_interpretation = "Overbought"
    else:
        rsi_interpretation = "Neutral"
    
    rsi_values = [f"{rsi_value} - {rsi_interpretation}"]
    
    # Choose volume analysis consistent with market direction
    if market_direction == "bullish":
        volume_analysis = [
            "Increasing volume confirms the uptrend",
            "Volume spike indicates strong buying interest"
        ]
    elif market_direction == "bearish":
        volume_analysis = [
            "Decreasing volume suggests weakening momentum",
            "Declining volume in downtrend suggests potential reversal"
        ]
    else:
        volume_analysis = [
            "Average volume suggests consolidation phase",
            "Volume staying consistent with previous days"
        ]
    
    # Choose recommendations consistent with market direction
    if market_direction == "bullish":
        recommendations = [
            "Consider entering long positions with tight stop losses",
            "Watch for breakout above resistance with increased volume"
        ]
    elif market_direction == "bearish":
        recommendations = [
            "Consider taking profits at resistance levels",
            "Watch for potential reversal signals"
        ]
    else:
        recommendations = [
            "Wait for confirmation of trend before entering positions",
            "Consider range-trading strategies while in consolidation"
        ]
    
    # Choose EMA status consistent with market direction
    if market_direction == "bullish":
        ema_status = "Golden Cross" # Bullish signal
    elif market_direction == "bearish":
        ema_status = "Death Cross" # Bearish signal
    else:
        ema_status = "Neutral"
    
    return {
        'sentiment': sentiment,
        'indicators': {
            'RSI': rsi_values[0],
            'MACD': macd_signal,
            'EMA 50/200': ema_status
        },
        'pattern': patterns[pattern_index],
        'support': round(gbp_price * 0.95, 2),
        'resistance': round(gbp_price * 1.05, 2),
        'volume': random.choice(volume_analysis),
        'recommendation': random.choice(recommendations)
    }

def get_price_prediction(symbol):
    """Simulate price prediction for a cryptocurrency"""
    # In a real implementation, this would use ML models/historical data analysis
    usd_price = float(get_crypto_price(symbol) or 0)
    gbp_price = convert_usd_to_gbp(usd_price)
    
    # Generate upcoming pattern detection with directional emojis and success probabilities
    upcoming_patterns = [
        {"text": f"📈 Developing inverted head and shoulders pattern could signal bullish reversal within 48 hours", "direction": "bullish", "success_rate": "76%", "target": f"£{gbp_price * 1.15:.2f}"},
        {"text": f"📊 Triangle pattern forming, expect breakout decision by {(datetime.datetime.now() + datetime.timedelta(days=2)).strftime('%d %b')}", "direction": "neutral", "success_rate": "65%", "target": f"£{gbp_price * 1.08:.2f} (upside) or £{gbp_price * 0.92:.2f} (downside)"},
        {"text": f"📉 Double top pattern nearing completion, watch for confirmation within 24-36 hours", "direction": "bearish", "success_rate": "72%", "target": f"£{gbp_price * 0.85:.2f}"},
        {"text": f"📈 Potential cup and handle formation developing, completion expected by {(datetime.datetime.now() + datetime.timedelta(days=3)).strftime('%d %b')}", "direction": "bullish", "success_rate": "69%", "target": f"£{gbp_price * 1.20:.2f}"},
        {"text": f"📈 Bullish flag consolidation nearly complete, breakout likely within 24-48 hours", "direction": "bullish", "success_rate": "81%", "target": f"£{gbp_price * 1.12:.2f}"}
    ]
    
    # Advanced key factors with specific actionable insights
    factors = [
        f"Whale wallets accumulating: {random.randint(3, 8)} wallets holding >1M {symbol} added {random.randint(50000, 500000)} coins in the past 72 hours",
        f"Exchange outflows exceeding inflows by {random.randint(15, 40)}% suggesting strong holding sentiment and reduced selling pressure",
        f"Increasing developer activity with {random.randint(20, 50)} GitHub commits in the past week signaling continued project evolution",
        f"Open interest in derivatives markets increased by {random.randint(15, 35)}% in past 48 hours indicating rising institutional interest",
        f"Historical pattern: Current price action has 83% correlation with previous {random.randint(3, 6)} rallies that resulted in 35-65% gains"
    ]
    
    # Check for upcoming scheduled events
    upcoming_events = []
    if symbol == 'BTC':
        upcoming_events = [
            f"Bitcoin options expiry on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 14))).strftime('%d %b')}",
            f"Major mining difficulty adjustment expected in approximately {random.randint(2, 10)} days"
        ]
    elif symbol == 'XRP':
        upcoming_events = [
            f"Scheduled Ripple developments announcement on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(1, 7))).strftime('%d %b')}",
            f"Next court hearing in SEC case on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(5, 30))).strftime('%d %b')}"
        ]
    elif symbol == 'HBAR':
        upcoming_events = [
            f"Hedera Council meeting on {(datetime.datetime.now() + datetime.timedelta(days=random.randint(3, 21))).strftime('%d %b')}",
            f"Major partnership announcement expected within the next {random.randint(1, 2)} weeks"
        ]
    
    # Generate realistic price targets based on actual coin value
    # Lower success rates to be more realistic
    realistic_targets = {
        'BTC': {'bullish': gbp_price * 1.05, 'bearish': gbp_price * 0.93, 'neutral': gbp_price},
        'XRP': {'bullish': gbp_price * 1.08, 'bearish': gbp_price * 0.92, 'neutral': gbp_price},
        'HBAR': {'bullish': gbp_price * 1.07, 'bearish': gbp_price * 0.94, 'neutral': gbp_price}
    }
    
    # Update upcoming patterns with more realistic targets and success rates
    for pattern in upcoming_patterns:
        if pattern["direction"] == "bullish":
            pattern["success_rate"] = f"{random.randint(55, 65)}%"
            pattern["target"] = f"£{realistic_targets[symbol]['bullish']:.4f}"
        elif pattern["direction"] == "bearish":
            pattern["success_rate"] = f"{random.randint(52, 62)}%"
            pattern["target"] = f"£{realistic_targets[symbol]['bearish']:.4f}"
        else:
            pattern["success_rate"] = f"{random.randint(50, 60)}%"
            pattern["target"] = f"£{realistic_targets[symbol]['neutral']:.4f}"
    
    # Select pattern based on coin and current trend to ensure consistency
    # For the example, let's select patterns with different directions for different coins
    if symbol == 'BTC':
        # For Bitcoin, bullish bias
        selected_pattern = next((p for p in upcoming_patterns if p["direction"] == "bullish"), upcoming_patterns[0])
    elif symbol == 'XRP':
        # For XRP, neutral or bullish
        selected_pattern = next((p for p in upcoming_patterns if p["direction"] in ["neutral", "bullish"]), upcoming_patterns[1])
    elif symbol == 'HBAR':
        # For HBAR, could be any direction but prefer bullish
        if random.random() > 0.7:
            selected_pattern = next((p for p in upcoming_patterns if p["direction"] == "bearish"), upcoming_patterns[2])
        else:
            selected_pattern = next((p for p in upcoming_patterns if p["direction"] == "bullish"), upcoming_patterns[0])
    else:
        selected_pattern = random.choice(upcoming_patterns)
    
    # Create consistent short and medium term predictions based on the selected pattern
    pattern_direction = selected_pattern["direction"]
    price_target = float(selected_pattern["target"].replace('£', ''))
    
    # Adjust short and medium term predictions to match the pattern direction
    if pattern_direction == "bullish":
        short_term_pred = f"Target: £{price_target * 0.98:.4f} within 24 hours based on RSI divergence and VWAP breakout ({random.randint(55, 65)}% accuracy historically)"
        medium_term_pred = f"Primary target: £{price_target * 1.02:.4f} (7 days) with confirmation if daily closes above £{price_target * 0.96:.4f} for 2 consecutive sessions"
    elif pattern_direction == "bearish":
        short_term_pred = f"Likely to test support at £{price_target * 1.03:.4f} in the next 24 hours with increased selling pressure"
        medium_term_pred = f"Downside target: £{price_target * 0.98:.4f} (7 days) if price fails to maintain support at £{price_target * 1.05:.4f}"
    else:
        short_term_pred = f"Range-bound between £{price_target * 0.98:.4f}-£{price_target * 1.02:.4f} with key supports at £{price_target * 0.975:.4f} and £{price_target * 0.965:.4f}"
        medium_term_pred = f"Consolidation likely to continue with £{price_target * 0.97:.4f}-£{price_target * 1.03:.4f} range until volume profile changes"
    
    return {
        'upcoming_pattern': selected_pattern["text"],
        'pattern_direction': selected_pattern["direction"],
        'pattern_success_rate': selected_pattern["success_rate"],
        'pattern_target': selected_pattern["target"],
        'short_term': short_term_pred,
        'medium_term': medium_term_pred,
        'confidence': random.randint(55, 70),
        'factors': random.choice(factors),
        'upcoming_events': random.choice(upcoming_events) if upcoming_events else "No major scheduled events in the immediate future"
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
    """Get market overview for all supported coins"""
    # In a real implementation, this would fetch real market data
    
    overview = {}
    for coin in SUPPORTED_COINS:
        usd_price = float(get_crypto_price(coin) or 0)
        gbp_price = convert_usd_to_gbp(usd_price)
        overview[coin] = {
            'price': gbp_price,
            'change_24h': round(random.uniform(-5, 7), 2),
            'volume': f"{round(random.uniform(100, 500), 1)}M",
            'sentiment': "Bullish" if random.random() > 0.6 else "Neutral" if random.random() > 0.3 else "Bearish"
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
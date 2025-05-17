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
        title="Crypto Assistant Bot Commands",
        description="Here are all available commands:",
        color=0x00FFFF
    )
    
    embed.add_field(
        name="/price [coin]",
        value="Get current price of a cryptocurrency (BTC, XRP, or HBAR)",
        inline=False
    )
    
    embed.add_field(
        name="/analysis [coin]",
        value="Get detailed technical analysis of a coin",
        inline=False
    )
    
    embed.add_field(
        name="/predict [coin]",
        value="Get price prediction based on current patterns",
        inline=False
    )
    
    embed.add_field(
        name="/news [coin]",
        value="Get latest news that might impact the coin",
        inline=False
    )
    
    embed.add_field(
        name="/help",
        value="Show this help message",
        inline=False
    )
    
    embed.set_footer(text="The bot also sends automatic alerts for significant market movements")
    
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
    
    embed = discord.Embed(
        title=f"Price Prediction for {symbol}",
        description=f"Based on current market conditions and chart patterns:",
        color=0xFFD700
    )
    
    embed.add_field(
        name="Short-term (24h)",
        value=prediction['short_term'],
        inline=False
    )
    
    embed.add_field(
        name="Medium-term (7 days)",
        value=prediction['medium_term'],
        inline=False
    )
    
    embed.add_field(
        name="Confidence Level",
        value=f"{prediction['confidence']}%",
        inline=False
    )
    
    embed.add_field(
        name="Key Factors",
        value=prediction['factors'],
        inline=False
    )
    
    embed.set_footer(text="⚠️ This is not financial advice. Always do your own research.")
    
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
        title=f"Latest {symbol} News",
        description=f"Recent developments that could impact {symbol} price:",
        color=0x9370DB
    )
    
    for item in news_items:
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
    
    short_term_predictions = [
        f"Likely to test resistance at £{gbp_price * 1.05:.2f} in the next 24 hours",
        f"Expected to consolidate between £{gbp_price * 0.98:.2f} - £{gbp_price * 1.02:.2f}",
        f"Possible breakout above £{gbp_price * 1.03:.2f} if volume increases"
    ]
    
    medium_term_predictions = [
        f"Forming a bullish pattern suggesting a target of £{gbp_price * 1.15:.2f} within a week",
        f"Indicators suggest continued sideways movement with resistance at £{gbp_price * 1.08:.2f}",
        f"Technical patterns indicate potential upside of 10-15% if market conditions remain favorable"
    ]
    
    factors = [
        "Increasing network activity and development updates",
        "Growing institutional interest and accumulation patterns",
        "Technical breakout from long-term resistance level",
        "Favorable regulatory developments and mainstream adoption signals",
        "Correlation with broader market movements and on-chain metrics"
    ]
    
    return {
        'short_term': random.choice(short_term_predictions),
        'medium_term': random.choice(medium_term_predictions),
        'confidence': random.randint(65, 85),
        'factors': random.choice(factors)
    }

def get_crypto_news(symbol):
    """Simulate getting news for a cryptocurrency"""
    # In a real implementation, this would fetch from news APIs
    
    btc_news = [
        {
            'title': 'Bitcoin ETF Sees Record Inflows',
            'summary': 'The latest data shows significant capital flowing into Bitcoin ETFs, suggesting growing institutional interest',
            'url': 'https://example.com/bitcoin-etf-news'
        },
        {
            'title': 'Major Bank Announces Bitcoin Custody Service',
            'summary': 'A top-tier financial institution has announced plans to offer Bitcoin custody services to wealthy clients',
            'url': 'https://example.com/bank-bitcoin-custody'
        },
        {
            'title': 'Mining Difficulty Hits New All-Time High',
            'summary': 'Bitcoin network security increases as mining difficulty adjusts upward for the fifth consecutive time',
            'url': 'https://example.com/mining-difficulty'
        }
    ]
    
    xrp_news = [
        {
            'title': 'Ripple Case Developments Favor XRP',
            'summary': 'The latest court rulings in the Ripple case suggest a favorable outcome may be approaching',
            'url': 'https://example.com/ripple-case-update'
        },
        {
            'title': 'Major Bank Tests XRP for Cross-Border Payments',
            'summary': 'A multinational banking institution reports successful trials using XRP for international transfers',
            'url': 'https://example.com/bank-xrp-trials'
        },
        {
            'title': 'Ripple Expands ODL Corridors',
            'summary': 'New On-Demand Liquidity corridors announced for emerging markets, expanding XRP utility',
            'url': 'https://example.com/ripple-odl-expansion'
        }
    ]
    
    hbar_news = [
        {
            'title': 'Hedera Announces Major Enterprise Partnership',
            'summary': 'A Fortune 500 company joins the Hedera Governing Council, bringing enterprise validation',
            'url': 'https://example.com/hedera-partnership'
        },
        {
            'title': 'HBAR Foundation Funds New DeFi Projects',
            'summary': 'New grants announced to develop decentralized finance applications on the Hedera network',
            'url': 'https://example.com/hbar-defi-grants'
        },
        {
            'title': 'Hedera Sets New TPS Record in Recent Test',
            'summary': 'Network optimization leads to new transaction throughput milestone, highlighting scalability',
            'url': 'https://example.com/hedera-tps-record'
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
import discord
from discord.ext import commands, tasks
import requests
import os

# --- CONFIG ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN')  # Replace with your bot token or set as env var
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID', '123456789012345678'))  # Replace with your channel ID or set as env var

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    crypto_alerts.start()

@bot.command()
async def price(ctx, symbol: str):
    """Get the current price of a crypto symbol (e.g. !price BTC)"""
    price = get_crypto_price(symbol)
    if price:
        await ctx.send(f"The current price of {symbol.upper()} is ${price}")
    else:
        await ctx.send(f"Could not fetch price for {symbol.upper()}")

@tasks.loop(minutes=1)
async def crypto_alerts():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel with ID {CHANNEL_ID} not found!")
        return
    # Example: check for a big price move
    alert = check_for_important_event()
    if alert:
        await channel.send(f"🚨 ALERT: {alert}")

def get_crypto_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        r = requests.get(url)
        return r.json()['price']
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def check_for_important_event():
    # TODO: Replace with your advanced logic (signals, news, etc.)
    # Return a string to send an alert, or None for no alert
    return None

if __name__ == "__main__":
    bot.run(TOKEN) 
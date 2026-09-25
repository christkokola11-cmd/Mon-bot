
import discord
import os
import aiohttp
import re
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# CONFIG
TIKTOK_USERNAME = "furiosbsofficiel"
YOUTUBE_CHANNEL_ID = "UCXXXXXXXXXXXXXXXX" # On mettra le bon après
DISCORD_CHANNEL_ID = 123456789012345678  # <- METS TON ID SALON ICI

last_tiktok_id = None
last_youtube_id = None

@bot.event
async def on_ready():
    print(f"Connecte: {bot.user}")
    check_tiktok.start()
    check_youtube.start()

@tasks.loop(minutes=5)
async def check_tiktok():
    global last_tiktok_id
    try:
        url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                html = await resp.text()
                # Cherche le dernier video ID
                match = re.search(r'"id":"(\d+)"', html)
                if not match:
                    return
                video_id = match.group(1)
                if last_tiktok_id is None:
                    last_tiktok_id = video_id
                    return
                if video_id != last_tiktok_id:
                    last_tiktok_id = video_id
                    channel = bot.get_channel(DISCORD_CHANNEL_ID)
                    if channel:
                        await channel.send(f"🔥 Nouveau TikTok de FuriosBS !\nhttps://www.tiktok.com/@{TIKTOK_USERNAME}/video/{video_id} @everyone")
    except Exception as e:
        print(f"TikTok error: {e}")

@tasks.loop(minutes=5)
async def check_youtube():
    global last_youtube_id
    # (garde le check youtube si tu veux les 2)
    pass

bot.run(os.getenv("TOKEN"))

import discord
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread
import asyncio
import aiohttp
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

SALON_YOUTUBE = 1375998725016780964
YOUTUBE_HANDLE = "@FuriosBS"
TIKTOK_USERNAME = "furiosbsoft"

dernier_yt = ""
dernier_tiktok = ""

@tasks.loop(minutes=3)
async def check_videos():
    global dernier_yt, dernier_tiktok
    channel = bot.get_channel(SALON_YOUTUBE)
    if not channel: return

    # YOUTUBE
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.youtube.com/{YOUTUBE_HANDLE}/videos", headers={"User-Agent":"Mozilla/5.0"}) as r:
                html = await r.text()
                if '"channelId":"' in html:
                    cid = html.split('"channelId":"')[1].split('"')[0]
                    async with session.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}") as r2:
                        xml = await r2.text()
                        if "<yt:videoId>" in xml:
                            vid = xml.split("<yt:videoId>")[1].split("</yt:videoId>")[0]
                            if dernier_yt == "":
                                dernier_yt = vid
                            elif vid!= dernier_yt:
                                dernier_yt = vid
                                await channel.send(f"🎬 **NOUVELLE VIDÉO YOUTUBE FURIOS!** @everyone\nhttps://www.youtube.com/watch?v={vid}")
    except Exception as e:
        print(f"YT: {e}")

    # TIKTOK
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://www.tiktok.com/@{TIKTOK_USERNAME}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                html = await r.text()
                m = re.search(r'"video":{"id":"(\d+)"', html)
                if m:
                    tid = m.group(1)
                    if dernier_tiktok == "":
                        dernier_tiktok = tid
                    elif tid!= dernier_tiktok:
                        dernier_tiktok = tid
                        await channel.send(f"🔥 **NOUVEAU TIKTOK FURIOS!** @everyone\nhttps://www.tiktok.com/@{TIKTOK_USERNAME}/video/{tid}")
    except Exception as e:
        print(f"TIKTOK: {e}")

@bot.event
async def on_ready():
    print(f"Bot online! {bot.user} - FURIOS BOT PRET!")
    check_videos.start()

@bot.command()
async def test(ctx):
    await ctx.send(f"✅ FURIOS-BOT ACTIF dans {ctx.channel.mention}!\nYT: {YOUTUBE_HANDLE} -> <#{SALON_YOUTUBE}>\nTikTok: @{TIKTOK_USERNAME}")

# KEEP ALIVE POUR RENDER
app = Flask('')
@app.route('/')
def home():
    return "FURIOS BOT EN LIGNE!"

def run():
    app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv("TOKEN"))

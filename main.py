import discord, os, aiohttp, re, xml.etree.ElementTree as ET
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TIKTOK_USERNAME = "furiosbsofficiel"
YOUTUBE_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id=UCvB4x..."
SALONS_ID = [1375998725016780964,1373558403712028773,1373707661408735443,1373712170906423398,1373739207394070728,1373739539012649050,1374857163104583782]

last_tiktok = None
last_yt = None

@bot.event
async def on_ready():
    print(f"Bot {bot.user} connecté!")
    check.start()

@tasks.loop(minutes=3)
async def check():
    global last_tiktok, last_yt
    # TIKTOK
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.tiktok.com/@{TIKTOK_USERNAME}", headers={"User-Agent": "Mozilla/5.0"}) as r:
                html = await r.text()
                vids = re.findall(r'"id":"(\d{19})"', html)
                if vids:
                    nid = vids[0]
                    if last_tiktok is None: last_tiktok = nid
                    elif nid!= last_tiktok:
                        last_tiktok = nid
                        link = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{nid}"
                        for sid in SALONS_ID:
                            ch = bot.get_channel(sid)
                            if ch:
                                try: await ch.send(f"🔥 **NOUVEAU TIKTOK FURIOSBS**\n{link} @everyone")
                                except: pass
    except Exception as e: print(e)

@bot.command()
async def test(ctx):
    await ctx.send("✅ BOT ACTIF - 7 SALONS!")
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    keep_alive()
bot.run(os.getenv("TOKEN"))

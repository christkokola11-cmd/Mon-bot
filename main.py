import discord,os,aiohttp
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TIKTOK_USERNAME = "furiosbsoft"
SALONS_ID = [1375998725016780964]

@bot.event
async def on_ready():
    print(f"{bot.user} connecte!")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.tikwm.com/api/user/posts?unique_id={TIKTOK_USERNAME}") as r:
                    data = await r.json()
                    if data.get("data"):
                        videos = data["data"].get("videos", [])
                        if videos:
                            latest_id = videos[0]["video_id"]
                            if hasattr(bot, "last_tiktok"):
                                if bot.last_tiktok!= latest_id:
                                    link = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{latest_id}"
                                    for sid in SALONS_ID:
                                        ch = bot.get_channel(sid)
                                        if ch:
                                            try:
                                                await ch.send(f"🔥 **NOUVEAU TIKTOK FURIOS!**\n{link}")
                                            except:
                                                pass
                                    bot.last_tiktok = latest_id
                            else:
                                bot.last_tiktok = latest_id
        except Exception as e:
            print(e)
        await asyncio.sleep(300)

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
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv("TOKEN"))

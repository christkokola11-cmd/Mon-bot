from flask import Flask
from threading import Thread
import os

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot en ligne !"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp, re

C_VIDEO = 1373712170906423398
C_BIENVENUE = 1373558403712028773
C_AUREVOIR = 1374432105420947576
C_MAPS = 1553100406081720350
C_TICKET = 1439017706010574859
C_LVL = 1373739207394070728
C_GIVEAWAY = 1375998725016780964
TOKEN = os.getenv("DISCORD_TOKEN")
YT_HANDLE = "@FuriosBS"
TIKTOK = "@furiosbsofficiel"
YT_RSS = None
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
xp_data = {}
last_vid = None
last_tik = None

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="t1")
    async def open(self, inter, btn):
        g = inter.guild
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), inter.user: discord.PermissionOverwrite(view_channel=True), g.me: discord.PermissionOverwrite(view_channel=True)}
        c = await g.create_text_channel(f"ticket-{inter.user.name}", overwrites=ow)
        await c.send(f"{inter.user.mention} Staff arrive!")
        await inter.response.send_message(f"Créé {c.mention}", ephemeral=True)

async def get_rss():
    global YT_RSS
    if YT_RSS: return YT_RSS
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.youtube.com/{YT_HANDLE}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                t = await r.text()
                import re
                m = re.search(r'"channelId":"(UC[^"]+)"', t)
                if m:
                    YT_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"
                    return YT_RSS
    except: pass
    return YT_RSS

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketView())
    check_youtube.start()
    check_tiktok.start()
    print(f"Furios OK {bot.user}")

@bot.event
async def on_member_join(m):
    ch = bot.get_channel(C_BIENVENUE)
    e = discord.Embed(title="Ho un nouveau membre", description=f"🎣 Salut {m.mention} bienvenue! Nous sommes {m.guild.member_count}", color=0x0099FF)
    await ch.send(embed=e)

@bot.event
async def on_member_remove(m):
    ch = bot.get_channel(C_AUREVOIR)
    e = discord.Embed(title="Au revoir", description=f"{m.name} a quitté", color=0x0099FF)
    await ch.send(embed=e)

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    uid = str(msg.author.id)
    xp_data[uid] = xp_data.get(uid, 0) + 20
    await bot.process_commands(msg)

@bot.tree.command(name="rank", description="Voir son lvl")
async def rank(interaction: discord.Interaction):
    xp = xp_data.get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"Niveau {xp//100} XP {xp}", ephemeral=True)

@bot.tree.command(name="setup_ticket", description="Poster ticket")
async def setup_ticket(interaction: discord.Interaction):
    ch = bot.get_channel(C_TICKET)
    e = discord.Embed(title="Besoin d'aide? Ouvre un ticket!", description="Click ouvrir un ticket", color=0x0099FF)
    await ch.send(embed=e, view=TicketView())
    await interaction.response.send_message("OK", ephemeral=True)

@tasks.loop(minutes=5)
async def check_youtube():
    global last_vid
    rss = await get_rss()
    if not rss: return
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(rss) as r:
                t = await r.text()
                if "videoId" in t:
                    vid = t.split("<yt:videoId>")[1].split("</yt:videoId>")[0]
                    if last_vid and vid!= last_vid:
                        ch = bot.get_channel(C_VIDEO)
                        await ch.send(f"ho furios Vien de poster une nouvelle vidéo vas faire exploser les compteurs de like 🙌🤩 @everyone https://www.youtube.com/watch?v={vid}")
                    last_vid = vid
    except: pass

@tasks.loop(minutes=15)
async def check_tiktok():
    global last_tik
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.tiktok.com/{TIKTOK}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                t = await r.text()
                m = re.search(r'"id":"(\d{19})"', t)
                if m and last_tik and m.group(1)!= last_tik:
                    ch = bot.get_channel(C_VIDEO)
                    await ch.send(f"ho furios Vien de poster TikTok 🙌 @everyone https://www.tiktok.com/{TIKTOK}/video/{m.group(1)}")
                if m: last_tik = m.group(1)
    except: pass

bot.run(TOKEN)

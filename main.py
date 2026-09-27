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
import aiohttp, re, asyncio, random, datetime

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
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open(self, inter, btn):
        g = inter.guild
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), g.me: discord.PermissionOverwrite(view_channel=True)}
        c = await g.create_text_channel(f"ticket-{inter.user.name}", overwrites=ow)
        await c.send(f"{inter.user.mention} Ton ticket est ouvert! Le staff arrive.")
        await inter.response.send_message(f"Ticket créé: {c.mention} ✅", ephemeral=True)

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

# --- GIVEAWAY ---
@bot.tree.command(name="giveaway", description="Lancer un giveaway")
@app_commands.describe(duree="Durée ex: 1m, 10m, 1h, 1d", gagnants="Nombre de gagnants", prix="Prix à gagner", salon="Salon du giveaway")
async def giveaway(interaction: discord.Interaction, duree: str, gagnants: int, prix: str, salon: discord.TextChannel = None):
    await interaction.response.defer()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([smhd])", duree.lower())
    if not match:
        await interaction.followup.send("Durée invalide! Ex: 10m, 1h, 1d", ephemeral=True)
        return
    seconds = int(match.group(1)) * units[match.group(2)]
    channel = salon or interaction.channel
    end_time = discord.utils.utcnow() + datetime.timedelta(seconds=seconds)
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"**Prix:** {prix}\n**Gagnants:** {gagnants}\n**Finit:** <t:{int(end_time.timestamp())}:R>\n\nClique sur 🎉 pour participer!", color=0xffd700)
    embed.set_footer(text=f"Lancé par {interaction.user}")
    msg = await channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await interaction.followup.send(f"Giveaway lancé dans {channel.mention}!", ephemeral=True)
    await asyncio.sleep(seconds)
    new_msg = await channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if not users:
        await channel.send("Personne n'a participé 😢")
        return
    winners = random.sample(users, min(gagnants, len(users)))
    win_mention = ", ".join([w.mention for w in winners])
    await channel.send(f"🎉 Félicitations {win_mention}! Vous avez gagné **{prix}**!")

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

@tasks.loop(minutes=5)
async def check_tiktok():
    global last_tik
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.tiktok.com/@tonpseudo") as r:
                t = await r.text()
                # tu pourras remettre ton regex tiktok ici apres
    except: pass

import os
bot.run(os.environ.get("TOKEN"))

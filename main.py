from flask import Flask
from threading import Thread
import os
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import random
import re
from datetime import datetime

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot en ligne!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

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
# --- ALERT MAPS BRAWL STARS ---
ALERT_MAPS_CHANNEL_ID = 1553100406081720471
BRAWL_API = "https://api.brawlapi.com/v1/events/rotation"
SAVE_FILE = "last_brawl_maps.json"

class BrawlAlertMaps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_maps = {}
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    self.last_maps = json.load(f)
            except:
                self.last_maps = {}

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_rotation.is_running():
            self.check_rotation.start()
            print("Alert Maps loop started")

    @tasks.loop(seconds=60)
    async def check_rotation(self):
        channel = self.bot.get_channel(ALERT_MAPS_CHANNEL_ID)
        if not channel:
            return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BRAWL_API) as r:
                    data = await r.json()
                    for event in data.get("active", []):
                        mode = event["map"]["gameMode"]["name"]
                        map_id = str(event["id"])
                        map_name = event["map"]["name"]
                        image_url = event["map"]["imageUrl"]
                        if self.last_maps.get(map_id) != map_name:
                            self.last_maps[map_id] = map_name
                            with open(SAVE_FILE, "w") as f:
                                json.dump(self.last_maps, f)
                            embed = discord.Embed(title=f"{mode} - {map_name}", color=0x00ff00)
                            embed.set_image(url=image_url)
                            view = discord.ui.View()
                            view.add_item(discord.ui.Button(label="JOIN GAME ✅", url=f"https://brawlify.com/maps/{map_id}", style=discord.ButtonStyle.link))
                            await channel.send(content=f"The {mode} maps have changed. Here are the new maps!!! - {datetime.now().strftime('%H:%M')}", embed=embed, view=view)
        except Exception as e:
            print(f"[Maps Error] {e}")

    def cog_unload(self):
        self.check_rotation.cancel()

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        bot.add_view(TicketView())
        try: check_youtube.start()
        except: pass
        try: check_tiktok.start()
        except: pass
        await bot.add_cog(BrawlAlertMaps(bot))
        print(f"Furios OK {bot.user} + Alert Maps ON")
    except Exception as e:
        print(f"[on_ready ERROR] {e}")
        import traceback
        traceback.print_exc()

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

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Fermer le ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="close_ticket_furios")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Ticket fermé par {interaction.user.mention}. Suppression dans 3 secondes...", ephemeral=False)
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except:
            pass

class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        super().__init__(title=f"Ticket — {ticket_type}")
        self.ticket_type = ticket_type
        self.raison = discord.ui.TextInput(label="Raison de votre demande", placeholder="Décrivez brièvement votre problème...", style=discord.TextStyle.paragraph, max_length=300, required=True)
        self.add_item(self.raison)
    async def on_submit(self, interaction: discord.Interaction):
        g = interaction.guild
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True), g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)}
        # LE SALON S'APPELLE #ticket-furios-NOM
        c = await g.create_text_channel(f"ticket-furios-{interaction.user.name}", overwrites=ow, reason=f"Ticket {self.ticket_type}")
        embed = discord.Embed(title=f"Ticket — {self.ticket_type}", description=f"**De {interaction.user.mention}**\n**Type:** {self.ticket_type}\n**Raison:**\n```{self.raison.value}```\n\nLe staff va te répondre. Quand c'est fini, clique sur 🔒 Fermer le ticket en bas.", color=0x2b2d31)
        embed.set_footer(text="Merci de patienter, FuriosBS arrive!")
        # ICI LE BOUTON ROUGE FERMER
        await c.send(content=f"{interaction.user.mention} <@&{R_STAFF if 'R_STAFF' in globals() else ''}>", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket créé: {c.mention} ✅", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Giveaway", description="Je souhaite réclamer une récompense d'un giveaway que j'ai gagné", emoji="🎉"),
            discord.SelectOption(label="Problème", description="J'ai un problème avec un membre ou un détail du serveur", emoji="👹"),
            discord.SelectOption(label="Partenariat", description="Je souhaite faire un partenariat avec ce serveur", emoji="💙"),
            discord.SelectOption(label="Ticket courrone", description="Je souhaite contacter Not Feller et les owner de ce serveur", emoji="👑"),
            discord.SelectOption(label="Candidature staff", description="Je souhaite devenir staff sur ce serveur (si les candidatures sont ouvertes)", emoji="⚠️"),
            discord.SelectOption(label="Autre", description="J'ai un autre problème", emoji="🎭"),
        ]
        super().__init__(placeholder="Choisissez un type de ticket...", options=options)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.values[0]))

class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Ouvrir un ticket", emoji="🎫", style=discord.ButtonStyle.blurple, custom_id="open_ticket_v4")
    async def open(self, inter, btn):
        e = discord.Embed(title="Type de ticket", description="Sélectionnez le type correspondant à votre demande.", color=0x2b2d31)
        await inter.response.send_message(embed=e, view=TicketSelectView(), ephemeral=True)
    @discord.ui.button(label="Informations", emoji="📖", style=discord.ButtonStyle.gray, custom_id="info_ticket_v4")
    async def info(self, inter, btn):
        await inter.response.send_message("Un seul ticket à la fois. Choisissez la bonne catégorie!", ephemeral=True)

@bot.tree.command(name="setup_ticket", description="Installer les tickets style Bot Feller")
async def setup_ticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    ch = bot.get_channel(C_TICKET) if 'C_TICKET' in globals() else interaction.channel
    if ch is None: ch = interaction.channel
    embed = discord.Embed(title="Support", description="**Besoin d'aide? Ouvre un ticket et l'équipe vous répondra dans un salon privé!**\n\n**Comment ouvrir une demande :**\n1. Cliquez sur \"Ouvrir un ticket\"\n2. Entrez les détails sur la raison de l'ouverture de votre ticket", color=0x2b2d31)
    embed.set_image(url="https://cdn.discordapp.com/attachments/1373609586824581153/1553730748547203113/IMG-20260922-WA00231.jpg")
    await ch.send(embed=embed, view=TicketView())
    await interaction.followup.send(f"Installé dans {ch.mention} ✅ Avec bouton FERMER", ephemeral=True)
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

@tasks.loop(minutes=10)
async def check_tiktok():
    global last_tik
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.tiktok.com/@tonpseudo") as r:
                t = await r.text()
                # tu pourras remettre ton regex tiktok ici apres
    except: pass

bot.run(os.environ.get("TOKEN"))

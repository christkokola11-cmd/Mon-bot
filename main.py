from flask import Flask
from threading import Thread
import os, json, re, asyncio, random, aiohttp
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands, tasks

# --- FLASK (UNE SEULE FOIS) ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot en ligne!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
Thread(target=run_flask, daemon=True).start()

# --- CONFIG ---
C_VIDEO = 1373712170906423398
C_BIENVENUE = 1373558403712028773
C_AUREVOIR = 1374432105420947576
C_MAPS = 1553100406081720350
C_TICKET = 1439017706010574859
C_LVL = 1373739207394070728
C_GIVEAWAY = 1375998725016780964
ALERT_MAPS_CHANNEL_ID = C_MAPS

YT_HANDLE = "@FuriosBS"
YT_RSS = None
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
xp_data = {}
last_vid = None
last_tik = None
# Mets ton TOKEN Render: soit DISCORD_TOKEN soit TOKEN
TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")

# --- TICKET AVEC DETAILS (ton système complet) ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Fermer le ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="close_ticket_furios")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"Ticket fermé par {interaction.user.mention}. Suppression dans 3 sec...", ephemeral=False)
        await asyncio.sleep(3)
        try: await interaction.channel.delete(reason=f"Fermé par {interaction.user}")
        except: pass

class TicketModal(discord.ui.Modal):
    def __init__(self, ticket_type: str):
        super().__init__(title=f"Ticket — {ticket_type}")
        self.ticket_type = ticket_type
        self.raison = discord.ui.TextInput(label="Raison", placeholder="Décris ton problème...", style=discord.TextStyle.paragraph, max_length=300, required=True)
        self.add_item(self.raison)
    async def on_submit(self, interaction: discord.Interaction):
        g = interaction.guild
        ow = {g.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True), g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)}
        c = await g.create_text_channel(f"ticket-furios-{interaction.user.name}", overwrites=ow)
        embed = discord.Embed(title=f"Ticket — {self.ticket_type}", description=f"**De {interaction.user.mention}**\n**Type:** {self.ticket_type}\n**Raison:**\n```{self.raison.value}```\n\nLe staff va répondre. Clique sur 🔒 pour fermer.", color=0x2b2d31)
        await c.send(content=f"{interaction.user.mention}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket créé: {c.mention} ✅", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Giveaway", description="Réclamer un giveaway gagné", emoji="🎉"),
            discord.SelectOption(label="Problème", description="Problème avec un membre", emoji="👹"),
            discord.SelectOption(label="Partenariat", description="Partenariat", emoji="💙"),
            discord.SelectOption(label="Ticket couronne", description="Contacter les owners", emoji="👑"),
            discord.SelectOption(label="Candidature staff", description="Devenir staff", emoji="⚠️"),
            discord.SelectOption(label="Autre", description="Autre problème", emoji="🎭"),
        ]
        super().__init__(placeholder="Choisissez un type...", options=options, custom_id="ticket_select_v4")
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
        e = discord.Embed(title="Type de ticket", description="Sélectionnez le type correspondant.", color=0x2b2d31)
        await inter.response.send_message(embed=e, view=TicketSelectView(), ephemeral=True)
    @discord.ui.button(label="Informations", emoji="📖", style=discord.ButtonStyle.gray, custom_id="info_ticket_v4")
    async def info(self, inter, btn):
        await inter.response.send_message("Un seul ticket à la fois!", ephemeral=True)

@bot.tree.command(name="setup_ticket", description="Installer les tickets")
async def setup_ticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    ch = bot.get_channel(C_TICKET) or interaction.channel
    embed = discord.Embed(title="Support", description="**Besoin d'aide? Ouvre un ticket!**\n1. Clique sur Ouvrir\n2. Entre les détails", color=0x2b2d31)
    await ch.send(embed=embed, view=TicketView())
    await interaction.followup.send(f"Installé dans {ch.mention} ✅", ephemeral=True)

# --- GIVEAWAY ---
@bot.tree.command(name="giveaway", description="Lancer un giveaway")
@app_commands.describe(duree="Durée ex: 1m, 10m, 1h, 1d", gagnants="Nombre de gagnants", prix="Prix", salon="Salon")
async def giveaway(interaction: discord.Interaction, duree: str, gagnants: int, prix: str, salon: discord.TextChannel = None):
    await interaction.response.defer()
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([smhd])", duree.lower())
    if not match:
        await interaction.followup.send("Durée invalide! Ex: 10m, 1h, 1d", ephemeral=True); return
    seconds = int(match.group(1)) * units[match.group(2)]
    channel = salon or interaction.channel
    end_time = datetime.utcnow() + timedelta(seconds=seconds)
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"**Prix:** {prix}\n**Gagnants:** {gagnants}\n**Finit:** <t:{int(end_time.timestamp())}:R>\n\nClique sur 🎉!", color=0xffd700)
    msg = await channel.send(embed=embed)
    await msg.add_reaction("🎉")
    await interaction.followup.send(f"Giveaway lancé dans {channel.mention}!", ephemeral=True)
    await asyncio.sleep(seconds)
    new_msg = await channel.fetch_message(msg.id)
    users = [u async for u in new_msg.reactions[0].users() if not u.bot]
    if not users:
        await channel.send("Personne n'a participé 😢"); return
    winners = random.sample(users, min(gagnants, len(users)))
    await channel.send(f"🎉 Félicitations {', '.join([w.mention for w in winners])}! Vous avez gagné **{prix}**!")

# --- ALERT MAPS ---
BRAWL_API = "https://api.brawlify.com/v1/events"
SAVE_FILE = "last_brawl_maps.json"
class BrawlAlertMaps(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_maps = {}
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    self.last_maps = json.load(f)
            except: pass

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_rotation.is_running():
            self.check_rotation.start()

    @tasks.loop(seconds=60)
    async def check_rotation(self):
        channel = self.bot.get_channel(1553100406081720350)
        if not channel: return
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(BRAWL_API) as r:
                    data = await r.json()
                    for ev in data.get("active", []):
                        mode = ev.get("mode",{}).get("name","Mode")
                        m = ev.get("map",{})
                        map_name = m.get("name","Unknown")
                        map_id = str(m.get("id", map_name))
                        img = m.get("imageUrl")
                        if self.last_maps.get(map_id) != map_name:
                            self.last_maps[map_id] = map_name
                            with open(SAVE_FILE,"w") as f:
                                json.dump(self.last_maps,f)
                            embed = discord.Embed(title=f"{mode} - {map_name}", color=0x00ff00)
                            if img: embed.set_image(url=img)
                            view = discord.ui.View()
                            view.add_item(discord.ui.Button(label="JOIN GAME ✅", url=f"https://brawlify.com/maps/{map_id}", style=discord.ButtonStyle.link))
                            await channel.send(content=f"The {mode} maps have changed! - {datetime.now().strftime('%H:%M')}", embed=embed, view=view)
        except Exception as e:
            print(f"[Maps Error] {e}")

async def setup_maps(bot):
    await bot.add_cog(BrawlAlertMaps(bot))

# --- YOUTUBE / TIKTOK ---
async def get_rss():
    global YT_RSS
    if YT_RSS: return YT_RSS
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.youtube.com/{YT_HANDLE}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                t = await r.text()
                m = re.search(r'"channelId":"(UC[^"]+)"', t)
                if m: YT_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"; return YT_RSS
    except: pass
    return YT_RSS

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
                        if ch: await ch.send(f"@everyone Nouvelle vidéo! https://www.youtube.com/watch?v={vid}")
                    last_vid = vid
    except: pass

@tasks.loop(minutes=10)
async def check_tiktok():
    pass

@bot.event
async def on_member_join(m):
    ch = bot.get_channel(C_BIENVENUE)
    if ch:
        e = discord.Embed(title="Nouveau membre", description=f"Salut {m.mention} bienvenue! {m.guild.member_count} membres", color=0x0099FF)
        await ch.send(embed=e)

@bot.event
async def on_member_remove(m):
    ch = bot.get_channel(C_AUREVOIR)
    if ch:
        await ch.send(embed=discord.Embed(title="Au revoir", description=f"{m.name} a quitté", color=0x0099FF))

@bot.event
async def on_message(msg):
    if msg.author.bot: return
    xp_data[str(msg.author.id)] = xp_data.get(str(msg.author.id), 0) + 20
    await bot.process_commands(msg)

@bot.tree.command(name="rank", description="Voir son lvl")
async def rank(interaction: discord.Interaction):
    xp = xp_data.get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"Niveau {xp//100} XP {xp}", ephemeral=True)

# --- ON READY FINAL ---
@bot.event
async def on_ready():
    print("ON_READY CALLE - DEBUT")
    try:
        bot.add_view(TicketView())
        bot.add_view(CloseTicketView())
        print("TicketView OK")
    except Exception as e: print(f"TicketView ERROR {e}")
    try:
        synced = await bot.tree.sync()
        print(f"Sync OK - {len(synced)} commandes")
    except Exception as e: print(f"Sync ERROR {e}")
    try:
        if not check_youtube.is_running(): check_youtube.start()
        if not check_tiktok.is_running(): check_tiktok.start()
        print("Youtube/Tiktok OK")
    except: pass
    try:
        await bot.add_cog(BrawlAlertMaps(bot))
        print("Maps Cog OK")
    except Exception as e:
        print(f"Maps Cog ERROR {e}")
        import traceback; traceback.print_exc()
    print(f"Furios OK {bot.user}")

bot.run(TOKEN)

import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import os
import re
import random
from datetime import datetime

# --- TES SALONS ---
C_VIDEO = 1373712170906423398
C_BIENVENUE = 1373558403712028773
C_AUREVOIR = 1374432105420947576
C_INFO_BRAWL = 1373714363533492346
C_MAPS = 1553100406081720350
C_TICKET = 1439017706010574859
C_LVL = 1373739207394070728
C_INFO_XP = 1373739539012649050
C_GIVE_XP = 1373803141899751444
C_GIVEAWAY = 1375998725016780964

TOKEN = os.getenv("DISCORD_TOKEN")
YT_HANDLE = "@FuriosBS"
TIKTOK_HANDLE = "@furiosbsofficiel"
YT_RSS_URL = None

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

xp_data = {}
last_video_id = None
last_tiktok_id = None
last_brawl_map = None

# --- TICKET SYSTEM ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        chan = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites, reason="Ticket Furios")
        await chan.send(f"{interaction.user.mention} Merci d'avoir ouvert un ticket! Décris ton problème, le staff arrive 🙌")
        await interaction.response.send_message(f"Ticket créé {chan.mention} ✅", ephemeral=True)

    @discord.ui.button(label="📖 Formulaire", style=discord.ButtonStyle.gray, custom_id="ticket_form")
    async def form(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Formulaire bientôt disponible!", ephemeral=True)

# --- AUTO RESOLVE YOUTUBE ID ---
async def get_yt_channel_id():
    global YT_RSS_URL
    if YT_RSS_URL: return YT_RSS_URL
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.youtube.com/{YT_HANDLE}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                text = await r.text()
                m = re.search(r'"channelId":"(UC[^"]+)"', text)
                if m:
                    cid = m.group(1)
                    YT_RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
                    print(f"Youtube ID trouvé: {cid}")
                    return YT_RSS_URL
    except Exception as e:
        print(f"Erreur YT ID: {e}")
    # fallback si echec
    return "https://www.youtube.com/feeds/videos.xml?channel_id=UCr1Ma2oK2eUZ2a4g4s5d6f7g"

@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketView())
    if not check_youtube.is_running(): check_youtube.start()
    if not check_tiktok.is_running(): check_tiktok.start()
    if not check_brawl_maps.is_running(): check_brawl_maps.start()
    print(f"Furios Bot connecté {bot.user} | {len(bot.tree.get_commands())} commandes /")

# 2 - BIENVENUE
@bot.event
async def on_member_join(member):
    ch = bot.get_channel(C_BIENVENUE)
    if not ch: return
    embed = discord.Embed(
        title="Ho un nouveau membre",
        description=f"🎣 Salut {member.mention} 🙌 bienvenue dans la team de furios!\n➡️ici:\n >> Amuse toi 🤩\n >> Chill un max 🥳 \n >> Nous sommes désormais **{member.guild.member_count}**\n🥰 N'hésite pas à te rename avec {{FXR}} sur le discord pour soutenir {{Furios}}\nPour bien commencer je te laisse voir le #règlement",
        color=0x0099FF
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=embed)

# 3 - AU REVOIR
@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(C_AUREVOIR)
    if not ch: return
    embed = discord.Embed(
        title="Au revoir 👋",
        description=f"😢 **{member.name}** a quitté le serveur...\nOn est plus que **{member.guild.member_count}** membres.",
        color=0x0099FF
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=embed)

# 7 & 8 & 9 - XP
@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    old_xp = xp_data.get(uid, 0)
    xp_data[uid] = old_xp + random.randint(15, 25)
    old_lvl = old_xp // 100
    new_lvl = xp_data[uid] // 100
    if new_lvl > old_lvl:
        ch = bot.get_channel(C_LVL)
        if ch:
            embed = discord.Embed(title="LEVEL UP! 🔥", description=f"GG {message.author.mention} est passé niveau **{new_lvl}**!\nXP total: **{xp_data[uid]}**", color=0x0099FF)
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await ch.send(embed=embed)
    await bot.process_commands(message)

@bot.tree.command(name="rank", description="Voir ton lvl XP dans Info XP")
async def rank(interaction: discord.Interaction):
    xp = xp_data.get(str(interaction.user.id), 0)
    lvl = xp // 100
    bar = int((xp % 100) / 10)
    barre = "█" * bar + "░" * (10-bar)
    embed = discord.Embed(title=f"Niveau de {interaction.user.name}", description=f"Niveau **{lvl}**\n{barre} {xp%100}/100\nTotal XP: {xp}", color=0x0099FF)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="givexp", description="Donner de l'XP (staff)")
@app_commands.describe(user="Membre", amount="Quantité d'XP")
async def givexp(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Staff only ❌", ephemeral=True); return
    xp_data[str(user.id)] = xp_data.get(str(user.id), 0) + amount
    await interaction.response.send_message(f"{amount} XP donné à {user.mention} ✅", ephemeral=True)

# 6 - TICKET SETUP
@bot.tree.command(name="setup_ticket", description="Poster le message ticket (admin)")
async def setup_ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin only", ephemeral=True); return
    ch = bot.get_channel(C_TICKET)
    embed = discord.Embed(
        title="Besoin d'aide? Ouvre un ticket et l'équipe vous répondra dans un salon privé!",
        description="**Comment ouvrir une demande?**\n1. Click sur \"ouvrir un ticket\"\n2. Entrez les détails sur la raison de l'ouverture de votre ticket.",
        color=0x0099FF
    )
    await ch.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Message ticket posté ✅", ephemeral=True)

# 10 - GIVEAWAY + DROP
@bot.tree.command(name="giveaway", description="Lancer un giveaway")
@app_commands.describe(duration="Ex: 10m 1h 1d", winners="Nombre gagnants", prize="Lot", description="Description")
async def giveaway(interaction: discord.Interaction, duration: str, winners: int, prize: str, description: str = ""):
    ch = bot.get_channel(C_GIVEAWAY)
    embed = discord.Embed(title=f"🎉 GIVEAWAY : {prize} 🎉", description=f"{description}\n\n**Durée:** {duration}\n**Gagnants:** {winners}\n\nRéagis avec 🎉 pour participer!", color=0x0099FF)
    msg = await ch.send(f"@everyone", embed=embed)
    await msg.add_reaction("🎉")
    await interaction.response.send_message("Giveaway lancé ✅", ephemeral=True)

@bot.tree.command(name="drop", description="Poster un drop style Olympus")
@app_commands.describe(amount="Nombre", name="Nom du lot", links="Liens séparés par espace")
async def drop(interaction: discord.Interaction, amount: int, name: str, links: str):
    ch = bot.get_channel(C_GIVEAWAY)
    embed = discord.Embed(title=f"{amount} x {name}", description=f"0/{amount} Claimed\nExpires in 60d 23h", color=0x2B2D31)
    txt = "\n".join([f"**{i}.** {l}" for i, l in enumerate(links.split(), 1)])
    embed.add_field(name="CLAIM LINKS", value=txt[:1024], inline=False)
    await ch.send("@everyone")
    await ch.send(embed=embed)
    await interaction.response.send_message("Drop posté ✅", ephemeral=True)

# 1 - YOUTUBE AUTO
@tasks.loop(minutes=5)
async def check_youtube():
    global last_video_id
    rss = await get_yt_channel_id()
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(rss) as r:
                text = await r.text()
                if "<yt:videoId>" in text:
                    vid = text.split("<yt:videoId>")[1].split("</yt:videoId>")[0]
                    if last_video_id is None:
                        last_video_id = vid
                        return
                    if vid!= last_video_id:
                        last_video_id = vid
                        ch = bot.get_channel(C_VIDEO)
                        if ch:
                            await ch.send(f"ho furios Vien de poster une nouvelle vidéo vas faire exploser les compteurs de like 🙌🤩 @everyone\nhttps://www.youtube.com/watch?v={vid}")
    except Exception as e:
        print(f"YT check err {e}")

# 1BIS - TIKTOK AUTO (best effort)
@tasks.loop(minutes=15)
async def check_tiktok():
    global last_tiktok_id
    try:
        # On utilise une API non-officielle simple
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.tiktok.com/{TIKTOK_HANDLE}", headers={"User-Agent":"Mozilla/5.0"}) as r:
                text = await r.text()
                m = re.search(r'"id":"(\d{19})"', text)
                if m:
                    tid = m.group(1)
                    if last_tiktok_id is None:
                        last_tiktok_id = tid
                        return
                    if tid!= last_tiktok_id:
                        last_tiktok_id = tid
                        ch = bot.get_channel(C_VIDEO)
                        if ch:
                            await ch.send(f"ho furios Vien de poster une nouvelle vidéo TikTok vas faire exploser les compteurs de like 🙌🤩 @everyone\nhttps://www.tiktok.com/{TIKTOK_HANDLE}/video/{tid}")
    except Exception as e:
        print(f"TikTok check err {e}")

# 5 - MAPS BRAWL STARS
@tasks.loop(hours=1)
async def check_brawl_maps():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.brawlapi.com/v1/maps") as r:
                data = await r.json()
                # On poste juste la map du moment (exemple survivant)
                if data and 'list' in data:
                    showdown = [m for m in data['list'] if 'Showdown' in m['gameMode']['name']][:1]
                    if showdown:
                        m = showdown[0]
                        ch = bot.get_channel(C_MAPS)
                        if ch:
                            embed = discord.Embed(title=f"🗺️ Map Survivant a changé: {m['name']}", description=f"Mode: {m['gameMode']['name']}", color=0x0099FF)
                            embed.set_image(url=m['imageUrl'])
                            await ch.send(embed=embed)
    except Exception as e:
        print(f"Maps err {e}")

# 4 - NEWS BRAWL
@tasks.loop(minutes=30)
async def check_brawl_news():
    pass # Tu peux brancher l'API Supercell ici

bot.run(TOKEN)

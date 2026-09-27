import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import asyncio
import json
import os
import random

# --- CONFIG ID DE TES SALONS ---
C_VIDEO = 1373712170906423398
C_BIENVENUE = 1373558403712028773
C_AUREVOIR = 1374432105420947576
C_INFO_BRAWL = 1373714363533492346
C_MAPS = 1553100406081720350
C_TICKET = 1439017706010574859
C_LVL = 1373739207394070728
C_GIVEAWAY = 1375998725016780964

TOKEN = os.getenv("DISCORD_TOKEN") # Mets ton token dans Railway > Variables
YT_CHANNEL_ID = "UC..." # Ton ID Youtube @FuriosBS
YT_RSS = f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_CHANNEL_ID}"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
xp_data = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    check_youtube.start()
    check_brawl_maps.start()
    print(f"Furios Bot connecté {bot.user} - {len(bot.tree.get_commands())} slash")

# --- 2. BIENVENUE ---
@bot.event
async def on_member_join(member):
    ch = bot.get_channel(C_BIENVENUE)
    if not ch: return
    count = member.guild.member_count
    embed = discord.Embed(
        title="Ho un nouveau membre",
        description=f"🎣 Salut {member.mention} 🙌 bienvenue dans la team de furios!\n➡️ici:\n>> Amuse toi 🤩\n>> Chill un max 🥳\n>> Nous sommes désormais **{count}**\n🥰 N'hésite pas à te rename avec {{FXR}} pour soutenir {{Furios}}\nPour bien commencer je te laisse voir le #règlement",
        color=0x0099ff
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=embed)

# --- 3. AU REVOIR ---
@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(C_AUREVOIR)
    if not ch: return
    embed = discord.Embed(title="Au revoir", description=f"😢 {member.name} nous a quitté, on était {member.guild.member_count}...", color=0x0099ff)
    await ch.send(embed=embed)

# --- 7. SYSTEME XP ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    uid = str(message.author.id)
    xp_data[uid] = xp_data.get(uid, 0) + random.randint(5,15)
    lvl = xp_data[uid] // 100
    if xp_data[uid] % 100 < 15: # level up
        ch = bot.get_channel(C_LVL)
        if ch:
            embed = discord.Embed(title="LEVEL UP!", description=f"GG {message.author.mention} est passé niveau **{lvl}**! 🔥", color=0x0099ff)
            await ch.send(embed=embed)
    await bot.process_commands(message)

@bot.tree.command(name="rank", description="Voir ton lvl")
async def rank(interaction: discord.Interaction):
    xp = xp_data.get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"{interaction.user.mention} tu as {xp} XP -> Niveau {xp//100}", ephemeral=True)

@bot.tree.command(name="givexp", description="Give XP staff")
@app_commands.describe(user="Membre", amount="XP à donner")
async def givexp(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Staff only", ephemeral=True); return
    xp_data[str(user.id)] = xp_data.get(str(user.id),0) + amount
    await interaction.response.send_message(f"{amount} XP donné à {user.mention}")

# --- 10. GIVEAWAY ---
@bot.tree.command(name="giveaway", description="Lancer un giveaway")
@app_commands.describe(duration="ex: 10m, 1h, 1d", winners="Nombre de gagnants", prize="Lot", description="Description")
async def giveaway(interaction: discord.Interaction, duration: str, winners: int, prize: str, description: str = ""):
    ch = bot.get_channel(C_GIVEAWAY)
    embed = discord.Embed(title=f"🎉 {prize}", description=f"{description}\n\nClique sur 🎉 pour participer\nFin dans {duration}\n{winners} gagnant(s)", color=0x0099ff)
    msg = await ch.send("@everyone", embed=embed)
    await msg.add_reaction("🎉")
    await interaction.response.send_message("Giveaway lancé!", ephemeral=True)

# --- 6. TICKETS ---
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True), guild.me: discord.PermissionOverwrite(view_channel=True)}
        channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
        await channel.send(f"{interaction.user.mention} explique ton problème, le staff arrive!")
        await interaction.response.send_message(f"Ticket créé {channel.mention}", ephemeral=True)

@bot.tree.command(name="setup_ticket", description="Poster le message ticket")
async def setup_ticket(interaction: discord.Interaction):
    ch = bot.get_channel(C_TICKET)
    embed = discord.Embed(title="Besoin d'aide? Ouvre un ticket et l'équipe vous répondra dans un salon privé!", description="**Comment ouvrir une demande?**\n1. Click sur 'ouvrir un ticket'\n2. Entrez les détails sur la raison de l'ouverture de votre ticket.", color=0x0099ff)
    await ch.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Fait", ephemeral=True)

# --- 1. YOUTUBE AUTO ---
last_video = None
@tasks.loop(minutes=5)
async def check_youtube():
    global last_video
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(YT_RSS) as r:
                text = await r.text()
                if '<yt:videoId>' in text:
                    vid = text.split('<yt:videoId>')[1].split('</yt:videoId>')[0]
                    if vid!= last_video:
                        last_video = vid
                        ch = bot.get_channel(C_VIDEO)
                        if ch:
                            await ch.send(f"ho furios Vien de poster une nouvelle vidéo vas faire exploser les compteurs de like 🙌🤩 @everyone\nhttps://www.youtube.com/watch?v={vid}")
    except: pass

# --- 5. MAPS BRAWL API ---
@tasks.loop(hours=1)
async def check_brawl_maps():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.brawlapi.com/v1/maps") as r:
                data = await r.json()
                # Ici tu peux comparer avec ancienne map et poster
                # Pour l'exemple on poste si tu veux forcer
                pass
    except: pass

bot.run(TOKEN)

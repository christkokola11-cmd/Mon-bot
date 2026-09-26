import discord
from discord.ext import tasks, commands
import feedparser, re, requests, aiohttp, os, random, asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- IDS ---
C_FURIOS = 1373712170906423398 # YouTube + TikTok Furios
C_TICKET = 1374857163104583782
C_BRAWL = 1373714363533492346
C_MAPS = 1553100406081720350
C_GIVEAWAY = 1375998725016780964

YOUTUBE_HANDLE = "FuriosBS"
TIKTOK_USERNAME = "furiosbsofficiel"

YT_FURIOS_ID = None
YT_BRAWL_ID = None
last_yt_furios = None
last_yt_brawl = None
last_tiktok = None

def get_channel_id(handle):
    try:
        r = requests.get(f"https://www.youtube.com/@{handle}", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        m = re.search(r'"channelId":"(UC[^"]+)"', r.text)
        if m: return m.group(1)
    except: pass
    return None

# --- TICKETS ---
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, inter: discord.Interaction, button: discord.ui.Button):
        guild = inter.guild
        name = f"ticket-{inter.user.name}".lower()
        if discord.utils.get(guild.channels, name=name):
            await inter.response.send_message("Tu as déjà un ticket ouvert!", ephemeral=True); return
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True)}
        ch = await guild.create_text_channel(name, overwrites=overwrites)
        await inter.response.send_message(f"Ticket créé {ch.mention}", ephemeral=True)
        await ch.send(f"{inter.user.mention} Explique ton problème ici. Staff va arriver.\n`!close` pour fermer.")

@bot.command()
@commands.has_permissions(administrator=True)
async def ticketpanel(ctx):
    if ctx.channel.id!= C_TICKET: return
    embed = discord.Embed(title="Support FuriosBS", description="Besoin d'aide?\nClique sur le bouton pour ouvrir un ticket.", color=0x5865F2)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name:
        await ctx.send("Fermeture..."); await asyncio.sleep(2); await ctx.channel.delete()

# --- AUTO CHECK YOUTUBE ---
@tasks.loop(minutes=5)
async def check_youtube():
    global last_yt_furios, last_yt_brawl
    # FuriosBS
    if YT_FURIOS_ID:
        try:
            feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_FURIOS_ID}")
            if feed.entries:
                v = feed.entries[0]
                if last_yt_furios and v.yt_videoid!= last_yt_furios:
                    ch = bot.get_channel(C_FURIOS)
                    if ch: await ch.send(f"@everyone 🎬 **Nouvelle vidéo YouTube Furios!**\n**{v.title}**\n{v.link}")
                last_yt_furios = v.yt_videoid
        except: pass
    # Brawl Stars
    if YT_BRAWL_ID:
        try:
            feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_BRAWL_ID}")
            if feed.entries:
                v = feed.entries[0]
                if last_yt_brawl and v.yt_videoid!= last_yt_brawl:
                    ch = bot.get_channel(C_BRAWL)
                    if ch:
                        embed = discord.Embed(title="💥 Nouveau Brawl Talk / MAJ!", description=v.title, color=0xFFD700, url=v.link)
                        if hasattr(v, 'media_thumbnail'): embed.set_image(url=v.media_thumbnail[0]['url'])
                        await ch.send(f"@everyone Nouvelle vidéo Brawl Stars! 🚀\n{v.link}", embed=embed)
                last_yt_brawl = v.yt_videoid
        except: pass

@tasks.loop(minutes=5)
async def check_tiktok():
    global last_tiktok
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.tikwm.com/api/user/posts?unique_id={TIKTOK_USERNAME}&count=1", timeout=10) as r:
                d = await r.json()
                vids = d.get('data',{}).get('videos',[])
                if not vids: return
                vid_id = vids[0]['video_id']
                if last_tiktok and vid_id!= last_tiktok:
                    ch = bot.get_channel(C_FURIOS)
                    if ch: await ch.send(f"@everyone 🔥 **Nouveau TikTok Furios!**\nhttps://www.tiktok.com/@{TIKTOK_USERNAME}/video/{vid_id}")
                last_tiktok = vid_id
    except: pass

@bot.command()
async def map(ctx, *, nom: str = None):
    if not nom: await ctx.send("Usage: `!map NomDeLaMap` + image"); return
    ch = bot.get_channel(C_MAPS)
    embed = discord.Embed(title=f"🗺️ {nom}", description=f"Par {ctx.author.mention}", color=0x00FF00)
    if ctx.message.attachments: embed.set_image(url=ctx.message.attachments[0].url)
    if ch: await ch.send(embed=embed)
    await ctx.send("Map postée!")

@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx, duree: int = 60, *, prix: str = "Prix mystère"):
    ch = bot.get_channel(C_GIVEAWAY) or ctx.channel
    embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"**Prix: {prix}**\nRéagis 🎉 pour participer!\nFin dans {duree} min", color=0xFF00FF)
    msg = await ch.send(embed=embed)
    await msg.add_reaction("🎉")
    await ctx.send(f"Giveaway lancé dans {ch.mention}")
    await asyncio.sleep(duree*60)
    msg = await ch.fetch_message(msg.id)
    users = [u async for u in msg.reactions[0].users() if not u.bot]
    if users: await ch.send(f"🎉 Bravo {random.choice(users).mention} tu gagnes **{prix}**!")
    else: await ch.send("Personne n'a participé...")

@bot.event
async def on_ready():
    global YT_FURIOS_ID, YT_BRAWL_ID, last_yt_furios, last_yt_brawl, last_tiktok
    print(f"Bot: {bot.user}")
    bot.add_view(TicketView())
    YT_FURIOS_ID = get_channel_id(YOUTUBE_HANDLE)
    YT_BRAWL_ID = get_channel_id("BrawlStars")
    print(f"Furios ID: {YT_FURIOS_ID} | Brawl ID: {YT_BRAWL_ID}")
    try:
        f = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_FURIOS_ID}")
        if f.entries: last_yt_furios = f.entries[0].yt_videoid
        f2 = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={YT_BRAWL_ID}")
        if f2.entries: last_yt_brawl = f2.entries[0].yt_videoid
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://www.tikwm.com/api/user/posts?unique_id={TIKTOK_USERNAME}&count=1") as r:
                d = await r.json()
                last_tiktok = d['data']['videos'][0]['video_id']
    except: pass
    if not check_youtube.is_running(): check_youtube.start()
    if not check_tiktok.is_running(): check_tiktok.start()

from flask import Flask
from threading import Thread
app = Flask('')
@app.route('/')
def home(): return "Bot Furios OK"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

bot.run(os.getenv("TOKEN"))

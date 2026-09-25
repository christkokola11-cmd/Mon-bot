import discord
from discord.ext import commands, tasks
import os, asyncio, aiohttp, random, re
from flask import Flask
from threading import Thread

# --- CONFIG BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

SALON_YOUTUBE = 1373712170906423398
YOUTUBE_HANDLE = "@FuriosBS"
dernier_yt = ""
dernieres_maps = {}
derniere_maj_info = ""

# --- FONCTIONS SALONS ---
def find_channel(guild, mots):
    for c in guild.text_channels:
        for m in mots:
            if m in c.name.lower():
                return c
    return None

def get_bienvenue(g): return find_channel(g, ["bienvenue"]) or g.system_channel
def get_aurevoir(g): return find_channel(g, ["au-revoir"]) or get_bienvenue(g)
def get_mape(g): return find_channel(g, ["info-mape"]) or find_channel(g, ["commande"])
def get_infos(g): return find_channel(g, ["informations"])
def get_videos(g): return find_channel(g, ["vidéos-abonnes", "videos-abonnes"]) or bot.get_channel(SALON_YOUTUBE)

def is_commande_channel():
    async def predicate(ctx):
        if "ticket-" in ctx.channel.name: return True
        if "commande" in ctx.channel.name.lower(): return True
        cmd = find_channel(ctx.guild, ["commande"])
        await ctx.send(f"❌ {ctx.author.mention} Va dans {cmd.mention if cmd else '#COMMANDE'}!", delete_after=5)
        try: await ctx.message.delete()
        except: pass
        return False
    return commands.check(predicate)

@bot.event
async def on_member_join(member):
    ch=get_bienvenue(member.guild)
    if not ch: return
    embed=discord.Embed(title=f"Bienvenue {member.name}! 🎉", description=f"Yo {member.mention}! Tu es le {member.guild.member_count}ème! 🔥", color=0x00FF00)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ch.send(f"{member.mention}", embed=embed)

@bot.event
async def on_member_remove(member):
    ch=get_aurevoir(member.guild)
    if not ch: return
    embed=discord.Embed(title=f"{member.name} a quitté 😢", description=f"On est plus que {member.guild.member_count}", color=0xFF0000)
    await ch.send(embed=embed)

# --- CHECK MAPS AVEC PHOTO -> #info-mape ---
@tasks.loop(minutes=30)
async def check_maps_brawl():
    global dernieres_maps
    for guild in bot.guilds:
        channel = get_mape(guild)
        if not channel: continue
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://api.brawlapi.com/v1/events") as r:
                    data = await r.json()
                    for ev in data.get("active", [])[:6]:
                        map_name = ev.get("map", {}).get("name")
                        map_image = ev.get("map", {}).get("imageUrl")
                        mode_name = ev.get("event", {}).get("name", "Event")
                        mode_key = ev.get("event", {}).get("id", mode_name)
                        if not map_name or not map_image: continue
                        if mode_key not in dernieres_maps:
                            dernieres_maps[mode_key]=map_name
                        elif dernieres_maps[mode_key]!=map_name:
                            ancien = dernieres_maps[mode_key]
                            dernieres_maps[mode_key]=map_name
                            embed=discord.Embed(title=f"🗺️ MAP CHANGÉE - {mode_name}!", description=f"Ancienne: `{ancien}`\nNouvelle: `{map_name}`", color=0xFF6B00)
                            embed.set_image(url=map_image)
                            await channel.send(content="@everyone Nouvelle map!", embed=embed)
        except: pass

# --- CHECK MAJ -> #INFORMATIONS ---
@tasks.loop(minutes=30)
async def check_brawl_updates():
    global derniere_maj_info
    for guild in bot.guilds:
        channel=get_infos(guild)
        if not channel: continue
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get("https://supercell.com/en/games/brawlstars/blog/", headers={"User-Agent":"Mozilla/5.0"}) as r:
                    html=await r.text()
                    m=re.search(r'<a[^>]*href="([^"]*brawlstars[^"]*)"[^>]*>([^<]*Update[^<]*|[^<]*Patch[^<]*)</a>', html, re.IGNORECASE)
                    if m:
                        link=m.group(1)
                        titre=m.group(2).strip()[:120]
                        if not link.startswith("http"): link="https://supercell.com"+link
                        if derniere_maj_info=="" : derniere_maj_info=titre
                        elif titre!=derniere_maj_info:
                            derniere_maj_info=titre
                            embed=discord.Embed(title="⭐ NOUVELLE MAJ BRAWL STARS!", description=f"**{titre}**\n\n{link}", color=0xFFD700)
                            await channel.send(content="@everyone 📢 MAJ BRAWL STARS!", embed=embed)
        except: pass

@tasks.loop(minutes=3)
async def check_videos():
    global dernier_yt
    for guild in bot.guilds:
        channel=get_videos(guild)
        if not channel: continue
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"https://www.youtube.com/{YOUTUBE_HANDLE}/videos", headers={"User-Agent":"Mozilla/5.0"}) as r:
                    html=await r.text()
                    if '"channelId":"' in html:
                        cid=html.split('"channelId":"')[1].split('"')[0]
                        async with s.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}") as r2:
                            xml=await r2.text()
                            if "<yt:videoId>" in xml:
                                vid=xml.split("<yt:videoId>")[1].split("</yt:videoId>")[0]
                                if dernier_yt=="": dernier_yt=vid
                                elif vid!=dernier_yt:
                                    dernier_yt=vid
                                    await channel.send(f"🎬 **NOUVELLE VIDÉO!** @everyone\nhttps://www.youtube.com/watch?v={vid}")
        except: pass

class GiveawayView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None); self.participants=set()
    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.success, custom_id="join_gw")
    async def join(self, interaction, button):
        if interaction.user.id in self.participants:
            await interaction.response.send_message("Déjà inscrit!", ephemeral=True)
        else:
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("✅ Inscrit!", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction, button):
        guild=interaction.guild
        if discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}"):
            await interaction.response.send_message("Déjà ouvert!", ephemeral=True); return
        overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        for r in guild.roles:
            if r.permissions.manage_messages: overwrites[r]=discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch=await guild.create_text_channel(f"🎫・ticket-{interaction.user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ {ch.mention}", ephemeral=True)
        await ch.send(f"{interaction.user.mention} Explique! `!close` pour fermer.")

@bot.event
async def on_ready():
    print(f"✅ FURIOS BOT EN LIGNE: {bot.user}")
    bot.add_view(TicketView())
    bot.add_view(GiveawayView())
    check_videos.start()
    check_maps_brawl.start()
    check_brawl_updates.start()

@bot.command()
@is_commande_channel()
async def ticket(ctx):
    embed=discord.Embed(title="🎫 Support", description="Clique pour ouvrir un ticket!", color=0x5865F2)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
@is_commande_channel()
async def giveaway(ctx, temps: int, *, prix):
    view=GiveawayView()
    embed=discord.Embed(title="🎁 GIVEAWAY!", description=f"Prix: {prix} - Fin dans {temps}min!", color=0xFFD700)
    await ctx.send(embed=embed, view=view)
    await asyncio.sleep(temps*60)
    if view.participants:
        gagnant=random.choice(list(view.participants))
        await ctx.send(f"🎉 Gagnant: <@{gagnant}> @everyone")

@bot.command()
async def close(ctx):
    if "ticket-" in ctx.channel.name:
        await ctx.channel.delete()

@bot.command()
@is_commande_channel()
async def test(ctx):
    await ctx.send("✅ FURIOS-BOT OK! Maps avec photo + MAJ + YouTube actifs!")

@bot.command()
@is_commande_channel()
async def helpfurios(ctx):
    embed=discord.Embed(title="🤖 COMMANDES FURIOS", color=0x5865F2)
    embed.add_field(name="AUTO", value="YouTube -> #VIDÉOS\nMaps + photo -> #info-mape\nMAJ -> #INFORMATIONS", inline=False)
    await ctx.send(embed=embed)

app=Flask('')
@app.route('/')
def home(): return "FURIOS BOT EN LIGNE!"
def run(): app.run(host='0.0.0.0',port=8080)
def keep_alive(): Thread(target=run).start()
keep_alive()
bot.run(os.getenv("TOKEN"))

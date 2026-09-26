import discord, json, os, random, asyncio
from discord.ext import commands, tasks
from io import BytesIO
import aiohttp
from PIL import Image, ImageDraw
import datetime

intents=discord.Intents.all()
bot=commands.Bot(command_prefix="!",intents=intents)

# --- TES SALONS ---
C_VIDEO=1373712170906423398
C_WELCOME=1373558403712028773
C_LEAVE=1374432105420947576
C_BRAWL=1373714363533492346
C_MAPS=1553100406081720350
C_TICKET=1439017706010574859
C_LVL=1373739207394070728
C_INFOXP=1373739539012649050
C_GIVEXP=1373803141899751444
C_GIVE=1375998725016780964

DB="levels.json"
def load():
 try: return json.load(open(DB))
 except: return {}
def save(d): json.dump(d,open(DB,"w"))
def getxp(uid): return load().get(str(uid),{"xp":0,"lv":0})
def addxp(uid,x):
 d=load();s=str(uid);u=d.get(s,{"xp":0,"lv":0})
 u["xp"]+=x;nl=int(u["xp"]**0.5//10)
 if u["xp"]>=100 and u["lv"]==0: nl=1
 if u["lv"]<nl: u["lv"]=nl
 d[s]=u;save(d);return u["lv"]

# --- TICKET ---
class TicketView(discord.ui.View):
 def __init__(self): super().__init__(timeout=None)
 @discord.ui.button(label="🎫 Ouvrir un ticket",style=discord.ButtonStyle.green,custom_id="open_ticket")
 async def open(self,inter,btn):
  guild=inter.guild
  overwrites={guild.default_role:discord.PermissionOverwrite(view_channel=False),inter.user:discord.PermissionOverwrite(view_channel=True,send_messages=True),guild.me:discord.PermissionOverwrite(view_channel=True)}
  ch=await guild.create_text_channel(f"ticket-{inter.user.name}",overwrites=overwrites)
  await ch.send(f"{inter.user.mention} l'équipe arrive!")
  await inter.response.send_message(f"Ticket ouvert {ch.mention}",ephemeral=True)

# --- GIVEAWAY ---
class GiveView(discord.ui.View):
 def __init__(self): super().__init__(timeout=None);self.users=set()
 @discord.ui.button(label="🎉 Participer",style=discord.ButtonStyle.blurple,custom_id="join_give")
 async def join(self,inter,btn):
  self.users.add(inter.user.id)
  await inter.response.send_message("Tu participes!",ephemeral=True)

@bot.event
async def on_ready():
 print("Furios Bot ON")
 bot.add_view(TicketView())
 bot.add_view(GiveView())

# --- BIENVENUE ---
@bot.event
async def on_member_join(m):
 ch=bot.get_channel(C_WELCOME)
 if ch:
  cnt=m.guild.member_count
  msg=f"Ho un nouveau membre\n\n🎣 Salut {m.mention} 🙌 bienvenue dans la team de furios!\n➡️ici:\n>> Amuse toi 🤩\n>> Chill un max 🥳\n>> Nous sommes desormais {cnt}\n🥰 N'hesite pas a te rename avec {{FXR}} pour soutenir Furios\nPour bien commencer va voir le <#{1367568068343234701}> reglement"
  await ch.send(msg)

@bot.event
async def on_member_remove(m):
 ch=bot.get_channel(C_LEAVE)
 if ch: await ch.send(f"😢 {m.name} a quitte le serveur. On t'oubliera pas!")

# --- XP SYSTEM ---
@bot.event
async def on_message(m):
 if m.author.bot: return
 if m.content.startswith("!"):
  await bot.process_commands(m);return
 old=getxp(m.author.id)["lv"]
 new=addxp(m.author.id,random.randint(15,25))
 if new>old and new>=1:
  ch=bot.get_channel(C_LVL) or m.channel
  await ch.send(f"{m.author.mention} vient de passer niveau {new}! 🔥")
 await bot.process_commands(m)

@bot.command()
async def rank(ctx):
 u=getxp(ctx.author.id)
 await ctx.send(f"{ctx.author.mention} Niv {u['lv']} | {u['xp']} XP")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def givexp(ctx,member:discord.Member,x:int):
 addxp(member.id,x)
 await ctx.send(f"{x} XP ajoute a {member.mention}")

# --- TICKET SETUP ---
@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx):
 ch=bot.get_channel(C_TICKET)
 embed=discord.Embed(title="Besoin d'aide?",description="Ouvre un ticket et l'equipe vous repondra dans un salon prive!\n\nComment ouvrir une demande?\n1. Click sur 'ouvrir un ticket'\n2. Entrez les details\n🎫 Ouvrir un ticket\n📖 Formulaire",color=0x00ff00)
 await ch.send(embed=embed,view=TicketView())
 await ctx.send("Ticket setup OK")

# --- YOUTUBE / TIKTOK ---
@bot.command()
@commands.has_permissions(administrator=True)
async def yt(ctx,link:str):
 ch=bot.get_channel(C_VIDEO)
 if ch:
  await ch.send(f"ho furios Vien de poster une nouvelle video vas faire exploser les compteurs de like 🙌🤩 @everyone\n{link}")

# --- GIVEAWAY ---
@bot.command()
@commands.has_permissions(administrator=True)
async def giveaway(ctx,*,args):
 # usage:!giveaway Nom | 1 | 2h
 try:
  parts=args.split("|");name=parts[0].strip();winners=int(parts[1].strip().split()[0]);time_str=parts[2].strip()
  seconds=0
  if "m" in time_str: seconds=int(time_str.replace("m",""))*60
  elif "h" in time_str: seconds=int(time_str.replace("h",""))*3600
  elif "j" in time_str: seconds=int(time_str.replace("j",""))*86400
  else: seconds=3600
  ch=bot.get_channel(C_GIVE)
  view=GiveView()
  embed=discord.Embed(title=f"🎉 GIVEAWAY: {name}",description=f"Gagnants: {winners}\nFin dans: {time_str}\nClique sur 🎉 pour participer!",color=0xff00ff)
  msg=await ch.send(embed=embed,view=view)
  await ctx.send("Giveaway lance!")
  await asyncio.sleep(seconds)
  if view.users:
   win=random.sample(list(view.users),min(winners,len(view.users)))
   mentions=" ".join([f"<@{i}>" for i in win])
   await ch.send(f"🎉 Fin du giveaway {name}! Bravo {mentions}")
  else: await ch.send("Personne n'a participe 😢")
 except Exception as e: await ctx.send(f"Erreur format. Fais:!giveaway Nom | 1 | 2h | Error {e}")

# --- DRAFBOT COMMANDS ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx,n:int=5): await ctx.channel.purge(limit=n+1)
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx,member:discord.Member,*,r=""): await member.ban(reason=r);await ctx.send(f"{member} ban")
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx,member:discord.Member,*,r=""): await member.kick(reason=r);await ctx.send(f"{member} kick")
@bot.command()
@commands.has_permissions(administrator=True)
async def say(ctx,*,txt): await ctx.send(txt)

bot.run(os.getenv("TOKEN"))

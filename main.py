import discord,os,asyncio,aiohttp,random,io
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands,tasks
from flask import Flask
from threading import Thread
intents=discord.Intents.default()
intents.message_content=True
intents.members=True
bot=commands.Bot(command_prefix="!",intents=intents)
V=1373712170906423398
B=1373558403712028773
A=1374432105420947576
I=1373714363533492346
M=1553100406081720350
T=1439017706010574859
L=1373739207394070728
YH="@FuriosBS"
TH="@furiosbsofficiel"
ly="";lt="";lm={};lb="";xp={}
def gx(u):
 return xp.get(str(u),{"xp":0,"lv":0})
def ax(u,a):
 d=gx(u)
 d["xp"]+=a
 l=int((d["xp"]/100)**0.5)
 d["lv"]=l
 xp[str(u)]=d
 return l
 async def make_level_card(avatar_url, level):
    W, H = 900, 350
    bg = Image.new("RGB", (W, H), (10, 20, 55))
    draw = ImageDraw.Draw(bg, "RGBA")
    for y in range(H):
        alpha = y / H
        r = int(10 + alpha*30); g = int(20 + alpha*50); b = int(80 + alpha*90)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    for _ in range(30):
        x,y = random.randint(0,W), random.randint(0,H)
        s = random.randint(1,3)
        draw.ellipse((x,y,x+s,y+s), fill=(100,160,255, random.randint(30,120)))
    card = Image.new("RGBA", (W,H), (0,0,0,0))
    c_draw = ImageDraw.Draw(card)
    c_draw.rounded_rectangle([(0,0),(W,H)], radius=35, fill=(8,18,50,230), outline=(60,110,255,180), width=2)
    bg = Image.alpha_composite(bg.convert("RGBA"), card)
    draw = ImageDraw.Draw(bg)
    async with aiohttp.ClientSession() as s:
        async with s.get(str(avatar_url)) as r:
            av_data = await r.read()
    av = Image.open(io.BytesIO(av_data)).convert("RGBA").resize((180,180))
    mask = Image.new("L", (180,180), 0)
    ImageDraw.Draw(mask).ellipse((0,0,180,180), fill=255)
    av_bg = Image.new("RGBA", (194,194), (255,255,255,255))
    av_bg_mask = Image.new("L", (194,194), 0)
    ImageDraw.Draw(av_bg_mask).ellipse((0,0,194,194), fill=255)
    bg.paste(av_bg, (58, 78), av_bg_mask)
    bg.paste(av, (65, 85), mask)
    f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
    f_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    f_bot = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
    draw.text((290, 85), "Félicitations !", fill="white", font=f_big)
    draw.text((290, 165), f"vous avez atteint le niveau {level}", fill=(220,230,255), font=f_small)
    draw.rounded_rectangle([(290,230),(330,270)], radius=8, fill=(63,85,212))
    draw.text((298, 234), "F", fill="white", font=f_bot)
    draw.text((340, 236), "Furios Bot", fill=(124,158,255), font=f_bot)
    out = io.BytesIO()
    bg.save(out, format="PNG")
    out.seek(0)
    return out                                                      
@bot.event
async def on_ready():
 print("ONLINE")
 bot.add_view(TV())
 bot.add_view(GV())
 cv.start()
 ct.start()
 cm.start()
 cb.start()
@bot.event
async def on_message(m):
  if m.author.bot:
    return
  old=gx(m.author.id)["lv"]
  new=ax(m.author.id, random.randint(15,25))
    if new>old and new>=1:
    try:
      lvl_channel = bot.get_channel(LEVEL_CHANNEL_ID)
      if lvl_channel is None:
        lvl_channel = m.channel
      card_file = await make_level_card(m.author.display_avatar.url, new)
      await lvl_channel.send(
        content=f"{m.author.mention} , vous venez de passer au niveau {new} !",
        file=discord.File(card_file, filename="level.png")
      )
    except Exception as e:
      print(f"Erreur level up: {e}")
    except Exception as e:
      print(e)
      e1=discord.Embed(description=f"{m.author.mention} niveau {new} !", color=0x2b2d31)
      await m.channel.send(embed=e1)
  await bot.process_commands(m)
@bot.event
async def on_member_join(mm):
 ch=bot.get_channel(B)
 if ch:
  e=discord.Embed(title="Ho un nouveau membre")
  e.description=f"🎣 Salut {mm.mention} bienvenue! Nous sommes {mm.guild.member_count} avec {{FXR}}"
  await ch.send(embed=e)
@bot.event
async def on_member_remove(mm):
 ch=bot.get_channel(A)
 if ch:
  await ch.send(f"{mm.name} a quitté")
@tasks.loop(minutes=3)
async def cv():
 global ly
 ch=bot.get_channel(V)
 try:
  async with aiohttp.ClientSession() as s:
   async with s.get(f"https://www.youtube.com/{YH}/videos",headers={"User-Agent":"Mozilla/5.0"}) as r:
    h=await r.text()
    if 'channelId' in h:
     cid=h.split('channelId":"')[1].split('"')[0]
     async with s.get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}") as r2:
      x=await r2.text()
      if "videoId" in x:
       v=x.split("videoId>")[1].split("<")[0]
       if ly=="":
        ly=v
       elif v!=ly:
        ly=v
        await ch.send(f"ho furios Vien de poster une nouvelle vidéo vas faire exploser les compteurs de like 🙌🤩 @everyone\nhttps://www.youtube.com/watch?v={v}")
 except:
  pass
@tasks.loop(minutes=5)
async def ct():
 global lt
 ch=bot.get_channel(V)
 try:
  async with aiohttp.ClientSession() as s:
   async with s.get(f"https://www.tiktok.com/{TH}",headers={"User-Agent":"Mozilla/5.0"}) as r:
    h=await r.text()
    m=re.search(r'"id":"(\d{19})"',h)
    if m:
     v=m.group(1)
     if lt=="":
      lt=v
     elif v!=lt:
      lt=v
      await ch.send(f"ho furios Vien de poster une nouvelle vidéo vas faire exploser les compteurs de like 🙌🤩 @everyone\nhttps://www.tiktok.com/{TH}/video/{v}")
 except:
  pass
@tasks.loop(minutes=10)
async def cm():
 global lm
 ch=bot.get_channel(M)
 try:
  async with aiohttp.ClientSession() as s:
   async with s.get("https://api.brawlapi.com/v1/events") as r:
    d=await r.json()
    for ev in d.get("active",[]):
     n=ev.get("map",{}).get("name")
     im=ev.get("map",{}).get("imageUrl")
     mo=ev.get("event",{}).get("name")
     mid=ev.get("event",{}).get("id")
     if not n or not im:
      continue
     if mid not in lm:
      lm[mid]=n
     elif lm[mid]!=n:
      lm[mid]=n
      e=discord.Embed(title=f"{mo} changé: {n}")
      e.set_image(url=im)
      await ch.send(f"@everyone {mo} : {n}",embed=e)
 except:
  pass
@tasks.loop(minutes=30)
async def cb():
 global lb
 ch=bot.get_channel(I)
 try:
  async with aiohttp.ClientSession() as s:
   async with s.get("https://api.brawlapi.com/v1/brawlers") as r:
    d=await r.json()
    cc=str(len(d.get("list",[])))
    if lb=="":
     lb=cc
    elif cc!=lb:
     lb=cc
     await ch.send("@everyone ⭐ MAJ BRAWL STARS!")
 except:
  pass
class TV(discord.ui.View):
 def __init__(self):
  super().__init__(timeout=None)
 @discord.ui.button(label="Ouvrir ticket",style=discord.ButtonStyle.primary,custom_id="ot3")
 async def o(self,i,b):
  g=i.guild
  ow={g.default_role:discord.PermissionOverwrite(view_channel=False),i.user:discord.PermissionOverwrite(view_channel=True),g.me:discord.PermissionOverwrite(view_channel=True)}
  ch=await g.create_text_channel(f"ticket-{i.user.name}",overwrites=ow)
  await i.response.send_message(f"✅ {ch.mention}",ephemeral=True)
class GV(discord.ui.View):
 def __init__(self):
  super().__init__(timeout=None)
  self.p=set()
 @discord.ui.button(label="Participer",style=discord.ButtonStyle.success,custom_id="gw3")
 async def j(self,i,b):
  self.p.add(i.user.id)
  await i.response.send_message("✅ Inscrit!",ephemeral=True)
@bot.command()
async def rank(ctx):
 d=gx(ctx.author.id)
 lvl=d['lv']
 xp=d['xp']
 need=int((lvl+1)**2*100)
 have=int(lvl**2*100)
 cur=xp-have
 maxxp=need-have if need-have>0 else 100
 pct=int(cur/maxxp*100) if maxxp>0 else 0
 b1=chr(9608)
 b2=chr(9617)
 p=int(pct//10)
 barre=b1*p+b2*(10-p)
 e=discord.Embed(title=f"{ctx.author.display_name}", description=f"**Niveau {lvl}**\n`{barre}` {pct}%\n{cur}/{maxxp} XP", color=0x2b2d31)
 e.set_thumbnail(url=ctx.author.display_avatar.url)
 e.set_footer(text=f"XP Total: {xp}")
 await ctx.send(embed=e)
@bot.command()
async def givexp(ctx,m:discord.Member,a:int):
 ax(m.id,a)
 await ctx.send(f"✅ {a} XP à {m.mention}")
@bot.command()
async def giveaway(ctx,temps:str,g:int,*,prix):
 v=GV()
 e=discord.Embed(title="GIVEAWAY",description=f"{prix} fin {temps}")
 await ctx.send(embed=e,view=v)
@bot.command()
async def ticketpanel(ctx):
 e=discord.Embed(title="Besoin d'aide? Ouvre un ticket!")
 await ctx.send(embed=e,view=TV())
@bot.command()
async def close(ctx):
 if "ticket-" in ctx.channel.name:
  await ctx.channel.delete()
app=Flask('')
@app.route('/')
def home():
 return "ON"
def run():
 app.run(host='0.0.0.0',port=8080)
Thread(target=run).start()
bot.run(os.getenv("TOKEN"))

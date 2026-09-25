import discord
import os
import aiohttp
import xml.etree.ElementTree as ET
from discord.ext import commands, tasks

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YOUTUBE_CHANNEL_ID = "UCxxxxxxxxxxxxxxxx"
SALON_ID = 123456789012345678

last_video_id = None

@bot.event
async def on_ready():
    print(f"Connecte: {bot.user}")
    check_youtube.start()

@tasks.loop(minutes=3)
async def check_youtube():
    global last_video_id
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.text()
                root = ET.fromstring(data)
                entry = root.find("{http://www.w3.org/2005/Atom}entry")
                if not entry: return
                video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
                title = entry.find("{http://www.w3.org/2005/Atom}title").text
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                if last_video_id is None:
                    last_video_id = video_id
                    return
                if video_id != last_video_id:
                    last_video_id = video_id
                    salon = bot.get_channel(SALON_ID)
                    if salon:
                        await salon.send(f"@everyone 🚀 **FuriosBS vient de sortir une nouvelle vidéo !**\n{video_url}\n**{title}** 🔥")
    except Exception as e:
        print(e)

bot.run(os.getenv("TOKEN"))

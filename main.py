# --- FIN DU BOT - NE PAS TOUCHER ---
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
    await ctx.send("✅ FURIOS-BOT OK! YouTube + Maps + MAJ actifs!")

# --- SERVEUR WEB POUR RENDER ---
app = Flask('')
@app.route('/')
def home():
    return "FURIOS BOT EN LIGNE!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()

# --- TOKEN - C'EST ICI ---
# Le token est caché dans Render, pas dans GitHub!
bot.run(os.getenv("TOKEN"))

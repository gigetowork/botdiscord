import os
import random
import json
import discord
from discord.ext import commands

# Initialisation du bot avec les commandes classiques
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_command="!", intents=intents)

# Chargement de tes objets personnalisés
with open('objets.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

@bot.event
async def on_ready():
    print(f"Le bot gacha {bot.user.name} est en ligne !")

@bot.command(name="roll")
async def roll(ctx):
    # Logique de tirage selon les raretés
    rarete_choisie = random.choices(
        list(data["probabilites"].keys()), 
        weights=list(data["probabilites"].values()), 
        k=1
    )[0]
    
    # Filtrer les objets de cette rareté
    objets_disponibles = [o for o in data["objets"] if o["rarete"] == rarete_choisie]
    
    if not objets_disponibles:
        await ctx.send("Erreur : Aucun objet configuré pour cette rareté.")
        return
        
    objet = random.choice(objets_disponibles)
    
    # Création d'un joli encadré Discord (Embed)
    embed = discord.Embed(
        title=f"🎉 TIRAGE REUSSI : {objet['nom']} !", 
        description=objet['description'], 
        color=0x00ff00 if objet['rarete'] == "Légendaire" else 0x0000ff
    )
    embed.add_field(name="Rareté", value=objet['rarete'], inline=True)
    embed.set_image(url=objet['image'])
    
    await ctx.send(embed=embed)

# Replit récupérera le Token Discord de manière sécurisée ici
bot.run(os.environ['DISCORD_TOKEN'])

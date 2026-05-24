import os
import random
import json
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType

# 1. CONFIGURATION DU BOT DISCORD
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. GESTION DES FICHIERS DE SAUVEGARDE LOCAUX
FICHIER_INVENTAIRES = "sauvegardes.json"
FICHIER_STOCKS = "stocks_serveur.json"

def charger_json(fichier, valeur_defaut):
    if not os.path.exists(fichier):
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(valeur_defaut, f, indent=4)
        return valeur_defaut
    with open(fichier, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return valeur_defaut

def sauvegarder_json(fichier, donnees):
    with open(fichier, 'w', encoding='utf-8') as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)

# Chargement initial des bases de données de suivi
inventaires = charger_json(FICHIER_INVENTAIRES, {})
stocks_serveur = charger_json(FICHIER_STOCKS, {})

# Chargement du catalogue de cartes (depuis ton GitHub)
def charger_catalogue():
    with open('cartes.json', 'r', encoding='utf-8') as f:
        return json.load(f)

@bot.event
async def on_ready():
    print(f"✨ Le bot Gacha Collectible {bot.user.name} est en ligne et ultra-personnalisé !")

# 3. COMMANDE DE TIRAGE (!roll) AVEC STOCKS LIMITÉS ET COOLDOWN
@bot.command(name="roll")
@commands.cooldown(1, 3600, commands.BucketType.user) # 1 fois toutes les 3600 secondes (1 heure)
async def roll(ctx):
    global inventaires, stocks_serveur
    data = charger_catalogue()
    user_id = str(ctx.author.id)
    
    # Étape A : Choisir une rareté selon tes probabilités
    raretes = list(data["probabilites"].keys())
    poids = list(data["probabilites"].values())
    
    # On va essayer de trouver une carte disponible (max 10 essais pour éviter les boucles infinies si tout est épuisé)
    carte_trouvee = None
    for _ in range(10):
        rarete_choisie = random.choices(raretes, weights=poids, k=1)[0]
        cartes_de_cette_rarete = [c for c in data["cartes"] if c["rarete"] == rarete_choisie]
        
        if not cartes_de_cette_rarete:
            continue
            
        carte_candidate = random.choice(cartes_de_cette_rarete)
        carte_id = carte_candidate["id"]
        stock_max = carte_candidate.get("stock_max", -1)
        stock_actuel = stocks_serveur.get(carte_id, 0)
        
        # Vérification du stock global sur le serveur
        if stock_max == -1 or stock_actuel < stock_max:
            carte_trouvee = carte_candidate
            break

    if not carte_trouvee:
        await ctx.send("⚠️ Mince ! Le destin a choisi une catégorie dont tous les stocks mondiaux sont épuisés sur le serveur. Réessaye !")
        ctx.command.reset_cooldown(ctx) # On annule le cooldown pour que le joueur puisse re-tester
        return

    # Étape B : Attribution de la carte et mise à jour des stocks
    carte_id = carte_trouvee["id"]
    
    # Mise à jour du stock serveur
    stocks_serveur[carte_id] = stocks_serveur.get(carte_id, 0) + 1
    sauvegarder_json(FICHIER_STOCKS, stocks_serveur)
    
    # Mise à jour de l'inventaire du joueur
    if user_id not in inventaires:
        inventaires[user_id] = {}
    inventaires[user_id][carte_id] = inventaires[user_id].get(carte_id, 0) + 1
    sauvegarder_json(FICHIER_INVENTAIRES, inventaires)

    # Étape C : Affichage de la carte dans un magnifique Embed Discord
    couleurs = {"Commun": 0x808080, "Rare": 0x00ff00, "Épique": 0x9400d3, "Légendaire": 0xffd700}
    couleur_embed = couleurs.get(carte_trouvee["rarete"], 0xffffff)
    
    embed = discord.Embed(
        title=f"🃏 {ctx.author.name} a obtenu une carte !",
        description=f"**{carte_trouvee['nom']}**\n*{carte_trouvee['description']}*",
        color=couleur_embed
    )
    embed.add_field(name="✨ Rareté", value=carte_trouvee["rarete"], inline=True)
    
    # Affichage du stock restant si la carte est limitée
    if carte_trouvee["stock_max"] != -1:
        restant = carte_trouvee["stock_max"] - stocks_serveur[carte_id]
        embed.add_field(name="📦 Exemplaires restants", value=f"{restant} / {carte_trouvee['stock_max']}", inline=True)
    else:
        embed.add_field(name="📦 Édition", value="Infinie", inline=True)
        
    if "image" in carte_trouvee and carte_trouvee["image"]:
        embed.set_image(url=carte_trouvee["image"])
        
    embed.set_footer(text=f"ID de la carte : {carte_id} | Tu pourras l'échanger grâce à cet ID !")
    await ctx.send(embed=embed)

# 4. GESTION DES ERREURS DE COOLDOWN (Pour afficher gentiment le temps restant)
@roll.error
async def roll_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        minutes_restantes = int(error.retry_after // 60)
        secondes_restantes = int(error.retry_after % 60)
        await ctx.send(f"⏱️ Pas si vite {ctx.author.mention} ! Tes potes se reposent. Tu pourras re-roll dans **{minutes_restantes} min et {secondes_restantes} s**.")

# Lancement du bot via ton secret Replit
bot.run(os.environ['DISCORD_TOKEN'])

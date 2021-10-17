# tactix-bot.py

import os
import json
import discord
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True # This allows us to see a list of members in guild.

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Save all rune data in an object
f = open('runes.json')
rune_data_raw = json.load(f) # this is a dict with 1 key-value pair
# key "runelist"; value is ALL rune info in a list of dicts
f.close()

rune_data = rune_data_raw["runelist"] # this is a list of dicts; 1 dict per rune

# Generate rune list
rune_list = []
for i in rune_data:
    rune_list.append(i["rune_name"])

#client = discord.Client()
bot = commands.Bot(command_prefix='!')

@bot.command()
async def test(ctx):
    await ctx.send("Test")

@bot.command()
async def runelist(ctx):
    s = ""
    for rune in rune_list:
        s += (rune + "\n")
    print("Done")
    await ctx.send(s)

@bot.command()
async def runeinfo(ctx, r):
    rune = r.capitalize() # 
    if rune not in rune_list:
        await ctx.send("That rune does not exist.")
    else:
        i = rune_list.index(rune)
        d = rune_data[i] # temporarily store the dict of info for this rune
        embed = build_rune_embed(rune, d) # construct embed
        await ctx.send(embed=embed)

def build_rune_embed(rune, data):
    # Create the rune embed object
    # rune - string, capitalized
    # data - list containing the rune information
    embed = discord.Embed(title=rune+" Rune", color=0x1c3818)
    url = "http://jameskennethnelson.com/discord_bot/tactix-bot/images/runes/"+rune+".PNG"
    print(url)
    embed.set_thumbnail(url=url)
    embed.add_field(name="Weapon Effect", value=data["weapon_effect"])
    embed.add_field(name="Armor Effect", value=data["armor_effect"])
    embed.add_field(name="Shield Effect", value=data["shield_effect"])
    embed.add_field(name="Character Level Required", \
        value=data["clvl_required"])
    embed.add_field(name="Previous Rune", value=data["upgrade_from"])
    embed.add_field(name="Next Rune", value=data["upgrade_to"])
    return embed

bot.run(TOKEN)
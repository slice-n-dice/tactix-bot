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
        s = ""
        s += ("__**" + rune + " Rune**__\n")
        s += ("**Weapon Effect:** " + d["weapon_effect"] + "\n")
        s += ("**Armor Effect:** " + d["armor_effect"] + "\n")
        s += ("**Shield Effect:** " + d["shield_effect"] + "\n")
        s += ("**Character Level Required:** " + d["clvl_required"] + "\n")
        s += (d["upgrade_from"] + "\n")
        s += (d["upgrade_to"] + "\n")
        await ctx.send(s)


#@client.event
#async def on_ready():
    #for guild in client.guilds:
    #    if guild.name == GUILD:
    #        print('Guild found!')

    #print(
    #    f'{client.user} is connected to the following guild:\n'
    #    f'{guild.name}(id: {guild.id})'
    #)

    #members = [member.name for member in guild.members]
    #print(members)
    #print(guild.members)

#@bot.event
#async def on_message(message):
#    if message.content.find("!hello") != -1:
#        await message.channel.send("Hi!")

def get_rune_number(rune):
    
    pass

bot.run(TOKEN)
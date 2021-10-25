# tactix-bot.py

import os
import random
import json
import discord
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True # This allows us to see a list of members in guild.

EMBED_COLOR = 0x1c3818

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Save all rune data in an object
f = open("runes.json")
rune_data_raw = json.load(f) # this is a dict with 1 key-value pair
# key "runelist"; value is ALL rune info in a list of dicts
f.close()

# Save all runeword data in an object
f = open("runewords.json")
runeword_data_raw = json.load(f) # this is a dict with 1 key-value pair
# key "runewords"; value is ALL runeword info in a list of dicts
f.close()

# Save all unique item data in an object
f = open("tools\\d2_uniques.json")
unique_data_raw = json.load(f) # this is a dict of many keys
# Each key is a different item category.
f.close()

rune_data = rune_data_raw["runelist"] # this is a list of dicts; 1 dict per rune
runeword_data = runeword_data_raw["runewords"] # list of dicts
unique_data = [] # list of dicts
for category in unique_data_raw:
    for d in unique_data_raw[category]:
        unique_data.append(d)

# Generate rune list
rune_list = []
for i in rune_data:
    rune_list.append(i["rune_name"])

# Generate runeword list
runeword_list = []
for i in runeword_data:
    runeword_list.append(i["name"].lower())

# Generate unique item list
unique_list = []
for i in unique_data:
    unique_list.append(i["Name"].lower())

bot = commands.Bot(command_prefix='!')

@bot.command()
async def about(ctx):
    '''Provides general information on this bot.'''
    embed = discord.Embed(title="TactiX-Bot", 
    url="https://github.com/slice-n-dice/tactix-bot",
    description="Created by tentacles for TactiX's War Room.",
    color=0x1c3818)
    url = "http://jameskennethnelson.com/discord_bot/tactix-bot/images/bot-avatar.png"
    embed.set_image(url=url)
    await ctx.send(embed=embed)

@bot.command()
async def github(ctx):
    '''Links to the bot resources on github.'''
    await ctx.send("https://github.com/slice-n-dice/tactix-bot")

@bot.command()
async def runelist(ctx):
    '''Prints the full Diablo 2 rune list.'''
    low_runes = rune_list[0:11]
    mid_runes = rune_list[11:22]
    high_runes = rune_list[22:]
    t = ", "
    s_low = t.join(low_runes)
    s_mid = t.join(mid_runes)
    s_high = t.join(high_runes)
    embed = discord.Embed(title="Rune List", color=EMBED_COLOR)
    embed.add_field(name="Low Runes", value=s_low)
    embed.add_field(name="Mid Runes", value=s_mid)
    embed.add_field(name="High Runes", value=s_high)
    random_rune = random.choice(rune_list)
    embed.set_footer(text="Use !runeinfo for more detail on any rune.\n" + \
        "Example: !runeinfo " + random_rune)
    await ctx.send(embed=embed)

@bot.command()
async def runeinfo(ctx, r):
    '''Prints information on the given Diablo 2 rune.'''
    rune = r.capitalize() # 
    if rune not in rune_list:
        await ctx.send("That rune does not exist.")
    else:
        i = rune_list.index(rune)
        d = rune_data[i] # temporarily store the dict of info for this rune
        embed = build_rune_embed(rune, d) # construct embed
        await ctx.send(embed=embed)

@bot.command()
async def runeword(ctx, *runeword):
    '''Prints information on the given Diablo 2 runeword.'''
    # Glue together the potentially multi-word argument
    r = " ".join(runeword)
    r = r.lower() # Match capitalization of runeword list object
    if r not in runeword_list:
        await ctx.send("That runeword does not exist.")
    else:
        i = runeword_list.index(r)
        d = runeword_data[i]
        embed = build_runeword_embed(r, d)
        await ctx.send(embed=embed)

@bot.command()
async def runesearch(ctx, rune):
    '''Returns a list of runewords that use the given rune.'''
    c_rune = rune.lower().capitalize()
    runeword_list = []
    for r in runeword_data:
        if c_rune in r["runes"]:
            t = clean_capitalize(r["name"])
            runeword_list.append(t)

    if not runeword_list:
        await ctx.send("Did not find any runewords. Are you sure you're searching " + \
            "for a valid rune? Use !runelist for a full list.")
        return

    embed = discord.Embed(title="Runewords With "+c_rune, color=EMBED_COLOR,
        description=", ".join(runeword_list))
    random_runeword = random.choice(runeword_list)
    embed.set_footer(text="Use !runeword for more info on any runeword.\n" + \
        "Example: !runeword " + random_runeword)
    await ctx.send(embed=embed)

@bot.command()
async def uniquename(ctx, *unique_name):
    '''Prints information on the provided unique item.'''
    u = " ".join(unique_name)
    u = u.lower() # Match capitalization of unique list object
    if u not in unique_list:
        await ctx.send("That unique item does not exist.")
    else:
        i = unique_list.index(u)
        d = unique_data[i]
        title = d["Name"]
        embed = discord.Embed(title=title, color=EMBED_COLOR)
        embed.add_field(name="Gear Type", value=d["Gear Type"])
        embed.add_field(name="Attributes", value=d["Attributes"], inline=False)
        await ctx.send(embed=embed)


def build_rune_embed(rune, data):
    '''Creates an embed object based on the given rune and its data.'''
    # rune - string, capitalized
    # data - list containing the rune information
    embed = discord.Embed(title=rune+" Rune", color=EMBED_COLOR)
    url = "http://jameskennethnelson.com/discord_bot/tactix-bot/images/runes/"+rune+".PNG"
    embed.set_thumbnail(url=url)
    embed.add_field(name="Weapon Effect", value=data["weapon_effect"])
    embed.add_field(name="Armor Effect", value=data["armor_effect"])
    embed.add_field(name="Shield Effect", value=data["shield_effect"])
    embed.add_field(name="Character Level Required", \
        value=data["clvl_required"])
    embed.add_field(name="Previous Rune", value=data["upgrade_from"])
    embed.add_field(name="Next Rune", value=data["upgrade_to"])
    return embed

def build_runeword_embed(runeword, data):
    '''Creates an embed object based on the given runeword and its data.'''
    # runeword - string, all words capitalized
    # data = list containing the runeword information
   
    title = clean_capitalize(runeword)
    embed = discord.Embed(title=title, color=EMBED_COLOR)
    runes = "".join(data["runes"])
    embed.add_field(name="Runeword", value=runes)
    gear = ", ".join(data["gear_types"])
    embed.add_field(name="Gear Types", value=gear)
    embed.add_field(name="Character Level Required", value=data["clvl"])
    attributes = "\n".join(data["attributes"])
    embed.add_field(name="Attributes", value=attributes, inline=False)
    return embed

def clean_capitalize(s):
    '''Returns a string where all words are capitalized.
    Letters immediately following symbols (like apostrophe) are NOT treated
    as new words, unlike the default python string.capitalize() function.'''
    t = [word.capitalize() for word in s.split()]
    return " ".join(t)

bot.run(TOKEN)
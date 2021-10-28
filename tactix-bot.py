# tactix-bot.py

import os
import random
import json
import requests
import discord
from discord.ext import tasks, commands
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv

load_dotenv()

EMBED_COLOR = 0x1c3818
TWITCH_NAME = "tactix11b"
TOKEN = os.getenv("DISCORD_TOKEN")
T_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
T_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("STREAM_ANNOUNCEMENT_CHANNEL_ID")
T_STREAM_API_ENDPOINT_V5 = "https://api.twitch.tv/kraken/streams/{}"
API_HEADERS = {
    "Client-ID": T_CLIENT_ID,
    "Accept": "application/vnd.twitchtv.v5+json"
}

intents = discord.Intents.default()
intents.members = True # This allows us to see a list of members in guild.
bot = commands.Bot(command_prefix='!', intents=intents)

# Authenticate with Twitch API.
twitch = Twitch(T_CLIENT_ID, T_CLIENT_SECRET)
twitch.authenticate_app([])

# Store state and functionality to communicate with Twitch.
class BotTwitchInterface(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announcement_sent = False
        self.channel = self.bot.get_channel(CHANNEL_ID)

    # When bot activates, set recurring loop to check tactix stream status
    @tasks.loop(seconds=180) # Check every 3 minutes whether stream is on
    async def live_notifs_loop(self):
        is_live = self.checkuser(TWITCH_NAME)
        if is_live and not self.announcement_sent:
            self.announcement_sent = True
            await self.channel.send(
                f"""TactiX just went live on Twitch!\n
                https://www.twitch.tv/{TWITCH_NAME}"""
            )
        elif self.announcement_sent and not is_live:
            self.announcement_sent = False

    # Wait until bot is ready before starting twitch checks
    @live_notifs_loop.before_loop
    async def before_live_notifs_loop(self):
        await self.bot.wait_until_ready()

    def checkuser(user):
        try:
            userid = twitch.get_users(logins=[user])["data"][0]["id"]
            url = T_STREAM_API_ENDPOINT_V5.format(userid)
            try:
                req = requests.Session().get(url, headers=API_HEADERS)
                jsondata = req.json()
                if "stream" in jsondata:
                    if jsondata["stream"] is not None:
                        return True
                    else:
                        return False
            except Exception as e:
                print("Error checking user: ", e)
                return False
        except IndexError:
            return False


bot.add_cog(BotTwitchInterface(bot))

# Save all rune data in an object
with open("runes.json") as f:
    rune_data_raw = json.load(f) # this is a dict with 1 key-value pair
    # key "runelist"; value is ALL rune info in a list of dicts

# Save all runeword data in an object
with open("runewords.json") as f:
    runeword_data_raw = json.load(f) # this is a dict with 1 key-value pair
    # key "runewords"; value is ALL runeword info in a list of dicts

# Save all unique item data in an object
with open(os.path.join("tools", "d2_uniques.json")) as f:
    unique_data_raw = json.load(f) # this is a dict of many keys
    # Each key is a different item category.

rune_data = rune_data_raw["runelist"] # this is a list of dicts; 1 dict per rune
runeword_data = runeword_data_raw["runewords"] # list of dicts
unique_data = [
    d for category in unique_data_raw for d in unique_data_raw[category]
    ] # list of dicts, each dict containing info on one unique item

rune_list = [r["rune_name"] for r in rune_data]
runeword_list = [r["name"].lower() for r in runeword_data]
unique_list = [u["Name"].lower() for u in unique_data]

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
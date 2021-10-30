# tactix-bot.py

import os
import random
import json
import requests
import discord
from discord.ext import tasks, commands
from twitchAPI.twitch import Twitch
from dotenv import load_dotenv, set_key

load_dotenv()

EMBED_COLOR = 0x1c3818
TWITCH_NAME = "tactix11b"
TOKEN = os.getenv("DISCORD_TOKEN")
T_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
T_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
GUILD_ID = os.getenv("GUILD_ID")
ANNOUNCEMENT_CHANNEL_ID = os.getenv("STREAM_ANNOUNCEMENT_CHANNEL_ID")
BOT_COMMAND_CHANNEL_ID = os.getenv("BOT_COMMAND_CHANNEL_ID")
T_STREAM_API_ENDPOINT_HELIX = "https://api.twitch.tv/helix/search/channels?query={}"

intents = discord.Intents.default()
intents.members = True # This allows us to see a list of members in guild.
bot = commands.Bot(command_prefix='!', intents=intents)

# Authenticate with Twitch API.
try:
    twitch = Twitch(T_CLIENT_ID, T_CLIENT_SECRET)
except Exception as e:
    print(e, "when creating Twitch object")

# Store state and functionality to communicate with Twitch.
class BotTwitchInterface(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announcement_sent = False
        self.channel = self.bot.get_channel(int(ANNOUNCEMENT_CHANNEL_ID))
        self.token = os.getenv("TWITCH_OAUTH_TOKEN")
        self.headers = {
            "Client-Id": T_CLIENT_ID,
            "Authorization": f"Bearer {self.token}"
        }
        self.live_notifs_loop.start()

    # When bot activates, set recurring loop to check tactix stream status
    @tasks.loop(seconds=180) # Check every 3 minutes whether stream is on
    async def live_notifs_loop(self):
        if self.channel is None:
            # if cog __init__ function ran before bot was done setting up,
            # then retry assigning self.channel.
            self.channel = self.bot.get_channel(int(ANNOUNCEMENT_CHANNEL_ID))
        stream_data = self.checkuser()
        is_live = stream_data["is_live"]
        if is_live and not self.announcement_sent:
            print("Streamer just went live!")
            self.announcement_sent = True
            embed = self.build_stream_embed(
                stream_data["game_name"],
                stream_data["title"]
                )
            await self.channel.send(embed=embed)
        elif self.announcement_sent and not is_live:
            print("Streamer just ended stream; resetting announcement flag.")
            self.announcement_sent = False

    # Wait until bot is ready before starting twitch checks
    @live_notifs_loop.before_loop
    async def before_live_notifs_loop(self):
        print("Waiting for bot to ready up before starting loops...")
        await self.bot.wait_until_ready()
    
    def checkuser(self):
        '''Use Twitch API to check whether streamer is live.
        This is run every loop.'''
        try:
                url = T_STREAM_API_ENDPOINT_HELIX.format(TWITCH_NAME)
                jsondata = self.get_request_json(url, self.headers)
                #print(json.dumps(jsondata, indent=4))
                try:
                    if "status" in jsondata and jsondata["status"] == 401: # OAuth expired
                        self.token = self.get_oauth_token()
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        jsondata = self.get_request_json(url, self.headers)
                    return self.get_stream_data(jsondata, TWITCH_NAME)
                except Exception as e:
                    print("Error checking user: ", e)
                    return
        except IndexError:
            print("Index error.")
            return
        except Exception as e:
            print(e)
            return
    
    @commands.command()
    async def checktwitch(self, ctx):
        '''Use Twitch API to check whether streamer is live.
        For debug purposes only.'''
        print("Running the check twitch command.")
        try:
                url = T_STREAM_API_ENDPOINT_HELIX.format(TWITCH_NAME)
                jsondata = self.get_request_json(url, self.headers)
                #print(json.dumps(jsondata, indent=4))
                try:
                    if "status" in jsondata and jsondata["status"] == 401: # OAuth expired
                        self.token = self.get_oauth_token()
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        jsondata = self.get_request_json(url, self.headers)
                    stream_data = self.get_stream_data(jsondata, TWITCH_NAME)
                    embed = self.build_stream_embed(
                        stream_data["game_name"],
                        stream_data["title"]
                        )
                    if stream_data["is_live"]:
                        await ctx.send(f"{TWITCH_NAME} is LIVE.", embed=embed)
                        return
                    else:
                        await ctx.send(f"{TWITCH_NAME} is NOT live.", embed=embed)
                        return
                except Exception as e:
                    print("Error checking user: ", e)
                    return
        except IndexError:
            print("Index error.")
            return
        except Exception as e:
            print(e)
            return

    def get_oauth_token(self):
        """Get new Twitch OAuth token using our global variable credentials.
        Also stores the OAuth token in the .env file."""
        url = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials"
        url = url.format(T_CLIENT_ID, T_CLIENT_SECRET)
        req = requests.Session().post(url)
        jsondata = req.json()
        new_token = jsondata["access_token"]
        set_key(".env", "TWITCH_OAUTH_TOKEN", new_token)
        return new_token

    def get_request_json(self, url, headers):
        """Sends a request to a (Twitch) URL with authentication headers.
        Returns the JSON sent back to us."""
        req = requests.Session().get(url, headers=headers)
        return req.json()

    def get_stream_data(self, jsondata, streamer):
        """Returns the dict containing the given streamer's data."""
        for stream_data in jsondata["data"]:
            if stream_data["display_name"] == streamer:
                return stream_data
        print(f"Error in get_stream_data: {streamer} data not found.")
        return None

    def build_stream_embed(self, game, title):
        """Returns a Twitch notification embed object."""
        url = f"https://www.twitch.tv/{TWITCH_NAME}"
        embed = discord.Embed(
            title=title,
            url=url,
            description=f"Now Playing: {game}\n\n[Watch Stream]({url})",
            color=EMBED_COLOR,
            )
        embed.set_author(
            name="🔴 TactiX just went live on Twitch!",
            url=url,
            icon_url="https://static-cdn.jtvnw.net/jtv_user_pictures/a252f218-198d-4746-8dd9-bc0b697896e7-profile_image-70x70.png"
        )
        return embed


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

print("Starting up bot.")
bot.run(TOKEN)
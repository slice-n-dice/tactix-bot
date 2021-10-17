# tactix-bot.py

import os
import discord
intents = discord.Intents.default()
intents.members = True # This allows us to see a list of members in guild.

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            print('Guild found!')

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    members = [member.name for member in guild.members]
    print(members)
    print(guild.members)

@client.event
async def on_message(message):
    if message.content.find("!hello") != -1:
        await message.channel.send("Hi!")

client.run(TOKEN)
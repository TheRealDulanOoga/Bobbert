import discord
from discord.ext import commands
import asyncio
import os
from discord import Activity, ActivityType

activity = Activity(name="!help", type=ActivityType.listening)
bot = commands.Bot(command_prefix='!', activity=activity,
                   intents=discord.Intents.all())

with open('token.txt', 'r') as file:
    token = file.readlines()[0]


async def load():
    bot.remove_command('help')
    for filename in os.listdir("./Code"):
        if filename.endswith(".py") and not filename.startswith("main"):
            await bot.load_extension(filename[:-3])


async def main():
    async with bot:
        await load()
        await bot.start(token)

asyncio.run(main())

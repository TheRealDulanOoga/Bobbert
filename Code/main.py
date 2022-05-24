import discord
from discord.ext import commands
from discord_components import ComponentsBot

from help_cog import help_cog
from music_cog import music_cog

bot = ComponentsBot(command_prefix='!')

bot.add_cog(music_cog(bot))

with open('token.txt', 'r') as file:
    token = file.read()
bot.run(token)

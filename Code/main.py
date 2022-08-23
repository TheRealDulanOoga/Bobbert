from discord_components import ComponentsBot
from discord import Activity, ActivityType
import os

from help_cog import help_cog
from music_cog import music_cog

activity = Activity(name="!help", type=ActivityType.listening)
bot = ComponentsBot(command_prefix='!', activity=activity)

bot.remove_command('help')

bot.add_cog(music_cog(bot))
bot.add_cog(help_cog(bot))

with open('token.txt', 'r') as file:
    token = file.readlines()[0]
bot.run(token)

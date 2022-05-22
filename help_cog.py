import discord
from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.initialMessage = """
`Hello there! I'm now online.
Type "!help" for general commands`
"""
        self.helpMessage = """
`General Commands:
!play - 
!resume - 
!pause - 
!queue -
!clear - 
!leave - 
!help - `
"""
        self.textChannelText = []

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                self.textChannelText.append(channel)

        await self.send_to_all(self.initialMessage)

    async def send_to_all(self, msg):
        for textChannel in self.textChannelText:
            await textChannel.send(msg)

    @commands.command(name="help", help="Displays all the available commands")
    async def help(self, ctx):
        await ctx.send(self.helpMessage)

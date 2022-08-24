import discord
import datetime
from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embedOrange = 0xeab148
        self.embedDarkPink = 0x7d3243

    def helloEmbedGen(self, name):
        embed = discord.Embed(
            title="Hello There!",
            description=f"""
            Hello, I'm {name}! You can type any command after typing my prefix **`'{self.bot.command_prefix}'`** to activate them. Use **`!help`** to see some command options.

            Here is a link to my [source code](https://github.com/TheRealDulanOoga/Bobbert.git) if you wanted to check it out!""",
            colour=self.embedOrange
        )
        return embed

    def errorEmbedGen(self, error):
        embed = discord.Embed(
            title="ERROR :(",
            description="There was an error. You can likely keep using the bot as is, or just to be safe, you can ask your server administrator to use !reboot to reboot the bot.\n\nError:\n**`" +
            str(error) + "`**",
            colour=self.embedDarkPink
        )
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        print(print("[" + datetime.time.now() + "] " + str(error)))
        await ctx.send(embed=self.errorEmbedGen(error))

    @ commands.Cog.listener()
    async def on_ready(self):
        sendToChannels = []
        botNames = {}
        for guild in self.bot.guilds:
            channel = guild.text_channels[0]
            sendToChannels.append(channel)
            botMember = await guild.fetch_member(975410595576840272)
            nickname = botMember.nick
            if nickname == None:
                nickname = botMember.name
            botNames[guild.id] = nickname
        for channel in sendToChannels:
            helloEmbed = self.helloEmbedGen(
                botNames[channel.guild.id])
            await channel.send(embed=helloEmbed)

    @ commands.command(
        name="help",
        aliases=["h"],
        help="""
            (command_name)
            Provides a description of all specified commands
            Gives a description of a specified command (optional). If no command is specified, then gives a less detailed description of all commands.
            """
    )
    async def help(self, ctx, arg=""):
        helpCog = self.bot.get_cog('help_cog')
        musicCog = self.bot.get_cog('music_cog')
        commands = helpCog.get_commands() + musicCog.get_commands()
        if arg != "":
            command = None
            for i, c in enumerate(commands):
                if c.name == arg:
                    command = commands[i]
            if command == None:
                await ctx.send("That is not a name of an available command.")
                return

            arguments = command.help.split("\n")[0]
            longHelp = command.help.split("\n")[2]
            aliases = ""
            for a in command.aliases:
                aliases += f"!{a}, "
            aliases = aliases.rstrip(", ")
            commandsEmbed = discord.Embed(
                title=f"!{command.name} Command Info",
                description=f"""
                Arguments: **`{arguments}`**
                {longHelp}

                Aliases: **`{aliases}`**
                """,
                colour=self.embedOrange
            )

        else:
            commandDescription = "**`!help (command)`** - Provides a description of all commands or a longer description of an inputted command\n\n"
            for c in commands:
                arguments = c.help.split("\n")[0]
                shortHelp = c.help.split("\n")[1]
                commandDescription += f"**`!{c.name} {arguments}`** - {shortHelp}\n"
            commandsEmbed = discord.Embed(
                title="Command List",
                description=commandDescription,
                colour=self.embedOrange
            )

        commandKey = """
            **`Command Prefix`** - '!'

            **`!command <>`** - No arguments required
            **`!command ()`** - Optional argument
            **`!command []`** - Required argument
            **`!command [arg]`** - 'arg' specifies argument type (eg. "url" or "keywords")
            **`!command (this || that)`** - Options between mutually exclusive inputs (this or that)
        """

        keyEmbed = discord.Embed(
            title="Key",
            description=commandKey,
            colour=self.embedOrange
        )
        await ctx.send(embed=commandsEmbed)
        await ctx.send(embed=keyEmbed)

    @ commands.command(
        name="reboot",
        aliases=["rb"],
        help="""
            <>
            Completely restarts the bot.
            Gives a complete restart of the bot. This will also update the [code from GitHub](https://github.com/TheRealDulanOoga/Bobbert.git). This command can only be called by the owner of the server.
            """
    )
    async def reboot(self, ctx):
        if ctx.message.author.guild_permissions.administrator:
            await ctx.send("Rebooting application now!")
            await self.bot.close()
        else:
            await ctx.send("You do not have proper permissions to reboot me.")

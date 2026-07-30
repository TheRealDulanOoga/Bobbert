import discord

# BLUE = 0x2c76dd
# RED = 0xdf1141
# GREEN = 0x0eaa51
# LGREEN = 0x40ec88
# DGREEN = 0x0a6820
# PINK = 0x7d3243

PLAYING = 0x35ace8
ADDED = 0xdb3b53
REMOVE = 0xb46fc7
QCURRENT = 0x31f564
QNEAR = 0x4da363
QFAR = 0x365e40


TITLE = False
LINK = False
THUMBNAIL = False
AUTHOR = False
AVATAR = False

def error(error):
    embed = discord.Embed(
        title="ERROR :(",
        description="There was an error. You can likely keep using the bot as is, or just to be safe, you can ask your server administrator to use !reboot to reboot the bot.\n\nError:\n**`" +
        str(error) + "`**",
        colour=REMOVE
    )
    return embed

def nowPlaying(ctx, song, index): #1
    embed = discord.Embed(
        title=f"({index}) Now Playing",
        description=f"[{song['title']}]({song['link']})",
        color=PLAYING
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def songAdded(ctx, song, index): #2
    embed = discord.Embed(
        title=f"({index}) Song Added To Queue!",
        description=f"[{song['title']}]({song['link']})",
        color=ADDED
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def songRemoved(ctx, song, index): #3
    embed = discord.Embed(
        title=f"({index}) Song Removed From Queue",
        description=f"[{song['title']}]({song['link']})",
        color=REMOVE
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def songInserted(ctx, song, index): #4
    embed = discord.Embed(
        title=f"({index}) Song Inserted Next In Queue!",
        description=f"[{song['title']}]({song['link']})",
        color=ADDED
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def queue(ctx, song, message, indexDiff):
    if abs(indexDiff) > 2: col = QFAR
    elif indexDiff == 0: col = QCURRENT
    else: col = QNEAR
    embed = discord.Embed(
        title=message,
        description=f"[{song['title']}]({song['link']})",
        color=col
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed
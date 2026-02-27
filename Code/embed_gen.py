import discord


BLUE = 0x2c76dd
RED = 0xdf1141
GREEN = 0x0eaa51
LGREEN = 0x40ec88
DGREEN = 0x0a6820
PINK = 0x7d3243

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
        colour=PINK
    )
    return embed

def nowPlaying(ctx, song, index): #1
    embed = discord.Embed(
        title=f"({index}) Now Playing",
        description=f"[{song['title']}]({song['link']})",
        color=BLUE
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
        color=RED
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def songRemoved(ctx, song, index): #3
    embed = discord.Embed(
        title=f"({index}) Song Removed From Queue!",
        description=f"[{song['title']}]({song['link']})",
        color=PINK
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
        color=RED
    )
    embed.set_thumbnail(url=song['thumbnail'])
    embed.set_footer(
        text=f"Song added by: {str(ctx.author)}",
        icon_url=ctx.author.avatar
    )
    return embed

def queue(ctx, song, message, indexDiff):
    if abs(indexDiff) > 2: col = LGREEN
    elif indexDiff == 0: col = DGREEN
    else: col = GREEN
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


# def valueAssignments(ctx, song):
#     global TITLE, LINK, THUMBNAIL, AUTHOR, AVATAR

#     TITLE = song['title']
#     LINK = song['link']
#     THUMBNAIL = song['thumbnail']
#     AUTHOR = ctx.author
#     AVATAR = AUTHOR.avatar

# def generalEmbed(color_, title_):
#     embed = discord.Embed(
#         title=title_,
#         description=f'[{TITLE}]({LINK})',
#         color=color_
#     )
#     embed.set_thumbnail(url=THUMBNAIL)
#     embed.set_footer(
#         text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
#     return embed

# def nowPlaying(ctx, song): #1
#     valueAssignments(ctx, song)
#     return generalEmbed("Now Playing", BLUE)

# def songAdded(ctx, song): #2
#     valueAssignments(ctx, song)
#     return generalEmbed("Song Added To Queue!", RED)

# def songRemoved(ctx, song): #3
#     valueAssignments(ctx, song)
#     return generalEmbed("Song AddeRemoved From Queue", RED)

# def songInserted(ctx, song): #4
#     valueAssignments(ctx, song)
#     return generalEmbed("Song Inserted Next In Queue!", RED)


# embed = discord.Embed(
#     title="Now Playing",
#     description=f'[{TITLE}]({LINK})',
#     colour=BLUE
# )
# embed.set_thumbnail(url=THUMBNAIL)
# embed.set_footer(
#     text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
# return embed

# embed = discord.Embed(
# title="Song Added To Queue!",
# description=f'[{TITLE}]({LINK})',
# colour=RED
# )
# embed.set_thumbnail(url=THUMBNAIL)
# embed.set_footer(
#     text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
# return embed

# embed = discord.Embed(
#     title="Song Removed From Queue",
#     description=f'[{TITLE}]({LINK})',
#     colour=RED
# )
# embed.set_thumbnail(url=THUMBNAIL)
# embed.set_footer(
#     text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)
# return embed

# embed = discord.Embed(
#     title="Song Inserted Next In Queue!",
#     description=f'[{TITLE}]({LINK})',
#     colour=RED
# )
# embed.set_thumbnail(url=THUMBNAIL)
# embed.set_footer(
#     text=f"Song inserted by: {str(AUTHOR)}", icon_url=AVATAR)
# return embed
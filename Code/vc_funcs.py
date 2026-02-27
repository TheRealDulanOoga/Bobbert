import discord
import asyncio
from yt_dlp import YoutubeDL
import embed_gen as embeds


bot = None
playing = {}
paused = {}
queue = {}
queueIndex = {}
nicknames = {}
vc = {}

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'no_warnings': True,
    'quiet': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


def init(id, nickname):
    queue[id] = []
    queueIndex[id] = 0
    playing[id] = False
    paused[id] = False
    nicknames[id] = nickname
    vc[id] = None


def extract_yt_info(query):
    print(f"Extracting information from YouTube for '{query}'")
    with YoutubeDL(YTDL_OPTIONS) as ydl: 
        info = ydl.extract_info(query, download=False)
    print("Extraction successful!\n")

    entries = info['entries'] if 'entries' in info else [info]
    entry = entries[0]
    return {
        'title': entry['title'],
        'link': entry['webpage_url'],
        'thumbnail': entry['thumbnail'],
        'stream_url': entry['url'],
    }


async def join(id, channel):
    if vc[id] is None or not vc[id].is_connected():
        vc[id] = await channel.connect()
    else:
        await vc[id].move_to(channel)


async def leave(id):
    playing[id] = False
    paused[id] = False
    queue[id] = []
    queueIndex[id] = 0
    if vc[id] != None:
        await vc[id].disconnect()
        vc[id] = None
        return True
    return False


async def resume(ctx):
    id = int(ctx.guild.id)
    playing[id] = True
    paused[id] = False
    vc[id].resume()
    await ctx.send("Audio resumed!")


async def start_playing(ctx):
    id = int(ctx.guild.id)

    if queueIndex[id] >= len(queue[id]):
        await ctx.send("There are no songs in the queue to be played.")
        playing[id] = False
        return

    print("start playing")
    QPOS = queue[id][queueIndex[id]]
    song = QPOS[0]
    channel = QPOS[1]

    playing[id] = True
    paused[id] = False
    await join(id, channel)
    await ctx.send(embed=embeds.nowPlaying(ctx, song, queueIndex[id] + 1))

    url = song['stream_url']
    ffmpeg_audio = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    def next_play_scheduler(error):
        if error: print("FFmpeg error:", error)
        asyncio.run_coroutine_threadsafe(continue_playing(ctx), bot.loop)

    vc[id].play(ffmpeg_audio, after=next_play_scheduler)


async def continue_playing(ctx):
    id = int(ctx.guild.id)
    queueIndex[id] += 1
    print(queue[id])

    if queueIndex[id] < len(queue[id]):
        print("continue playing")
        QPOS = queue[id][queueIndex[id]]
        song = QPOS[0]
        channel = QPOS[1]

        await join(id, channel)
        await ctx.send(embed=embeds.nowPlaying(ctx, song, queueIndex[id] + 1))

        ffmpeg_audio = discord.FFmpegPCMAudio(song['stream_url'], **FFMPEG_OPTIONS)

        def next_play_scheduler(error):
            if error: print("ffmpeg error:", error)
            asyncio.run_coroutine_threadsafe(continue_playing(ctx), bot.loop)

        vc[id].play(ffmpeg_audio, after=next_play_scheduler)
    elif playing[id] or paused[id]:
        print("end of queue")
        playing[id] = False
        paused[id] = False
        await ctx.send("The end of the queue has been reached.")
    else:
        queueIndex[id] = 0


async def jump(ctx, position):
    id = int(ctx.guild.id)
    length = len(queue[id])
    if vc[id] == None: return await ctx.send("I have to be connected to a voice channel to use this command.")
    elif position >= length or position < 0: await ctx.send("You tried to jump to a position that wasn't there. I'll replay the current song instead.")
    else: queueIndex[id] = position

    vc[id].pause()
    await start_playing(ctx)

# async def startPlaying(self, ctx):
#     id = int(ctx.guild.id)

#     if queueIndex[id] >= len(queue[id]):
#         await ctx.send("There are no songs in the queue to be played.")
#         playing[id] = False
#         return

#     QPOS = queue[id][queueIndex[id]]
#     song = QPOS[0]
#     channel = QPOS[1]

#     await join(ctx, channel)
#     playing[id] = True
#     paused[id] = False

#     await ctx.send(embed=embeds.nowPlaying(ctx, song))

#     ffmpeg_audio = discord.FFmpegPCMAudio(
#         song['stream_url'],  # <- extracted by yt-dlp
#         pipe=False,
#         **FFMPEG_OPTIONS
#     )

#     def after_playing(error):
#         if error:
#             print("FFmpeg error:", error)
#         loop = asyncio.get_event_loop()
#         loop.create_task(continuePlaying(self, ctx))

#     vc[id].play(ffmpeg_audio, after=lambda e: continuePlaying(self, ctx))

# async def continuePlaying(self, ctx):
#     id = int(ctx.guild.id)

#     if not playing[id]:
#         return

#     queueIndex[id] += 1

#     if queueIndex[id] < len(queue[id]):
#         QPOS = queue[id][queueIndex[id]]
#         song = QPOS[0]
#         channel = QPOS[1]

#         await join(ctx, channel)
#         await ctx.send(embed=embeds.nowPlaying(ctx, song))

#         ffmpeg_audio = discord.FFmpegPCMAudio(
#             song['stream_url'],  # <- extracted by yt-dlp
#             pipe=False,
#             **FFMPEG_OPTIONS
#         )

#         def after_playing(error):
#             if error:
#                 print("FFmpeg error:", error)
#             loop = asyncio.get_event_loop()
#             loop.create_task(continuePlaying(self, ctx))

#         vc[id].play(ffmpeg_audio, after=lambda e: continuePlaying(self, ctx))
#     else:
#         playing[id] = False
#         await ctx.send("Reached the end of the queue.")
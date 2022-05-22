from asyncio import run_coroutine_threadsafe
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
import urllib.parse
import urllib.request
import re

# TODO Add to GitHub repo
# TODO Make queue command list time left in audio
# TODO Make a search command
# TODO Add playlist mechanics

# TODO Load onto raspi


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.musicQueue = []
        self.queueIndex = 0
        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

    def generate_embed(self, ctx, song, type):
        TITLE = song['title']
        LINK = song['link']
        THUMBNAIL = song['thumbnail']
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar_url

        nowPlaying = discord.Embed(
            title="Now Playing",
            description=f'[{TITLE}]({LINK})',
            colour=discord.Colour.from_rgb(r=0, g=100, b=220)
        )
        nowPlaying.set_thumbnail(url=THUMBNAIL)
        nowPlaying.set_footer(
            text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)

        songAdded = discord.Embed(
            title="Song Added To Queue!",
            description=f'[{TITLE}]({LINK})',
            colour=discord.Colour.from_rgb(r=220, g=0, b=100)
        )
        songAdded.set_thumbnail(url=THUMBNAIL)
        songAdded.set_footer(
            text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)

        match type:
            case 1: return nowPlaying
            case 2: return songAdded

    async def join_VC(self, ctx, channel):
        if self.vc == None or not self.vc.is_connected():
            self.vc = await channel.connect()

            if self.vc == None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc.move_to(channel)

    def search_YT(self, search):
        queryString = urllib.parse.urlencode({'search_query': search})
        htmContent = urllib.request.urlopen(
            'http://www.youtube.com/results?' + queryString)
        searchResults = re.findall(
            '/watch\?v=(.{11})', htmContent.read().decode())
        return searchResults[0:10]

    def extract_YT(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.ytimg.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'source': info['formats'][0]['url'],
            'title': info['title']
        }

    def play_next(self, ctx):
        if self.queueIndex < len(self.musicQueue):
            print(self.queueIndex)
            self.queueIndex += 1
            self.is_playing = True

            song = self.musicQueue[self.queueIndex][0]
            message = self.generate_embed(ctx, song, 1)
            coro = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc.play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            print(self.queueIndex, len(self.musicQueue))
            self.is_playing = False

    async def play_music(self, ctx):
        if self.queueIndex < len(self.musicQueue):
            print(self.queueIndex)
            self.is_playing = True

            await self.join_VC(ctx, self.musicQueue[self.queueIndex][1])

            song = self.musicQueue[self.queueIndex][0]
            message = self.generate_embed(ctx, song, 1)
            await ctx.send(embed=message)

            self.vc.play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            print(self.queueIndex, len(self.musicQueue))
            self.is_playing = False

    # Play Command

    @ commands.command(name="play", aliases=["p", "playing"], help="Play a song from YouTube")
    async def play(self, ctx, *args):
        search = " ".join(args)

        userChannel = ctx.author.voice.channel
        if userChannel is None:
            await ctx.send("You must be connected to a voice channel.")
        elif not args:
            if self.is_paused:
                self.is_paused = False
                self.is_playing = True
                self.vc.resume()
            else:
                return
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
            else:
                self.musicQueue.append([song, userChannel])

                if self.is_playing == False:
                    await self.play_music(ctx)
                else:
                    message = self.generate_embed(ctx, song, 2)
                    await ctx.send(embed=message)

    # Add Command

    @ commands.command(name="add", aliases=["a"], help="Adds a song to the playlist")
    async def add(self, ctx, *args):
        search = " ".join(args)

        userChannel = ctx.author.voice.channel
        if userChannel is None:
            await ctx.send("You must be connected to a voice channel.")
        elif not args:
            await ctx.send("You need to specify a song to be added.")
            return
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
            else:
                self.musicQueue.append([song, userChannel])
                message = self.generate_embed(ctx, song, 2)
                await ctx.send(embed=message)

    # Pause Command

    @ commands.command(name="pause", aliases=["stop"], help="Pauses the current song being played")
    async def pause(self, ctx):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

    # Resume Command

    @ commands.command(name="resume", aliases=["r", "unpause"], help="Resumes the current song being played")
    async def resume(self, ctx):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    # Skip Command

    @ commands.command(name="previous", aliases=["pre"], help="Plays the previous song in the queue")
    async def previous(self, ctx):
        if self.queueIndex == 0:
            await ctx.send("There is no previous song in the queue.")
        elif self.vc != None and self.vc:
            self.vc.pause()
            self.queueIndex -= 1
            await self.play_music(ctx)

    @ commands.command(name="skip", aliases=["s", "next"], help="Plays the next song in the queue")
    async def skip(self, ctx):
        if self.queueIndex >= len(self.musicQueue) - 1:
            await ctx.send("You need to have another song in the queue.")
        elif self.vc != None and self.vc:
            self.vc.pause()
            self.queueIndex += 1
            await self.play_music(ctx)

    # List Queue Command

    @ commands.command(name="queue", aliases=["q", "list"], help="Lists the four next songs currently in the queue")
    async def queue(self, ctx):
        returnValue = ""

        for i in range(self.queueIndex, len(self.musicQueue)):
            upNextSongs = len(self.musicQueue) - self.queueIndex
            if i > 5 + upNextSongs:
                break
            returnIndex = i - self.queueIndex
            if returnIndex == 0:
                returnIndex = "Playing"
            elif returnIndex == 1:
                returnIndex = "Next"
            returnValue += f"{returnIndex} - [{self.musicQueue[i][0]['title']}]({self.musicQueue[i][0]['link']})\n"

            if returnValue == "":
                await ctx.send("There are no songs in the queue.")
                return

        queue = discord.Embed(
            title="Current Queue",
            description=returnValue,
            colour=discord.Colour.from_rgb(r=0, g=180, b=75)
        )
        await ctx.send(embed=queue)

    # Clear Queue Command

    @ commands.command(name="clear", aliases=["c", "clearqueue"], help="Clears all of the songs from the queue")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.musicQueue = []
        self.queueIndex = 0
        await ctx.send("The music queue has been cleared.")

    # Join VC Command

    @ commands.command(name="join", aliases=["j"], help="Connects the bot to the voice channel")
    async def join(self, ctx):
        userChannel = ctx.author.voice.channel
        await self.join_VC(ctx, userChannel)

    # Leave VC Command

    @ commands.command(name="leave", aliases=["l"], help="Removes the bot from the voice channel")
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        self.musicQueue = []
        self.queueIndex = 0
        await self.vc.disconnect()

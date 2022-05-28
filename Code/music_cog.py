import discord
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
from youtube_dl import YoutubeDL

# TODO Make refresh command that restarts the bot
# TODO Make skip and previous commands replay first and last songs (respectively) when at the ends of queue
# TODO Make queue command list time left in audio
# TODO Add playlist mechanics
# TODO When Jason types #poop play fortnite battle pass 10 hours
# Made a search command
# Made bot leave vc after 3 minutes of inactivity
# Made the bot auto leave the VC when no-one is in it
# Made search command faster (download after selection)
# Made a cancel button for the search option

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

        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51

        self.vc = None

    # Auto Leave

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # if the trigger was the bot and the action was joining a channel
        if member.id == self.bot.user.id and before.channel == None and after.channel != None:
            cooldownMinutes = 3
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1
                if self.is_playing and not self.is_paused:
                    time = 0
                if time == cooldownMinutes * 60:
                    self.is_playing = False
                    self.is_paused = False
                    self.musicQueue = []
                    self.queueIndex = 0
                    await self.vc.disconnect()
                if not self.vc.is_connected():
                    break
        # if the trigger is a user (not the bot) and the action was leaving a channel
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc.is_connected():
                self.is_playing = False
                self.is_paused = False
                self.musicQueue = []
                self.queueIndex = 0
                await self.vc.disconnect()

    def generate_embed(self, ctx, song, type):
        TITLE = song['title']
        LINK = song['link']
        THUMBNAIL = song['thumbnail']
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar_url

        nowPlaying = discord.Embed(
            title="Now Playing",
            description=f'[{TITLE}]({LINK})',
            colour=self.embedBlue
        )
        nowPlaying.set_thumbnail(url=THUMBNAIL)
        nowPlaying.set_footer(
            text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)

        songAdded = discord.Embed(
            title="Song Added To Queue!",
            description=f'[{TITLE}]({LINK})',
            colour=self.embedRed
        )
        songAdded.set_thumbnail(url=THUMBNAIL)
        songAdded.set_footer(
            text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)

        songRemoved = discord.Embed(
            title="Song Removed From Queue",
            description=f'[{TITLE}]({LINK})',
            colour=self.embedRed
        )
        songRemoved.set_thumbnail(url=THUMBNAIL)
        songRemoved.set_footer(
            text=f"Song added by: {str(AUTHOR)}", icon_url=AVATAR)

        match type:
            case 1: return nowPlaying
            case 2: return songAdded
            case 3: return songRemoved

    async def join_VC(self, ctx, channel):
        if self.vc == None or not self.vc.is_connected():
            self.vc = await channel.connect()

            if self.vc == None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc.move_to(channel)

    def get_YT_title(self, VideoID):
        params = {"format": "json",
                  "url": "https://www.youtube.com/watch?v=%s" % VideoID}
        url = "https://www.youtube.com/oembed"
        query_string = parse.urlencode(params)
        url = url + "?" + query_string
        with request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data['title']

    def search_YT(self, search):
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen(
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
        if not self.is_playing:
            return
        if self.queueIndex + 1 < len(self.musicQueue):
            self.is_playing = True
            self.queueIndex += 1

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
            print("Play_next error")
            self.queueIndex += 1
            self.is_playing = False

    async def play_music(self, ctx):
        if self.queueIndex < len(self.musicQueue):
            self.is_playing = True
            self.is_paused = False

            await self.join_VC(ctx, self.musicQueue[self.queueIndex][1])

            song = self.musicQueue[self.queueIndex][0]
            message = self.generate_embed(ctx, song, 1)
            await ctx.send(embed=message)

            self.vc.play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send(f"There are no songs in the queue to be played.")
            self.queueIndex += 1
            self.is_playing = False

    # Play Command

    @ commands.command(
        name="play",
        aliases=["pl"],
        help="""
            (url || search terms)
            Plays (or resumes) the audio of a specified YouTube video
            Takes either a url or search terms for a YouTube video and starts playing the first result. If no arguments are specified then the current audio is resumed.
            """
    )
    async def play(self, ctx, *args):
        search = " ".join(args)

        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return
        if not args:
            if len(self.musicQueue) == 0:
                await ctx.send("There are no songs in the queue to be played.")
                return
            elif not self.is_playing:
                if self.musicQueue == None or self.vc == None:
                    await self.play_music(ctx)
                else:
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

                if not self.is_playing:
                    await self.play_music(ctx)
                else:
                    message = self.generate_embed(ctx, song, 2)
                    await ctx.send(embed=message)

    # Search Command

    @ commands.command(
        name="search",
        aliases=["find", "sr"],
        help="""
            [url || search terms]
            Provides a list of YouTube search results
            Provides a list of the first ten YouTube search results for a url or specified search terms. You can then select one of the results to add to the current queue.
            """
    )
    async def search(self, ctx, *args):
        search = " ".join(args)
        songNames = []
        selectionOptions = []
        embedText = ""

        if not args:
            await ctx.send("You must specify search terms to use this command.")
            return
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return

        await ctx.send("Fetching search results . . .")

        songTokens = self.search_YT(search)

        for i, token in enumerate(songTokens):
            url = 'https://www.youtube.com/watch?v=' + token
            name = self.get_YT_title(token)
            songNames.append(name)
            embedText += f"{i + 1} - [{name}]({url})\n"

        for i, title in enumerate(songNames):
            selectionOptions.append(SelectOption(
                label=f"{i + 1} - {title[:95]}", value=i))
        searchResults = discord.Embed(
            title="Search Results",
            description=embedText,
            colour=self.embedRed
        )
        selectionComponents = [
            Select(
                placeholder="Select an option",
                options=selectionOptions
            ),
            Button(
                label="Cancel",
                custom_id="Cancel",
                style=4
            )
        ]
        message = await ctx.send(embed=searchResults, components=selectionComponents)
        try:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    "button_click",
                    timeout=60.0,
                    check=None
                ), name="button"),
                asyncio.create_task(self.bot.wait_for(
                    "select_option",
                    timeout=60.0,
                    check=None
                ), name="select")
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            finished: asyncio.Task = list(done)[0]

            for task in pending:
                try:
                    task.cancel()
                except asyncio.CancelledError:
                    pass

            if finished == None:
                searchResults.title = "Search Failed"
                searchResults.description = ""
                await message.delete()
                await ctx.send(embed=searchResults)
                return

            action = finished.get_name()

            if action == "button":
                searchResults.title = "Search Cancelled"
                searchResults.description = ""
                await message.delete()
                await ctx.send(embed=searchResults)
            elif action == "select":
                result = finished.result()
                chosenIndex = int(result.values[0])
                songRef = self.extract_YT(songTokens[chosenIndex])
                if type(songRef) == type(True):
                    await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
                    return
                embedResponse = discord.Embed(
                    title=f"Option #{int(result.values[0]) + 1} Selected",
                    description=f"[{songRef['title']}]({songRef['link']}) added to the queue!",
                    colour=self.embedRed
                )
                embedResponse.set_thumbnail(url=songRef['thumbnail'])
                await message.delete()
                await ctx.send(embed=embedResponse)
                self.musicQueue.append([songRef, userChannel])
        except:
            searchResults.title = "Search Failed"
            searchResults.description = ""
            await message.delete()
            await ctx.send(embed=searchResults)

    # Add Command

    @ commands.command(
        name="add",
        aliases=["a"],
        help="""
            [url || search terms]
            Adds the first search result to the queue
            Adds the first YouTube search result for a url or specified search terms to the queue.
            """
    )
    async def add(self, ctx, *args):
        search = " ".join(args)

        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return
        if not args:
            await ctx.send("You need to specify a song to be added.")
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
                return
            else:
                self.musicQueue.append([song, userChannel])
                message = self.generate_embed(ctx, song, 2)
                await ctx.send(embed=message)

    # Remove Command

    @ commands.command(
        name="remove",
        aliases=["rm"],
        help="""
            <>
            Removes the last song in the queue
            Removes the last song in the queue.
            """
    )
    async def remove(self, ctx):
        if self.musicQueue != []:
            song = self.musicQueue[-1][0]
            removeSongEmbed = self.generate_embed(ctx, song, 3)
            await ctx.send(embed=removeSongEmbed)
        else:
            await ctx.send("There are no songs to be removed in the queue.")
        self.musicQueue = self.musicQueue[:-1]
        if self.musicQueue == []:
            # clear queue and stop playing
            if self.vc != None and self.is_playing:
                self.is_playing = False
                self.is_paused = False
                self.vc.stop()
            self.queueIndex = 0
        elif self.queueIndex == len(self.musicQueue) and self.vc != None and self.vc:
            self.vc.pause()
            self.queueIndex -= 1
            await self.play_music(ctx)

    # Pause Command

    @ commands.command(
        name="pause",
        aliases=["stop", "pa"],
        help="""
            <>
            Pauses the current song being played
            Pauses the current song being played.
            """,
    )
    async def pause(self, ctx):
        if not self.vc:
            await ctx.send("There is no audio to be paused at the moment.")
        elif self.is_playing:
            await ctx.send("Audio paused!")
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

    # Resume Command

    @ commands.command(
        name="resume",
        aliases=["unpause", "re"],
        help="""
            <>
            Resumes a paused song
            Resumes a paused song
            """,
    )
    async def resume(self, ctx):
        if not self.vc:
            await ctx.send("There is no audio to be played at the moment.")
        if self.is_paused:
            await ctx.send("The audio is now playing!")
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    # Skip Command

    @ commands.command(
        name="previous",
        aliases=["pre", "pr"],
        help="""
            <>
            Plays the previous song in the queue
            Plays the previous song in the queue. If there is no previous song then nothing happens.
            """,
    )
    async def previous(self, ctx):
        if self.queueIndex <= 0:
            await ctx.send("There is no previous song in the queue.")
        elif self.vc != None and self.vc:
            self.vc.pause()
            self.queueIndex -= 1
            await self.play_music(ctx)

    # Skip Command

    @ commands.command(
        name="skip",
        aliases=["next", "sk"],
        help="""
            <>
            Skips to the next song in the queue.
            Skips to the next song in the queue. If there is no following song then nothing happens.
            """,
    )
    async def skip(self, ctx):
        if self.queueIndex >= len(self.musicQueue) - 1:
            await ctx.send("You need to have another song in the queue.")
        elif self.vc != None and self.vc:
            self.vc.pause()
            self.queueIndex += 1
            await self.play_music(ctx)

    # List Queue Command

    @ commands.command(
        name="queue",
        aliases=["list", "q"],
        help="""
            <>
            Lists the next few songs in the queue.
            Lists the song that is currently playing and the next few songs in the queue. Up to five songs can be listed depending on how many are in the queue. 
            """,
    )
    async def queue(self, ctx):
        returnValue = ""
        if self.musicQueue == []:
            await ctx.send("There are no songs in the queue.")
            return

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
            colour=self.embedGreen
        )
        await ctx.send(embed=queue)

    # Clear Queue Command

    @ commands.command(
        name="clear",
        aliases=["cl"],
        help="""
            <>
            Clears all of the songs from the queue
            Stops the current audio from playing and clears all of the songs from the queue.
            """,
    )
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.is_playing = False
            self.is_paused = False
            self.vc.stop()
        if self.musicQueue != []:
            await ctx.send("The music queue has been cleared.")
            self.musicQueue = []
        self.queueIndex = 0

    # Join VC Command

    @ commands.command(
        name="join",
        aliases=["j"],
        help="""
            <>
            Connects Bobbert to the voice channel
            Connects Bobbert to the voice channel of whoever called the command. If you are not in a voice channel then nothing will happen.
            """,
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await self.join_VC(ctx, userChannel)
            await ctx.send(f"Bobbert has joined {userChannel}!")
        else:
            await ctx.send("You need to be connected to a voice channel.")

    # Leave VC Command

    @ commands.command(
        name="leave",
        aliases=["l"],
        help="""
            <>
            Removes Bobbert from the voice channel and clears the queue
            Removes Bobbert from the voice channel and clears all of the songs from the queue.
            """,
    )
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        self.musicQueue = []
        self.queueIndex = 0
        if self.vc != None:
            await ctx.send("Bobbert has left the building!")
            await self.vc.disconnect()

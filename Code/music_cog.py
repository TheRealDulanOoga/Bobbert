import discord
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
from youtube_dl import YoutubeDL

# TODO Make queue command list time left in audio
# TODO Add playlist mechanics
# Made a search command
# Made bot leave vc after 3 minutes of inactivity
# Made the bot auto leave the VC when no-one is in it
# Made search command faster (download after selection)
# Made a cancel button for the search option
# Loaded onto raspi
# Made refresh command that restarts the bot
# Allowed for bot to play in multiple servers at once
# Made skip and previous commands replay first and last songs (respectively) when at the ends of queue


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}

        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51

        self.vc = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = guild.id
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False

    # Auto Leave

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # if the trigger was the bot and the action was joining a channel
        id = member.guild.id
        if member.id == self.bot.user.id and before.channel == None and after.channel != None:
            cooldownMinutes = 3
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1
                if self.is_playing[id] and not self.is_paused[id]:
                    time = 0
                if time == cooldownMinutes * 60:
                    self.is_playing[id] = False
                    self.is_paused[id] = False
                    self.musicQueue[id] = []
                    self.queueIndex = 0
                    await self.vc[id].disconnect()
                if not self.vc[id].is_connected():
                    break
        # if the trigger is a user (not the bot) and the action was leaving a channel
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()

    @commands.Cog.listener()
    async def on_message(self, message):
        with open('token.txt', 'r') as file:
            userID = file.readlines()[1]
        if '#poop' in message.content and message.author.id == userID:
            await message.channel.send("I gotcha fam ;)")
            ctx = await self.bot.get_context(message)
            await self.play(ctx, "https://youtu.be/AkJYdRGu14Y")

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
        id = ctx.guild.id
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()

            if self.vc[id] == None:
                await ctx.send("Could not connect to the voice channel.")
                return
        else:
            await self.vc[id].move_to(channel)

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
        id = ctx.guild.id
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            coro = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            print("Play_next error")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    async def play_music(self, ctx):
        id = ctx.guild.id
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False

            await self.join_VC(ctx, self.musicQueue[id][self.queueIndex[id]][1])

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            await ctx.send(embed=message)

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send(f"There are no songs in the queue to be played.")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

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
        id = ctx.guild.id
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("You must be connected to a voice channel.")
            return
        if not args:
            if len(self.musicQueue[id]) == 0:
                await ctx.send("There are no songs in the queue to be played.")
                return
            elif not self.is_playing[id]:
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
            else:
                self.musicQueue[id].append([song, userChannel])

                if not self.is_playing[id]:
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
                self.musicQueue[ctx.guild.id].append([songRef, userChannel])
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
                self.musicQueue[ctx.guild.id].append([song, userChannel])
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
        id = ctx.guild.id
        if self.musicQueue[id] != []:
            song = self.musicQueue[id][-1][0]
            removeSongEmbed = self.generate_embed(ctx, song, 3)
            await ctx.send(embed=removeSongEmbed)
        else:
            await ctx.send("There are no songs to be removed in the queue.")
        self.musicQueue[id] = self.musicQueue[id][:-1]
        if self.musicQueue[id] == []:
            # clear queue and stop playing
            if self.vc[id] != None and self.is_playing[id]:
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.vc[id].stop()
            self.queueIndex[id] = 0
        elif self.queueIndex[id] == len(self.musicQueue[id]) and self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
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
        id = ctx.guild.id
        if not self.vc[id]:
            await ctx.send("There is no audio to be paused at the moment.")
        elif self.is_playing[id]:
            await ctx.send("Audio paused!")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()

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
        id = ctx.guild.id
        if not self.vc[id]:
            await ctx.send("There is no audio to be played at the moment.")
        if self.is_paused[id]:
            await ctx.send("The audio is now playing!")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()

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
        id = ctx.guild.id
        if self.queueIndex[id] <= 0:
            await ctx.send("There is no previous song in the queue. Replaying current song.")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
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
        id = ctx.guild.id
        if self.queueIndex[id] >= len(self.musicQueue[id]) - 1:
            await ctx.send("You need to have another song in the queue. Replaying current song.")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] += 1
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
        id = ctx.guild.id
        returnValue = ""
        if self.musicQueue[id] == []:
            await ctx.send("There are no songs in the queue.")
            return

        for i in range(self.queueIndex[id], len(self.musicQueue[id])):
            upNextSongs = len(
                self.musicQueue[id]) - self.queueIndex[id]
            if i > 5 + upNextSongs:
                break
            returnIndex = i - self.queueIndex[id]
            if returnIndex == 0:
                returnIndex = "Playing"
            elif returnIndex == 1:
                returnIndex = "Next"
            returnValue += f"{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})\n"

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
        id = ctx.guild.id
        if self.vc[id] != None and self.is_playing[id]:
            self.is_playing[id] = False
            self.is_paused[id] = False
            self.vc[id].stop()
        if self.musicQueue[id] != []:
            await ctx.send("The music queue has been cleared.")
            self.musicQueue[id] = []
        self.queueIndex[id] = 0

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
        id = ctx.guild.id
        self.is_playing[id] = False
        self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        if self.vc[id] != None:
            await ctx.send("Bobbert has left the building!")
            await self.vc[id].disconnect()

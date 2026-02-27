from discord.ext import commands
import discord
import datetime
import asyncio
import os

import embed_gen as embeds
import vc_funcs as VC


async def setup(bot):
    await bot.add_cog(music_cog(bot))

class music_cog(commands.Cog):
    def __init__(self, bot):
        VC.bot = bot
        CWD = os.getcwd()


    #setup
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in VC.bot.guilds:
            id = int(guild.id)

            botMember = await guild.fetch_member(975410595576840272)
            nickname = botMember.nick
            if nickname == None:
                nickname = botMember.name
            
            VC.init(id, nickname)


    #error handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print("[" + datetime.time.now() + "] " + str(error))
        await ctx.send(embed=embeds.error(error))


    #auto-leave
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # if the trigger was the bot and the action was joining a channel
        id = int(member.guild.id)
        channelJoined = before.channel == None and after.channel != None
        channelLeft = before.channel != None and after.channel != before.channel
        triggerIsBot = member.id == VC.bot.user.id

        if channelJoined and triggerIsBot:
            cooldownMinutes = 10
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1
                if VC.playing[id]:
                    time = 0
                if time == cooldownMinutes * 60:
                    await VC.leave(id)
                if VC.vc[id] == None or not VC.vc[id].is_connected():
                    break
        if channelLeft and not triggerIsBot:
            membersRemaining = before.channel.members
            lonelyBot = len(membersRemaining) == 1 and membersRemaining[0].id == VC.bot.user.id and VC.vc[id].is_connected()
            if lonelyBot:
                await VC.leave(id)
    

    #join vc
    @ commands.command(
        name="join",
        aliases=["j"],
        help="""
            <>
            Connects the bot to the voice channel
            Connects the bot to the voice channel of whoever called the command. If you are not in a voice channel then nothing will happen.
            """
    )
    async def join(self, ctx):
        id = int(ctx.guild.id)
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await VC.join(id, userChannel)
            await ctx.send(f"{VC.nicknames[id]} has joined {userChannel}!")
        else:
            await ctx.send("You need to be connected to a voice channel.")


    #leave vc
    @ commands.command(
        name="leave",
        aliases=["l"],
        help="""
            <>
            Removes the bot from the voice channel and clears the queue
            Removes the bot from the voice channel and clears all of the songs from the queue.
            """
    )
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        
        success = await VC.leave(id)

        if success: await ctx.send(f"{VC.nicknames[id]} has left the building! The queue has been cleared as well.")
        else: await ctx.send("I'm not currently in a voice channel... so I can't really leave")


    #play a song
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
        id = int(ctx.guild.id)
        
        try: userChannel = ctx.message.author.voice.channel
        except: return await ctx.send("You must be connected to a voice channel.")  
        
        if not args: # no song specified
            if len(VC.queue[id]) == 0: await ctx.send("There are no songs in the queue to be played.") # no queue
            elif VC.playing[id]: await ctx.send("Audio is already being played right now.")            # bot is already playing
            elif VC.vc[id] == None: await VC.start_playing(ctx)  # bot is NOT playing and is not connected to VC
            else: await VC.resume(ctx)                           # bot is NOT playing and IS connected to VC
            return
        else: # song was specified
            for arg in args: arg.replace("'", '')
            query = " ".join(args)
            song = VC.extract_yt_info(query)
            if type(song) == type(True): # invalid song
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
            else:
                VC.queue[id].append([song, userChannel])
                print(VC.paused[id], VC.playing[id], VC.vc[id])
                if VC.paused[id] and VC.vc[id].is_connected(): await VC.resume(ctx)
                elif VC.playing[id]: await ctx.send(embed=embeds.songAdded(ctx, song, len(VC.queue[id])))
                else: await VC.start_playing(ctx)


    #add a song
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
        id = int(ctx.guild.id)
        query = " ".join(args)

        try: userChannel = ctx.message.author.voice.channel
        except: return await ctx.send("You must be connected to a voice channel.")
            
        if not args: await ctx.send("You need to specify a song to be added.")
        else:
            song = VC.extract_yt_info(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
            else:
                VC.queue[id].append([song, userChannel])
                await ctx.send(embed=embeds.songAdded(ctx, song, len(VC.queue[id])))

    #add a song
    @ commands.command(
        name="insert",
        aliases=["ins", "i"],
        help="""
            [url || search terms]
            Inserts the first search result after a specified index in the queue
            Inserts the first YouTube search result for a url or specified search terms to the queue after the specified index (up next if index not specified).
            """
    )
    async def insert(self, ctx, *args):
        id = int(ctx.guild.id)

        index = 0
        try:
            index = int(args[0]) 
            args = args[1:]
        except: pass

        query = " ".join(args)
        index = max(VC.queueIndex[id] + 1, min(index, len(VC.queue[id]) - 1))

        try: userChannel = ctx.author.voice.channel
        except: return await ctx.send("You must be connected to a voice channel.")
            
        if not args: await ctx.send("You need to specify a song to be added.")
        else:
            song = VC.extract_yt_info(query)
            if type(song) == type(True):
                await ctx.send("Could not download the song. Incorrect format, try a different keyword.")
                return
            else:
                VC.queue[id].insert(index, [song, userChannel])
                await ctx.send(embed=embeds.songInserted(ctx, song, index + 1))

    # remove last song
    @ commands.command(
        name="remove",
        aliases=["rm"],
        help="""
            <>
            Removes the last song in the queue
            Removes the last song in the queue.
            """
    )
    async def remove(self, ctx, *args):
        id = int(ctx.guild.id)
        if VC.queue[id] == []: return await ctx.send("There are no songs to be removed in the queue.")

        pos = -1
        print(args)
        if args and int(args[0]):
            arg = int(args[0])
            if arg >= 1 and arg <= len(VC.queue[id]): 
                pos = arg - 1
            else: return await ctx.send("Your insertion index between 1 and the queue length")

        index = VC.queueIndex[id]
        qLen = len(VC.queue[id])
        pos %= qLen

        song = VC.queue[id][pos][0]
        await ctx.send(embed=embeds.songRemoved(ctx, song, pos + 1))
        
        # VC.queue[id] = VC.queue[id][:pos] + VC.queue[id][pos+1:]
        del VC.queue[id][pos]

        if VC.queue[id] == []:
            await ctx.send("The queue is now empty: pausing audio")
            VC.vc[id].stop()
            VC.playing[id] = False
            VC.paused[id] = False
            VC.queueIndex[id] = 0
            return

        VC.queueIndex[id] = min(index, qLen - 2)
        if index > pos:
            VC.queueIndex[id] -= 1
        if index == pos or index > qLen - 2:
            VC.vc[id].pause()
            await VC.start_playing(ctx)
        

    # Pause Command
    @ commands.command(
        name="pause",
        aliases=["stop", "pa"],
        help="""
            <>
            Pauses the current song being played
            Pauses the current song being played.
            """
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if VC.vc[id] == None or VC.paused[id] or not VC.playing[id]:
            await ctx.send("There is no audio to be paused at the moment.")
        
        VC.playing[id] = False
        VC.paused[id] = True
        VC.vc[id].pause()
        await ctx.send("Audio paused!")


    # Resume Command
    @ commands.command(
        name="resume",
        aliases=["unpause", "re"],
        help="""
            <>
            Resumes a paused song
            Resumes a paused song
            """
    )
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        if not VC.vc[id]: await ctx.send("There is no audio to be played at the moment.")
        elif VC.playing[id]: await ctx.send("Audio is already being played right now.")
        else: await VC.resume(ctx)


    # Skip Command
    @ commands.command(
        name="previous",
        aliases=["pre", "pr"],
        help="""
            <>
            Plays the previous song in the queue
            Plays the previous song in the queue. If there is no previous song then nothing happens.
            """
    )
    async def previous(self, ctx):
        id = int(ctx.guild.id)
        index = VC.queueIndex[id]
        await VC.jump(ctx, index - 1)


    # Skip Command
    @ commands.command(
        name="skip",
        aliases=["next", "sk"],
        help="""
            <>
            Skips to the next song in the queue.
            Skips to the next song in the queue. If there is no following song then nothing happens.
            """
    )
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        index = VC.queueIndex[id]
        await VC.jump(ctx, index + 1)


 # List Queue Command
    @ commands.command(
        name="queue",
        aliases=["list", "q"],
        help="""
            <>
            Lists the next few songs in the queue.
            Lists the song that is currently playing and the next few songs in the queue. Up to five songs can be listed depending on how many are in the queue.
            """
    )
    async def queue(self, ctx, *args):
        id = int(ctx.guild.id)
        QI = VC.queueIndex[id]
        if VC.queue[id] == []:
            await ctx.send("There are no songs in the queue.")
            return

        start = max(QI, 0)
        end = len(VC.queue[id])

        if not args: pass
        elif int(args[0]):
            print('int')
            start = int(args[0]) - 1
            start = min(max(0, start), end)
            if len(args) > 1 and int(args[1]):
                end = int(args[1])
                end = min(max(start, end), len(VC.queue[id]))
        
        for i in range(start, end):
            song = VC.queue[id][i]
            message = f"({i + 1}) "
            indexDiff = i - VC.queueIndex[id]
            if indexDiff == 0: message += "Now Playing"
            elif indexDiff == 1: message += "Up Next"
            elif indexDiff == -1: message += "Last Played"
            elif indexDiff > 0: message += f"+{indexDiff}"
            else: message += f"{indexDiff}"

            # print(message)
            # print(song[0]['title'])
            await ctx.send(embed=embeds.queue(ctx, song[0], message, indexDiff))

        # id = int(ctx.guild.id)
        # returnValue = ""
        # if VC.queue[id] == []:
        #     await ctx.send("There are no songs in the queue.")
        #     return

        # if len(VC.queue[id]) <= VC.queueIndex[id]:
        #     await ctx.send("You have reached the end of the queue.")
        #     return

        # for i in range(VC.queueIndex[id], len(VC.queue[id])):
        #     upNextSongs = len(
        #         VC.queue[id]) - VC.queueIndex[id]
        #     if i > 5 + upNextSongs:
        #         break
        #     returnIndex = i - VC.queueIndex[id]
        #     if returnIndex == 0:
        #         returnIndex = "Playing"
        #     elif returnIndex == 1:
        #         returnIndex = "Next"
        #     returnValue += f"{returnIndex} - [{VC.queue[id][i][0]['title']}]({VC.queue[id][i][0]['link']})\n"

        #     if returnValue == "":
        #         await ctx.send("There are no songs in the queue.")
        #         return

        # queue = discord.Embed(
        #     title="Current Queue",
        #     description=returnValue,
        #     colour=embeds.GREEN
        # )
        # await ctx.send(embed=queue)


    # Clear Queue Command
    @ commands.command(
        name="clear",
        aliases=["cl"],
        help="""
            <>
            Clears all of the songs from the queue
            Stops the current audio from playing and clears all of the songs from the queue.
            """
    )
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        if VC.vc[id] != None and VC.playing[id]:
            VC.playing[id] = False
            VC.paused[id] = False
            VC.vc[id].stop()

        VC.queue[id] = []
        VC.queueIndex[id] = 0
        await ctx.send("The music queue has been cleared.")

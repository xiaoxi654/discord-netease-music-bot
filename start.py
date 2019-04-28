import discord
import asyncio
import logging
import time
from configparser import ConfigParser
from discord.ext import commands
import neteaselib

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
bot = commands.Bot(command_prefix='$')
bot.remove_command("help")
queueList = neteaselib.Queue()
if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')
config = ConfigParser()
config.read("config.ini", encoding="UTF-8")


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx: commands.Context):
        # 已在播放，忽略相同命令
        if ctx.voice_client.is_playing():
            return

        retry_count = 0
        while True:
            # 判断队列中是否有未播放的歌曲
            if queueList.is_empty() is False:
                # 有，则计数清零
                retry_count = 0
                # 并且开始播放
                musicInfo = queueList.dequeue()
                embed = discord.Embed(title="Now Playing: " + musicInfo["musicArResult"] + " - " + musicInfo["musicTitle"])\
                    .add_field(name="Link", value="[Click Here](%s)" % musicInfo["163Url"], inline=False)\
                    .set_footer(text="Length: " + str(musicInfo["musicLength"] + " • " + time.asctime(time.localtime(time.time()))))\
                    .set_thumbnail(url=musicInfo["musicPic"])
                await ctx.send(embed=embed)
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(musicInfo["musicFileName"]), volume=0.6)
                ctx.voice_client.play(source, after=lambda e: print('Player error: %s' % e) if e else None)
            else:
                # 无，且计数达到阈值
                if retry_count >= 60:
                    # 计数清零，退出
                    retry_count = 0
                    await ctx.voice_client.disconnect()
                    await ctx.send("Nothing to play.")
                    return
                else:
                    # 未达到阈值，计数增加
                    retry_count += 1
                    await asyncio.sleep(1)

    @commands.command()
    async def add(self, ctx: commands.Context, music_name: str):
        print("Searching %s, user is %s" % (music_name, ctx.message.author))
        musicInfo = neteaselib.get_music_info(music_name)
        queueList.enqueue(musicInfo)
        await ctx.send("%s added to queue." % musicInfo["musicTitle"])

    @commands.command()
    async def skip(self, ctx: commands.Context):
        ctx.voice_client.stop()
        await ctx.send("Music Skipped")

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send("Changed volume to {}%".format(volume))

    @commands.command()
    async def stop(self, ctx: commands.Context):
        await ctx.send("Music stopped")
        if not queueList.is_empty():
            queueList.clear()
        await ctx.voice_client.disconnect()

    @commands.command()
    async def cleancache(self, ctx: commands.Context):
        if str(ctx.message.author) == config.get("config", "username"):
            await ctx.send("Command sent by `%s`, cleaning cache." % ctx.message.author)
            neteaselib.clean_cache()
        else:
            await ctx.send("Command sent by `%s`, you don't have permission to clean cache." % ctx.message.author)

    @commands.command()
    async def logout(self, ctx: commands.Context):
        if str(ctx.message.author) == config.get("config", "username"):
            await ctx.send("Command sent by `%s`, logging out." % ctx.message.author)
            await discord.Client.logout(bot)
        else:
            await ctx.send("Command sent by `%s`, you don't have permission to logout this bot." % ctx.message.author)

    @play.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


bot.add_cog(Music(bot))
bot.run(config.get("config", "token"))

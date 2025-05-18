import discord
from discord.ext import commands
from typing import Dict, Optional
from bot.features.music.player import MusicPlayer, Song, YTDLSource
from bot.core.config import DEFAULT_GUILD_ID

# Dictionary to store music players for each guild
players: Dict[int, MusicPlayer] = {}

class Music(commands.Cog):
    """Music commands for the bot"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_player(self, ctx: commands.Context) -> MusicPlayer:
        """Get or create a music player for a guild"""
        if ctx.guild.id in players:
            return players[ctx.guild.id]

        player = MusicPlayer(ctx)
        players[ctx.guild.id] = player
        return player

    async def cleanup(self, guild: discord.Guild):
        """Cleanup the player for a guild"""
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del players[guild.id]
        except KeyError:
            pass

    async def cog_before_invoke(self, ctx: commands.Context):
        """Ensure the command context has a voice client"""
        # We can't set ctx.voice_client directly as it's a property
        # Just check if it exists, no need to set it
        # The voice client can be accessed via ctx.voice_client or ctx.guild.voice_client

    async def cog_command_error(self, ctx: commands.Context, error):
        """Handle errors in music commands"""
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(f"An error occurred: {str(error.original)}")
        else:
            await ctx.send(f"An error occurred: {str(error)}")

    @commands.hybrid_command(name="join", description="Join a voice channel")
    async def join(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Join a voice channel"""
        if not channel and not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel.")
            return

        destination = channel or ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(destination)
        else:
            # Connect to the voice channel
            voice_client = await destination.connect()
            # Auto-mute the bot to prevent it from hearing itself
            await ctx.guild.me.edit(deafen=True)

        await ctx.send(f"Joined {destination.name}")

    @commands.hybrid_command(name="play", description="Play a song (YouTube, Spotify, etc.)")
    async def play(self, ctx: commands.Context, *, search: str):
        """Play a song with a given search query or URL"""
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                # It's a single track (YouTube or Spotify) or search query
                source = await YTDLSource.create_source(search, loop=self.bot.loop, requester=ctx.author)
                song = Song(source, ctx.author)

                player = await self.get_player(ctx)
                player.queue.append(song)

                if not ctx.voice_client.is_playing():
                    player.next.set()
                    await ctx.send(f"Now playing: **{song.title}**")
                else:
                    await ctx.send(f"Added to queue: **{song.title}**")
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")
                import traceback
                traceback.print_exc()

    @commands.hybrid_command(name="pause", description="Pause the currently playing song")
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("Nothing is playing right now.")
            return

        ctx.voice_client.pause()
        await ctx.send("Paused ⏸️")

    @commands.hybrid_command(name="resume", description="Resume the currently paused song")
    async def resume(self, ctx: commands.Context):
        """Resume the currently paused song"""
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            await ctx.send("Nothing is paused right now.")
            return

        ctx.voice_client.resume()
        await ctx.send("Resumed ▶️")

    @commands.hybrid_command(name="skip", description="Skip the currently playing song")
    async def skip(self, ctx: commands.Context):
        """Skip the currently playing song"""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await ctx.send("Nothing is playing right now.")
            return

        ctx.voice_client.stop()
        await ctx.send("Skipped ⏭️")

    @commands.hybrid_command(name="leave", description="Leave the voice channel")
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel and clear the queue"""
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel.")
            return

        await self.cleanup(ctx.guild)
        await ctx.send("Disconnected from voice channel.")

async def setup(bot: commands.Bot):
    """Add the music cog to the bot"""
    await bot.add_cog(Music(bot))
    print(f"Registered Music cog")

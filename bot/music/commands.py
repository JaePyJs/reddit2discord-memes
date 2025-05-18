import discord
from discord.ext import commands
from typing import Dict
from bot.music.player import MusicPlayer, Song, YTDLSource
from bot.utils.config import DEFAULT_GUILD_ID

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

    @commands.hybrid_command(name="joinvc", description="Join a specific voice channel")
    @commands.has_permissions(connect=True)
    async def joinvc(self, ctx: commands.Context, *, channel: discord.VoiceChannel):
        """Join a specific voice channel by name or ID"""
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            # Connect to the voice channel
            voice_client = await channel.connect()
            # Auto-mute the bot to prevent it from hearing itself
            await ctx.guild.me.edit(deafen=True)

        await ctx.send(f"Joined {channel.name}")

    @commands.hybrid_command(name="play", description="Play a song (YouTube, Spotify, etc.)")
    async def play(self, ctx: commands.Context, *, search: str):
        """Play a song with a given search query or URL
        
        Supports:
        - YouTube URLs and search queries
        - Spotify tracks, albums, and playlists
        - Direct audio file URLs
        
        Examples:
        /play never gonna give you up
        /play https://www.youtube.com/watch?v=dQw4w9WgXcQ
        /play https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT
        /play https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h
        /play https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq
        """
        if not ctx.voice_client:
            await ctx.invoke(self.join)

        async with ctx.typing():
            try:
                # Check if it's a Spotify URL (playlist, album, or track)
                if search.startswith("https://open.spotify.com/"):
                    # Initialize the Spotify client
                    spotify_client = YTDLSource.spotify_client
                    if spotify_client is None:
                        from bot.music.spotify import SpotifyClient
                        spotify_client = SpotifyClient()
                        YTDLSource.spotify_client = spotify_client
                        
                    # Make sure Spotify client is properly initialized
                    if not spotify_client.initialized:
                        await ctx.send("⚠️ Spotify client failed to initialize. Please check your Spotify API credentials in the .env file.")
                        return

                    # Handle Spotify URLs based on type
                    spotify_type = None
                    if "playlist" in search:
                        spotify_type = "playlist"
                    elif "album" in search:
                        spotify_type = "album"
                    elif "track" in search:
                        spotify_type = "track"
                    else:
                        await ctx.send("Unsupported Spotify URL type. Please use a track, album, or playlist URL.")
                        return
                    
                    # Parse Spotify URL
                    try:
                        await ctx.send(f"Processing Spotify {spotify_type}... This may take a moment.")
                        result = await spotify_client.parse_spotify_url(search)
                        
                        # Handle track differently from playlist/album
                        if spotify_type == "track":
                            if not result:
                                await ctx.send("Could not find the Spotify track.")
                                return
                                
                            # Single track
                            source = await YTDLSource.create_source(
                                result['search_query'], 
                                loop=self.bot.loop, 
                                requester=ctx.author
                            )
                            song = Song(source, ctx.author)
                            
                            player = await self.get_player(ctx)
                            player.queue.append(song)
                            
                            # Create an embed with Spotify information
                            embed = discord.Embed(
                                title="Spotify Track Added",
                                description=f"**{result['title']}**",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="Artist", value=result['artist'], inline=True)
                            embed.set_footer(text="Playing via YouTube")
                            
                            if not ctx.voice_client.is_playing():
                                player.next.set()
                                embed.title = "Now Playing Spotify Track"
                                await ctx.send(embed=embed)
                            else:
                                await ctx.send(embed=embed)
                        else:
                            # Playlist or album
                            tracks = result
                            if not tracks:
                                await ctx.send(f"No tracks found in this Spotify {spotify_type}.")
                                return
                            
                            # Add the first track to play immediately
                            first_track = tracks[0]
                            first_source = await YTDLSource.create_source(
                                first_track['search_query'], 
                                loop=self.bot.loop, 
                                requester=ctx.author
                            )
                            first_song = Song(first_source, ctx.author)
                            
                            player = await self.get_player(ctx)
                            
                            # Create an embed for the Spotify playlist/album
                            embed = discord.Embed(
                                title=f"Spotify {spotify_type.capitalize()} Added",
                                description=f"**{first_track['artist']}'s {spotify_type}**",
                                color=discord.Color.green()
                            )
                            
                            # Add the first song to play it immediately if nothing is playing
                            if not ctx.voice_client.is_playing():
                                player.queue.append(first_song)
                                player.next.set()
                                embed.add_field(name="Now Playing", value=first_song.title, inline=False)
                            else:
                                player.queue.append(first_song)
                                embed.add_field(name="First Track", value=first_song.title, inline=False)
                            
                            
                            # Add remaining tracks to the queue (limit to 25 to avoid overloading)
                            remaining_tracks = tracks[1:26]
                            added_count = 1  # We already added the first track
                            
                            for track in remaining_tracks:
                                try:
                                    source = await YTDLSource.create_source(
                                        track['search_query'], 
                                        loop=self.bot.loop, 
                                        requester=ctx.author
                                    )
                                    song = Song(source, ctx.author)
                                    player.queue.append(song)
                                    added_count += 1
                                except Exception as e:
                                    # Log the error but continue with the next track
                                    print(f"Error adding track {track['title']}: {e}")
                                    continue
                            
                            total_tracks = len(tracks)
                            skipped = max(0, total_tracks - 26)
                            
                            embed.add_field(
                                name="Tracks Added", 
                                value=f"{added_count} tracks added to queue" + 
                                    (f" ({skipped} skipped due to queue limits)" if skipped > 0 else ""),
                                inline=False
                            )
                            embed.set_footer(text=f"Spotify {spotify_type} • Playing via YouTube")
                            
                            await ctx.send(embed=embed)
                    except Exception as e:
                        error_embed = discord.Embed(
                            title="❌ Spotify Error",
                            description=f"Error processing Spotify URL: {str(e)}",
                            color=discord.Color.red()
                        )
                        error_embed.add_field(
                            name="Troubleshooting", 
                            value="• Check if your Spotify API credentials are correct\n"
                                  "• Make sure the URL is valid and accessible\n"
                                  "• Try again later if Spotify API is having issues",
                            inline=False
                        )
                        await ctx.send(embed=error_embed)
                        import traceback
                        traceback.print_exc()
                else:
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

    @commands.hybrid_command(name="queue", description="Show the current song queue")
    async def queue(self, ctx: commands.Context):
        """Show the current song queue"""
        if not ctx.guild.id in players:
            await ctx.send("No active music player.")
            return

        player = players[ctx.guild.id]

        if not player.queue and not player.current:
            await ctx.send("The queue is empty.")
            return

        # Create an embed for the queue
        embed = discord.Embed(
            title="Song Queue",
            color=discord.Color.blurple()
        )

        # Add the current song
        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f"[{player.current.title}]({player.current.url}) | Requested by {player.current.requester.mention}",
                inline=False
            )

        # Add the queued songs (up to 10)
        if player.queue:
            queue_list = []
            for i, song in enumerate(list(player.queue)[:10], start=1):
                queue_list.append(f"{i}. [{song.title}]({song.url}) | Requested by {song.requester.mention}")

            queue_text = "\n".join(queue_list)

            if len(player.queue) > 10:
                queue_text += f"\n... and {len(player.queue) - 10} more"

            embed.add_field(
                name="Up Next",
                value=queue_text,
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="volume", description="Change the player volume")
    async def volume(self, ctx: commands.Context, volume: int):
        """Change the player volume (0-100)"""
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel.")
            return

        if not 0 <= volume <= 100:
            await ctx.send("Volume must be between 0 and 100.")
            return

        if ctx.guild.id in players:
            players[ctx.guild.id].volume = volume / 100

        if ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100

        await ctx.send(f"Volume set to {volume}%")

    @commands.hybrid_command(name="leave", description="Leave the voice channel")
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel and clear the queue"""
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel.")
            return

        await self.cleanup(ctx.guild)
        await ctx.send("Disconnected from voice channel.")

    @commands.hybrid_command(name="loop", description="Toggle looping of the current song")
    async def loop(self, ctx: commands.Context):
        """Toggle looping of the current song"""
        if not ctx.guild.id in players:
            await ctx.send("No active music player.")
            return

        player = players[ctx.guild.id]
        player.loop = not player.loop

        await ctx.send(f"Looping is now {'enabled' if player.loop else 'disabled'}")

    @commands.hybrid_command(name="nowplaying", description="Show information about the currently playing song")
    async def nowplaying(self, ctx: commands.Context):
        """Show information about the currently playing song"""
        if not ctx.guild.id in players or not players[ctx.guild.id].current:
            await ctx.send("Nothing is playing right now.")
            return

        player = players[ctx.guild.id]
        await ctx.send(embed=player.current.create_embed())

    @play.before_invoke
    @joinvc.before_invoke
    async def ensure_voice_for_music(self, ctx: commands.Context):
        """Ensure the bot is in a voice channel before playing music"""
        if not ctx.author.voice and not ctx.voice_client:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")

        if ctx.voice_client:
            return

        # Connect to the voice channel
        await ctx.author.voice.channel.connect()
        # Auto-mute the bot to prevent it from hearing itself
        await ctx.guild.me.edit(deafen=True)

async def setup(bot: commands.Bot):
    """Add the music cog to the bot"""
    # Register music cog globally, not guild-specific
    cog = Music(bot)
    await bot.add_cog(cog)
    print(f"Registered Music cog with {len(cog.get_commands())} commands")

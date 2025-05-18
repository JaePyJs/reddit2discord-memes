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
                        from bot.features.music.spotify import SpotifyClient
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
                            
                            # Add Spotify metadata
                            source['artist'] = result.get('artist')
                            source['album'] = result.get('album')
                            source['album_art'] = result.get('album_art')
                            source['spotify'] = True
                            
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
                            
                            # Add album info if available
                            if 'album' in result:
                                embed.add_field(name="Album", value=result['album'], inline=True)
                                
                            # Add album art if available
                            if result.get('album_art'):
                                embed.set_thumbnail(url=result['album_art'])
                                
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
                            
                            # Add Spotify metadata
                            first_source['artist'] = first_track.get('artist')
                            first_source['album'] = first_track.get('album')
                            first_source['album_art'] = first_track.get('album_art')
                            first_source['spotify'] = True
                            
                            first_song = Song(first_source, ctx.author)
                            
                            player = await self.get_player(ctx)
                            
                            # Create an embed for the Spotify playlist/album
                            embed = discord.Embed(
                                title=f"Spotify {spotify_type.capitalize()} Added",
                                description=f"**{first_track['artist']}'s {spotify_type}**",
                                color=discord.Color.green()
                            )
                            
                            # Add album art if available
                            if first_track.get('album_art'):
                                embed.set_thumbnail(url=first_track['album_art'])
                            
                            # Add the first song to play it immediately if nothing is playing
                            if not ctx.voice_client.is_playing():
                                player.queue.append(first_song)
                                player.next.set()
                                embed.add_field(name="Now Playing", value=first_song.title, inline=False)
                            else:
                                player.queue.append(first_song)
                                embed.add_field(name="First Track", value=first_song.title, inline=False)
                            
                            # Add remaining tracks to the queue (limit to 50 with pagination support)
                            remaining_tracks = tracks[1:51]  # Increased from 25 to 50
                            added_count = 1  # We already added the first track
                            
                            for track in remaining_tracks:
                                try:
                                    source = await YTDLSource.create_source(
                                        track['search_query'], 
                                        loop=self.bot.loop, 
                                        requester=ctx.author
                                    )
                                    
                                    # Add Spotify metadata
                                    source['artist'] = track.get('artist')
                                    source['album'] = track.get('album')
                                    source['album_art'] = track.get('album_art')
                                    source['spotify'] = True
                                    
                                    song = Song(source, ctx.author)
                                    player.queue.append(song)
                                    added_count += 1
                                except Exception as e:
                                    # Log the error but continue with the next track
                                    print(f"Error adding track {track['title']}: {e}")
                                    continue
                            
                            total_tracks = len(tracks)
                            skipped = max(0, total_tracks - 51)
                            
                            embed.add_field(
                                name="Tracks Added", 
                                value=f"{added_count} tracks added to queue" + 
                                    (f" ({skipped} skipped due to queue limits)" if skipped > 0 else ""),
                                inline=False
                            )
                            
                            # Add pagination info if there are more tracks
                            if skipped > 0:
                                embed.add_field(
                                    name="More Tracks", 
                                    value=f"Use `/spotify_more {spotify_type} {search}` to add more tracks from this {spotify_type}",
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

    @commands.hybrid_command(name="spotify_more", description="Add more tracks from a Spotify playlist or album")
    async def spotify_more(self, ctx: commands.Context, content_type: str, url: str, offset: int = 50):
        """Add more tracks from a Spotify playlist or album with pagination
        
        Parameters:
        - content_type: Type of content (playlist or album)
        - url: Spotify URL
        - offset: Offset to start from (default: 50)
        
        Examples:
        /spotify_more playlist https://open.spotify.com/playlist/37i9dQZF1DXdbRLJPSmnyq 50
        /spotify_more album https://open.spotify.com/album/5r36AJ6VOJtp00oxSkBZ5h 50
        """
        if not ctx.voice_client:
            await ctx.invoke(self.join)
            
        if content_type.lower() not in ['playlist', 'album']:
            await ctx.send("Invalid content type. Please use 'playlist' or 'album'.")
            return
            
        if not url.startswith("https://open.spotify.com/"):
            await ctx.send("Invalid Spotify URL. Please provide a valid Spotify playlist or album URL.")
            return
            
        async with ctx.typing():
            try:
                # Initialize the Spotify client
                spotify_client = YTDLSource.spotify_client
                if spotify_client is None:
                    from bot.features.music.spotify import SpotifyClient
                    spotify_client = SpotifyClient()
                    YTDLSource.spotify_client = spotify_client
                    
                # Make sure Spotify client is properly initialized
                if not spotify_client.initialized:
                    await ctx.send("⚠️ Spotify client failed to initialize. Please check your Spotify API credentials in the .env file.")
                    return
                    
                # Get tracks with pagination
                await ctx.send(f"Loading more tracks from Spotify {content_type}... This may take a moment.")
                
                if content_type.lower() == 'playlist':
                    result = await spotify_client.get_playlist_tracks(url, limit=50, offset=offset)
                    tracks = result['tracks']
                    total_tracks = result['total_tracks']
                else:  # album
                    result = await spotify_client.get_album_tracks(url, limit=50, offset=offset)
                    tracks = result['tracks']
                    total_tracks = result['total_tracks']
                    
                if not tracks:
                    await ctx.send(f"No more tracks found in this Spotify {content_type}.")
                    return
                    
                # Add tracks to the queue
                player = await self.get_player(ctx)
                added_count = 0
                
                for track in tracks:
                    try:
                        source = await YTDLSource.create_source(
                            track['search_query'], 
                            loop=self.bot.loop, 
                            requester=ctx.author
                        )
                        
                        # Add Spotify metadata
                        source['artist'] = track.get('artist')
                        source['album'] = track.get('album')
                        source['album_art'] = track.get('album_art')
                        source['spotify'] = True
                        
                        song = Song(source, ctx.author)
                        player.queue.append(song)
                        added_count += 1
                    except Exception as e:
                        # Log the error but continue with the next track
                        print(f"Error adding track {track['title']}: {e}")
                        continue
                
                # Create an embed for the added tracks
                embed = discord.Embed(
                    title=f"More Spotify Tracks Added",
                    description=f"Added {added_count} more tracks from the {content_type}",
                    color=discord.Color.green()
                )
                
                # Add pagination info
                remaining = total_tracks - (offset + len(tracks))
                if remaining > 0:
                    next_offset = offset + 50
                    embed.add_field(
                        name="More Tracks", 
                        value=f"There are {remaining} more tracks available. Use `/spotify_more {content_type} {url} {next_offset}` to add more.",
                        inline=False
                    )
                    
                embed.set_footer(text=f"Spotify {content_type} • Tracks {offset+1}-{offset+added_count} of {total_tracks}")
                
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send(f"An error occurred: {str(e)}")
                import traceback
                traceback.print_exc()

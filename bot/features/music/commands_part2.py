    @commands.hybrid_command(name="recommend", description="Get song recommendations based on the current track")
    async def recommend(self, ctx: commands.Context, count: int = 5):
        """Get song recommendations based on the currently playing track
        
        Parameters:
        - count: Number of recommendations to get (default: 5, max: 10)
        
        Example:
        /recommend 5
        """
        if count < 1 or count > 10:
            await ctx.send("Please specify a number between 1 and 10.")
            return
            
        if not ctx.guild.id in players or not players[ctx.guild.id].current:
            await ctx.send("Nothing is playing right now. Play a song first to get recommendations.")
            return
            
        player = players[ctx.guild.id]
        current_song = player.current
        
        # Check if the current song has Spotify data
        if not current_song.source.get('spotify'):
            await ctx.send("Recommendations are only available for Spotify tracks. Try playing a Spotify track first.")
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
                    
                # Get recommendations based on the current track
                await ctx.send(f"Finding recommendations based on the current track... This may take a moment.")
                
                # Use the track URI if available, otherwise use search
                track_uri = current_song.source.get('uri')
                recommendations = await spotify_client.get_recommendations(
                    track_url=track_uri,
                    limit=count
                )
                
                if not recommendations or not recommendations['tracks']:
                    await ctx.send("Could not find any recommendations for this track.")
                    return
                    
                # Create an embed for the recommendations
                embed = discord.Embed(
                    title="Song Recommendations",
                    description=f"Based on: **{current_song.title}** by {current_song.artist}",
                    color=discord.Color.green()
                )
                
                # Add each recommendation to the embed
                for i, track in enumerate(recommendations['tracks'], 1):
                    embed.add_field(
                        name=f"{i}. {track['title']}",
                        value=f"By {track['artist']} • [Listen on Spotify]({track['external_urls']['spotify']})",
                        inline=False
                    )
                    
                # Add a thumbnail if available
                if current_song.album_art:
                    embed.set_thumbnail(url=current_song.album_art)
                    
                embed.set_footer(text="Use /play with the Spotify URL to play any of these tracks")
                
                await ctx.send(embed=embed)
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
                value=f"[{player.current.title}]({player.current.url}) | {player.current.artist} | Requested by {player.current.requester.mention}",
                inline=False
            )

        # Add the queued songs (up to 10)
        if player.queue:
            queue_list = []
            for i, song in enumerate(list(player.queue)[:10], start=1):
                queue_list.append(f"{i}. [{song.title}]({song.url}) | {song.artist} | Requested by {song.requester.mention}")

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
        await ctx.send(embed=player.current.create_embed(show_progress=True))

"""
Tenor GIF Commands

This module provides Discord commands for searching and posting GIFs using the Tenor API.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import Optional, List

from bot.features.tenor.api import TenorClient, TenorAPIError
from bot.core.analytics import analytics
from bot.core.performance_monitor import timed

class TenorCommands(commands.Cog):
    """Commands for searching and posting GIFs using the Tenor API"""
    
    def __init__(self, bot):
        """
        Initialize the Tenor commands
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.tenor_client = TenorClient()
        
        # Log initialization
        if self.tenor_client.initialized:
            logging.info("Tenor commands initialized")
        else:
            logging.warning("Tenor commands initialized but API client not initialized")
    
    @app_commands.command(name="gif", description="Search for and post a GIF")
    @app_commands.describe(
        query="Search query for the GIF",
        hidden="Whether to show the GIF only to you (default: False)"
    )
    @timed(operation_type="command")
    async def gif_command(self, interaction: discord.Interaction, query: str, hidden: bool = False):
        """
        Search for and post a GIF
        
        Args:
            interaction: Discord interaction
            query: Search query
            hidden: Whether to show the GIF only to the user
        """
        # Track command usage
        analytics.track_command("gif", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"query": query, "hidden": hidden})
        
        # Defer response to allow time for API call
        await interaction.response.defer(ephemeral=hidden)
        
        try:
            if not self.tenor_client.initialized:
                await interaction.followup.send(
                    "⚠️ Tenor API is not configured. Please set TENOR_API_KEY in the .env file.",
                    ephemeral=True
                )
                return
            
            # Search for GIFs
            results = await self.tenor_client.search_gifs(query, limit=10)
            
            if not results:
                await interaction.followup.send(
                    f"No GIFs found for '{query}'",
                    ephemeral=True
                )
                return
            
            # Get a random GIF from the results
            gif_data = results[0]  # Use the first result for now
            
            # Extract GIF URL
            gif_url = self.tenor_client.extract_gif_url(gif_data)
            
            if not gif_url:
                await interaction.followup.send(
                    f"Error extracting GIF URL",
                    ephemeral=True
                )
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"GIF: {query}",
                color=discord.Color.blue()
            )
            embed.set_image(url=gif_url)
            
            # Add attribution
            embed.set_footer(text=f"Powered by Tenor | Requested by {interaction.user.display_name}")
            
            # Send the GIF
            await interaction.followup.send(embed=embed)
            
        except TenorAPIError as e:
            logging.error(f"Tenor API error: {e}")
            await interaction.followup.send(
                f"Error searching for GIFs: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in gif command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )
    
    @app_commands.command(name="trending_gifs", description="Show trending GIFs")
    @app_commands.describe(
        limit="Number of GIFs to show (default: 5, max: 10)",
        hidden="Whether to show the GIFs only to you (default: False)"
    )
    @timed(operation_type="command")
    async def trending_gifs_command(self, interaction: discord.Interaction, 
                                  limit: int = 5, hidden: bool = False):
        """
        Show trending GIFs
        
        Args:
            interaction: Discord interaction
            limit: Number of GIFs to show
            hidden: Whether to show the GIFs only to the user
        """
        # Track command usage
        analytics.track_command("trending_gifs", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"limit": limit, "hidden": hidden})
        
        # Validate limit
        if limit < 1:
            limit = 1
        elif limit > 10:
            limit = 10
        
        # Defer response to allow time for API call
        await interaction.response.defer(ephemeral=hidden)
        
        try:
            if not self.tenor_client.initialized:
                await interaction.followup.send(
                    "⚠️ Tenor API is not configured. Please set TENOR_API_KEY in the .env file.",
                    ephemeral=True
                )
                return
            
            # Get trending GIFs
            results = await self.tenor_client.get_trending_gifs(limit=limit)
            
            if not results:
                await interaction.followup.send(
                    "No trending GIFs found",
                    ephemeral=True
                )
                return
            
            # Send each GIF as a separate message
            for i, gif_data in enumerate(results):
                # Extract GIF URL
                gif_url = self.tenor_client.extract_gif_url(gif_data)
                
                if not gif_url:
                    continue
                
                # Create embed
                embed = discord.Embed(
                    title=f"Trending GIF #{i+1}",
                    color=discord.Color.blue()
                )
                embed.set_image(url=gif_url)
                
                # Add attribution
                embed.set_footer(text=f"Powered by Tenor | Requested by {interaction.user.display_name}")
                
                # Send the GIF
                await interaction.followup.send(embed=embed)
                
                # Add a small delay between messages to avoid rate limiting
                if i < len(results) - 1:
                    await asyncio.sleep(0.5)
            
        except TenorAPIError as e:
            logging.error(f"Tenor API error: {e}")
            await interaction.followup.send(
                f"Error getting trending GIFs: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in trending_gifs command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )

async def setup(bot):
    """
    Set up the Tenor commands
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(TenorCommands(bot))
    logging.info("Tenor commands cog registered")

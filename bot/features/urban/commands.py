"""
Urban Dictionary Commands

This module provides Discord commands for looking up slang terms using the Urban Dictionary API.
"""

import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio
from typing import Optional, List
import random

from bot.features.urban.api import UrbanDictionaryClient, UrbanDictionaryAPIError
from bot.core.analytics import analytics
from bot.core.performance_monitor import timed

class UrbanDictionaryCommands(commands.Cog):
    """Commands for looking up slang terms using the Urban Dictionary API"""
    
    def __init__(self, bot):
        """
        Initialize the Urban Dictionary commands
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.urban_client = UrbanDictionaryClient()
        
        # Log initialization
        logging.info("Urban Dictionary commands initialized")
    
    @app_commands.command(name="define", description="Look up a slang term on Urban Dictionary")
    @app_commands.describe(
        term="Term to look up",
        ephemeral="Whether to show the definition only to you (default: False)"
    )
    @timed(operation_type="command")
    async def define_command(self, interaction: discord.Interaction, 
                           term: str, ephemeral: bool = False):
        """
        Look up a slang term on Urban Dictionary
        
        Args:
            interaction: Discord interaction
            term: Term to look up
            ephemeral: Whether to show the definition only to the user
        """
        # Track command usage
        analytics.track_command("define", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"term": term, "ephemeral": ephemeral})
        
        # Defer response to allow time for API call
        await interaction.response.defer(ephemeral=ephemeral)
        
        try:
            # Get definitions
            definitions = await self.urban_client.define(term)
            
            if not definitions:
                await interaction.followup.send(
                    f"No definitions found for '{term}'",
                    ephemeral=True
                )
                return
            
            # Sort definitions by thumbs up
            definitions.sort(key=lambda d: d.get("thumbs_up", 0), reverse=True)
            
            # Create paginated view
            view = UrbanDictionaryPaginator(interaction.user, definitions, self.urban_client)
            
            # Send the first definition
            await interaction.followup.send(
                embed=view.get_embed(),
                view=view
            )
            
        except UrbanDictionaryAPIError as e:
            logging.error(f"Urban Dictionary API error: {e}")
            await interaction.followup.send(
                f"Error looking up definition: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in define command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )
    
    @app_commands.command(name="urban_random", description="Get a random definition from Urban Dictionary")
    @app_commands.describe(
        ephemeral="Whether to show the definition only to you (default: False)"
    )
    @timed(operation_type="command")
    async def random_command(self, interaction: discord.Interaction, ephemeral: bool = False):
        """
        Get a random definition from Urban Dictionary
        
        Args:
            interaction: Discord interaction
            ephemeral: Whether to show the definition only to the user
        """
        # Track command usage
        analytics.track_command("urban_random", str(interaction.user.id), 
                              str(interaction.guild_id) if interaction.guild else None,
                              str(interaction.channel_id),
                              {"ephemeral": ephemeral})
        
        # Defer response to allow time for API call
        await interaction.response.defer(ephemeral=ephemeral)
        
        try:
            # Get random definitions
            definitions = await self.urban_client.random()
            
            if not definitions:
                await interaction.followup.send(
                    "No random definitions found",
                    ephemeral=True
                )
                return
            
            # Sort definitions by thumbs up
            definitions.sort(key=lambda d: d.get("thumbs_up", 0), reverse=True)
            
            # Create paginated view
            view = UrbanDictionaryPaginator(interaction.user, definitions, self.urban_client)
            
            # Send the first definition
            await interaction.followup.send(
                embed=view.get_embed(),
                view=view
            )
            
        except UrbanDictionaryAPIError as e:
            logging.error(f"Urban Dictionary API error: {e}")
            await interaction.followup.send(
                f"Error getting random definition: {str(e)}",
                ephemeral=True
            )
        except Exception as e:
            logging.error(f"Unexpected error in random command: {e}")
            await interaction.followup.send(
                f"An unexpected error occurred",
                ephemeral=True
            )

class UrbanDictionaryPaginator(discord.ui.View):
    """Paginator for Urban Dictionary definitions"""
    
    def __init__(self, user, definitions, urban_client):
        """
        Initialize the paginator
        
        Args:
            user: User who triggered the command
            definitions: List of definition dictionaries
            urban_client: Urban Dictionary client
        """
        super().__init__(timeout=300)  # 5 minute timeout
        self.user = user
        self.definitions = definitions
        self.urban_client = urban_client
        self.current_index = 0
        self.total_definitions = len(definitions)
        
        # Update button states
        self._update_buttons()
    
    def _update_buttons(self):
        """Update button states based on current index"""
        # Disable previous button if at first definition
        self.previous_button.disabled = self.current_index == 0
        
        # Disable next button if at last definition
        self.next_button.disabled = self.current_index == self.total_definitions - 1
    
    def get_embed(self):
        """
        Get the current definition embed
        
        Returns:
            Discord embed
        """
        definition = self.definitions[self.current_index]
        
        # Create embed
        embed = discord.Embed(
            title=definition.get("word", "Unknown"),
            url=definition.get("permalink", "https://www.urbandictionary.com"),
            color=discord.Color.blurple(),
            description=self.urban_client._clean_text(definition.get("definition", "No definition available"))
        )
        
        # Add example if available
        example = definition.get("example", "")
        if example:
            embed.add_field(
                name="Example",
                value=self.urban_client._clean_text(example),
                inline=False
            )
        
        # Add author and votes
        thumbs_up = definition.get("thumbs_up", 0)
        thumbs_down = definition.get("thumbs_down", 0)
        author = definition.get("author", "Unknown")
        
        embed.add_field(
            name="Stats",
            value=f"👍 {thumbs_up} | 👎 {thumbs_down} | by {author}",
            inline=False
        )
        
        # Add pagination info
        embed.set_footer(text=f"Definition {self.current_index + 1} of {self.total_definitions}")
        
        return embed
    
    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Handle previous button click
        
        Args:
            interaction: Discord interaction
            button: Button that was clicked
        """
        # Check if the user who clicked is the one who triggered the command
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your definition lookup!",
                ephemeral=True
            )
            return
        
        # Go to previous definition
        self.current_index = max(0, self.current_index - 1)
        
        # Update button states
        self._update_buttons()
        
        # Update the message
        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )
    
    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Handle next button click
        
        Args:
            interaction: Discord interaction
            button: Button that was clicked
        """
        # Check if the user who clicked is the one who triggered the command
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your definition lookup!",
                ephemeral=True
            )
            return
        
        # Go to next definition
        self.current_index = min(self.total_definitions - 1, self.current_index + 1)
        
        # Update button states
        self._update_buttons()
        
        # Update the message
        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )
    
    @discord.ui.button(label="Random", style=discord.ButtonStyle.success, emoji="🔀")
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Handle random button click
        
        Args:
            interaction: Discord interaction
            button: Button that was clicked
        """
        # Check if the user who clicked is the one who triggered the command
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This isn't your definition lookup!",
                ephemeral=True
            )
            return
        
        # Go to a random definition
        new_index = random.randint(0, self.total_definitions - 1)
        while new_index == self.current_index and self.total_definitions > 1:
            new_index = random.randint(0, self.total_definitions - 1)
        
        self.current_index = new_index
        
        # Update button states
        self._update_buttons()
        
        # Update the message
        await interaction.response.edit_message(
            embed=self.get_embed(),
            view=self
        )
    
    async def on_timeout(self):
        """Handle view timeout"""
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Try to update the message
        try:
            await self.message.edit(view=self)
        except:
            pass

async def setup(bot):
    """
    Set up the Urban Dictionary commands
    
    Args:
        bot: Discord bot instance
    """
    await bot.add_cog(UrbanDictionaryCommands(bot))
    logging.info("Urban Dictionary commands cog registered")

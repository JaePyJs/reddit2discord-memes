import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
import asyncio
import random
import string
from typing import Optional, List, Dict, Any
from PIL import Image
from bot.features.memes.template_manager import (
    get_template_list, get_template_by_name, get_template_by_id,
    add_template, create_template_embed, save_template_image
)
from bot.features.memes.effects import apply_effect, get_available_effects
from bot.utils.text_utils import draw_wrapped_text
from bot.core.config import SAVED_MEMES_DIR

def init_saved_memes_dir():
    """Initialize the saved memes directory if it doesn't exist"""
    if not os.path.exists(SAVED_MEMES_DIR):
        os.makedirs(SAVED_MEMES_DIR)
        logging.info(f"Created saved memes directory: {SAVED_MEMES_DIR}")

class MemeCommands(commands.Cog):
    """Meme generation commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_saved_memes_dir()
        
    @app_commands.command(
        name='meme_create',
        description='Create a meme from a template'
    )
    @app_commands.describe(
        template='Template name or ID',
        top_text='Text for the top of the meme',
        bottom_text='Text for the bottom of the meme',
        font_size='Font size (default: auto)',
        font_color='Font color (default: auto-contrast)',
        outline_color='Text outline color (default: auto-contrast)'
    )
    async def meme_create(
        self, 
        interaction: discord.Interaction, 
        template: str,
        top_text: Optional[str] = None,
        bottom_text: Optional[str] = None,
        font_size: Optional[int] = None,
        font_color: Optional[str] = None,
        outline_color: Optional[str] = None
    ):
        """Create a meme from a template"""
        # Defer the response since this might take a moment
        await interaction.response.defer()
        
        # Get the template
        template_obj = get_template_by_name(template)
        if not template_obj:
            try:
                template_id = int(template)
                template_obj = get_template_by_id(template_id)
            except ValueError:
                pass
                
        if not template_obj:
            await interaction.followup.send(
                f"Template '{template}' not found. Use `/template_browse` to see available templates."
            )
            return
            
        # Check if at least one text is provided
        if not top_text and not bottom_text:
            await interaction.followup.send(
                "Please provide at least one of: top_text or bottom_text."
            )
            return
            
        # Load the template image
        try:
            template_path = template_obj['file_path']
            if not os.path.exists(template_path):
                await interaction.followup.send(
                    f"Template file not found: {template_path}"
                )
                return
                
            img = Image.open(template_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Draw text on the image
            if top_text:
                img = draw_wrapped_text(
                    img, 
                    top_text, 
                    position='top',
                    font_size=font_size,
                    font_color=font_color,
                    outline_color=outline_color
                )
                
            if bottom_text:
                img = draw_wrapped_text(
                    img, 
                    bottom_text, 
                    position='bottom',
                    font_size=font_size,
                    font_color=font_color,
                    outline_color=outline_color
                )
                
            # Generate a random filename
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            output_path = os.path.join(SAVED_MEMES_DIR, f"meme_{random_str}.jpg")
            
            # Save the meme
            img.save(output_path, 'JPEG', quality=95)
            
            # Create embed
            embed = discord.Embed(
                title=f"Meme: {template_obj['name']}",
                color=discord.Color.green()
            )
            
            # Add creator info
            embed.set_footer(
                text=f"Created by {interaction.user.display_name}"
            )
            
            # Send the meme
            await interaction.followup.send(
                embed=embed,
                file=discord.File(output_path)
            )
            
        except Exception as e:
            logging.error(f"Error creating meme: {e}")
            await interaction.followup.send(
                f"An error occurred while creating the meme: {str(e)}"
            )
            
    @app_commands.command(
        name='template_upload',
        description='Upload a new meme template'
    )
    @app_commands.describe(
        name='Name for the template',
        image='Image file to use as template'
    )
    async def template_upload(
        self,
        interaction: discord.Interaction,
        name: str,
        image: discord.Attachment
    ):
        """Upload a new meme template"""
        # Check if the attachment is an image
        if not image.content_type or not image.content_type.startswith('image/'):
            await interaction.response.send_message(
                "Please upload an image file (JPEG, PNG, etc.).",
                ephemeral=True
            )
            return
            
        # Check if the template name already exists
        existing_template = get_template_by_name(name)
        if existing_template:
            await interaction.response.send_message(
                f"A template named '{name}' already exists. Please choose a different name.",
                ephemeral=True
            )
            return
            
        # Defer the response since this might take a moment
        await interaction.response.defer()
        
        try:
            # Save the template image
            file_path = await save_template_image(image, name)
            if not file_path:
                await interaction.followup.send(
                    "Failed to save the template image. Please try again."
                )
                return
                
            # Add the template to the database
            template_id = add_template(
                name,
                file_path,
                str(interaction.user.id),
                interaction.user.display_name
            )
            
            # Get the template object
            template_obj = get_template_by_id(template_id)
            
            # Create embed
            embed = create_template_embed(template_obj, self.bot.user)
            
            # Send confirmation
            await interaction.followup.send(
                content=f"Template '{name}' has been added! Use `/meme_create template:{name}` to create memes with it.",
                embed=embed,
                file=discord.File(file_path)
            )
            
        except Exception as e:
            logging.error(f"Error uploading template: {e}")
            await interaction.followup.send(
                f"An error occurred while uploading the template: {str(e)}"
            )
            
    @app_commands.command(
        name='template_browse',
        description='Browse available meme templates'
    )
    @app_commands.describe(
        page='Page number to view'
    )
    async def template_browse(
        self,
        interaction: discord.Interaction,
        page: int = 1
    ):
        """Browse available meme templates"""
        # Get all templates
        templates = get_template_list()
        
        if not templates:
            await interaction.response.send_message(
                "No templates found. Use `/template_upload` to add some!",
                ephemeral=True
            )
            return
            
        # Calculate pagination
        items_per_page = 1
        max_pages = (len(templates) + items_per_page - 1) // items_per_page
        
        # Validate page number
        if page < 1:
            page = 1
        elif page > max_pages:
            page = max_pages
            
        # Get the template for this page
        start_idx = (page - 1) * items_per_page
        template = templates[start_idx]
        
        # Create embed
        embed = create_template_embed(template, self.bot.user)
        embed.title = f"Template {page}/{max_pages}: {template['name']}"
        
        # Create navigation buttons
        class TemplateNavigation(discord.ui.View):
            def __init__(self, cog, current_page, max_pages):
                super().__init__(timeout=60)
                self.cog = cog
                self.current_page = current_page
                self.max_pages = max_pages
                
                # Disable prev button on first page
                if current_page == 1:
                    self.prev_button.disabled = True
                    
                # Disable next button on last page
                if current_page == max_pages:
                    self.next_button.disabled = True
                
            @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray)
            async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await self.cog.template_browse(interaction, page=self.current_page - 1)
                
            @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await self.cog.template_browse(interaction, page=self.current_page + 1)
                
            @discord.ui.button(label="Use This Template", style=discord.ButtonStyle.green)
            async def use_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                # Create a modal for entering meme text
                modal = MemeTextModal(templates[start_idx]['name'])
                await interaction.response.send_modal(modal)
        
        # Create a modal for entering meme text
        class MemeTextModal(discord.ui.Modal, title="Create Meme"):
            def __init__(self, template_name):
                super().__init__()
                self.template_name = template_name
                
            top_text = discord.ui.TextInput(
                label="Top Text",
                placeholder="Enter text for the top of the meme",
                required=False,
                max_length=100
            )
            
            bottom_text = discord.ui.TextInput(
                label="Bottom Text",
                placeholder="Enter text for the bottom of the meme",
                required=False,
                max_length=100
            )
            
            async def on_submit(self, interaction: discord.Interaction):
                # Check if at least one text is provided
                if not self.top_text.value and not self.bottom_text.value:
                    await interaction.response.send_message(
                        "Please provide at least one of: Top Text or Bottom Text.",
                        ephemeral=True
                    )
                    return
                    
                # Create the meme
                await interaction.response.defer()
                await self.cog.meme_create(
                    interaction,
                    template=self.template_name,
                    top_text=self.top_text.value,
                    bottom_text=self.bottom_text.value
                )
        
        # Send the embed with navigation
        file_path = template['file_path']
        view = TemplateNavigation(self, page, max_pages)
        
        if os.path.exists(file_path):
            await interaction.response.send_message(
                embed=embed,
                view=view,
                file=discord.File(file_path)
            )
        else:
            await interaction.response.send_message(
                content=f"Template file not found: {file_path}",
                embed=embed,
                view=view
            )
            
    @app_commands.command(
        name='meme_effects',
        description='Apply special effects to a meme template'
    )
    @app_commands.describe(
        template='Template name or ID',
        effect='Effect to apply',
        intensity='Effect intensity (0.1 to 1.0)',
        top_text='Text for the top of the meme',
        bottom_text='Text for the bottom of the meme'
    )
    @app_commands.choices(
        effect=[
            app_commands.Choice(name=effect, value=effect)
            for effect in get_available_effects()
        ]
    )
    async def meme_effects(
        self,
        interaction: discord.Interaction,
        template: str,
        effect: str,
        intensity: Optional[float] = 0.5,
        top_text: Optional[str] = None,
        bottom_text: Optional[str] = None
    ):
        """Apply special effects to a meme template"""
        # Validate intensity
        if intensity < 0.1 or intensity > 1.0:
            await interaction.response.send_message(
                "Intensity must be between 0.1 and 1.0.",
                ephemeral=True
            )
            return
            
        # Defer the response since this might take a moment
        await interaction.response.defer()
        
        # Get the template
        template_obj = get_template_by_name(template)
        if not template_obj:
            try:
                template_id = int(template)
                template_obj = get_template_by_id(template_id)
            except ValueError:
                pass
                
        if not template_obj:
            await interaction.followup.send(
                f"Template '{template}' not found. Use `/template_browse` to see available templates."
            )
            return
            
        # Load the template image
        try:
            template_path = template_obj['file_path']
            if not os.path.exists(template_path):
                await interaction.followup.send(
                    f"Template file not found: {template_path}"
                )
                return
                
            img = Image.open(template_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Apply the effect
            img = apply_effect(img, effect, intensity)
            if img is None:
                await interaction.followup.send(
                    f"Effect '{effect}' not found or could not be applied."
                )
                return
                
            # Draw text on the image if provided
            if top_text:
                img = draw_wrapped_text(img, top_text, position='top')
                
            if bottom_text:
                img = draw_wrapped_text(img, bottom_text, position='bottom')
                
            # Generate a random filename
            random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            output_path = os.path.join(SAVED_MEMES_DIR, f"meme_{effect}_{random_str}.jpg")
            
            # Save the meme
            img.save(output_path, 'JPEG', quality=95)
            
            # Create embed
            embed = discord.Embed(
                title=f"Meme: {template_obj['name']} with {effect} effect",
                color=discord.Color.green()
            )
            
            # Add creator info
            embed.set_footer(
                text=f"Created by {interaction.user.display_name} • Intensity: {intensity}"
            )
            
            # Send the meme
            await interaction.followup.send(
                embed=embed,
                file=discord.File(output_path)
            )
            
        except Exception as e:
            logging.error(f"Error creating meme with effect: {e}")
            await interaction.followup.send(
                f"An error occurred while creating the meme: {str(e)}"
            )

async def setup(bot: commands.Bot):
    """Add the meme commands cog to the bot"""
    cog = MemeCommands(bot)
    await bot.add_cog(cog)
    print(f"Registered Meme commands cog")

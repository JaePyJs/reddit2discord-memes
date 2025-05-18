"""
Template Manager for Meme Generation

This module handles the management of meme templates, including loading, saving,
and retrieving templates from the database.
"""

import os
import logging
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import discord
from bot.core.config import TEMPLATE_DIR, DB_PATH

def init_templates_dir():
    """Initialize the templates directory if it doesn't exist"""
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)
        logging.info(f"Created templates directory: {TEMPLATE_DIR}")

def get_template_list() -> List[Dict[str, Any]]:
    """
    Get a list of all available templates from the database

    Returns:
        List of template dictionaries with id, name, file_path, creator_id, creator_name
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT id, name, file_path, creator_id, creator_name, width, height, created_at
    FROM templates
    ORDER BY name
    """)

    templates = [dict(row) for row in c.fetchall()]
    conn.close()

    return templates

def get_template_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a template by name

    Args:
        name: The name of the template

    Returns:
        Template dictionary or None if not found
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT id, name, file_path, creator_id, creator_name, width, height, created_at
    FROM templates
    WHERE name = ?
    """, (name,))

    row = c.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def get_template_by_id(template_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a template by ID

    Args:
        template_id: The ID of the template

    Returns:
        Template dictionary or None if not found
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
    SELECT id, name, file_path, creator_id, creator_name, width, height, created_at
    FROM templates
    WHERE id = ?
    """, (template_id,))

    row = c.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None

def add_template(name: str, file_path: str, creator_id: str, creator_name: str) -> int:
    """
    Add a new template to the database

    Args:
        name: The name of the template
        file_path: The path to the template image
        creator_id: The Discord ID of the creator
        creator_name: The Discord name of the creator

    Returns:
        The ID of the newly created template
    """
    # Get image dimensions
    try:
        with Image.open(file_path) as img:
            width, height = img.size
    except Exception as e:
        logging.error(f"Error getting image dimensions: {e}")
        width, height = 0, 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
    INSERT INTO templates (name, file_path, creator_id, creator_name, width, height)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (name, file_path, creator_id, creator_name, width, height))

    template_id = c.lastrowid
    conn.commit()
    conn.close()

    return template_id

def delete_template(template_id: int) -> bool:
    """
    Delete a template from the database

    Args:
        template_id: The ID of the template to delete

    Returns:
        True if successful, False otherwise
    """
    # Get the template to check if it exists and get the file path
    template = get_template_by_id(template_id)
    if not template:
        return False

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Delete the template from the database
        c.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        conn.commit()

        # Delete the file if it exists
        file_path = template['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)

        return True
    except Exception as e:
        logging.error(f"Error deleting template: {e}")
        return False
    finally:
        conn.close()

def create_template_embed(template: Dict[str, Any], bot_user: discord.User = None) -> discord.Embed:
    """
    Create a Discord embed for a template

    Args:
        template: The template dictionary
        bot_user: The bot's user object for the footer

    Returns:
        Discord embed for the template
    """
    embed = discord.Embed(
        title=f"Template: {template['name']}",
        color=discord.Color.blue()
    )

    # Add template image
    file_path = template['file_path']
    if os.path.exists(file_path):
        # Use file:// URL for local files
        embed.set_image(url=f"attachment://{os.path.basename(file_path)}")

    # Add creator info if available
    if template['creator_id'] != 'SYSTEM':
        embed.add_field(
            name="Created by",
            value=template['creator_name'],
            inline=True
        )

    # Add dimensions if available
    if template.get('width') and template.get('height'):
        embed.add_field(
            name="Dimensions",
            value=f"{template['width']}×{template['height']}",
            inline=True
        )

    # Add creation date if available
    if template.get('created_at'):
        embed.add_field(
            name="Added on",
            value=template['created_at'],
            inline=True
        )

    # Add footer with bot info if available
    if bot_user:
        embed.set_footer(
            text=f"Use /meme_create template:{template['name']} to create a meme",
            icon_url=bot_user.avatar.url if bot_user.avatar else None
        )

    return embed

def get_template_file(template_name_or_id: str) -> Optional[str]:
    """
    Get the file path for a template by name or ID

    Args:
        template_name_or_id: The name or ID of the template

    Returns:
        The file path or None if not found
    """
    # Try to parse as ID first
    try:
        template_id = int(template_name_or_id)
        template = get_template_by_id(template_id)
        if template:
            return template['file_path']
    except ValueError:
        # Not an ID, try as name
        template = get_template_by_name(template_name_or_id)
        if template:
            return template['file_path']

    return None

async def save_template_image(attachment: discord.Attachment, template_name: str) -> Optional[str]:
    """
    Save a template image from a Discord attachment

    Args:
        attachment: The Discord attachment
        template_name: The name to give the template

    Returns:
        The file path where the image was saved, or None if failed
    """
    # Initialize templates directory
    init_templates_dir()

    # Clean template name for filename
    clean_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in template_name)
    clean_name = clean_name.lower().replace(" ", "_")

    # Get file extension from attachment
    _, ext = os.path.splitext(attachment.filename)
    if not ext:
        ext = ".jpg"  # Default extension

    # Create file path
    file_path = os.path.join(TEMPLATE_DIR, f"{clean_name}{ext}")

    try:
        # Save the attachment
        await attachment.save(file_path)
        return file_path
    except Exception as e:
        logging.error(f"Error saving template image: {e}")
        return None

"""
Meme Effects Module

This module provides various effects that can be applied to meme images,
such as deep-frying, vaporwave, and more.
"""

import os
import random
import logging
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
import numpy as np
from bot.utils.color_utils import get_contrasting_color

def deep_fry(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """
    Apply a 'deep-fried' effect to an image
    
    Args:
        img: The input image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        The processed image
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Scale intensity
    intensity = max(0.1, min(1.0, intensity))
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.0 + 2.0 * intensity)
    
    # Increase saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.0 + 1.5 * intensity)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.0 + 5.0 * intensity)
    
    # Add noise
    if intensity > 0.5:
        img = add_noise(img, intensity * 0.1)
    
    # Add JPEG artifacts by saving at low quality and reloading
    if intensity > 0.3:
        # Convert to RGB if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Save with low quality
        temp_path = "temp_deepfry.jpg"
        quality = int(30 - intensity * 25)  # Quality from 5 to 30
        img.save(temp_path, quality=quality, optimize=True)
        
        # Reload the image
        img = Image.open(temp_path)
        
        # Clean up
        try:
            os.remove(temp_path)
        except:
            pass
    
    return img

def vaporwave(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """
    Apply a vaporwave aesthetic to an image
    
    Args:
        img: The input image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        The processed image
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Scale intensity
    intensity = max(0.1, min(1.0, intensity))
    
    # Convert to RGB if not already
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Split into channels
    r, g, b = img.split()
    
    # Shift red channel
    shift_amount = int(10 * intensity)
    if shift_amount > 0:
        r = ImageChops.offset(r, shift_amount, 0)
    
    # Shift blue channel
    if shift_amount > 0:
        b = ImageChops.offset(b, -shift_amount, 0)
    
    # Merge channels back
    img = Image.merge('RGB', (r, g, b))
    
    # Adjust colors
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.0 + intensity)
    
    # Add purple/pink tint
    img = add_color_tint(img, (255, 105, 180), intensity * 0.3)
    
    return img

def pixelate(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """
    Pixelate an image
    
    Args:
        img: The input image
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        The processed image
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Scale intensity
    intensity = max(0.1, min(1.0, intensity))
    
    # Calculate pixel size based on intensity and image size
    width, height = img.size
    pixel_size = max(2, int(min(width, height) * intensity / 20))
    
    # Resize down and back up to create pixelation
    small_img = img.resize(
        (width // pixel_size, height // pixel_size),
        resample=Image.NEAREST
    )
    
    return small_img.resize(img.size, Image.NEAREST)

def add_noise(img: Image.Image, intensity: float = 0.1) -> Image.Image:
    """
    Add random noise to an image
    
    Args:
        img: The input image
        intensity: Noise intensity (0.0 to 1.0)
        
    Returns:
        The processed image with noise
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Convert to numpy array
    img_array = np.array(img).astype(np.float64)
    
    # Generate noise
    noise = np.random.normal(0, 255 * intensity, img_array.shape)
    
    # Add noise to image
    img_array = img_array + noise
    
    # Clip values to valid range
    img_array = np.clip(img_array, 0, 255).astype(np.uint8)
    
    # Convert back to PIL image
    return Image.fromarray(img_array)

def add_color_tint(img: Image.Image, color: Tuple[int, int, int], intensity: float = 0.5) -> Image.Image:
    """
    Add a color tint to an image
    
    Args:
        img: The input image
        color: RGB color tuple
        intensity: Tint intensity (0.0 to 1.0)
        
    Returns:
        The tinted image
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Create a solid color image
    tint = Image.new('RGB', img.size, color)
    
    # Blend the original with the tint
    return Image.blend(img, tint, intensity)

def grayscale(img: Image.Image) -> Image.Image:
    """
    Convert an image to grayscale
    
    Args:
        img: The input image
        
    Returns:
        Grayscale version of the image
    """
    return ImageOps.grayscale(img).convert('RGB')

def invert(img: Image.Image) -> Image.Image:
    """
    Invert the colors of an image
    
    Args:
        img: The input image
        
    Returns:
        Color-inverted version of the image
    """
    return ImageOps.invert(img)

def blur(img: Image.Image, intensity: float = 1.0) -> Image.Image:
    """
    Apply blur to an image
    
    Args:
        img: The input image
        intensity: Blur intensity (0.0 to 1.0)
        
    Returns:
        Blurred version of the image
    """
    # Scale intensity
    intensity = max(0.1, min(1.0, intensity))
    
    # Calculate blur radius based on intensity
    radius = intensity * 5
    
    return img.filter(ImageFilter.GaussianBlur(radius))

def add_caption(img: Image.Image, text: str, position: str = 'top') -> Image.Image:
    """
    Add a caption to an image in the classic meme style
    
    Args:
        img: The input image
        text: Caption text
        position: 'top' or 'bottom'
        
    Returns:
        Image with caption
    """
    # Make a copy to avoid modifying the original
    img = img.copy()
    
    # Get image dimensions
    width, height = img.size
    
    # Calculate caption height (proportional to image height)
    caption_height = max(60, int(height * 0.15))
    
    # Create a new image with space for the caption
    if position == 'top':
        new_img = Image.new('RGB', (width, height + caption_height), (255, 255, 255))
        new_img.paste(img, (0, caption_height))
        caption_y = 0
    else:  # bottom
        new_img = Image.new('RGB', (width, height + caption_height), (255, 255, 255))
        new_img.paste(img, (0, 0))
        caption_y = height
    
    # Create a drawing context
    draw = ImageDraw.Draw(new_img)
    
    # Try to load Impact font, fall back to default
    try:
        font_size = int(caption_height * 0.7)
        font = ImageFont.truetype("Impact", font_size)
    except:
        font_size = int(caption_height * 0.7)
        font = ImageFont.load_default()
    
    # Draw the caption
    text_width, text_height = draw.textsize(text, font=font)
    text_x = (width - text_width) // 2
    text_y = caption_y + (caption_height - text_height) // 2
    
    # Draw text with black outline
    for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
        draw.text((text_x + offset_x, text_y + offset_y), text, font=font, fill=(0, 0, 0))
    
    # Draw the main text in white
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255))
    
    return new_img

def apply_effect(img: Image.Image, effect_name: str, intensity: float = 1.0) -> Optional[Image.Image]:
    """
    Apply a named effect to an image
    
    Args:
        img: The input image
        effect_name: Name of the effect to apply
        intensity: Effect intensity (0.0 to 1.0)
        
    Returns:
        Processed image or None if effect not found
    """
    effect_map = {
        'deep_fry': deep_fry,
        'vaporwave': vaporwave,
        'pixelate': pixelate,
        'noise': add_noise,
        'grayscale': lambda img, _: grayscale(img),
        'invert': lambda img, _: invert(img),
        'blur': blur
    }
    
    if effect_name in effect_map:
        try:
            return effect_map[effect_name](img, intensity)
        except Exception as e:
            logging.error(f"Error applying effect {effect_name}: {e}")
            return img
    
    return None

def get_available_effects() -> list:
    """
    Get a list of available effect names
    
    Returns:
        List of effect names
    """
    return [
        'deep_fry',
        'vaporwave',
        'pixelate',
        'noise',
        'grayscale',
        'invert',
        'blur'
    ]

from PIL import Image
import os

def add_overlay(base_path, overlay_path, output_path, x=0, y=0, scale=1.0):
    """
    Add a transparent overlay/sticker to the base image.
    x, y: top-left position for overlay
    scale: scale factor for overlay image
    """
    base = Image.open(base_path).convert('RGBA')
    overlay = Image.open(overlay_path).convert('RGBA')
    if scale != 1.0:
        ow, oh = overlay.size
        overlay = overlay.resize((int(ow * scale), int(oh * scale)), Image.ANTIALIAS)
    base.paste(overlay, (x, y), overlay)
    base.save(output_path)
    return output_path

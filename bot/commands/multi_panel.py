from PIL import Image
import os

def create_multi_panel(template_paths, output_path, direction='horizontal'):
    """
    Combine multiple images into a single multi-panel meme.
    direction: 'horizontal' or 'vertical'
    """
    images = [Image.open(p).convert('RGB') for p in template_paths]
    if direction == 'horizontal':
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)
        new_img = Image.new('RGB', (total_width, max_height), color='white')
        x_offset = 0
        for img in images:
            new_img.paste(img, (x_offset, 0))
            x_offset += img.width
    else:
        max_width = max(img.width for img in images)
        total_height = sum(img.height for img in images)
        new_img = Image.new('RGB', (max_width, total_height), color='white')
        y_offset = 0
        for img in images:
            new_img.paste(img, (0, y_offset))
            y_offset += img.height
    new_img.save(output_path)
    return output_path

"""
End-to-end test of the meme creation process with effects
This simulates what happens when a user runs the /meme_create command with an effect
"""
import io
import os
from PIL import Image, ImageDraw, ImageFont
from bot.utils.text_utils import draw_wrapped_text
from bot.utils.font_utils import get_best_fit_font
from bot.utils.color_utils import get_average_luminance, pick_text_color
from bot.utils.meme_effects import apply_effect, list_effects

def simulate_meme_create(template_path, top_text, bottom_text, effect_name=None):
    print(f"Creating meme with template: {template_path}")
    print(f"Top text: {top_text}")
    print(f"Bottom text: {bottom_text}")
    print(f"Effect: {effect_name or 'None'}")
    
    # Open the template image
    img = Image.open(template_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # Set default parameters
    top_x, top_y = 10, 10
    bottom_x, bottom_y = 10, h - 50
    font_size = 36
    font_color = "white"
    outline_color = "black"
    
    # Calculate bounding boxes
    top_box = (top_x, top_y, w - top_x * 2, int(h / 3))
    bottom_box = (bottom_x, bottom_y, w - bottom_x * 2, int(h / 3))
    
    # Try to find a font
    # This is simplified - in reality we'd use proper font paths
    try:
        # Try to find a font that exists on the system
        potential_fonts = ["arial.ttf", "Arial.ttf", "times.ttf", "Times.ttf", "cour.ttf", "Courier.ttf"]
        font_path = None
        for f in potential_fonts:
            if os.path.exists(f):
                font_path = f
                break
        
        if not font_path:
            # Fallback to default
            print("Warning: No system font found, using default font")
            font_path = None
    except Exception as e:
        print(f"Error finding font: {e}")
        font_path = None
    
    # Determine best fit fonts - simplified for testing
    top_font = get_best_fit_font(top_text, font_path, top_box[2], top_box[3], start_size=font_size)
    bottom_font = get_best_fit_font(bottom_text, font_path, bottom_box[2], bottom_box[3], start_size=font_size)
    
    # Use adaptive text colors
    top_text_color = pick_text_color(get_average_luminance(img, top_box))
    bottom_text_color = pick_text_color(get_average_luminance(img, bottom_box))
    
    # Helper to draw outlined/wrapped text
    def draw_with_outline(box, text, font, fill_color):
        x, y, w_box, h_box = box
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx == 0 and dy == 0:
                    continue
                draw_wrapped_text(draw, text, font, (x + dx, y + dy, w_box, h_box), outline_color)
        draw_wrapped_text(draw, text, font, box, fill_color)
    
    # Draw text on image
    draw_with_outline(top_box, top_text, top_font, top_text_color)
    draw_with_outline(bottom_box, bottom_text, bottom_font, bottom_text_color)
    
    # Apply special effect if specified
    if effect_name and effect_name.lower() != 'none':
        print(f"Applying effect: {effect_name}")
        img = apply_effect(img, effect_name)
    
    # Save the image
    output_filename = f"meme_test_{effect_name or 'no_effect'}.png"
    img.save(output_filename)
    print(f"Meme saved to: {output_filename}")
    return output_filename

if __name__ == "__main__":
    # Test our meme creation with a few different effects
    template_path = "templates/drake.jpg"
    top_text = "Regular memes"
    bottom_text = "Memes with cool effects"
    
    # Create a plain meme first (no effect)
    simulate_meme_create(template_path, top_text, bottom_text)
    
    # Test with a few different effects
    for effect_name in ["deep-fry", "vaporwave", "glitch"]:
        simulate_meme_create(template_path, top_text, bottom_text, effect_name)
    
    print("\nAll test memes created successfully!")
    print("Available effects:")
    for name, desc in list_effects().items():
        print(f"- {name}: {desc}")

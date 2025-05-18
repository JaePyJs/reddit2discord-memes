"""
Demo script to test all meme effects on a sample template
"""
from PIL import Image
import os
import sys
from bot.utils.meme_effects import apply_effect, list_effects

def main():
    # Verify we have at least one template
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        print(f"Error: {template_dir} directory not found")
        return
    
    templates = [f for f in os.listdir(template_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not templates:
        print(f"No template images found in {template_dir}. Please add some .jpg or .png files.")
        return
    
    # Use the first template
    template_path = os.path.join(template_dir, templates[0])
    print(f"Using template: {template_path}")
    
    # Create output directory if it doesn't exist
    output_dir = 'effect_samples'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get all effects
    effects = list_effects()
    print(f"Testing {len(effects)} effects...")
    
    # Load the image once
    img = Image.open(template_path).convert('RGB')
    
    # Apply each effect and save the result
    for effect_name in effects:
        print(f"Applying effect: {effect_name}")
        try:
            result = apply_effect(img.copy(), effect_name)
            output_path = os.path.join(output_dir, f"{effect_name}.png")
            result.save(output_path)
            print(f"  Saved to: {output_path}")
        except Exception as e:
            print(f"  Error applying {effect_name}: {e}")
    
    print("\nAll effects processed! Check the 'effect_samples' directory for results.")

if __name__ == "__main__":
    main()

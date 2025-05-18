from PIL import Image
from bot.utils.meme_effects import apply_effect, list_effects

# Test on drake.jpg
template_path = 'templates/drake.jpg'
print(f"Using template: {template_path}")

# Load the image
img = Image.open(template_path).convert('RGB')

# Apply deep-fry effect
effect_name = 'deep-fry'
result = apply_effect(img, effect_name)

# Save result
output_path = f"{effect_name}_drake.png"
result.save(output_path)
print(f"Saved {effect_name} effect to: {output_path}")

# Apply vaporwave effect
effect_name = 'vaporwave'
result = apply_effect(img, effect_name)

# Save result
output_path = f"{effect_name}_drake.png"
result.save(output_path)
print(f"Saved {effect_name} effect to: {output_path}")

print("Test completed. Check the current directory for output images.")

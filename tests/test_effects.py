"""
This script is used to test meme effects functionality
"""
from PIL import Image
from bot.utils.meme_effects import apply_effect, list_effects

def main():
    # Print all available effects with descriptions
    print("Available meme effects:")
    for name, description in list_effects().items():
        print(f"- {name}: {description}")
    
    # You can also test an effect on an image
    print("\nTo test an effect on an image, uncomment and modify this code:")
    """
    # Load an image
    test_image = Image.open('templates/your_template.jpg')
    
    # Apply an effect
    effect_name = 'deep-fry'  # Change to any effect name
    result = apply_effect(test_image, effect_name)
    
    # Save the result
    result.save(f'test_{effect_name}.png')
    print(f"Saved test_{effect_name}.png")
    """

if __name__ == "__main__":
    main()
from PIL import Image, ImageSequence

def create_gif_meme(template_paths, output_path, duration=200):
    """
    Combine images into a GIF meme.
    template_paths: list of image paths
    duration: frame duration in ms
    """
    frames = [Image.open(p).convert('RGBA') for p in template_paths]
    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=duration, loop=0)
    return output_path

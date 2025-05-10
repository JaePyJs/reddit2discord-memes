import random
from PIL import Image

def meme_battle(img1_path, img2_path):
    """
    Simulate a meme battle by randomly picking a winner.
    Returns the winner's image path and the loser image path.
    """
    winner = random.choice([img1_path, img2_path])
    loser = img2_path if winner == img1_path else img1_path
    return winner, loser

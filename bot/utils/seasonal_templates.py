import os
import random
from datetime import datetime

SEASONAL_MAP = {
    'winter': ['christmas.png', 'snowman.png'],
    'spring': ['easter.png', 'flowers.png'],
    'summer': ['beach.png', 'sun.png'],
    'autumn': ['pumpkin.png', 'leaves.png'],
}

THEME_ROTATION = ['winter', 'spring', 'summer', 'autumn']


def get_current_theme():
    month = datetime.now().month
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def get_seasonal_templates():
    theme = get_current_theme()
    return SEASONAL_MAP.get(theme, [])

def pick_random_seasonal():
    templates = get_seasonal_templates()
    if not templates:
        return None
    return random.choice(templates)

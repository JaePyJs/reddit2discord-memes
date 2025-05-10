import requests
import os

IMGFLIP_API_URL = 'https://api.imgflip.com/caption_image'
IMGFLIP_USERNAME = os.getenv('IMGFLIP_USERNAME')  # Set this in your .env file
IMGFLIP_PASSWORD = os.getenv('IMGFLIP_PASSWORD')  # Set this in your .env file

# Get meme templates (static list for simplicity; can fetch via /get_memes endpoint if needed)
IMGFLIP_TEMPLATES = {
    'Drake Hotline Bling': '181913649',
    'Distracted Boyfriend': '112126428',
    'Two Buttons': '87743020',
    'Expanding Brain': '93895088',
    'Left Exit 12 Off Ramp': '124822590',
    'Change My Mind': '129242436',
    'UNO Draw 25 Cards': '217743513',
    'Batman Slapping Robin': '438680',
}

def generate_imgflip_meme(template_id, top_text, bottom_text):
    if not IMGFLIP_USERNAME or not IMGFLIP_PASSWORD:
        return None, 'Imgflip credentials not set.'
    payload = {
        'template_id': template_id,
        'username': IMGFLIP_USERNAME,
        'password': IMGFLIP_PASSWORD,
        'text0': top_text,
        'text1': bottom_text,
    }
    resp = requests.post(IMGFLIP_API_URL, data=payload)
    if resp.status_code == 200:
        data = resp.json()
        if data['success']:
            return data['data']['url'], None
        else:
            return None, data['error_message']
    return None, 'Failed to contact Imgflip API.'

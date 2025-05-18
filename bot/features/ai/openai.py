import os
import requests

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Set this in your .env file
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

DEFAULT_MODEL = 'gpt-3.5-turbo'

HEADERS = {
    'Authorization': f'Bearer {OPENAI_API_KEY}',
    'Content-Type': 'application/json',
}

def suggest_meme_caption(template_name, style_hint=None):
    if not OPENAI_API_KEY:
        return None, 'OpenAI API key not set.'
    prompt = f"Suggest a funny meme caption for the template '{template_name}'."
    if style_hint:
        prompt += f" Style: {style_hint}."
    data = {
        'model': DEFAULT_MODEL,
        'messages': [
            {'role': 'system', 'content': 'You are a creative meme caption generator.'},
            {'role': 'user', 'content': prompt},
        ],
        'max_tokens': 60,
        'temperature': 0.9,
    }
    resp = requests.post(OPENAI_API_URL, headers=HEADERS, json=data)
    if resp.status_code == 200:
        out = resp.json()
        try:
            return out['choices'][0]['message']['content'].strip(), None
        except Exception:
            return None, 'No suggestion returned.'
    return None, f'OpenAI API error: {resp.status_code} {resp.text}'

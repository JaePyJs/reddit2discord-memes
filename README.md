# reddit2discord-memes

A feature-rich Discord bot for generating memes and automatically posting fresh Reddit content to your server.

---

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Create `.env` with `DISCORD_TOKEN=your-bot-token-here` (and any API keys).
3. Run the bot: `python bot/main.py`

## Features
- Meme creation from templates (`/meme_create`)
- Auto-posting newest & top Reddit posts with 5-min cooldown (`/reddit_autopost`, `/reddit_autopost_list`)
- Random meme fetches, meme battles, filters, and more
- Rich logging & analytics (SQLite)

See `MemeGeneratorChecklist.md` for the full roadmap and progress.

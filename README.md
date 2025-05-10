# 🎉 Reddit ➜ Discord Meme Bot

Bring the freshest memes straight from Reddit to your Discord server *and* let users forge their own masterpieces.

---

## 🚀 Quick Launch
```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Configure secrets (.env)
DISCORD_TOKEN=YOUR_BOT_TOKEN

# 3. Fire it up
python -m bot.main
```

> SQLite (`meme_bot.db`) stores subreddit settings & seen-post IDs – safe across restarts.

---

## 🛠️ Creating a Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. **Bot** tab → *Add Bot* → copy **Token** → paste in `.env`.
3. **Privileged Gateway Intents** → enable *Message Content*.
4. **OAuth2 → URL Generator** → scopes: `bot applications.commands`; perms: *Send Messages, Embed Links*.
5. Visit generated URL, add bot to your server. ✅

---

## 🎮 Commands Cheat-Sheet
| Slash Command | What It Does |
|---------------|-------------|
| `/meme_create` | Generate a meme from a chosen template (top/bottom text, font auto-fit, emoji safe). |
| `/reddit_autopost <subreddit> [channel]` | Start posting newest **and** top posts from a subreddit every ~5 min to a channel (no duplicates). |
| `/reddit_autopost_list` | Interactive paginated list: view, navigate & disable subreddits with buttons. |

---

## 🤖 Auto-Post Engine
• Runs every 60 s; respects 5-min cooldown per type (NEW / BEST).  
• Stores each posted ID → never reposts, even if you reboot.  
• Configuration persisted in SQLite (`subreddit_configs`, `seen_posts`).

---

## 🗺️ Roadmap
See `MemeGeneratorChecklist.md` for upcoming features (GIF support, ratings, analytics…). Pull requests welcome! ✨

---

## ❤️ Contributing
1. Fork the repo  
2. `pre-commit install` (optional lint hooks)  
3. Keep CHANGELOG and Checklist up-to-date.  
4. Open PR – we love memes!

---

## ☁️ Deploy to Railway (Free 24/7)

1. **One-Click:** [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?repositoryUrl=https://github.com/your/repo)
2. Or via CLI:
   ```bash
   railway login             # first time
   railway init              # inside repo folder
   railway variables set DISCORD_TOKEN=YOUR_BOT_TOKEN
   railway up                # deploy + tail logs
   ```
3. Leave “Service Type” as **Worker** (Procfile already provided).

Railway’s free plan gives ~500 CPU-hours/month – perfect for a small bot. It persists the `meme_bot.db` volume automatically.

---

MIT License • 2025

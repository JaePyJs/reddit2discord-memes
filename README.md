# 🎉 Reddit2Discord: Memes & Music Bot

A versatile Discord bot that brings the freshest memes from Reddit to your server, lets users create custom memes, and plays music in voice channels!

---

## 🚀 Quick Launch

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy .env.example to .env and configure your secrets
cp .env.example .env
# Edit .env with your API keys and tokens

# 3. Start the bot
python -m bot.main
```

> SQLite database (`data/meme_bot.db`) stores all settings, templates, and user data – safe across restarts.

### 🔐 Security

This project follows strict security practices to protect sensitive information:

- **Never commit API keys or tokens to the repository**
- Store all sensitive information in the `.env` file (which is git-ignored)
- Use the provided security tools to prevent accidental leaks:
  - Pre-commit hook: `cp scripts/pre-commit .git/hooks/ && chmod +x .git/hooks/pre-commit`
  - Secret scanner: `python scripts/check_secrets.py`

For detailed security guidelines, see [SECURITY.md](docs/SECURITY.md) and [API_SETUP.md](docs/API_SETUP.md).

---

## 🛠️ Creating a Discord Bot

...

| Slash Command      | Description                                                                        |
| ------------------ | ---------------------------------------------------------------------------------- |
| `/meme_create`     | Generate a meme from a template with customizable text, position, and font options |
| `/template_upload` | Upload a new meme template to use with the meme creator                            |
| `/template_browse` | Browse all available meme templates                                                |

### Reddit Integration

...

| Slash Command     | Description                                    |
| ----------------- | ---------------------------------------------- |
| `/join`           | Join your current voice channel                |
| `/play <search>`  | Play a song from YouTube (URL or search query) |
| `/pause`          | Pause the currently playing song               |
| `/resume`         | Resume playback of a paused song               |
| `/skip`           | Skip the currently playing song                |
| `/queue`          | View the current song queue                    |
| `/volume <0-100>` | Adjust the playback volume                     |
| `/loop`           | Toggle looping of the current song             |
| `/nowplaying`     | Show details about the currently playing song  |
| `/leave`          | Leave the voice channel and clear the queue    |

---

## ✨ Features

### 🤖 AI Chat

The bot includes an AI-powered chat feature using Llama 4 Maverick through OpenRouter:

- `/ai_chat_set` - Designate a channel for AI chat conversations
- `/clear_chat` - Clear conversation history (optionally specify number of messages)
- `/delete_messages` - Remove actual messages from the chat channel
- `/ai_chat_help` - Display help information for using the AI chat
- `/ai_preferences` - Set your personal preferences for AI chat interactions
- `/ai_preferences_view` - View your current AI chat preferences

Simply send messages in the designated AI chat channel to interact with the bot.

#### 🔧 AI Chat Preferences

Customize your AI chat experience with personalized preferences:

- **Tone**: Choose from super casual, casual, neutral, or formal communication styles
- **Emoji Usage**: Control how many emojis appear in responses
- **Name Addressing**: Decide if the AI should address you by name in responses

### 🎭 Meme Creation

- Create memes with customizable text positioning
- Automatic text scaling to fit available space
- Upload and manage custom templates
- Browse available templates with creator information
- Adaptive text colors based on background luminance

---

## 🎵 Music Player

The bot includes a powerful music player with the following features:

- Play music from YouTube, Spotify, and direct audio URLs
- Support for Spotify tracks, albums, and playlists
- Real-time progress bar for currently playing tracks
- Queue management with pagination
- Volume control and looping
- Song recommendations based on currently playing track
- Caching for faster Spotify track processing
- Enhanced metadata display including album art

### Music Commands

- `/join` - Join your current voice channel
- `/joinvc` - Join a specific voice channel
- `/play` - Play a song from YouTube search or URL
- `/spotify_more` - Add more tracks from a Spotify playlist or album with pagination
- `/recommend` - Get song recommendations based on the currently playing track
- `/pause` - Pause the currently playing song
- `/resume` - Resume playback
- `/skip` - Skip to the next song
- `/queue` - View the current song queue
- `/volume` - Adjust the playback volume (0-100)
- `/loop` - Toggle song repetition
- `/nowplaying` - Show details about the current song with progress bar
- `/leave` - Disconnect from voice channel

The bot automatically mutes itself to avoid hearing its own audio output.

---

## 🌟 Additional Features

### 🖼️ GIF Search

The bot includes integration with the Tenor GIF API:

- `/gif <query>` - Search for and post a GIF
- `/trending_gifs` - Show trending GIFs

### 🌦️ Weather Forecasts

Get weather information using the OpenWeatherMap API:

- `/weather <location>` - Get current weather for a location
- `/forecast <location> <days>` - Get weather forecast for a location

### 📚 Urban Dictionary

Look up slang terms and internet culture definitions:

- `/define <term>` - Look up a slang term on Urban Dictionary
- `/urban_random` - Get a random definition from Urban Dictionary

## 🗺️ Future Roadmap

• User ratings and leaderboards
• More music sources (SoundCloud)
• Advanced audio effects and filters
• Playlist management
• Meme challenges and competitions

---

## ❤️ Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📁 Project Structure

```plaintext
reddit2discord_memes/
├── bot/                      # Main bot package
│   ├── __init__.py
│   ├── main.py               # Main entry point
│   ├── core/                 # Core bot functionality
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration
│   │   ├── db.py             # Database operations
│   │   ├── dependency_checker.py # Dependency verification
│   │   ├── analytics.py      # Analytics tracking
│   │   └── performance_monitor.py # Performance monitoring
│   ├── features/             # Feature modules
│   │   ├── __init__.py
│   │   ├── memes/            # Meme generation
│   │   ├── music/            # Music player
│   │   ├── reddit/           # Reddit integration
│   │   ├── ai/               # AI chat
│   │   ├── tenor/            # GIF search
│   │   ├── weather/          # Weather forecasts
│   │   ├── urban/            # Urban Dictionary
│   │   └── profiles/         # User profiles
│   └── utils/                # Utility functions
│       ├── secure_logging.py # Secure logging utilities
│       └── ...               # Other utility modules
├── assets/                   # Static assets
│   └── images/               # Image assets
├── templates/                # Meme templates
├── data/                     # Data storage
│   ├── meme_bot.db           # SQLite database
│   └── spotify_cache/        # Spotify cache
├── docs/                     # Documentation
│   ├── API_SETUP.md          # API integration setup guide
│   ├── SECURITY.md           # Security best practices
│   ├── db_schema.md          # Database schema
│   └── MONGODB_SETUP.md      # MongoDB setup guide
├── scripts/                  # Utility scripts
│   ├── check_secrets.py      # Script to detect leaked secrets
│   ├── pre-commit            # Git pre-commit hook for security
│   ├── README.md             # Scripts documentation
│   └── reorganize.sh         # Codebase reorganization script
├── tests/                    # Test files
│   ├── core/                 # Core functionality tests
│   ├── features/             # Feature-specific tests
│   ├── test_spotify_*.py     # Spotify integration tests
│   └── test_effects.py       # Meme effects tests
├── .env.example              # Example environment variables (template)
├── .gitignore                # Git ignore file
├── requirements.txt          # Dependencies
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # License information
└── README.md                 # Documentation
```

---

## 📝 License

MIT License • 2025

---

## 🙏 Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [Pillow](https://python-pillow.org/) - Image processing library
- [spotipy](https://github.com/spotipy-dev/spotipy) - Spotify API wrapper
- [Tenor API](https://developers.google.com/tenor/guides/quickstart) - GIF search API
- [OpenWeatherMap API](https://openweathermap.org/api) - Weather data API
- [Urban Dictionary API](https://github.com/zdict/zdict/wiki/Urban-dictionary-API-documentation) - Slang definitions API

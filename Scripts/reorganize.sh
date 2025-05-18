#!/bin/bash

# Create necessary directories
mkdir -p data/spotify_cache

# Move files to new structure
cp bot/main.py.new bot/main.py
cp README.md.new README.md

# Create data directory if it doesn't exist
mkdir -p data

# Move database if it exists
if [ -f meme_bot.db ]; then
    mv meme_bot.db data/
fi

echo "Reorganization complete!"

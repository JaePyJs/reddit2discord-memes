# API Integration Setup Guide

This guide explains how to set up the various API integrations used by the bot.

## Table of Contents

1. [Tenor GIF API](#tenor-gif-api)
2. [OpenWeatherMap API](#openweathermap-api)
3. [Urban Dictionary API](#urban-dictionary-api)
4. [Spotify API](#spotify-api)
5. [OpenRouter API](#openrouter-api)

## Tenor GIF API

The Tenor GIF API is used for searching and posting GIFs.

### Getting an API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Tenor API for your project
4. Create an API key
5. Add the API key to your `.env` file:

```
TENOR_API_KEY=your_api_key_here
```

### Features

- `/gif <query>` - Search for and post a GIF
- `/trending_gifs` - Show trending GIFs

### Documentation

For more information, see the [Tenor API documentation](https://developers.google.com/tenor/guides/quickstart).

## OpenWeatherMap API

The OpenWeatherMap API is used for weather forecasting.

### Getting an API Key

1. Go to the [OpenWeatherMap website](https://openweathermap.org/)
2. Sign up for a free account
3. Go to your account dashboard and get your API key
4. Add the API key to your `.env` file:

```
OPENWEATHERMAP_API_KEY=your_api_key_here
```

### Features

- `/weather <location>` - Get current weather for a location
- `/forecast <location> <days>` - Get weather forecast for a location

### Documentation

For more information, see the [OpenWeatherMap API documentation](https://openweathermap.org/api).

## Urban Dictionary API

The Urban Dictionary API is used for looking up slang terms and internet culture definitions.

### API Key

No API key is required for the Urban Dictionary API.

### Features

- `/define <term>` - Look up a slang term on Urban Dictionary
- `/urban_random` - Get a random definition from Urban Dictionary

### Documentation

The Urban Dictionary API is not officially documented, but you can find information about it in various places, such as [this unofficial documentation](https://github.com/zdict/zdict/wiki/Urban-dictionary-API-documentation).

## Spotify API

The Spotify API is used for music playback and integration with Spotify.

### Getting API Credentials

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Sign in with your Spotify account
3. Create a new application
4. Get your Client ID and Client Secret
5. Add the credentials to your `.env` file:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

### Features

- Play Spotify tracks, albums, and playlists
- Search for music on Spotify
- Get recommendations based on tracks, artists, or genres

### Documentation

For more information, see the [Spotify API documentation](https://developer.spotify.com/documentation/web-api/).

## OpenRouter API

The OpenRouter API is used for AI chat functionality.

### Getting an API Key

1. Go to the [OpenRouter website](https://openrouter.ai/)
2. Sign up for an account
3. Get your API key
4. Add the API key to your `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
```

### Features

- AI chat in designated channels
- DM conversations with the AI
- User preferences for AI interactions

### Documentation

For more information, see the [OpenRouter API documentation](https://openrouter.ai/docs).

# MongoDB Setup Guide for Discord Bot

This guide will walk you through setting up MongoDB for your Discord bot, using MongoDB Compass as a graphical interface.

## Prerequisites

- MongoDB Compass installed (you mentioned you already have this)
- Python packages installed (`pymongo`, `motor`, `dnspython`)

## Step 1: Start MongoDB Server

If you're using MongoDB Compass with a local MongoDB server:

1. Make sure your MongoDB server is running
   - On Windows, it should be running as a service named "MongoDB"
   - You can check in Services (services.msc) or Task Manager

If you're not sure if MongoDB is running, you can start it manually:

```cmd
"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath="C:\data\db"
```

(Adjust the path based on your MongoDB installation)

## Step 2: Connect with MongoDB Compass

1. Open MongoDB Compass
2. Connect to your local MongoDB server:
   - Use the connection string: `mongodb://localhost:27017`
   - Click "Connect"

## Step 3: Create the Discord Bot Database

1. In MongoDB Compass, click the "+" button next to "Databases"
2. Enter "discord_meme_bot" for the Database Name
3. Enter "ai_channels" for the Collection Name (we'll create more collections later)
4. Click "Create Database"

## Step 4: Run the Bot's MongoDB Initialization Script

Now that your database is ready, initialize the required collections:

```cmd
cd c:\Users\jmbar\Downloads\reddit2discord_memes
python init_mongodb.py
```

This will create the following collections:

- ai_channels: Stores which channel in each guild is set for AI chat
- ai_conversations: Stores conversation metadata
- ai_messages: Stores the actual messages in conversations
- ai_user_preferences: Stores user preferences for AI chat

## Step 5: Verify Your Configuration

Ensure your .env file has the correct MongoDB settings:

```
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=discord_meme_bot
USE_MONGO_FOR_AI=True
```

## Step 6: Test the MongoDB Integration

Run the test script to verify everything is working:

```cmd
python test_mongodb.py
```

You should see "✅ MongoDB integration test successful!" if everything is set up correctly.

## Step 7: Run Your Discord Bot

Start your bot with MongoDB support enabled:

```cmd
python -m bot.main
```

## Using MongoDB Compass to Manage Data

MongoDB Compass provides an intuitive interface for managing your database:

1. **Viewing Data**: Click on any collection to view its documents
2. **Querying Data**: Use the filter bar to query documents (e.g., `{"guild_id": "123456789"}`)
3. **Modifying Data**: Click on any document to edit its fields
4. **Indexing**: In the "Indexes" tab, you can view and manage indexes

## Monitoring Bot Activity

As users interact with your bot's AI chat features, you'll see data appear in:

1. **ai_channels**: Shows which Discord channels have AI chat enabled
2. **ai_conversations**: Tracks ongoing conversations
3. **ai_messages**: Contains the actual messages exchanged
4. **ai_user_preferences**: Stores personalized settings for users

## Troubleshooting

If you encounter issues:

1. **Connection Problems**: Ensure MongoDB server is running
2. **Missing Collections**: Run `init_mongodb.py` again
3. **Error Messages**: Check the bot logs for specific errors
4. **Data Not Saving**: Verify `USE_MONGO_FOR_AI=True` in your .env file
5. **Permissions Issues**: Ensure MongoDB has appropriate filesystem permissions

## Additional Features

Now that MongoDB is set up, you can:

1. Set personalized AI preferences with `/ai_preferences`
2. View your current settings with `/ai_preferences_view`
3. Enjoy persistent conversations that survive bot restarts
4. Experience AI responses tailored to your preferred style

# MongoDB Quick Reference Guide

This document provides useful MongoDB commands for managing your Discord bot data.

## Connecting to MongoDB

### MongoDB Compass (GUI)

1. Connect with URI: `mongodb://localhost:27017`
2. Navigate to the `discord_meme_bot` database
3. Select a collection to view documents

### MongoDB Shell (Command line)

```
mongosh "mongodb://localhost:27017/discord_meme_bot"
```

## Common MongoDB Commands

### View Collections

```javascript
// List all collections
show collections

// Count documents in a collection
db.ai_messages.countDocuments()

// Get collection statistics
db.ai_channels.stats()
```

### Query Documents

```javascript
// Find all documents in a collection
db.ai_channels.find();

// Pretty-print results
db.ai_channels.find().pretty();

// Find by specific field
db.ai_channels.find({ guild_id: "123456789" });

// Find with multiple conditions
db.ai_conversations.find({
  is_archived: false,
  is_dm: false,
});

// Find with projection (only return specific fields)
db.ai_messages.find({ role: "user" }, { content: 1, timestamp: 1, _id: 0 });

// Find most recent conversations
db.ai_conversations.find().sort({ last_activity: -1 }).limit(5);

// Find users with specific preferences
db.ai_user_preferences.find({ tone_preference: "formal" });
```

### Update Documents

```javascript
// Update a single document
db.ai_user_preferences.updateOne(
  { user_id: "123456789" },
  { $set: { tone_preference: "casual" } }
);

// Update multiple documents
db.ai_conversations.updateMany(
  { is_archived: false },
  { $set: { is_archived: true } }
);

// Increment a field
db.ai_user_preferences.updateOne(
  { user_id: "123456789" },
  { $inc: { message_count: 1 } }
);
```

### Delete Documents

```javascript
// Delete a single document
db.ai_messages.deleteOne({ _id: ObjectId("123456789abcdef") });

// Delete multiple documents
db.ai_messages.deleteMany({ conversation_id: "123456789abcdef" });

// Delete all documents older than a specific date
db.ai_messages.deleteMany({
  timestamp: { $lt: new Date("2025-01-01") },
});
```

### Aggregation (Advanced Queries)

```javascript
// Count messages by role
db.ai_messages.aggregate([{ $group: { _id: "$role", count: { $sum: 1 } } }]);

// Find average message length
db.ai_messages.aggregate([
  { $project: { length: { $strLenCP: "$content" } } },
  { $group: { _id: null, avgLength: { $avg: "$length" } } },
]);

// Find most active users
db.ai_messages.aggregate([
  { $match: { role: "user" } },
  { $group: { _id: "$user_id", messageCount: { $sum: 1 } } },
  { $sort: { messageCount: -1 } },
  { $limit: 5 },
]);
```

## Backup and Restore

### Backup Database

```cmd
mongodump --db discord_meme_bot --out C:\mongodb_backups\%date:~-4,4%%date:~-7,2%%date:~-10,2%
```

### Restore Database

```cmd
mongorestore --db discord_meme_bot C:\mongodb_backups\20250518\discord_meme_bot
```

## Monitoring

### Check Database Status

```javascript
db.stats();
```

### Check Server Status

```javascript
db.serverStatus();
```

## Performance Tips

1. Use indexes for frequently queried fields
2. Limit returned fields using projection
3. Use appropriate data types (e.g., store dates as ISODate objects)
4. Archive old conversations to maintain performance
5. Monitor database size over time
6. Use TTL (Time-To-Live) indexes for temporary data

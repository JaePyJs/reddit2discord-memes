# Meme Bot Database Schema

## templates
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- filename (TEXT, unique)
- uploader_id (TEXT)
- upload_time (DATETIME)
- is_builtin (BOOLEAN)

## user_preferences
- user_id (TEXT PRIMARY KEY)
- favorite_templates (TEXT, comma-separated or JSON)
- favorite_style (TEXT)
- notify_challenges (BOOLEAN)

## saved_memes
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- user_id (TEXT)
- meme_url (TEXT)
- saved_time (DATETIME)

## meme_history
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- server_id (TEXT)
- user_id (TEXT)
- meme_url (TEXT)
- created_time (DATETIME)
- template_filename (TEXT)

## meme_ratings
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- meme_id (INTEGER)
- user_id (TEXT)
- rating (INTEGER)
- rated_time (DATETIME)

---
- All tables use TEXT for IDs for compatibility with Discord's snowflake IDs.
- favorite_templates in user_preferences can be a comma-separated string or JSON array for extensibility.
- This schema supports all checklist features and is ready for ORM model creation.

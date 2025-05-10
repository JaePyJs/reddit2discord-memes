# Changelog

## [2025-05-10] - Activate `/meme_create` Command

### Added
- Imports for `TemplateManager`, `db`, PIL (`Image`, `ImageDraw`, `ImageFont`), `io`, `re`, `draw_wrapped_text`, `get_best_fit_font`, `get_average_luminance`, `pick_text_color`.
- Logging helpers: `log_command_registration`, `log_command_execution`.

### Changed
- Uncommented and fully implemented `/meme_create`:
  - Validates template existence via `TemplateManager`.
  - Sanitizes Discord emojis from top/bottom text.
  - Calculates bounding boxes, automatic font sizing, and adaptive text colors.
  - Draws outlined, wrapped text onto the image.
  - Supports tagging up to 5 friends.
  - Sends image from an in-memory buffer and optional mentions.
  - Logs creations to the `meme_history` SQLite table.
- Added `log_command_registration('meme_create')` call to record registration.
- Ensured `bot.run(DISCORD_TOKEN)` remains at file end.

### Removed
- Old commented-out stub implementation of `/meme_create`.

## [2025-05-10] - Switch to r/PampamilyangPaoLUL & Random Meme Fetch

### Added
- `fetch_random_new_meme` helper in `bot/integrations/reddit.py` to retrieve random image memes excluding previously posted IDs.
- Slash command `/ppl_meme` to fetch random new meme from r/PampamilyangPaoLUL.

### Changed
- Replaced `/hsr_meme` and all `HonkaiMemeRail` references with `/ppl_meme` and `PampamilyangPaoLUL` in `bot/main.py`.
- Background meme posting loop now uses `fetch_random_new_meme` and skips previously posted IDs to prevent duplicates.

## [2025-05-10] - Reddit Auto-Post System

### Added
- `bot/utils/autopost_store.py` to persist per-guild subreddit auto-post settings.
- `fetch_new_posts` and `fetch_random_best_post` helpers in `bot/integrations/reddit.py`.
- Background `autopost_loop` that polls enabled subreddits every 30 s and posts truly new image posts.
- `/reddit_autopost` slash-command to enable auto-posting for a subreddit URL in the current channel.
- `/reddit_autopost_list` slash-command that lists enabled subreddits and provides interactive Disable buttons.

### Changed
- Removed legacy `/ppl_meme` command and old meme polling loop.
- Updated `main.py` to bootstrap the new auto-post loop on `on_ready`.
- Changelog updated automatically.

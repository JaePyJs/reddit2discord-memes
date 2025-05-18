# Changelog

## [2025-05-21] - Critical Security Fix and Enhanced Protection

### Security

- **CRITICAL**: Fixed security vulnerability by removing leaked API keys from commit history
- Implemented comprehensive security measures to protect API keys:
  - Added pre-commit hook to prevent committing sensitive information
  - Created script to check for leaked secrets in the codebase
  - Added detailed security documentation in `docs/SECURITY.md`
  - Implemented secure logging system that masks sensitive information

### Added

- Added `bot/utils/secure_logging.py` module with:
  - Pattern-based detection of sensitive information
  - Automatic masking of API keys, tokens, and passwords in logs
  - Secure logger class that wraps standard logging
- Added `scripts/check_secrets.py` to scan codebase for leaked credentials
- Added `scripts/pre-commit` hook to prevent committing sensitive information
- Added `docs/SECURITY.md` with detailed security best practices

### Changed

- Updated all configuration files to use environment variables exclusively
- Improved error handling for missing or invalid API keys
- Enhanced documentation with security best practices
- Updated README.md with security guidelines and installation instructions
- Updated project structure documentation to include security components

## [2025-05-19] - New API Integrations and Enhanced Analytics

### Added

- Integrated Tenor GIF API for searching and posting GIFs
  - Added `/gif` command to search for and post GIFs
  - Added `/trending_gifs` command to show trending GIFs
- Integrated OpenWeatherMap API for weather forecasting
  - Added `/weather` command to get current weather for a location
  - Added `/forecast` command to get weather forecast for a location
- Integrated Urban Dictionary API for looking up slang terms
  - Added `/define` command to look up slang terms
  - Added `/urban_random` command to get random definitions
- Implemented comprehensive analytics system for tracking feature usage
- Added performance monitoring for API calls and command execution
- Enhanced error handling for all API interactions

### Changed

- Consolidated duplicate AI chat implementations into a single module
- Updated configuration to support new API keys
- Enhanced Spotify integration with improved caching and analytics
- Updated documentation to reflect new features and APIs

## [2025-05-18] - Comprehensive Codebase Reorganization and Spotify Enhancements

### Added

- Implemented caching system for Spotify tracks to reduce API calls
- Added pagination support for large Spotify playlists (up to 50 tracks)
- Enhanced track information display with album art and more details
- Added visual progress indicators for currently playing tracks
- Implemented song recommendations based on Spotify's API
- Created new directory structure for better organization
- Added documentation for MongoDB setup and database schema

### Changed

- Restructured the entire codebase into a more maintainable architecture
- Organized code by feature modules (memes, music, reddit, ai)
- Separated core functionality from feature-specific code
- Created proper **init**.py files for all packages
- Improved error handling and logging throughout the codebase
- Updated import statements to reflect the new structure
- Moved test files to dedicated tests directory
- Moved documentation files to docs directory
- Moved utility scripts to scripts directory
- Moved image files to assets/images directory

### Fixed

- Fixed various bugs and edge cases
- Enhanced error handling for API interactions
- Improved user experience with better feedback and visuals

## [2025-05-18] - Meme Effects System

### Added

- Comprehensive meme effects system in `bot/utils/meme_effects.py` with 9 special effects:
  - deep-fry: Intense saturation, contrast and noise
  - vaporwave: Retro 80s/90s aesthetic with purple/blue tint
  - jpeg: JPEG compression artifacts
  - glitch: Digital glitch effect with color channel shifts
  - grayscale: Black and white conversion
  - invert: Color inversion
  - blur: Soft blur effect
  - pixelate: Low-resolution pixelated look
  - sepia: Old-fashioned brownish tone
- New `/meme_effects` command to list all available effects with descriptions
- Added NumPy requirement for advanced image processing

### Enhanced

- Modified `/meme_create` to support applying effects to memes
- Updated effect parameter description to reference the new `/meme_effects` command
- Refactored code to support extensible effect system

### Fixed

- Ensured effects are only applied when explicitly requested

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

## [2025-05-10] - Dual Auto-Post (NEW & BEST)

#### Added

- Independent 5-minute auto-posting for both **newest** and **best** (top) subreddit posts.
- Visual indicators `[NEW]` (blue) and `[BEST]` (orange) in embed titles.
- `last_best_post_ts` field in `autopost_store.py` to track best-post cooldown.
- Helper `send_reddit_embed()` for consistent embed construction.

#### Changed

- Refactored `autopost_loop` to post up to two messages per cycle (latest + best) while respecting cooldowns.
- Consolidated `.gitignore` and resolved README merge conflicts.

## [2025-05-10] - Housekeeping & Persistence

### Added

- Optional `channel` parameter to `/reddit_autopost` command to select target channel.
- SQLite persistence for subreddit configurations and seen post IDs (`autopost_store.py` now writes to `meme_bot.db`).

### Changed

- Migrated storage from JSON (`autopost_store.json`) to SQLite.
- Updated `README.md` and `MemeGeneratorChecklist.md` to reflect minimal core features.
- Removed unused imports in `bot/main.py` and resolved minor lint issues.

### Removed

- Deprecated feature placeholders and overly detailed checklist items not implemented in current version.

## [2025-05-10] - Interactive List & Persistence

### Added

- Paginated `/reddit_autopost_list` view with **Prev/Next** navigation (5 subs per page) and on-the-fly disable buttons.

### Confirmed

- Auto-post configuration and seen-post IDs are now persisted in `meme_bot.db`; the list survives bot restarts, crashes, and redeploys.

## [2025-05-10] - Railway Hosting Support

### Added

- `Procfile` with `worker: python bot/main.py` so the bot can run 24/7 on Railway.
- README section detailing one-click Railway deployment & CLI instructions.

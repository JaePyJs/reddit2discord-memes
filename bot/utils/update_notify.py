import logging
import discord

# Call this from main.py after updates (e.g., template update, bot update)
async def notify_admins(bot, guild, message):
    try:
        for member in guild.members:
            if member.guild_permissions.administrator and not member.bot:
                try:
                    await member.send(f'[MemeBot Update] {message}')
                except Exception as e:
                    logging.warning(f'Failed to notify {member}: {e}')
    except Exception as e:
        logging.error(f'Failed to notify admins: {e}')

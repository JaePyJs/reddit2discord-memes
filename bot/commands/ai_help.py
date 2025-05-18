@bot.tree.command(
    name='ai_chat_help',
    description='Get help with using the AI chatbot'
)
async def ai_chat_help(interaction: discord.Interaction):
    """Display help information for the AI chatbot"""
    log_command_execution('ai_chat_help', interaction)
    
    # Create an embed with helpful information
    embed = discord.Embed(
        title="AI Chat Help",
        description="Here's how to use the AI chatbot features!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Setting up the AI Chat",
        value=(
            "Use `/ai_chat_set` to set a channel as the AI chat channel.\n"
            "Only server admins or members with the Manage Channels permission can do this.\n"
            "Once set, the bot will respond to all messages in that channel."
        ),
        inline=False
    )
    
    embed.add_field(
        name="Private Conversations",
        value=(
            "Use `/dm_chat` to start a private conversation with the AI in your DMs.\n"
            "This is perfect for having one-on-one chats without any confusion from other users."
        ),
        inline=False
    )
    
    embed.add_field(
        name="Managing Chat History",
        value=(
            "Use `/clear_chat` to clear all conversation history for the AI.\n"
            "Use `/clear_chat count:5` to clear only the 5 most recent messages.\n"
            "This helps if the AI gets confused or if you want to start a new topic."
        ),
        inline=False
    )
    
    embed.add_field(
        name="Multiple Users",
        value=(
            "The AI will try to keep track of who's talking to it in the channel.\n"
            "It will mention your name when responding to you.\n"
            "For clearer conversations, consider using the `/dm_chat` command for private chats."
        ),
        inline=False
    )
    
    embed.add_field(
        name="Deleting Messages",
        value=(
            "Use `/delete_messages count:10` to delete the last 10 messages in the channel.\n"
            "This requires the Manage Messages permission in the server."
        ),
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

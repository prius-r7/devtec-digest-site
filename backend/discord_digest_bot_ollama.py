"""
discord_digest_bot_ollama.py
===========================

This script implements a Discord digest bot that produces daily (or
configurable) summaries of your server conversations and surfaces
unanswered questions. It uses the local Ollama API to perform
summarization, eliminating reliance on paid external APIs.

To run the bot:

1. Install dependencies listed in requirements.txt.
2. Install and run Ollama (https://ollama.ai/) and pull a model,
   e.g. `ollama pull llama3:8b-instruct`.
3. Copy `.env.example` to `.env` and fill in your Discord bot token,
   guild ID, channel IDs, etc.
4. Launch the bot with `python discord_digest_bot_ollama.py`.

The bot posts digests to the channel specified in DIGEST_CHANNEL_ID
and supports summarizing on demand via the `/summarize` slash command.
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple

import discord
from discord.ext import commands, tasks
import ollama

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
DIGEST_CHANNEL_ID = os.getenv("DIGEST_CHANNEL_ID")
CHANNEL_IDS = os.getenv("CHANNEL_IDS")  # optional comma-separated list
DIGEST_INTERVAL_MINUTES = int(os.getenv("DIGEST_INTERVAL_MINUTES", "1440"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct")

if not (DISCORD_TOKEN and GUILD_ID and DIGEST_CHANNEL_ID):
    raise RuntimeError(
        "DISCORD_TOKEN, GUILD_ID and DIGEST_CHANNEL_ID must be set in the environment"
    )

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = False

bot = commands.Bot(command_prefix="!", intents=intents)


async def summarize_text(text: str) -> str:
    """Send a summarization request to the local Ollama model."""
    prompt = (
        "Summarize the following Discord conversations into a concise digest. "
        "Highlight key topics, decisions and action items. Use bullet points where appropriate.\n\n"
        f"{text}\n\nSummary:"
    )
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=False,
    )
    return response["message"]["content"].strip()


async def collect_messages(guild: discord.Guild, since: datetime) -> Tuple[str, List[discord.Message]]:
    """Collect recent messages from selected channels in the guild since the given datetime.

    Returns a tuple of concatenated message text and a list of messages.
    """
    aggregate_text: List[str] = []
    all_messages: List[discord.Message] = []
    channels: List[int] = []
    if CHANNEL_IDS:
        channels = [int(cid.strip()) for cid in CHANNEL_IDS.split(",") if cid.strip()]

    for channel in guild.text_channels:
        if channels and channel.id not in channels:
            continue
        try:
            async for msg in channel.history(after=since, limit=200):
                # ignore bot messages
                if msg.author.bot:
                    continue
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M")
                aggregate_text.append(f"[{channel.name}] {msg.author.display_name}: {msg.content}")
                all_messages.append(msg)
        except Exception:
            continue
    combined_text = "\n".join(aggregate_text)
    return combined_text, all_messages


def find_unanswered_questions(messages: List[discord.Message]) -> List[discord.Message]:
    """Return a list of messages that look like questions with no subsequent replies."""
    questions = []
    for msg in messages:
        content = msg.content.strip()
        if "?" in content and not msg.reference and not msg.author.bot:
            # consider unanswered if no reactions and no replies
            has_reply = False
            # Look through messages to see if any reply references this message
            for other in messages:
                if other.reference and other.reference.message_id == msg.id:
                    has_reply = True
                    break
            if not has_reply:
                questions.append(msg)
    return questions


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # Start the digest task
    if not digest_task.is_running():
        digest_task.start()


@tasks.loop(minutes=DIGEST_INTERVAL_MINUTES)
async def digest_task():
    guild = bot.get_guild(int(GUILD_ID))
    if not guild:
        print("Guild not found")
        return
    since = datetime.utcnow() - timedelta(minutes=DIGEST_INTERVAL_MINUTES)
    combined_text, messages = await collect_messages(guild, since)
    if not combined_text:
        print("No messages to summarize")
        return
    # Summarize via Ollama
    summary = await summarize_text(combined_text)
    # Find unanswered questions
    unanswered = find_unanswered_questions(messages)
    unanswered_lines = []
    for q in unanswered[:5]:  # show at most 5
        url = f"https://discord.com/channels/{guild.id}/{q.channel.id}/{q.id}"
        unanswered_lines.append(f"- [{q.author.display_name}]({url}): {q.content}")
    unanswered_section = (
        "\n**Unanswered Questions:**\n" + "\n".join(unanswered_lines)
        if unanswered_lines
        else ""
    )
    digest_message = f"**Daily Digest** (last {DIGEST_INTERVAL_MINUTES} min)\n\n{summary}{unanswered_section}"
    channel = guild.get_channel(int(DIGEST_CHANNEL_ID))
    if channel:
        await channel.send(digest_message)


@bot.tree.command(name="summarize", description="Generate a summary of recent conversations")
async def summarize_command(interaction: discord.Interaction):
    guild = interaction.guild
    since = datetime.utcnow() - timedelta(hours=1)
    combined_text, messages = await collect_messages(guild, since)
    if not combined_text:
        await interaction.response.send_message("No recent messages to summarize.",
                                              delete_after=10, ephermal=True)
        return
    await interaction.response.defer()
    summary = await summarize_text(combined_text)
    unanswered = find_unanswered_questions(messages)
    unanswered_lines = []
    for q in unanswered[:5]:
        url = f"https://discord.com/channels/{guild.id}/{q.channel.id}/{q.id}"
        unanswered_lines.append(f"- [{q.author.display_name}]({url}): {q.content}")
    unanswered_section = (
        "\n**Unanswered Questions:**\n" + "\n".join(unanswered_lines)
        if unanswered_lines
        else ""
    )
    digest_message = f"**Summary** (last hour)\n\n{summary}{unanswered_section}"
    await interaction.followup.send(digest_message)



def main():
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()

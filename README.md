# DevTec Digest

This repository contains the landing page and self‑hosted digest bot for **DevTec Digest**, a micro‑SaaS that posts daily digests and flags unanswered questions in Discord servers. It provides a static website for marketing plus the Python bot code to run the service yourself without any paid APIs.

## Contents

```
backend/
  discord_digest_bot_ollama.py – Python bot using Ollama for local LLM summarization
  requirements.txt – dependencies for the bot
  .env.example – environment variable template
docs/
  how-to-self-host-with-ollamda.md – guide to running the bot locally (typo)
index.html – landing page markup
style.css – styles for the site
script.js – simple JS for pricing toggle
```

## Hosting the site

This is a static site; you can deploy it on GitHub Pages or any other static hosting provider. To publish on GitHub Pages:

1. Upload the repository to your GitHub account.
2. Go to repository settings → Pages → Source and choose the `main` branch.
3. After saving, your site will be live at `https://<username>.github.io/<repo>`.

## Running the bot

The digest bot lives in the `backend` directory. It uses `discord.py` and an Ollama model to generate summaries locally. To run it:

1. Install Python 3.9+.
2. Navigate to `backend` and run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and fill in your Discord bot token, server ID and channel ID.
4. Install Ollama and pull a model (e.g. `ollama pull llama3:8b-instruct`).
5. Run `python discord_digest_bot_ollama.py` to start the bot.

For detailed instructions, see the guide in `docs/how-to-self-host-with-ollamda.md`.

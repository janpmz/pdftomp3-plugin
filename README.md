# PDFTOMP3-Plugin

Create audiobooks with PDFTOMP3. This Codex plugin helps your AI to prepare text for reading aloud, explain key ideas, or generate multi-speaker conversations. PDFTOMP3 then converts that text into MP3 files on our servers.

The plugin runs locally in Codex and requires Python 3.10 or later. It has no extra Python dependencies and connects to the live PDFTOMP3 service.

The audiobook will appear in your library on the website: https://pdftomp3.com/

Set your API-Key here: https://pdftomp3.com/connect-ai/


## Install in Codex

1. Copy this repository URL: `https://github.com/janpmz/pdftomp3-plugin`
2. In Codex, open **Plugins** → **Add** → **Add a marketplace**.
3. Paste the URL into **Source** and click **Add marketplace**. Leave the branch and path fields empty to use the default branch and root.
4. Select the **PDFTOMP3-Plugin** marketplace and click **Install** on **PDFTOMP3-Plugin**.
5. Start a new chat and ask:

```text
Set up PDFTOMP3-Plugin and connect my account.
```

The helper opens your browser. Sign in to PDFTOMP3 and click **Connect**. If speech setup is incomplete, Codex provides a link to save or select your own OpenAI or Gemini speech key. Enter the key on that site—never in the chat.

## Create your first audiobook

Attach a PDF in Codex and ask:

```text
Use PDFTOMP3-Plugin to read this PDF aloud, with a second speaker to explain each paragraph.
```

You can also request the original wording, a plain explanation, a summary, or a multi-speaker conversation. Codex writes the spoken text in the chat. PDFTOMP3 stores it and generates the audio. Open the returned player link and press **Play**.

Your AI chat’s plan and limits cover text preparation. For the finished audiobook, your saved OpenAI or Gemini key covers speech costs; PDFTOMP3 subscription credits do not.

## Sign-in and saved keys

The helper stores sign-in tokens as plain text in your user data folder (outside this repository) and restricts file access to your account. Other apps running as you, or administrators, can still access them. Speech keys remain on the website.

Ask Codex to disconnect PDFTOMP3-Plugin to sign out. You can also revoke the connection on the website.

## Use the terminal

```sh
codex plugin marketplace add janpmz/pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

Then start a new chat and run the setup prompt above.

## Updates

Refresh the PDFTOMP3-Plugin marketplace, reinstall the plugin, and start a new chat. From the terminal:

```sh
codex plugin marketplace upgrade pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

See the [OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli) for more on GitHub marketplace sources.

# PDFTOMP3-Plugin

Create audiobooks with PDFTOMP3. This Codex plugin helps your AI to prepare text for reading aloud, explain key ideas, or generate multi-speaker conversations. PDFTOMP3 then converts that text into MP3 files on our servers.

The plugin includes the PDFTOMP3-MCP connection and connects to the live PDFTOMP3 service. Codex handles sign-in. You need no Python, helper program, or separate MCP setup.

The audiobook will appear in your library on the website: https://pdftomp3.com/

Set your API-Key here: https://pdftomp3.com/connect-ai/

Audio examples: https://pdftomp3.com/examples/

## Install in Codex

1. Copy this repository URL: `https://github.com/janpmz/pdftomp3-plugin`
2. In Codex, open **Plugins** → **Add** → **Add a marketplace**.
3. Paste the URL into **Source** and click **Add marketplace**. Leave the branch and path fields empty to use the default branch and root.
4. Select the **PDFTOMP3-Plugin** marketplace and click **Install** on **PDFTOMP3-Plugin**.
5. When Codex asks to connect, sign in to PDFTOMP3 in your browser and click **Connect**. Then start a new chat.

If you need help with the connection or speech setup, ask:

```text
Set up PDFTOMP3-Plugin and connect my account.
```

If speech setup is incomplete, Codex provides a link to save or select your own OpenAI or Gemini speech key. Enter the key on that site—never in the chat. If you already have a speech key saved and selected, you can use it.

## Create your first audiobook

Attach a PDF in Codex and ask:

```text
Use PDFTOMP3-Plugin to read this PDF aloud, with a second speaker to explain each paragraph.
```

You can also request the original wording, a plain explanation, a summary, or a multi-speaker conversation. Codex writes the spoken text in the chat. PDFTOMP3 stores it and generates the audio. Open the returned player link and press **Play**.

Your AI chat’s plan and limits cover text preparation. For the finished audiobook, your saved OpenAI or Gemini key covers speech costs; PDFTOMP3 subscription credits do not.

## Sign-in and saved keys

Codex manages the MCP connection and saved sign-in. The plugin does not keep its own token file. Speech keys remain on the website.

Use the plugin's connection controls in Codex to disconnect. You can also revoke the connection on the website.

## Use the terminal

```sh
codex plugin marketplace add janpmz/pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

Complete the connection in Codex, then start a new chat.

## Updates

Refresh the PDFTOMP3-Plugin marketplace, reinstall the plugin, and start a new chat. From the terminal:

```sh
codex plugin marketplace upgrade pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

If you used version 0.1.x, connect once through Codex after updating. The plugin does not import the old Python helper's saved sign-in. You can revoke that old connection on the website.

See the [OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli) for more on GitHub marketplace sources.

# PDFTOMP3-Plugin

Turn PDFs into audiobooks with PDFTOMP3. This Codex plugin gives your AI the skills to prepare text for reading aloud, explain key ideas, or write conversations with several speakers. PDFTOMP3 then turns that text into MP3 files on our servers.

This plugin runs in Codex on your computer and needs Python 3.10 or later. It needs no extra Python packages. It connects to the live PDFTOMP3 service.

## Install in Codex

1. Copy this GitHub URL: `https://github.com/janpmz/pdftomp3-plugin`.
2. In Codex, open **Plugins**, click **Add**, then **Add a marketplace**.
3. Paste the GitHub URL into **Source** and click **Add marketplace**. Leave the branch and path fields empty to use this repository's default branch and root folder.
4. Choose the **PDFTOMP3-Plugin** marketplace and click **Install** on **PDFTOMP3-Plugin**.
5. Start a new chat and ask:

```text
Set up PDFTOMP3-Plugin and connect my account.
```

The helper opens your browser. Sign in to PDFTOMP3 and choose **Connect**. If speech setup is missing, Codex gives you a link to save or select your own OpenAI or Gemini speech key. Enter it on that website, never in the chat.

## Make your first audiobook

Attach a PDF in Codex and ask:

```text
Use PDFTOMP3-Plugin to read this PDF aloud, with a second speaker to explain each paragraph.
```

You can also ask for the original wording, a plain explanation, a summary, or a conversation with several speakers. Codex writes the spoken text in your chat. PDFTOMP3 saves that text and makes the speech. Open the returned player link and press **Play**.

Your AI chat's plan and limits apply to reading and writing the text. For prepared audiobooks, your saved OpenAI or Gemini key pays for speech; PDFTOMP3 subscription credits do not pay for it.

## Sign-in and saved keys

The helper saves sign-in tokens as plain text in your user data folder, outside this repository. It limits file access to your user account. Apps running as you and administrators can still gain access. Speech keys stay on the website.

Ask Codex to disconnect PDFTOMP3-Plugin when you want to sign out. You can also revoke the connection on the website.

## Use a terminal instead

```sh
codex plugin marketplace add janpmz/pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

Then start a new chat and run setup as above.

## Updates

Refresh the PDFTOMP3-Plugin marketplace, reinstall the plugin, and start a new chat. In a terminal:

```sh
codex plugin marketplace upgrade pdftomp3-plugin
codex plugin add pdftomp3-plugin@pdftomp3-plugin
```

The [OpenAI plugin guide](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli) describes GitHub marketplace sources.

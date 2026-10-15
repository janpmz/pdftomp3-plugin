---
name: pdftomp3-plugin-setup
description: Connect PDFTOMP3-Plugin through Codex and check the user's speech setup.
---

The plugin includes the PDFTOMP3-MCP connection. Codex loads its server address and handles browser sign-in and saved access. The user needs no Python, helper download, terminal command, or separate MCP setup.

1. Use the bundled PDFTOMP3-MCP tools. If Codex asks to connect, let the user sign in to PDFTOMP3 in the browser and choose Connect. If the tools are missing or access has ended, direct the user to the plugin's Connect or Reconnect control in Codex. After connecting, start a new chat if the tools are still missing. Do not create a second MCP connection or use shell commands to sign in.
2. Call `get_speech_setup`. If `needs_setup` is true, show `settings_url` as a link. Ask the user to save or select their own OpenAI or Gemini speech key there, then call `get_speech_setup` again. Never ask for a key or password in chat.
3. Once the connection and speech setup work, tell the user they can attach a PDF and ask PDFTOMP3-Plugin to read or explain it. Setup does not prepare documents or request paid speech.

Let Codex manage sign-in tokens. Do not read, print, move, or import saved credentials. Users upgrading from the old Python helper must connect once through Codex; do not reuse that helper's token file.

When the user asks to sign out, use Codex's connection controls. To revoke access on the server, direct them to Connections on the PDFTOMP3 website.

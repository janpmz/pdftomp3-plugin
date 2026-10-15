---
name: pdftomp3-plugin-setup
description: Install the PDFTOMP3-Plugin helper, connect the user's account, or fix its sign-in and speech setup.
---

Use the bundled helper at `../pdftomp3-plugin/scripts/pdftomp3.py`, resolved from this skill's folder. Use its full path in commands. It runs on the user's computer and needs Python 3.10 or later.

On Windows, use `py -3` if `python3` is not available. Keep the same helper path and arguments.

1. Run `python3 <helper> install`. It prepares the user's data folder and returns `sign_in_file`, the path where it will save sign-in tokens as plain text JSON. It needs no extra Python packages.
2. Run `python3 <helper> status`. If it reports `SIGN_IN_REQUIRED`, or `connected: false`, run `python3 <helper> login`. Keep the process running while the user signs in. Show its returned sign-in link if the browser did not open. Finish the same process; do not start a second login.
3. Check `python3 <helper> speech-setup`. If `needs_setup` is true, show `settings_url` as a link. Tell the user to save or select their own OpenAI or Gemini speech key there, then check again. Never ask for a key or password in chat.
4. Once connected, tell the user they can attach a document and ask PDFTOMP3-Plugin to read or explain it.

No MCP connection is needed. The helper calls the website's API and renews sign-in as needed. Use `logout` when the user asks to disconnect. It revokes access before removing the saved sign-in. A failed sign-out still needs another attempt or Disconnect on the website.

Let the helper manage its sign-in file and set access for the user's account. Do not read it into chat, print its contents, or copy it into the task or plugin folder. If the helper cannot set access rules, save the file, or read it, report its message. Do not bypass the file access checks.

Use the server address shipped with the helper. The install result shows it as `api_url`. Override it with `--api-url` only when the user asks to use a different server. Setup makes no speech requests.

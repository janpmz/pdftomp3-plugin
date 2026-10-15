# Prepared documents

In these commands, `<helper>` means the full path to `../scripts/pdftomp3.py`. Put request files in the task's workspace, outside the installed plugin. Use UTF-8 JSON. The helper also accepts `--input -` to read a request from standard input.

1. Check `speech-setup`, then run `voices`. Use only returned voice IDs. For an existing document, use `voices --document-id <id>` to get its saved speech service and model.
2. Write the chapters and spoken text from the source in this chat, following the writing guide in [SKILL.md](../SKILL.md).
3. Choose a fresh `request_id` for each new draft. Run `begin --input <draft.json>` and save the returned `document_id`. Keep that request ID for retries.
4. Run `chapter --input <chapter.json>` for each top-level chapter, in order from index zero.
5. Run `finish --document-id <id>` after every chapter is saved. This seals the text and starts no paid work.
6. When the user requests speech, run `audio --document-id <id> --paid-audio`. Return its player link.
7. Check progress and speech cost with `get --document-id <id>`. Use a short wait between checks; do not keep polling unchanged work.

## Normal reading or explanations

Start a draft:

```json
{
  "request_id": "source-volume-one",
  "title": "A clear title",
  "summary": "A short account of the source.",
  "language": "en",
  "mode": "original",
  "agent": "codex",
  "chapter_count": 1
}
```

Use `original` to keep the wording, with small changes for speech. Use `teacher` when the user asks for plain explanations. An optional `default_voice` must match a returned voice ID. Omitting it uses the service's default. `chapter_count` counts only top-level chapters.

Send a chapter:

```json
{
  "document_id": "<returned ID>",
  "chapter_index": 0,
  "title": "First chapter",
  "pages": [
    {
      "title": "First passage",
      "text": "The source text.",
      "spoken_text": "The final text to read aloud."
    }
  ]
}
```

Each page is one reading passage, not necessarily a printed page. Keep a sentence together. In normal reading, each page needs source `text` and final `spoken_text`. Write explanations here; the server makes speech from the words you send.

## Several speakers

Use `mode: "script"` and set `speakers` when starting the draft:

```json
{
  "request_id": "reading-with-explanations-one",
  "title": "Read and explain",
  "language": "en",
  "mode": "script",
  "agent": "codex",
  "chapter_count": 1,
  "speakers": [
    { "id": "reader", "name": "Alex", "voice": "<listed voice>" },
    { "id": "explainer", "name": "Anna", "voice": "<listed voice>" },
    { "id": "recap", "name": "Ben", "voice": "<listed voice>" }
  ]
}
```

Keep each person's ID, name, and voice fixed. Use the user's names, or choose plain names when none were given. Names label the passages; they are not spoken words. Do not use roles, gender, or voice IDs as names.

Each page has ordered turns:

```json
{
  "document_id": "<returned ID>",
  "chapter_index": 0,
  "title": "First chapter",
  "pages": [
    {
      "title": "First point",
      "text": "The source paragraph.",
      "spoken_segments": [
        { "speaker": "reader", "text": "The source paragraph." },
        { "speaker": "explainer", "text": "A plain explanation." },
        { "speaker": "recap", "text": "A short account of the section." }
      ]
    }
  ]
}
```

Send either `spoken_text` or `spoken_segments`, never both. A podcast may omit source `text`. When requested, put each reading immediately before its explanation, then add the recap after a larger section. Vary spoken lead-ins when the user asks. Each turn uses the saved speaker ID; no special field is needed for a recap.

## Nested chapters and limits

Keep up to three chapter levels. Put children in `subchapters`, using the same `title`, `pages`, and optional `subchapters` fields. A chapter's own pages play before its children. Use `pages: []` for a heading with children. Every chapter needs text or children.

- At most 100 chapters per document, including children, and 100 pages per chapter.
- At most 10,000 source characters and 20,000 spoken characters per page.
- Source plus spoken text: 200,000 characters per chapter call and 500,000 per document.
- At most 20 unfinished drafts.

Use a new draft for changes to saved text or speakers. Use the same request ID for a retry of the same draft. A rejected call saves no part of that step. Read the returned field errors and correct the request.

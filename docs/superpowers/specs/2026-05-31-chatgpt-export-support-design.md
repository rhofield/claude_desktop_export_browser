# ChatGPT Export Support Design

## Goal

Extend the existing Claude export browser so it can browse and export standard text conversations from both Claude and ChatGPT `conversations.json` exports while preserving current Claude behavior.

## Scope

This first version supports standard text ChatGPT conversations only. It does not render attachments, images, canvas data, code-interpreter artifacts, or tool output as Markdown. Unsupported non-text source data remains available in the exported JSON through a preserved `raw` field.

The application remains a terminal-based, standard-library Python tool. No third-party dependencies are introduced.

## User-Facing Behavior

The primary executable becomes `chat_export_browser.py`.

Example usage:

```bash
./chat_export_browser.py ./data-export-folder
./chat_export_browser.py ./data-export-folder/conversations.json
./chat_export_browser.py ./data-export-folder --all
./chat_export_browser.py ./data-export-folder --all --output-format md
```

The existing `claude_chat_browser.py` file remains as a small compatibility wrapper that delegates to `chat_export_browser.py`. This avoids abruptly breaking existing shell history, documentation links, or user habits.

The UI and exported Markdown use provider-neutral language:

```text
CHAT EXPORT BROWSER
Export your AI chat conversations
```

Markdown speaker labels are provider-neutral:

```markdown
**User**:
**Assistant**:
**System**:
**Tool**:
```

## Architecture

The implementation keeps the current single-script structure, but renames the main script to `chat_export_browser.py` and renames `ClaudeChatBrowser` to `ChatExportBrowser`.

The key design change is a normalization layer. The loader reads `conversations.json`, detects whether the export is Claude or ChatGPT, and converts each raw conversation into one canonical internal shape before the UI or exporter sees it.

Canonical conversation shape:

```python
{
    "id": "conversation-id",
    "source": "claude" | "chatgpt",
    "title": "Conversation title",
    "updated_at": "timestamp string",
    "messages": [
        {
            "sender": "user" | "assistant" | "system" | "tool" | "unknown",
            "text": "message text",
            "created_at": "timestamp string"
        }
    ],
    "raw": {...}
}
```

The UI, batch exporter, Markdown exporter, and JSON exporter use only this normalized shape.

## Format Detection

Detection happens after loading `conversations.json`.

Claude export detection:

- Top-level JSON is a list.
- At least one conversation contains `chat_messages`.
- Claude conversations usually include fields such as `uuid`, `name`, `updated_at`, and message-level `sender`.

ChatGPT export detection:

- Top-level JSON is a list.
- At least one conversation contains `mapping`.
- ChatGPT conversations usually include fields such as `id`, `title`, `create_time`, `update_time`, and nested `message.author.role`.

If the format cannot be detected, the program exits with a clear error:

```text
Error: unsupported conversations.json format. Expected a Claude or ChatGPT conversations export.
```

## Claude Normalization

Claude normalization preserves current behavior while translating field names.

Rules:

- `id` comes from `uuid`, falling back to `id`, then `"unknown"`.
- `title` comes from `name`, falling back to the first human text message, then `"Untitled conversation"`.
- `updated_at` comes from `updated_at`.
- Messages come from `chat_messages`.
- Message `sender` maps as:
  - `human` to `user`
  - `assistant` to `assistant`
  - any other Claude sender value to `assistant`, preserving the current app behavior where every non-human message is rendered as the assistant.
- Message text comes from `text`, falling back to text items in `content`.
- `raw` stores the original Claude conversation object.

## ChatGPT Normalization

ChatGPT normalization supports standard text messages from the `mapping` graph.

Rules:

- `id` comes from `id`, falling back to `"unknown"`.
- `title` comes from `title`, falling back to the first user message text, then `"Untitled conversation"`.
- `updated_at` comes from `update_time`, falling back to the latest message `create_time`.
- Messages come from `mapping` node values.
- Nodes with no `message` are skipped.
- Messages with no text content are skipped.
- Messages are sorted by `create_time`.
- `author.role` maps as:
  - `user` to `user`
  - `assistant` to `assistant`
  - `system` to `system`
  - `tool` to `tool`
  - any other role to `unknown`
- Text comes from `message.content.parts`.
- Only string `parts` are rendered to Markdown in this first version.
- Non-string parts and other unsupported content remain preserved in `raw`.

ChatGPT timestamps may be numeric Unix timestamps. The normalized `created_at` and `updated_at` values should be converted to ISO-like UTC strings when possible so existing date formatting code can continue to work consistently. If conversion fails, the original value should be stringified.

## Export Behavior

Markdown export uses normalized fields:

- Heading from `title`.
- Date from `updated_at`.
- ID from `id`.
- Messages from `messages`.
- Speaker labels from normalized `sender`.

JSON export writes the normalized conversation, including `raw`.

This makes JSON exports useful for downstream tooling while preserving the full original provider data for unsupported content.

## Error Handling

The loader should fail clearly when:

- The input path does not exist.
- The input path is a file other than `conversations.json`.
- The export directory does not contain `conversations.json`.
- The JSON cannot be parsed.
- The parsed JSON is not a list of conversations.
- The format is neither recognized Claude nor recognized ChatGPT.

Individual malformed conversations should not crash `--all` export. Batch mode should warn and continue, matching the existing failed-export behavior.

## Testing

Add a `tests/` directory using Python's standard-library `unittest`.

Fixtures:

- A minimal Claude `conversations.json` fixture with one user message and one assistant message.
- A minimal ChatGPT `conversations.json` fixture with one user message and one assistant message in `mapping`.
- A ChatGPT fixture containing empty or non-text nodes to verify they are skipped in Markdown but preserved in `raw`.

Test coverage:

- Claude format detection.
- ChatGPT format detection.
- Unsupported format produces a clear error path.
- Claude normalization preserves title, ID, date, and messages.
- ChatGPT normalization extracts title, ID, date, sorted messages, and text.
- Markdown export uses provider-neutral speaker labels.
- JSON export includes normalized fields and `raw`.
- Batch export still supports `--output-format both`, `md`, and `json`.

## Documentation

Update `README.md`, `docs/DEVELOPMENT.md`, and `CLAUDE.md` to describe the project as a generic chat export browser.

Documentation should state:

- Claude exports are supported.
- Standard text ChatGPT exports are supported.
- ChatGPT attachments, images, canvas data, code-interpreter artifacts, and rich tool outputs are not rendered to Markdown in the first version.
- Unsupported raw data remains available in JSON exports.
- `chat_export_browser.py` is the primary command.
- `claude_chat_browser.py` remains available as a compatibility wrapper.

## Non-Goals

This design does not add:

- Web UI.
- Search.
- Date filtering.
- Attachment extraction.
- Image rendering.
- Canvas rendering.
- Code-interpreter artifact export.
- Support for providers other than Claude and ChatGPT.
- Third-party dependencies.

## Acceptance Criteria

- Existing Claude exports still browse and export successfully.
- Standard text ChatGPT exports browse and export successfully.
- The new primary script name is `chat_export_browser.py`.
- The old script name still works as a wrapper.
- Markdown exports are provider-neutral.
- JSON exports preserve raw source data.
- Automated tests cover detection, normalization, and export paths for both Claude and ChatGPT.

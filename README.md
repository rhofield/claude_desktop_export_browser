# Chat Export Browser
Export Claude and ChatGPT conversations to Markdown and JSON

A simple terminal tool that helps you browse and export conversations from Claude or ChatGPT data exports. Get your chat history in both human-readable Markdown and structured JSON formats.

![Chat Export Browser Screenshot](images/claude_chat_exporter.png)

## Quick Start

1. Download your Claude or ChatGPT data export.
2. Unzip the file.
3. Run the tool with `./chat_export_browser.py <path-to-export-folder-or-conversations.json>`.
4. Browse your conversations with arrow keys.
5. Press Enter to select a conversation.
6. Press Y to export using your selected output format.

## Supported Inputs

- Claude data exports containing `conversations.json`
- ChatGPT data exports containing `conversations.json`

ChatGPT support currently renders standard text messages only. Attachments, images, canvas data, code-interpreter artifacts, and rich tool outputs are not rendered to Markdown, but the original source data is preserved in JSON exports under `raw`.

## What You Can Do

- **Browse All Conversations**: Newest conversations appear first
- **See Previews**: View the first few messages before exporting
- **Export Easily**: Save Markdown, JSON, or both
- **Read Chronologically**: Exported conversations are organized by time with timestamps
- **No Extra Software Needed**: Uses only standard Python libraries

## How to Use

### Step 1: Get Your Data

- For Claude, go to your Claude account settings and export your data.
- For ChatGPT, export your data from ChatGPT settings.
- Download and extract the ZIP file.

### Step 2: Run the Browser

```bash
# Make executable (first time only)
chmod +x chat_export_browser.py

# Start the browser with a Claude or ChatGPT export directory
./chat_export_browser.py ./data-export-folder
# or
./chat_export_browser.py ./data-export-folder/conversations.json

# Export all conversations without opening the UI
./chat_export_browser.py ./data-export-folder --all

# Export markdown files only
./chat_export_browser.py ./data-export-folder --output-format md

# Export JSON files only (works with --all too)
./chat_export_browser.py ./data-export-folder --all --output-format json
```

### Step 3: Navigate and Export

- **Navigate**: Use up/down arrows to select conversations
- **Change Pages**: Use left/right arrows to move between pages (10 conversations per page)
- **View Details**: Press Enter to see conversation details
- **Export**: Press Y when prompted to save in the selected format
- **Exit**: Press Q to quit

### What You Get

When you export a conversation, files are created in the `exports/` folder based on `--output-format`:

- `both` (default): both files below
- `md`: only `[name].md` (easy-to-read Markdown)
- `json`: only `[name].json` (structured data for tools, including the original source data under `raw`)

## Tips

- Pass the export directory or `conversations.json` path via CLI input
- Use `--output-format md` or `--output-format json` to export a single file type
- If a filename already exists, the exporter adds ` (1)`, ` (2)`, etc. to avoid overwriting
- Exported conversations have timestamps so you can see when each message was sent
- Use the JSON exports if you want to process your conversations with other tools

For developer information, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## License

MIT License - See LICENSE file for details.

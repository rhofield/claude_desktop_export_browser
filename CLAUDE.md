# Chat Export Browser - Assistant Guide

## Project Overview
This project provides tools for browsing and exporting Claude and ChatGPT conversation histories from data exports. The primary tool is a terminal-based browser that allows users to navigate and export conversations.

## Tools & Commands
- **Chat Browser**: `./chat_export_browser.py` - Interactive CLI for browsing and exporting Claude or ChatGPT chats
- **Installation**: No additional dependencies required (uses standard Python libraries)
- **Usage**: Run `./chat_export_browser.py <path-to-export-folder-or-conversations.json>`
- **Format selection**: Use `--output-format both|md|json` to control generated file types
- **Tests**: Run `python3 -m unittest discover -v`

## Code Style Guidelines
- **Formatting**: Use consistent indentation (4 spaces for Python)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Imports**: Group imports in the following order:
  1. Standard library imports
  2. Third-party library imports (if any are added in the future)
  3. Local application imports
- **Types**: Use type hints for function parameters and return values
- **Comments**: Use docstrings for classes and functions following the Google style
- **Error Handling**: Use try/except blocks with specific exception types
- **Architecture**: Keep provider-specific parsing in normalization helpers so UI and export code consume only the canonical conversation shape

## Chat Browser Features
- Browse conversations chronologically (newest first)
- Pagination with 10 items per page
- View conversation details and preview content
- Export selected conversations in configurable format(s) to the exports/ directory
- Optional `--output-format` flag to export only Markdown or only JSON
  - Messages are sorted chronologically with timestamps
  - Preserves complete source data in JSON under `raw`
  - Creates human-readable Markdown alongside machine-readable JSON
- Navigation using arrow keys and keyboard shortcuts
- Optional `--all` flag to export every conversation in one run

## Development Guidelines
- Add new features by extending the `ChatExportBrowser` class or provider normalization helpers
- Use curses for terminal-based UI components
- Maintain backward compatibility with existing Claude data export formats
- ChatGPT support currently renders standard text messages only
- Handle exceptions gracefully with user-friendly error messages
- When adding new export formats, maintain the dual approach of human-readable + machine-readable
- Test with supported Claude and ChatGPT data export formats to ensure compatibility

# Chat Export Browser - Development Guide

This document provides information for developers who want to contribute to or modify the Chat Export Browser tool.

## Project Structure

- `chat_export_browser.py` - Main application file (terminal UI, normalization, and export functionality)
- `tests/` - Standard-library `unittest` test suite
- `exports/` - Directory where exported conversations are stored
- `docs/` - Documentation for developers
- `CLAUDE.md` - Additional guidelines for AI assistants when working with this codebase

## Architecture

The tool uses a simple object-oriented approach:

- `ChatExportBrowser` class handles loading, displaying, and exporting conversations
- Provider-specific exports are normalized into a common internal conversation shape before UI or export code runs
- Claude and ChatGPT detection happens from the parsed `conversations.json` structure
- Keep provider-specific parsing in normalization helpers so UI and export code consume only the canonical conversation shape
- `curses` library is used for the terminal UI
- The app intentionally remains dependency-free and uses Python's standard library only
- `argparse` provides CLI input handling for path selection and batch export mode

## CLI Interface

The script requires an explicit input path:

- `./chat_export_browser.py <path-to-export-folder-or-conversations.json>`

Supported modes:

- **Interactive mode** (default): opens the curses browser UI
- **Batch mode**: `./chat_export_browser.py <path> --all` exports all conversations without opening the UI

Output format control:

- `--output-format both` (default): write both `.md` and `.json`
- `--output-format md`: write only `.md`
- `--output-format json`: write only `.json`
- Export filenames use conversation title only (`<title>.md` / `<title>.json`) with numeric suffixes on conflicts

Path validation behavior:

- Accepts either an export directory or a direct `conversations.json` file path
- Exits with an error if the path does not exist or `conversations.json` cannot be found

## Supported Inputs

- Claude data exports containing `conversations.json`
- ChatGPT data exports containing `conversations.json`

ChatGPT support currently renders standard text messages only. Attachments, images, canvas data, code-interpreter artifacts, and rich tool outputs are not rendered to Markdown, but the original source data is preserved in JSON exports under `raw`.

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

## Adding New Features

When extending the functionality, consider the following guidelines:

1. **UI Changes**: Keep the terminal UI simple and intuitive
2. **Export Formats**: Maintain the dual approach of human-readable + machine-readable formats
3. **Backward Compatibility**: Ensure compatibility with existing Claude data export formats
4. **Error Handling**: Add robust error handling for any new functionality
5. **Normalization First**: Add provider-specific parsing to normalization helpers before changing UI or export code

## Testing

Run all tests with `python3 -m unittest discover -v`.

Tests use Python's standard `unittest` library and live in `tests/`.

## Future Improvements

Potential areas for enhancement:

- **Search Functionality**: Allow searching for conversations by keyword
- **Filtering**: Add options to filter by date range or conversation length
- **Export Templates**: Customizable templates for Markdown exports
- **Web UI**: A lightweight web interface as an alternative to the terminal UI
- **Batch Filters**: Add selective batch export criteria (date range, message count, keyword)
- **Rich ChatGPT Content**: Render attachments, images, canvas data, or code-interpreter artifacts

## Debugging Tips

When debugging the curses UI:

1. Use the `stdscr.addstr(0, 0, f"Debug: {variable}")` approach to display debug info
2. Remember to call `stdscr.refresh()` after adding debug text
3. Handle exceptions and display error messages for easier troubleshooting

## Pull Request Guidelines

When submitting changes:

1. Follow the existing code style and conventions
2. Ensure your changes maintain compatibility with existing features
3. Update documentation to reflect your changes
4. Describe the purpose and implementation details in your PR

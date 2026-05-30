# ChatGPT Export Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the app to a generic chat export browser and add standard text ChatGPT `conversations.json` support while preserving Claude export behavior.

**Architecture:** Keep a single standard-library Python app in `chat_export_browser.py`. Add a normalization layer that detects Claude vs ChatGPT exports and converts both into one internal conversation shape before UI/export code runs. Remove the old `claude_chat_browser.py` entrypoint rather than keeping a compatibility wrapper.

**Tech Stack:** Python 3 standard library only: `argparse`, `json`, `os`, `sys`, `datetime`, `curses`, `unittest`, `tempfile`, `subprocess`, `pathlib`.

---

## File Structure

- Rename: `claude_chat_browser.py` -> `chat_export_browser.py`
- Delete: `claude_chat_browser.py`
- Modify: `chat_export_browser.py`
  - Owns CLI parsing, path resolution, format detection, normalization, terminal UI, Markdown export, JSON export, and batch export.
- Create: `tests/test_chat_export_browser.py`
  - Unit tests for format detection, normalization, export behavior, path resolution, and batch output formats.
- Modify: `README.md`
  - Rename the project wording and CLI examples to generic Claude/ChatGPT support.
- Modify: `docs/DEVELOPMENT.md`
  - Update architecture and testing notes for normalized multi-provider support.
- Modify: `CLAUDE.md`
  - Update assistant guide to reference `chat_export_browser.py` and the provider-neutral architecture.

---

### Task 1: Rename Entrypoint And Establish Test Harness

**Files:**
- Rename: `claude_chat_browser.py` -> `chat_export_browser.py`
- Delete: `claude_chat_browser.py`
- Create: `tests/test_chat_export_browser.py`

- [ ] **Step 1: Rename the script**

Run:

```bash
mv claude_chat_browser.py chat_export_browser.py
chmod +x chat_export_browser.py
```

Expected: `chat_export_browser.py` exists and `claude_chat_browser.py` does not exist.

- [ ] **Step 2: Write the failing import and rename tests**

Create `tests/test_chat_export_browser.py` with this initial content:

```python
import os
import unittest

import chat_export_browser


class EntrypointRenameTests(unittest.TestCase):
    def test_new_module_imports(self):
        self.assertTrue(hasattr(chat_export_browser, "ChatExportBrowser"))

    def test_old_claude_entrypoint_was_removed(self):
        repo_root = os.path.dirname(os.path.dirname(__file__))
        self.assertFalse(os.path.exists(os.path.join(repo_root, "claude_chat_browser.py")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python -m unittest tests.test_chat_export_browser.EntrypointRenameTests -v
```

Expected: FAIL because `ChatExportBrowser` does not exist yet.

- [ ] **Step 4: Rename the class and direct references**

In `chat_export_browser.py`, change:

```python
class ClaudeChatBrowser:
```

to:

```python
class ChatExportBrowser:
```

Change this line in `main()`:

```python
browser = ClaudeChatBrowser(data_dir, output_format=args.output_format)
```

to:

```python
browser = ChatExportBrowser(data_dir, output_format=args.output_format)
```

- [ ] **Step 5: Run the rename tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.EntrypointRenameTests -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py
git add -u claude_chat_browser.py
git commit -m "refactor: rename chat export browser entrypoint"
```

---

### Task 2: Add Format Detection And Timestamp Utilities

**Files:**
- Modify: `chat_export_browser.py`
- Modify: `tests/test_chat_export_browser.py`

- [ ] **Step 1: Add failing tests for format detection and timestamp conversion**

Append these tests above the `if __name__ == "__main__":` block in `tests/test_chat_export_browser.py`:

```python
class FormatDetectionTests(unittest.TestCase):
    def test_detects_claude_export(self):
        conversations = [{"uuid": "claude-1", "chat_messages": []}]
        self.assertEqual(chat_export_browser.detect_export_format(conversations), "claude")

    def test_detects_chatgpt_export(self):
        conversations = [{"id": "chatgpt-1", "mapping": {}}]
        self.assertEqual(chat_export_browser.detect_export_format(conversations), "chatgpt")

    def test_rejects_unknown_export(self):
        with self.assertRaises(ValueError) as context:
            chat_export_browser.detect_export_format([{"id": "unknown"}])
        self.assertIn("unsupported conversations.json format", str(context.exception))

    def test_rejects_non_list_export(self):
        with self.assertRaises(ValueError) as context:
            chat_export_browser.detect_export_format({"mapping": {}})
        self.assertIn("expected conversations.json to contain a list", str(context.exception))


class TimestampFormattingTests(unittest.TestCase):
    def test_formats_unix_timestamp_as_utc_iso_string(self):
        self.assertEqual(
            chat_export_browser.normalize_timestamp(1710000000.0),
            "2024-03-09T16:00:00+00:00",
        )

    def test_preserves_existing_timestamp_string(self):
        timestamp = "2025-03-02T15:59:23.000Z"
        self.assertEqual(chat_export_browser.normalize_timestamp(timestamp), timestamp)

    def test_empty_timestamp_becomes_empty_string(self):
        self.assertEqual(chat_export_browser.normalize_timestamp(None), "")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests.test_chat_export_browser.FormatDetectionTests tests.test_chat_export_browser.TimestampFormattingTests -v
```

Expected: FAIL because `detect_export_format` and `normalize_timestamp` are not defined.

- [ ] **Step 3: Implement detection and timestamp helpers**

In `chat_export_browser.py`, add these functions after the imports and before `class ChatExportBrowser`:

```python
def normalize_timestamp(value: Any) -> str:
    """Return a string timestamp, converting Unix timestamps to UTC ISO format."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).isoformat()
    return str(value)


def detect_export_format(conversations: Any) -> str:
    """Detect the provider format for a parsed conversations.json payload."""
    if not isinstance(conversations, list):
        raise ValueError("expected conversations.json to contain a list of conversations")

    if any(isinstance(conversation, dict) and "chat_messages" in conversation for conversation in conversations):
        return "claude"
    if any(isinstance(conversation, dict) and "mapping" in conversation for conversation in conversations):
        return "chatgpt"

    raise ValueError(
        "unsupported conversations.json format. Expected a Claude or ChatGPT conversations export."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.FormatDetectionTests tests.test_chat_export_browser.TimestampFormattingTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py
git commit -m "feat: detect chat export formats"
```

---

### Task 3: Normalize Claude Conversations

**Files:**
- Modify: `chat_export_browser.py`
- Modify: `tests/test_chat_export_browser.py`

- [ ] **Step 1: Add failing Claude normalization tests**

Append these tests above the `if __name__ == "__main__":` block in `tests/test_chat_export_browser.py`:

```python
class ClaudeNormalizationTests(unittest.TestCase):
    def test_normalizes_claude_conversation(self):
        raw = {
            "uuid": "claude-1",
            "name": "Claude title",
            "updated_at": "2025-03-02T15:59:23.000Z",
            "chat_messages": [
                {
                    "sender": "human",
                    "text": "Hello Claude",
                    "created_at": "2025-03-02T15:59:20.000Z",
                },
                {
                    "sender": "assistant",
                    "text": "Hello user",
                    "created_at": "2025-03-02T15:59:21.000Z",
                },
            ],
        }

        normalized = chat_export_browser.normalize_claude_conversation(raw)

        self.assertEqual(normalized["id"], "claude-1")
        self.assertEqual(normalized["source"], "claude")
        self.assertEqual(normalized["title"], "Claude title")
        self.assertEqual(normalized["updated_at"], "2025-03-02T15:59:23.000Z")
        self.assertEqual(normalized["raw"], raw)
        self.assertEqual(
            normalized["messages"],
            [
                {
                    "sender": "user",
                    "text": "Hello Claude",
                    "created_at": "2025-03-02T15:59:20.000Z",
                },
                {
                    "sender": "assistant",
                    "text": "Hello user",
                    "created_at": "2025-03-02T15:59:21.000Z",
                },
            ],
        )

    def test_claude_title_falls_back_to_first_human_message(self):
        raw = {
            "uuid": "claude-2",
            "updated_at": "2025-03-02T15:59:23.000Z",
            "chat_messages": [
                {"sender": "assistant", "text": "Assistant preface", "created_at": "1"},
                {"sender": "human", "text": "Use this as title", "created_at": "2"},
            ],
        }

        normalized = chat_export_browser.normalize_claude_conversation(raw)

        self.assertEqual(normalized["title"], "Use this as title")

    def test_claude_message_text_falls_back_to_content_text(self):
        raw = {
            "uuid": "claude-3",
            "name": "Content text",
            "chat_messages": [
                {
                    "sender": "human",
                    "created_at": "2025-03-02T15:59:20.000Z",
                    "content": [{"type": "text", "text": "Text from content"}],
                }
            ],
        }

        normalized = chat_export_browser.normalize_claude_conversation(raw)

        self.assertEqual(normalized["messages"][0]["text"], "Text from content")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ClaudeNormalizationTests -v
```

Expected: FAIL because `normalize_claude_conversation` is not defined.

- [ ] **Step 3: Implement Claude normalization helpers**

In `chat_export_browser.py`, add these functions below `detect_export_format`:

```python
def extract_claude_message_text(message: Dict[str, Any]) -> str:
    """Extract text from a Claude message."""
    text = message.get("text") or ""
    if text:
        return text

    for content_item in message.get("content", []):
        if isinstance(content_item, dict) and content_item.get("type") == "text":
            return content_item.get("text", "") or ""

    return ""


def normalize_claude_sender(sender: str) -> str:
    """Map Claude sender names to canonical sender names."""
    if sender == "human":
        return "user"
    return "assistant"


def normalize_claude_conversation(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Claude conversation to the canonical internal shape."""
    raw_messages = conversation.get("chat_messages", [])
    messages = []

    for message in raw_messages:
        if not isinstance(message, dict):
            continue
        text = extract_claude_message_text(message)
        if not text:
            continue
        messages.append(
            {
                "sender": normalize_claude_sender(message.get("sender", "")),
                "text": text,
                "created_at": normalize_timestamp(message.get("created_at")),
            }
        )

    title = conversation.get("name") or ""
    if not title:
        for message in messages:
            if message["sender"] == "user" and message["text"]:
                title = message["text"][:50]
                break
    if not title:
        title = "Untitled conversation"

    return {
        "id": conversation.get("uuid") or conversation.get("id") or "unknown",
        "source": "claude",
        "title": title,
        "updated_at": normalize_timestamp(conversation.get("updated_at")),
        "messages": messages,
        "raw": conversation,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ClaudeNormalizationTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py
git commit -m "feat: normalize claude conversations"
```

---

### Task 4: Normalize ChatGPT Conversations

**Files:**
- Modify: `chat_export_browser.py`
- Modify: `tests/test_chat_export_browser.py`

- [ ] **Step 1: Add failing ChatGPT normalization tests**

Append these tests above the `if __name__ == "__main__":` block in `tests/test_chat_export_browser.py`:

```python
class ChatGPTNormalizationTests(unittest.TestCase):
    def test_normalizes_chatgpt_conversation_messages_in_time_order(self):
        raw = {
            "id": "chatgpt-1",
            "title": "ChatGPT title",
            "update_time": 1710000002.0,
            "mapping": {
                "assistant-node": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1710000001.0,
                        "content": {"content_type": "text", "parts": ["Hello user"]},
                    }
                },
                "user-node": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1710000000.0,
                        "content": {"content_type": "text", "parts": ["Hello ChatGPT"]},
                    }
                },
            },
        }

        normalized = chat_export_browser.normalize_chatgpt_conversation(raw)

        self.assertEqual(normalized["id"], "chatgpt-1")
        self.assertEqual(normalized["source"], "chatgpt")
        self.assertEqual(normalized["title"], "ChatGPT title")
        self.assertEqual(normalized["updated_at"], "2024-03-09T16:00:02+00:00")
        self.assertEqual(normalized["raw"], raw)
        self.assertEqual(
            normalized["messages"],
            [
                {
                    "sender": "user",
                    "text": "Hello ChatGPT",
                    "created_at": "2024-03-09T16:00:00+00:00",
                },
                {
                    "sender": "assistant",
                    "text": "Hello user",
                    "created_at": "2024-03-09T16:00:01+00:00",
                },
            ],
        )

    def test_chatgpt_skips_empty_and_non_text_parts_but_preserves_raw(self):
        raw = {
            "id": "chatgpt-2",
            "mapping": {
                "empty-node": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1710000000.0,
                        "content": {"content_type": "text", "parts": [""]},
                    }
                },
                "non-text-node": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1710000001.0,
                        "content": {"content_type": "multimodal_text", "parts": [{"asset_pointer": "file-service://image"}]},
                    }
                },
                "text-node": {
                    "message": {
                        "author": {"role": "assistant"},
                        "create_time": 1710000002.0,
                        "content": {"content_type": "text", "parts": ["Renderable text"]},
                    }
                },
            },
        }

        normalized = chat_export_browser.normalize_chatgpt_conversation(raw)

        self.assertEqual(len(normalized["messages"]), 1)
        self.assertEqual(normalized["messages"][0]["text"], "Renderable text")
        self.assertEqual(normalized["raw"], raw)

    def test_chatgpt_title_falls_back_to_first_user_message(self):
        raw = {
            "id": "chatgpt-3",
            "mapping": {
                "user-node": {
                    "message": {
                        "author": {"role": "user"},
                        "create_time": 1710000000.0,
                        "content": {"parts": ["Use this as title"]},
                    }
                }
            },
        }

        normalized = chat_export_browser.normalize_chatgpt_conversation(raw)

        self.assertEqual(normalized["title"], "Use this as title")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ChatGPTNormalizationTests -v
```

Expected: FAIL because `normalize_chatgpt_conversation` is not defined.

- [ ] **Step 3: Implement ChatGPT normalization helpers**

In `chat_export_browser.py`, add these functions below `normalize_claude_conversation`:

```python
def normalize_chatgpt_sender(role: str) -> str:
    """Map ChatGPT roles to canonical sender names."""
    if role in {"user", "assistant", "system", "tool"}:
        return role
    return "unknown"


def extract_chatgpt_message_text(message: Dict[str, Any]) -> str:
    """Extract renderable standard text from a ChatGPT message."""
    content = message.get("content") or {}
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts") or []
    text_parts = [part for part in parts if isinstance(part, str) and part]
    return "\n\n".join(text_parts)


def normalize_chatgpt_conversation(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a ChatGPT conversation to the canonical internal shape."""
    mapping = conversation.get("mapping") or {}
    sortable_messages = []

    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        text = extract_chatgpt_message_text(message)
        if not text:
            continue

        create_time = message.get("create_time")
        author = message.get("author") or {}
        role = author.get("role", "") if isinstance(author, dict) else ""
        sortable_messages.append(
            (
                create_time if create_time is not None else 0,
                {
                    "sender": normalize_chatgpt_sender(role),
                    "text": text,
                    "created_at": normalize_timestamp(create_time),
                },
            )
        )

    sortable_messages.sort(key=lambda item: item[0])
    messages = [message for _, message in sortable_messages]

    title = conversation.get("title") or ""
    if not title:
        for message in messages:
            if message["sender"] == "user" and message["text"]:
                title = message["text"][:50]
                break
    if not title:
        title = "Untitled conversation"

    updated_at = conversation.get("update_time")
    if updated_at is None and sortable_messages:
        updated_at = sortable_messages[-1][0]

    return {
        "id": conversation.get("id") or "unknown",
        "source": "chatgpt",
        "title": title,
        "updated_at": normalize_timestamp(updated_at),
        "messages": messages,
        "raw": conversation,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ChatGPTNormalizationTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py
git commit -m "feat: normalize chatgpt conversations"
```

---

### Task 5: Integrate Normalization Into Loading, UI, And Export

**Files:**
- Modify: `chat_export_browser.py`
- Modify: `tests/test_chat_export_browser.py`

- [ ] **Step 1: Add failing export integration tests**

Append these imports near the top of `tests/test_chat_export_browser.py`:

```python
import json
import tempfile
```

Append these tests above the `if __name__ == "__main__":` block:

```python
class ExportIntegrationTests(unittest.TestCase):
    def make_export_dir(self, conversations):
        temp_dir = tempfile.TemporaryDirectory()
        with open(os.path.join(temp_dir.name, "conversations.json"), "w", encoding="utf-8") as handle:
            json.dump(conversations, handle)
        self.addCleanup(temp_dir.cleanup)
        return temp_dir.name

    def test_loads_claude_export_as_normalized_conversations(self):
        data_dir = self.make_export_dir(
            [
                {
                    "uuid": "claude-1",
                    "name": "Claude title",
                    "updated_at": "2025-03-02T15:59:23.000Z",
                    "chat_messages": [
                        {"sender": "human", "text": "Hello", "created_at": "2025-03-02T15:59:20.000Z"}
                    ],
                }
            ]
        )

        browser = chat_export_browser.ChatExportBrowser(data_dir, output_format="both")

        self.assertEqual(browser.source_format, "claude")
        self.assertEqual(browser.conversations[0]["title"], "Claude title")
        self.assertEqual(browser.conversations[0]["messages"][0]["sender"], "user")

    def test_loads_chatgpt_export_as_normalized_conversations(self):
        data_dir = self.make_export_dir(
            [
                {
                    "id": "chatgpt-1",
                    "title": "ChatGPT title",
                    "update_time": 1710000001.0,
                    "mapping": {
                        "node": {
                            "message": {
                                "author": {"role": "assistant"},
                                "create_time": 1710000000.0,
                                "content": {"parts": ["Hello"]},
                            }
                        }
                    },
                }
            ]
        )

        browser = chat_export_browser.ChatExportBrowser(data_dir, output_format="both")

        self.assertEqual(browser.source_format, "chatgpt")
        self.assertEqual(browser.conversations[0]["title"], "ChatGPT title")
        self.assertEqual(browser.conversations[0]["messages"][0]["sender"], "assistant")

    def test_exports_markdown_with_provider_neutral_labels(self):
        data_dir = self.make_export_dir(
            [
                {
                    "id": "chatgpt-1",
                    "title": "ChatGPT title",
                    "update_time": 1710000001.0,
                    "mapping": {
                        "user-node": {
                            "message": {
                                "author": {"role": "user"},
                                "create_time": 1710000000.0,
                                "content": {"parts": ["Hello ChatGPT"]},
                            }
                        },
                        "assistant-node": {
                            "message": {
                                "author": {"role": "assistant"},
                                "create_time": 1710000001.0,
                                "content": {"parts": ["Hello user"]},
                            }
                        },
                    },
                }
            ]
        )
        browser = chat_export_browser.ChatExportBrowser(data_dir, output_format="both")

        md_path, json_path = browser.export_conversation(browser.conversations[0])

        with open(md_path, "r", encoding="utf-8") as handle:
            markdown = handle.read()
        with open(json_path, "r", encoding="utf-8") as handle:
            exported_json = json.load(handle)

        self.assertIn("# ChatGPT title", markdown)
        self.assertIn("**User**:", markdown)
        self.assertIn("**Assistant**:", markdown)
        self.assertNotIn("**Claude**:", markdown)
        self.assertEqual(exported_json["source"], "chatgpt")
        self.assertIn("raw", exported_json)

    def test_output_format_md_only_writes_markdown_only(self):
        data_dir = self.make_export_dir(
            [
                {
                    "uuid": "claude-1",
                    "name": "Claude title",
                    "chat_messages": [{"sender": "human", "text": "Hello", "created_at": "1"}],
                }
            ]
        )
        browser = chat_export_browser.ChatExportBrowser(data_dir, output_format="md")

        md_path, json_path = browser.export_conversation(browser.conversations[0])

        self.assertTrue(os.path.exists(md_path))
        self.assertIsNone(json_path)

    def test_output_format_json_only_writes_json_only(self):
        data_dir = self.make_export_dir(
            [
                {
                    "uuid": "claude-1",
                    "name": "Claude title",
                    "chat_messages": [{"sender": "human", "text": "Hello", "created_at": "1"}],
                }
            ]
        )
        browser = chat_export_browser.ChatExportBrowser(data_dir, output_format="json")

        md_path, json_path = browser.export_conversation(browser.conversations[0])

        self.assertIsNone(md_path)
        self.assertTrue(os.path.exists(json_path))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ExportIntegrationTests -v
```

Expected: FAIL because `ChatExportBrowser.load_conversations()`, UI title formatting, and export still expect Claude-specific fields.

- [ ] **Step 3: Add generic normalization dispatcher**

In `chat_export_browser.py`, add this function below `normalize_chatgpt_conversation`:

```python
def normalize_conversation(conversation: Dict[str, Any], source_format: str) -> Dict[str, Any]:
    """Normalize one raw conversation for the detected provider format."""
    if source_format == "claude":
        return normalize_claude_conversation(conversation)
    if source_format == "chatgpt":
        return normalize_chatgpt_conversation(conversation)
    raise ValueError(f"unsupported export format: {source_format}")
```

- [ ] **Step 4: Update `ChatExportBrowser.__init__`**

In `chat_export_browser.py`, add a `source_format` attribute in `__init__`:

```python
self.source_format = ""
```

Place it immediately after:

```python
self.conversations = []
```

- [ ] **Step 5: Update `load_conversations()` to normalize loaded JSON**

Replace the body of `load_conversations()` with:

```python
    def load_conversations(self):
        """Load and normalize conversations from the JSON file."""
        try:
            with open(self.conversations_path, "r", encoding="utf-8") as f:
                raw_conversations = json.load(f)

            self.source_format = detect_export_format(raw_conversations)
            self.conversations = [
                normalize_conversation(conversation, self.source_format)
                for conversation in raw_conversations
                if isinstance(conversation, dict)
            ]

            self.conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        except Exception as e:
            print(f"Error loading conversations: {str(e)}")
            sys.exit(1)
```

- [ ] **Step 6: Update title formatting for normalized conversations**

Replace `format_conversation_title()` with:

```python
    def format_conversation_title(self, conversation: Dict[str, Any]) -> str:
        """Format a normalized conversation for display in the list."""
        name = conversation.get("title") or "Untitled conversation"

        date_str = "No date"
        if conversation.get("updated_at"):
            try:
                date = datetime.datetime.fromisoformat(conversation["updated_at"].replace("Z", "+00:00"))
                date_str = date.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        msg_count = len(conversation.get("messages", []))
        return f"{date_str} | {msg_count} msgs | {name}"
```

- [ ] **Step 7: Add a generic speaker label helper**

Add this function below `normalize_conversation()`:

```python
def format_sender_label(sender: str) -> str:
    """Return a Markdown/UI label for a normalized sender."""
    labels = {
        "user": "User",
        "assistant": "Assistant",
        "system": "System",
        "tool": "Tool",
        "unknown": "Unknown",
    }
    return labels.get(sender, "Unknown")
```

- [ ] **Step 8: Update `export_conversation()` for normalized conversations**

In `export_conversation()`, change the title, ID, date, message sorting, and markdown loop to use normalized fields.

Replace this block:

```python
original_name = conversation.get('name', '') or "conversation"
```

with:

```python
original_name = conversation.get("title", "") or "conversation"
```

Replace the message sorting block with:

```python
export_conversation = conversation.copy()
export_conversation["messages"] = sorted(
    conversation.get("messages", []),
    key=lambda x: x.get("created_at", ""),
)
```

Replace the Markdown header block with:

```python
markdown = [f"# {original_name or 'Chat Conversation'}\n"]
markdown.append(f"Date: {date_str}\n")
markdown.append(f"ID: {conversation.get('id', 'Unknown')}\n")
markdown.append(f"Source: {conversation.get('source', 'unknown')}\n\n")
```

Replace the message loop with:

```python
for msg in export_conversation.get("messages", []):
    sender = f"**{format_sender_label(msg.get('sender', 'unknown'))}**:"
    text = msg.get("text", "")

    timestamp = ""
    if msg.get("created_at"):
        try:
            msg_date = datetime.datetime.fromisoformat(msg.get("created_at").replace("Z", "+00:00"))
            timestamp = f"[{msg_date.strftime('%Y-%m-%d %H:%M:%S')}]"
        except Exception:
            pass

    if text:
        if timestamp:
            markdown.append(f"{sender} {timestamp}\n\n{text}\n\n---\n\n")
        else:
            markdown.append(f"{sender}\n\n{text}\n\n---\n\n")
```

- [ ] **Step 9: Update failed batch export IDs**

In `export_all_conversations()`, change:

```python
conversation_id = conversation.get('uuid', 'Unknown')
```

to:

```python
conversation_id = conversation.get("id", "Unknown")
```

- [ ] **Step 10: Update the curses UI strings and detail preview**

In `_curses_main()`, change:

```python
header = "CLAUDE CHAT EXPORT BROWSER"
subheader = "Export your Claude Desktop chats"
```

to:

```python
header = "CHAT EXPORT BROWSER"
subheader = "Export your AI chat conversations"
```

In `_show_conversation_details()`, change:

```python
title = "CLAUDE CHAT EXPORT BROWSER"
```

to:

```python
title = "CHAT EXPORT BROWSER"
```

Replace the conversation info and preview extraction in `_show_conversation_details()` with normalized-field logic:

```python
name = conversation.get("title", "") or "Untitled conversation"
date_str = "No date"
if conversation.get("updated_at"):
    try:
        date = datetime.datetime.fromisoformat(conversation["updated_at"].replace("Z", "+00:00"))
        date_str = date.strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass

msg_count = len(conversation.get("messages", []))

info = [
    f"Title: {name}",
    f"Date: {date_str}",
    f"Source: {conversation.get('source', 'unknown')}",
    f"Message count: {msg_count}",
    f"ID: {conversation.get('id', 'Unknown')}",
]

messages = []
for msg in conversation.get("messages", [])[:3]:
    sender = f"{format_sender_label(msg.get('sender', 'unknown'))}:"
    text = msg.get("text", "")
    if text:
        if len(text) > 100:
            text = text[:97] + "..."
        messages.append(f"{sender} {text}")
```

- [ ] **Step 11: Run integration tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.ExportIntegrationTests -v
```

Expected: PASS.

- [ ] **Step 12: Run all tests**

Run:

```bash
python -m unittest discover -v
```

Expected: PASS.

- [ ] **Step 13: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py
git commit -m "feat: export normalized chat conversations"
```

---

### Task 6: Update CLI Text, Path Errors, And Documentation

**Files:**
- Modify: `chat_export_browser.py`
- Modify: `tests/test_chat_export_browser.py`
- Modify: `README.md`
- Modify: `docs/DEVELOPMENT.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add failing CLI text tests**

Append this import near the top of `tests/test_chat_export_browser.py`:

```python
import subprocess
```

Append these tests above the `if __name__ == "__main__":` block:

```python
class CliBehaviorTests(unittest.TestCase):
    def test_help_uses_generic_description(self):
        result = subprocess.run(
            ["python", "chat_export_browser.py", "--help"],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Browse Claude or ChatGPT conversations", result.stdout)
        self.assertNotIn("Path to a Claude export", result.stdout)

    def test_missing_conversations_json_error_is_provider_neutral(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        result = subprocess.run(
            ["python", "chat_export_browser.py", temp_dir.name],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conversations.json not found", result.stdout)
        self.assertNotIn("Claude", result.stdout)
```

- [ ] **Step 2: Run CLI tests to verify they fail**

Run:

```bash
python -m unittest tests.test_chat_export_browser.CliBehaviorTests -v
```

Expected: FAIL because the CLI description and help text still say Claude.

- [ ] **Step 3: Update provider-neutral CLI text**

In `chat_export_browser.py`, update `resolve_data_directory()` docstring:

```python
"""Resolve a CLI input path into an export directory containing conversations.json."""
```

Update the parser description:

```python
description="Browse Claude or ChatGPT conversations and export them to Markdown and JSON."
```

Update the `input_path` help text:

```python
help="Path to an export directory or directly to conversations.json",
```

Update the loaded-data print:

```python
print(f"Using chat export data from: {data_dir}")
```

- [ ] **Step 4: Run CLI tests to verify they pass**

Run:

```bash
python -m unittest tests.test_chat_export_browser.CliBehaviorTests -v
```

Expected: PASS.

- [ ] **Step 5: Update `README.md`**

Replace Claude-only wording with provider-neutral wording. The README should include these exact usage examples:

```bash
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

Add a support-scope section:

```markdown
## Supported Inputs

- Claude data exports containing `conversations.json`
- ChatGPT data exports containing `conversations.json`

ChatGPT support currently renders standard text messages only. Attachments, images, canvas data, code-interpreter artifacts, and rich tool outputs are not rendered to Markdown, but the original source data is preserved in JSON exports under `raw`.
```

- [ ] **Step 6: Update `docs/DEVELOPMENT.md`**

Update the project structure section to name `chat_export_browser.py` as the main app. Add an architecture note:

```markdown
- Provider-specific exports are normalized into a common internal conversation shape before UI or export code runs.
- Claude and ChatGPT detection happens from the parsed `conversations.json` structure.
- The app intentionally remains dependency-free and uses Python's standard library only.
```

Update testing guidance to say:

```markdown
Run all tests with `python -m unittest discover -v`.
```

- [ ] **Step 7: Update `CLAUDE.md`**

Update the assistant guide so it references:

```markdown
- **Chat Browser**: `./chat_export_browser.py` - Interactive CLI for browsing and exporting Claude or ChatGPT chats
- **Usage**: Run `./chat_export_browser.py <path-to-export-folder-or-conversations.json>`
```

Add this architecture bullet:

```markdown
- Keep provider-specific parsing in normalization helpers so UI and export code consume only the canonical conversation shape.
```

- [ ] **Step 8: Run all tests**

Run:

```bash
python -m unittest discover -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add chat_export_browser.py tests/test_chat_export_browser.py README.md docs/DEVELOPMENT.md CLAUDE.md
git commit -m "docs: describe generic chat export support"
```

---

### Task 7: Manual Verification With Real Claude Fixture And Sample ChatGPT Fixture

**Files:**
- Modify: `tests/test_chat_export_browser.py` only if a verification issue exposes a missing automated test

- [ ] **Step 1: Run full automated test suite**

Run:

```bash
python -m unittest discover -v
```

Expected: PASS.

- [ ] **Step 2: Verify real Claude export batch mode**

Run:

```bash
./chat_export_browser.py ./data-07e37944-4f2d-4ddb-8e6c-31253384fb57-1780140016-d2e79dca-batch-0000 --all --output-format md
```

Expected: Command exits 0 and prints a successful export count.

- [ ] **Step 3: Create a temporary sample ChatGPT export**

Run:

```bash
mkdir -p /tmp/chatgpt-export-sample
cat > /tmp/chatgpt-export-sample/conversations.json <<'JSON'
[
  {
    "id": "chatgpt-sample-1",
    "title": "Sample ChatGPT Conversation",
    "update_time": 1710000001.0,
    "mapping": {
      "user-node": {
        "message": {
          "author": {"role": "user"},
          "create_time": 1710000000.0,
          "content": {"parts": ["Hello ChatGPT"]}
        }
      },
      "assistant-node": {
        "message": {
          "author": {"role": "assistant"},
          "create_time": 1710000001.0,
          "content": {"parts": ["Hello user"]}
        }
      }
    }
  }
]
JSON
```

- [ ] **Step 4: Verify sample ChatGPT export batch mode**

Run:

```bash
./chat_export_browser.py /tmp/chatgpt-export-sample --all --output-format both
```

Expected: Command exits 0 and creates Markdown and JSON files under `/tmp/exports`.

- [ ] **Step 5: Inspect generated ChatGPT Markdown**

Run:

```bash
cat /tmp/exports/Sample\ ChatGPT\ Conversation.md
```

Expected output contains:

```markdown
# Sample ChatGPT Conversation

**User**:

Hello ChatGPT

**Assistant**:

Hello user
```

- [ ] **Step 6: Inspect generated ChatGPT JSON**

Run:

```bash
python -m json.tool /tmp/exports/Sample\ ChatGPT\ Conversation.json | sed -n '1,80p'
```

Expected output contains normalized fields `id`, `source`, `title`, `updated_at`, `messages`, and `raw`.

- [ ] **Step 7: Check git status**

Run:

```bash
git status --short
```

Expected: clean working tree, unless manual verification created only ignored/cache files.


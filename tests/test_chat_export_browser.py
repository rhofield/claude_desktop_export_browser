import os
import unittest

import chat_export_browser


class EntrypointRenameTests(unittest.TestCase):
    def test_new_module_imports(self):
        self.assertTrue(hasattr(chat_export_browser, "ChatExportBrowser"))

    def test_old_claude_entrypoint_was_removed(self):
        repo_root = os.path.dirname(os.path.dirname(__file__))
        self.assertFalse(os.path.exists(os.path.join(repo_root, "claude_chat_browser.py")))



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


if __name__ == "__main__":
    unittest.main()

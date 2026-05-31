import json
import os
import tempfile
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


if __name__ == "__main__":
    unittest.main()

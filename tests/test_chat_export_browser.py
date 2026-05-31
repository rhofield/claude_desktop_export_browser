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

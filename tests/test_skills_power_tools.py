"""Unit tests for developer power tools, system security diagnostics, and document intelligence."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vyra.skills.assistant import audit_action_history
from vyra.skills.comms import git_repo_status
from vyra.skills.files import read_file_tree, summarize_document
from vyra.skills.system import emergency_lockdown, kill_port, network_diagnostics


class TestPowerToolsSystem(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_kill_port_invalid_input(self):
        """kill_port should gracefully handle non-numeric port strings."""
        res = kill_port(self.mock_memory, "not-a-port")
        self.assertIn("valid port number", res)

    def test_kill_port_unbound_port(self):
        """kill_port should report no process found on a high unallocated port."""
        res = kill_port(self.mock_memory, 59123)
        self.assertIn("No active process was found listening on port 59123", res)

    def test_network_diagnostics_report(self):
        """network_diagnostics should gather latency, local IP, and report status without crashing."""
        res = network_diagnostics(self.mock_memory)
        self.assertIn("Network Diagnostics", res)
        self.assertIn("Local IP:", res)
        self.assertIn("Cloudflare Latency", res)

    @patch("ctypes.windll.user32")
    def test_emergency_lockdown_protocol_zero(self, mock_user32):
        """emergency_lockdown (Protocol Zero) must lock workstation, mute audio, and log action."""
        mock_user32.LockWorkStation = MagicMock(return_value=1)
        mock_user32.keybd_event = MagicMock()

        res = emergency_lockdown(self.mock_memory)
        self.assertIn("Protocol Zero executed", res)
        mock_user32.LockWorkStation.assert_called_once()
        self.assertTrue(mock_user32.keybd_event.called)
        self.mock_memory.log_action.assert_called_once()
        args, kwargs = self.mock_memory.log_action.call_args
        self.assertEqual(args[0], "emergency_lockdown")


class TestPowerToolsFiles(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.test_dir = tempfile.mkdtemp(prefix="rusty_tree_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_read_file_tree_filters_and_formats(self):
        """read_file_tree generates an ASCII tree and filters out git and venv artifacts."""
        os.makedirs(os.path.join(self.test_dir, "src", "core"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, ".git"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "__pycache__"), exist_ok=True)

        with open(os.path.join(self.test_dir, "src", "app.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(self.test_dir, ".git", "HEAD"), "w") as f:
            f.write("ref: refs/heads/main")

        tree = read_file_tree(self.mock_memory, folder=self.test_dir)
        self.assertIn("Directory tree of", tree)
        self.assertIn("src/", tree)
        self.assertIn("app.py", tree)
        self.assertNotIn(".git", tree)
        self.assertNotIn("__pycache__", tree)

    def test_summarize_document_local_extract(self):
        """summarize_document produces an executive extract when LLM client is not configured."""
        doc_path = os.path.join(self.test_dir, "notes.md")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("# Project Titan Architecture\n\n- Phase 1: Microservices deployment\n- Phase 2: High availability clustering")

        summary = summarize_document(self.mock_memory, path=doc_path)
        self.assertIn("notes.md", summary)
        self.assertIn("Project Titan Architecture", summary)


class TestPowerToolsGit(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_git_repo_status_workspace(self):
        """git_repo_status inspects current active workspace git repo."""
        res = git_repo_status(self.mock_memory)
        self.assertIn("Git Dashboard for", res)
        self.assertIn("Active Branch:", res)
        self.assertIn("Working Tree:", res)

    def test_git_repo_status_non_repo(self):
        """git_repo_status identifies directories that are not Git repositories."""
        temp_dir = tempfile.mkdtemp(prefix="rusty_non_git_")
        try:
            res = git_repo_status(self.mock_memory, path=temp_dir)
            self.assertIn("is not a Git repository", res)
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class TestPowerToolsAssistant(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_audit_action_history_empty(self):
        """audit_action_history returns graceful message when log is empty."""
        self.mock_memory.get_recent_actions.return_value = []
        res = audit_action_history(self.mock_memory)
        self.assertIn("No recent system actions recorded", res)

    def test_audit_action_history_with_entries(self):
        """audit_action_history formats timestamps, durations, and skills."""
        self.mock_memory.get_recent_actions.return_value = [
            {
                "timestamp": "2026-10-15T18:00:00.123",
                "skill_name": "kill_port",
                "duration_ms": 14.5,
                "status": "success",
                "result": "Freed port 3000 by terminating node.exe",
            }
        ]
        res = audit_action_history(self.mock_memory, limit=5)
        self.assertIn("Recent Action Audit Log", res)
        self.assertIn("kill_port", res)
        self.assertIn("14.5ms", res)
        self.assertIn("Freed port 3000", res)


if __name__ == "__main__":
    unittest.main()

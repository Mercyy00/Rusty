"""Unit tests for Antigravity desktop application controller, skills, and safety boundaries."""

import os
import unittest
from unittest.mock import MagicMock, patch

from vyra.skills import antigravity_app
from vyra.skills.antigravity_app import (
    ANTIGRAVITY_SKILLS,
    AntigravityController,
    ag_approve,
    ag_install_extension,
    ag_open_file,
    ag_read_agent_output,
    ag_reject,
    ag_run_in_terminal,
    ag_selftest,
    ag_status,
    ag_stop_agent,
)


class TestAntigravityController(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.controller = AntigravityController()

    def test_selftest_diagnostics(self):
        """ag_selftest must validate all channels and return structured diagnostics."""
        res = ag_selftest(self.mock_memory)
        self.assertIn("Antigravity Self-Test Diagnostics:", res)
        self.assertIn("Cli Launcher", res)
        self.assertIn("Ui Map", res)

    def test_status_reporting(self):
        """ag_status must report process, window, conversation, and CLI status."""
        status = ag_status(self.mock_memory)
        self.assertIn("Antigravity Status Report", status)
        self.assertIn("Process Active:", status)
        self.assertIn("Windows Open:", status)
        self.assertIn("Latest Conversation:", status)

    def test_read_agent_output_format(self):
        """ag_read_agent_output parses and formats recent steps from transcript."""
        output = ag_read_agent_output(self.mock_memory, limit=2)
        self.assertIn("Antigravity Agent Telemetry", output)
        self.assertIn("Step", output)

    def test_ag_approve_sensitive_safety_gate(self):
        """ag_approve must refuse execution unless confirm=True is explicitly passed."""
        res = ag_approve(self.mock_memory, "step_102", confirm=False)
        self.assertIn("SAFETY GATE (Sensitive Action)", res)
        self.assertIn("Please explicitly confirm", res)

    @patch.object(AntigravityController, "focus")
    @patch("vyra.skills.system.press_hotkey")
    def test_ag_approve_with_confirm(self, mock_hotkey, mock_focus):
        """ag_approve executes with explicit user confirmation."""
        mock_focus.return_value = {"ok": True}
        res = ag_approve(self.mock_memory, "step_102", confirm=True)
        self.assertIn("Approved Antigravity step 'step_102'", res)
        mock_hotkey.assert_called_with(None, "enter")

    @patch.object(AntigravityController, "focus")
    @patch("vyra.skills.system.press_hotkey")
    def test_ag_reject(self, mock_hotkey, mock_focus):
        """ag_reject cancels step and dismisses dialog."""
        mock_focus.return_value = {"ok": True}
        res = ag_reject(self.mock_memory, "step_102", reason="Invalid diff")
        self.assertIn("Rejected Antigravity step 'step_102'", res)
        self.assertIn("Invalid diff", res)
        mock_hotkey.assert_called_with(None, "esc")

    @patch.object(AntigravityController, "focus")
    def test_ag_stop_agent_kill_switch(self, mock_focus):
        """ag_stop_agent sends emergency stop signal and returns immediate confirmation."""
        mock_focus.return_value = {"ok": True}
        res = ag_stop_agent(self.mock_memory)
        self.assertIn("Emergency stop signal", res)

    def test_ag_open_file_blocks_protected_paths(self):
        """ag_open_file blocks opening protected system directories."""
        res = ag_open_file(self.mock_memory, "C:\\Windows\\System32\\config\\SAM")
        self.assertIn("Access denied", res)

    def test_ag_run_in_terminal_safety_gate(self):
        """Destructive terminal commands in Antigravity terminal require confirmation."""
        res = ag_run_in_terminal(self.mock_memory, "rm -rf /var/log", confirm=False)
        self.assertIn("Safety Hold", res)

    def test_ag_install_extension_safety_gate(self):
        """Installing extensions requires confirmation."""
        res = ag_install_extension(self.mock_memory, "unknown.publisher.extension", confirm=False)
        self.assertIn("Safety Hold", res)

    def test_all_antigravity_skills_schema_validity(self):
        """All 28 Antigravity skills must have valid parameters and descriptions."""
        self.assertEqual(len(ANTIGRAVITY_SKILLS), 28)
        for s in ANTIGRAVITY_SKILLS:
            with self.subTest(skill=s["name"]):
                self.assertIn("name", s)
                self.assertIn("fn", s)
                self.assertTrue(callable(s["fn"]))
                self.assertIn("description", s)
                self.assertIn("parameters", s)
                self.assertEqual(s["parameters"].get("type"), "object")


if __name__ == "__main__":
    unittest.main()

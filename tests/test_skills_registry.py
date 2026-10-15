"""Unit tests verifying the integrity, completeness, and schema validity of all skills."""

import unittest
from unittest.mock import MagicMock

from vyra import skills


class TestSkillsRegistry(unittest.TestCase):
    def test_total_skills_count(self):
        """Verify exactly 146 skills are registered across all modular categories."""
        self.assertEqual(len(skills.SKILLS), 146)
        self.assertIn("search_memory", skills._BY_NAME)
        self.assertIn("real_web_search", skills._BY_NAME)
        self.assertIn("check_weather", skills._BY_NAME)
        self.assertIn("check_stock_crypto", skills._BY_NAME)
        self.assertIn("news_briefing", skills._BY_NAME)
        self.assertIn("summarize_webpage", skills._BY_NAME)
        # Power tools and diagnostics
        self.assertIn("kill_port", skills._BY_NAME)
        self.assertIn("network_diagnostics", skills._BY_NAME)
        self.assertIn("emergency_lockdown", skills._BY_NAME)
        self.assertIn("read_file_tree", skills._BY_NAME)
        self.assertIn("summarize_document", skills._BY_NAME)
        self.assertIn("git_repo_status", skills._BY_NAME)
        self.assertIn("audit_action_history", skills._BY_NAME)
        # Antigravity Desktop App Control
        self.assertIn("ag_launch", skills._BY_NAME)
        self.assertIn("ag_status", skills._BY_NAME)
        self.assertIn("ag_focus", skills._BY_NAME)
        self.assertIn("ag_send_prompt", skills._BY_NAME)
        self.assertIn("ag_read_agent_output", skills._BY_NAME)
        self.assertIn("ag_wait_for_agent", skills._BY_NAME)
        self.assertIn("ag_approve", skills._BY_NAME)
        self.assertIn("ag_reject", skills._BY_NAME)
        self.assertIn("ag_stop_agent", skills._BY_NAME)
        self.assertIn("ag_build_feature", skills._BY_NAME)
        self.assertIn("ag_selftest", skills._BY_NAME)
        # Custom Skills (SKILL.md format)
        self.assertIn("list_custom_skills", skills._BY_NAME)
        self.assertIn("create_custom_skill", skills._BY_NAME)
        # MCP Client
        self.assertIn("mcp_list_servers", skills._BY_NAME)
        self.assertIn("mcp_call_tool", skills._BY_NAME)
        # Computer Use
        self.assertIn("cu_focus_app", skills._BY_NAME)
        self.assertIn("cu_type_in_app", skills._BY_NAME)
        self.assertIn("cu_click_app", skills._BY_NAME)
        # Research Mode
        self.assertIn("research_topic", skills._BY_NAME)
        # Self-Awareness
        self.assertIn("list_my_tools", skills._BY_NAME)
        self.assertIn("explain_last_action", skills._BY_NAME)
        self.assertIn("undo_last_action", skills._BY_NAME)
        # Sub-Agents
        self.assertIn("spawn_subagent", skills._BY_NAME)
        self.assertIn("check_subagent", skills._BY_NAME)
        self.assertIn("cancel_subagent", skills._BY_NAME)
        self.assertIn("list_subagents", skills._BY_NAME)
        # Projects & Scheduler
        self.assertIn("set_project_context", skills._BY_NAME)
        self.assertIn("get_project_context", skills._BY_NAME)
        self.assertIn("schedule_routine", skills._BY_NAME)
        self.assertIn("list_scheduled_routines", skills._BY_NAME)

    def test_no_duplicate_skill_names(self):
        """Verify all skill names are globally unique."""
        names = [s["name"] for s in skills.SKILLS]
        self.assertEqual(len(names), len(set(names)), "Found duplicate skill names in registry")

    def test_skill_structure_and_schemas(self):
        """Verify every skill defines a callable fn, a description, and a valid parameters object."""
        for skill in skills.SKILLS:
            with self.subTest(skill=skill.get("name")):
                self.assertIn("name", skill)
                self.assertIn("fn", skill)
                self.assertIn("description", skill)
                self.assertIn("parameters", skill)

                self.assertTrue(callable(skill["fn"]), f"Skill {skill['name']} fn is not callable")
                self.assertIsInstance(skill["description"], str)
                self.assertTrue(len(skill["description"]) > 5)

                params = skill["parameters"]
                self.assertIsInstance(params, dict)
                self.assertEqual(params.get("type"), "object")
                self.assertIn("properties", params)
                self.assertIn("required", params)

    def test_tool_schemas_format_for_llm(self):
        """Verify tool_schemas() exports LLM-compatible JSON objects without internal fn pointers."""
        schemas = skills.tool_schemas()
        self.assertEqual(len(schemas), len(skills.SKILLS))
        for s in schemas:
            self.assertIn("name", s)
            self.assertIn("description", s)
            self.assertIn("parameters", s)
            self.assertNotIn("fn", s)  # Python function pointer must not be exposed to LLM

    def test_execute_unknown_skill(self):
        """Executing an unregistered skill must return a graceful error message without crashing."""
        mock_memory = MagicMock()
        res = skills.execute("non_existent_fake_skill", {}, mock_memory)
        self.assertIn("unknown skill", res)

    def test_execute_bad_arguments(self):
        """Passing incompatible arguments to a skill must return a bad argument error without crashing."""
        mock_memory = MagicMock()
        # open_app requires 'name'
        res = skills.execute("open_app", {"unrecognized_arg": 123}, mock_memory)
        self.assertIn("bad arguments", res)


if __name__ == "__main__":
    unittest.main()

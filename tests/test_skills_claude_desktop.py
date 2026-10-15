"""Unit tests for Claude-Desktop-Class capabilities: Skill Folders, MCP Client, and Computer Use."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from vyra.skills.computer_use import AppProfile, get_app_profile
from vyra.skills.mcp_client import MCPClient, mcp_add_server, mcp_call_tool, mcp_list_servers
from vyra.skills.skills_manager import (
    create_custom_skill,
    delete_custom_skill,
    list_custom_skills,
    read_custom_skill,
)



class TestCustomSkillsManager(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.test_dir = tempfile.mkdtemp(prefix="rusty_custom_skills_")
        self.patcher = patch("vyra.skills.skills_manager.SKILLS_DIR", self.test_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_and_read_custom_skill(self):
        """create_custom_skill creates a valid SKILL.md file and read_custom_skill reads it."""
        res = create_custom_skill(
            self.mock_memory,
            name="deploy_staging",
            description="Deploys container image to staging cluster",
            instructions="1. Run pytest\n2. Build docker image\n3. Push to registry",
            trigger_conditions=["deploy staging", "push to staging"],
            risk_level="confirm"
        )
        self.assertIn("Successfully created custom skill", res)

        skill_file = os.path.join(self.test_dir, "deploy_staging", "SKILL.md")
        self.assertTrue(os.path.exists(skill_file))

        info = read_custom_skill(self.mock_memory, "deploy_staging")
        self.assertIn("deploy_staging", info)
        self.assertIn("Deploys container image", info)
        self.assertIn("deploy staging", info)
        self.assertIn("Run pytest", info)

    def test_list_custom_skills(self):
        """list_custom_skills enumerates all custom skills in skills_custom/."""
        create_custom_skill(self.mock_memory, "code_review", "Reviews PR diffs", "Inspect modified files")
        listing = list_custom_skills(self.mock_memory)
        self.assertIn("code_review", listing)
        self.assertIn("Reviews PR diffs", listing)

    def test_delete_custom_skill_requires_confirmation(self):
        """delete_custom_skill requires confirmation before deleting."""
        create_custom_skill(self.mock_memory, "temp_skill", "desc", "instructions")
        res = delete_custom_skill(self.mock_memory, "temp_skill", confirm=False)
        self.assertIn("Safety Hold", res)

        del_res = delete_custom_skill(self.mock_memory, "temp_skill", confirm=True)
        self.assertIn("Deleted custom skill", del_res)


class TestMCPClient(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.test_dir = tempfile.mkdtemp(prefix="rusty_mcp_")
        self.config_path = os.path.join(self.test_dir, "mcp_servers.json")
        self.patcher = patch("vyra.skills.mcp_client.MCP_CONFIG_PATH", self.config_path)
        self.patcher.start()


    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mcp_add_and_list_server(self):
        """mcp_add_server registers an MCP server and mcp_list_servers lists it."""
        res = mcp_add_server(self.mock_memory, "weather_mcp", command="python", args=["server.py"])
        self.assertIn("Successfully registered MCP server", res)

        servers = mcp_list_servers(self.mock_memory)
        self.assertIn("weather_mcp", servers)
        self.assertIn("python", servers)

    def test_mcp_call_tool_safety_gate(self):
        """Destructive MCP tools require explicit confirmation."""
        res = mcp_call_tool(self.mock_memory, "filesystem", "delete_file", arguments={"path": "/tmp/a"}, confirm=False)
        self.assertIn("SAFETY GATE", res)


class TestComputerUseAppProfile(unittest.TestCase):
    def test_get_app_profile_caching(self):
        """get_app_profile returns cached or dynamically created profiles."""
        p1 = get_app_profile("browser")
        p2 = get_app_profile("browser")
        self.assertIs(p1, p2)
        self.assertIn("chrome.exe", p1.process_names)

        custom = get_app_profile("blender")
        self.assertEqual(custom.name, "blender")
        self.assertIn("blender", custom.process_names)


class TestResearchMode(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    @patch("vyra.skills.research._fetch_url_text")
    @patch("vyra.skills.browser.real_web_search")
    def test_research_topic_generation(self, mock_search, mock_fetch):
        from vyra.skills.research import research_topic
        mock_search.return_value = "- [AlphaFold Docs](https://alphafold.ebi.ac.uk): Protein structure predictions database."
        mock_fetch.return_value = "AlphaFold is an AI system developed by Google DeepMind that predicts 3D structure."

        res = research_topic(self.mock_memory, topic="AlphaFold 3 Architecture", depth="quick")
        self.assertIn("Research protocol completed", res)
        self.assertIn("AlphaFold 3 Architecture", res)
        self.assertIn("Report saved to", res)


class TestSelfAwareness(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_list_my_tools_summary(self):
        from vyra.skills.self_awareness import list_my_tools
        res = list_my_tools(self.mock_memory)
        self.assertIn("Capability Matrix", res)
        self.assertIn("Antigravity IDE Automation", res)
        self.assertIn("Computer Use", res)
        self.assertIn("Model Context Protocol (MCP)", res)

    def test_list_my_tools_filtered(self):
        from vyra.skills.self_awareness import list_my_tools
        res = list_my_tools(self.mock_memory, category="antigravity")
        self.assertIn("Antigravity IDE Automation", res)
        self.assertIn("ag_launch", res)

    def test_explain_last_action_redaction(self):
        from vyra.skills.self_awareness import explain_last_action
        self.mock_memory.get_recent_actions.return_value = [{
            "skill_name": "backup_to_drive",
            "args": {"api_key": "secret123", "folder": "docs"},
            "result": "Upload successful",
            "status": "success",
            "duration_ms": 120.5,
            "timestamp": "2026-10-15T18:00:00",
        }]
        res = explain_last_action(self.mock_memory)
        self.assertIn("backup_to_drive", res)
        self.assertIn("[REDACTED]", res)
        self.assertNotIn("secret123", res)

    def test_undo_last_action_recycle_bin(self):
        from vyra.skills.self_awareness import undo_last_action
        self.mock_memory.get_recent_actions.return_value = [{
            "skill_name": "delete_file",
            "args": {"path": "notes.txt"},
            "result": "Deleted",
            "status": "success",
        }]
        res = undo_last_action(self.mock_memory)
        self.assertIn("Recycle Bin", res)
        self.assertIn("notes.txt", res)


class TestSubagentFramework(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_spawn_check_cancel_subagent(self):
        from vyra.skills.subagents import (
            cancel_subagent,
            check_subagent,
            list_subagents,
            spawn_subagent,
        )
        res = spawn_subagent(self.mock_memory, task="Audit security rules", role="CodeAuditor")
        self.assertIn("Spawned sub-agent", res)
        self.assertIn("subagent-", res)

        sub_id = res.split("`")[1]
        listing = list_subagents(self.mock_memory)
        self.assertIn(sub_id, listing)

        status_res = check_subagent(self.mock_memory, sub_id)
        self.assertIn(sub_id, status_res)
        self.assertIn("CodeAuditor", status_res)

        cancel_res = cancel_subagent(self.mock_memory, sub_id)
        self.assertIn("Cancellation signal dispatched", cancel_res)


class TestProjectContext(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.test_dir = tempfile.mkdtemp(prefix="rusty_projects_")
        from pathlib import Path
        self.patcher = patch("vyra.skills.projects.PROJECTS_STORE", Path(self.test_dir) / "projects.json")
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_set_and_get_project_context(self):
        from vyra.skills.projects import (
            delete_project_context,
            get_project_context,
            list_project_contexts,
            set_project_context,
        )
        set_res = set_project_context(
            self.mock_memory,
            project_name="JarvisCore",
            instructions="Maintain 100% test coverage and safe deletion.",
            files=["main.py", "config.py"],
        )
        self.assertIn("saved successfully", set_res)

        get_res = get_project_context(self.mock_memory, "JarvisCore")
        self.assertIn("JarvisCore", get_res)
        self.assertIn("100% test coverage", get_res)
        self.assertIn("main.py", get_res)

        listing = list_project_contexts(self.mock_memory)
        self.assertIn("JarvisCore", listing)

        del_res = delete_project_context(self.mock_memory, "JarvisCore", confirm=True)
        self.assertIn("deleted", del_res)


class TestScheduledRoutines(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()
        self.test_dir = tempfile.mkdtemp(prefix="rusty_sched_")
        from pathlib import Path
        self.patcher = patch("vyra.skills.scheduler.SCHEDULE_STORE", Path(self.test_dir) / "schedules.json")
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_schedule_and_cancel_routine(self):
        from vyra.skills.scheduler import (
            cancel_scheduled_routine,
            list_scheduled_routines,
            schedule_routine,
        )
        res = schedule_routine(self.mock_memory, routine_name="start my day", trigger_time="08:00")
        self.assertIn("Scheduled routine", res)
        self.assertIn("start my day", res)
        sched_id = res.split("`")[1]

        listing = list_scheduled_routines(self.mock_memory)
        self.assertIn(sched_id, listing)
        self.assertIn("08:00", listing)

        cancel_res = cancel_scheduled_routine(self.mock_memory, sched_id, confirm=True)
        self.assertIn("cancelled", cancel_res)


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

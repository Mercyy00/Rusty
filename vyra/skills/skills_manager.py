"""Custom Skill Folders Manager for Rusty (Claude-Desktop / Antigravity skill architecture).

Supports loading, listing, reading, and creating modular skills defined in:
  skills_custom/<name>/SKILL.md

Each SKILL.md consists of YAML frontmatter (name, description, trigger_conditions, risk)
followed by structured markdown instructions and workflow parameters.
"""

from __future__ import annotations

import os
import re
import shutil
from typing import Any, Dict, List, Optional

from .common import ROOT, is_path_safe

SKILLS_DIR = os.path.join(ROOT, "skills_custom")


def _ensure_skills_dir():
    os.makedirs(SKILLS_DIR, exist_ok=True)


def parse_skill_md(file_path: str) -> Optional[Dict[str, Any]]:
    """Parse a SKILL.md file extracting frontmatter and body instructions."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if match:
            frontmatter_raw, body = match.group(1), match.group(2)
            meta: Dict[str, Any] = {}
            for line in frontmatter_raw.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    k = key.strip()
                    v = val.strip().strip("\"'")
                    if v.startswith("[") and v.endswith("]"):
                        items = [item.strip().strip("\"'") for item in v[1:-1].split(",") if item.strip()]
                        meta[k] = items
                    else:
                        meta[k] = v
            meta["instructions"] = body.strip()
            return meta
        else:
            name = os.path.basename(os.path.dirname(file_path))
            return {
                "name": name,
                "description": f"Custom skill {name}",
                "trigger_conditions": [],
                "risk_level": "safe",
                "instructions": content.strip()
            }
    except Exception:
        return None


def list_custom_skills(memory) -> str:
    """List all custom modular skills installed in skills_custom/."""
    _ensure_skills_dir()
    entries = sorted(os.listdir(SKILLS_DIR))
    skills_found = []

    for entry in entries:
        folder_path = os.path.join(SKILLS_DIR, entry)
        if os.path.isdir(folder_path):
            skill_file = os.path.join(folder_path, "SKILL.md")
            if os.path.exists(skill_file):
                parsed = parse_skill_md(skill_file)
                if parsed:
                    name = parsed.get("name", entry)
                    desc = parsed.get("description", "No description provided.")
                    skills_found.append(f"  - **{name}**: {desc}")

    if not skills_found:
        return "No custom modular skills found in skills_custom/, Sir. You can save any workflow using create_custom_skill."

    return f"Custom Modular Skills ({len(skills_found)} installed):\n" + "\n".join(skills_found)


def read_custom_skill(memory, name: str) -> str:
    """Read the full instructions and metadata of a custom skill."""
    _ensure_skills_dir()
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower().strip())
    skill_file = os.path.join(SKILLS_DIR, clean_name, "SKILL.md")
    if not os.path.exists(skill_file):
        return f"Skill '{name}' not found, Sir."

    parsed = parse_skill_md(skill_file)
    if not parsed:
        return f"Could not parse SKILL.md for '{name}'."

    triggers = ", ".join(parsed.get("trigger_conditions", [])) or "None specified"
    risk = parsed.get("risk_level", "safe")
    return (
        f"Skill: {parsed.get('name', clean_name)} (Risk Level: {risk})\n"
        f"Description: {parsed.get('description', '')}\n"
        f"Trigger Conditions: {triggers}\n\n"
        f"Instructions:\n{parsed.get('instructions', '')}"
    )


def create_custom_skill(
    memory,
    name: str,
    description: str,
    instructions: str,
    trigger_conditions: list[str] | str = None,
    risk_level: str = "safe"
) -> str:
    """Create a new custom skill folder and SKILL.md specification (Save workflow as a skill)."""
    _ensure_skills_dir()
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower().strip())
    if not clean_name:
        return "Please specify a valid skill name (alphanumeric and dashes/underscores)."

    target_dir = os.path.join(SKILLS_DIR, clean_name)
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "SKILL.md")

    if isinstance(trigger_conditions, str):
        triggers = [t.strip() for t in trigger_conditions.split(",") if t.strip()]
    elif isinstance(trigger_conditions, list):
        triggers = [str(t).strip() for t in trigger_conditions if t]
    else:
        triggers = [clean_name.replace("_", " ")]

    trigger_str = "[" + ", ".join(f'"{t}"' for t in triggers) + "]"
    valid_risk = risk_level if risk_level in ("safe", "confirm", "sensitive") else "safe"

    content = (
        f"---\n"
        f'name: "{clean_name}"\n'
        f'description: "{description.strip()}"\n'
        f"trigger_conditions: {trigger_str}\n"
        f'risk_level: "{valid_risk}"\n'
        f"---\n\n"
        f"# {clean_name.replace('_', ' ').title()}\n\n"
        f"{instructions.strip()}\n"
    )

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully created custom skill '{clean_name}' at skills_custom/{clean_name}/SKILL.md, Sir."
    except Exception as exc:
        return f"Failed to save custom skill: {exc}"


def delete_custom_skill(memory, name: str, confirm: bool = False) -> str:
    """Delete an existing custom skill folder. Requires confirmation."""
    _ensure_skills_dir()
    clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", name.lower().strip())
    target_dir = os.path.join(SKILLS_DIR, clean_name)
    if not os.path.exists(target_dir):
        return f"Skill '{name}' does not exist, Sir."

    if not confirm:
        return f"Safety Hold: Confirm to permanently delete custom skill '{clean_name}'."

    try:
        shutil.rmtree(target_dir)
        return f"Deleted custom skill '{clean_name}', Sir."
    except Exception as exc:
        return f"Failed to delete skill: {exc}"


CUSTOM_SKILL_TOOLS = [
    {"name": "list_custom_skills", "fn": list_custom_skills, "description": "List all custom modular skills defined in skills_custom/ (Claude-Desktop / Antigravity format).",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "read_custom_skill", "fn": read_custom_skill, "description": "Read the instructions and trigger rules of a specific custom skill.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Skill name or identifier"}}, "required": ["name"]}},
    {"name": "create_custom_skill", "fn": create_custom_skill, "description": "Save a workflow or set of instructions as a persistent modular skill in skills_custom/<name>/SKILL.md.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Unique identifier for skill (e.g. 'deploy_pipeline')"}, "description": {"type": "string", "description": "Short explanation of what the skill does"}, "instructions": {"type": "string", "description": "Detailed step-by-step instructions for Rusty to follow"}, "trigger_conditions": {"type": "array", "items": {"type": "string"}, "description": "Phrases or keywords that trigger this skill"}, "risk_level": {"type": "string", "enum": ["safe", "confirm", "sensitive"], "description": "Risk classification"}}, "required": ["name", "description", "instructions"]}},
    {"name": "delete_custom_skill", "fn": delete_custom_skill, "description": "Delete a custom skill folder. Requires confirm=True.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Skill identifier to delete"}, "confirm": {"type": "boolean", "description": "Set true to confirm deletion"}}, "required": ["name"]}},
]

__all__ = [
    "CUSTOM_SKILL_TOOLS",
    "list_custom_skills",
    "read_custom_skill",
    "create_custom_skill",
    "delete_custom_skill",
]

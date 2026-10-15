"""Per-project instructions and context management for Rusty.

Allows Rusty to maintain isolated context, custom instructions, and related files
for specific development projects or workspaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import ROOT

PROJECTS_STORE = Path(ROOT) / "data" / "project_contexts.json"


def _load_projects() -> Dict[str, dict]:
    if PROJECTS_STORE.exists():
        try:
            return json.loads(PROJECTS_STORE.read_text("utf-8"))
        except Exception:
            return {}
    return {}


def _save_projects(data: Dict[str, dict]):
    PROJECTS_STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = PROJECTS_STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    tmp.replace(PROJECTS_STORE)


def set_project_context(
    memory: Any,
    project_name: str,
    instructions: str,
    files: Optional[List[str]] = None,
) -> str:
    """Save or update custom context, guidelines, and key files for a specific project.

    Args:
        memory: Rusty memory instance.
        project_name: Name of the project (e.g. 'Rusty', 'JARVIS-UI', 'FinanceTracker').
        instructions: Custom system prompt / instructions specific to this project.
        files: Optional list of relative or absolute file paths relevant to the project.
    """
    clean_name = (project_name or "").strip()
    if not clean_name:
        return "Please specify a project name, Sir."

    data = _load_projects()
    key = clean_name.lower()
    data[key] = {
        "name": clean_name,
        "instructions": (instructions or "").strip(),
        "files": files or [],
    }
    _save_projects(data)
    return f"Project context for '{clean_name}' saved successfully. Future actions in this project will honor these instructions."


def get_project_context(memory: Any, project_name: str) -> str:
    """Retrieve saved instructions and key files for a project."""
    clean_name = (project_name or "").strip()
    if not clean_name:
        return "Please specify which project context to view, Sir."

    data = _load_projects()
    item = data.get(clean_name.lower())
    if not item:
        available = ", ".join(d["name"] for d in data.values()) if data else "None"
        return f"No context found for '{clean_name}'. Available project contexts: {available}."

    lines = [
        f"Project Context: **{item['name']}**",
        f"Instructions:\n{item['instructions']}",
    ]
    if item.get("files"):
        lines.append("\nKey Files:")
        for f in item["files"]:
            lines.append(f"  - {f}")
    return "\n".join(lines)


def list_project_contexts(memory: Any) -> str:
    """List all projects that have custom instructions configured."""
    data = _load_projects()
    if not data:
        return "No project contexts currently configured, Sir. Use `set_project_context` to add one."

    lines = [f"Configured Project Contexts ({len(data)} total):"]
    for item in data.values():
        num_files = len(item.get("files", []))
        ins_preview = item.get("instructions", "")[:60].replace("\n", " ")
        lines.append(f"  - **{item['name']}** ({num_files} files): \"{ins_preview}...\"")
    return "\n".join(lines)


def delete_project_context(memory: Any, project_name: str, confirm: bool = False) -> str:
    """Remove a project context."""
    clean_name = (project_name or "").strip()
    if not clean_name:
        return "Please specify a project name to delete, Sir."

    data = _load_projects()
    key = clean_name.lower()
    if key not in data:
        return f"No context found for '{clean_name}'."

    if not confirm:
        return f"Are you sure you want to delete context for '{clean_name}'? Call with confirm=True to proceed."

    del data[key]
    _save_projects(data)
    return f"Project context for '{clean_name}' deleted."


PROJECT_SKILLS = [
    {
        "name": "set_project_context",
        "fn": set_project_context,
        "description": "Configure custom instructions, guidelines, and key files for a specific software project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project identifier or folder name"},
                "instructions": {"type": "string", "description": "Custom prompt, architecture rules, or coding conventions"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Key files list"},
            },
            "required": ["project_name", "instructions"],
        },
    },
    {
        "name": "get_project_context",
        "fn": get_project_context,
        "description": "Retrieve the custom context and instructions for a specific project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Name of the project to retrieve"}
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "list_project_contexts",
        "fn": list_project_contexts,
        "description": "List all projects that have custom instructions configured.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "delete_project_context",
        "fn": delete_project_context,
        "description": "Delete saved context for a project. Requires confirm=True.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project name to remove"},
                "confirm": {"type": "boolean", "description": "Explicit confirmation required to delete"},
            },
            "required": ["project_name"],
        },
    },
]

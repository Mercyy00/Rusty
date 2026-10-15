"""Self-awareness and introspection tools for Rusty.

Provides tool enumeration by capability domain, detailed post-action explanation
via the append-only audit log, and safe undo/recovery mechanisms.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


def list_my_tools(memory: Any, category: str = "") -> str:
    """Enumerate Rusty's full tool suite categorized by capability domain.

    Args:
        memory: Rusty memory instance.
        category: Optional category filter (e.g. 'system', 'antigravity', 'mcp', 'files', 'browser', 'research', 'media').
    """
    from . import SKILLS

    domains: Dict[str, List[dict]] = {
        "System & Hardware": [],
        "Files & Workspace": [],
        "Browser & Web": [],
        "Research Intelligence": [],
        "Media & Vision": [],
        "Communications & Cloud": [],
        "Assistant & Memory": [],
        "Document & App Creation": [],
        "Antigravity IDE Automation": [],
        "Custom Skills": [],
        "Model Context Protocol (MCP)": [],
        "Computer Use": [],
        "Sub-Agents": [],
        "Self-Awareness & Safety": [],
    }

    for s in SKILLS:
        name = s["name"]
        if name.startswith("ag_"):
            domains["Antigravity IDE Automation"].append(s)
        elif name.startswith("cu_"):
            domains["Computer Use"].append(s)
        elif name.startswith("mcp_"):
            domains["Model Context Protocol (MCP)"].append(s)
        elif "custom_skill" in name:
            domains["Custom Skills"].append(s)
        elif "subagent" in name:
            domains["Sub-Agents"].append(s)
        elif name in ("list_my_tools", "explain_last_action", "undo_last_action"):
            domains["Self-Awareness & Safety"].append(s)
        elif name.startswith("research_"):
            domains["Research Intelligence"].append(s)
        elif name in ("create_word", "create_pdf", "create_ppt", "create_excel", "create_project", "create_website", "ask_claude_code", "export_note_to_pdf", "convert_document"):
            domains["Document & App Creation"].append(s)
        elif name in ("remember", "forget_fact", "set_my_name", "save_note", "list_notes", "delete_note", "search_memory", "audit_action_history", "read_clipboard", "write_clipboard", "set_reminder", "list_reminders", "cancel_reminder", "daily_briefing", "run_routine", "list_routines", "send_to_claude", "deep_think", "get_datetime", "set_project_context", "get_project_context", "list_project_contexts", "delete_project_context", "schedule_routine", "list_scheduled_routines", "cancel_scheduled_routine"):
            domains["Assistant & Memory"].append(s)
        elif name in ("write_file", "search_files", "open_folder", "read_file", "open_file", "delete_file", "delete_folder", "list_folder", "empty_recycle_bin", "read_file_tree", "summarize_document"):
            domains["Files & Workspace"].append(s)
        elif name in ("real_web_search", "check_weather", "check_stock_crypto", "news_briefing", "summarize_webpage", "web_search", "web_answer", "open_url", "open_youtube", "close_browser_tab", "save_link", "open_saved_link", "list_saved_links", "delete_link"):
            domains["Browser & Web"].append(s)
        elif name in ("play_music", "media_play_pause", "media_next", "media_previous", "see_screen", "save_screenshot", "generate_image"):
            domains["Media & Vision"].append(s)
        elif name in ("send_file_to_phone", "send_whatsapp_message", "backup_to_drive", "github", "git_repo_status", "mobile_phone_gateway"):
            domains["Communications & Cloud"].append(s)
        else:
            domains["System & Hardware"].append(s)

    clean_cat = (category or "").lower().strip()
    if clean_cat:
        matched_domain = None
        for dom in domains:
            if clean_cat in dom.lower():
                matched_domain = dom
                break
        if not matched_domain:
            valid_cats = ", ".join(f"'{k}'" for k in domains.keys())
            return f"Unknown category '{category}'. Available categories: {valid_cats}."

        tools = domains[matched_domain]
        lines = [f"=== {matched_domain} ({len(tools)} tools) ==="]
        for t in tools:
            lines.append(f"  - {t['name']}: {t.get('description', '')[:90]}")
        return "\n".join(lines)

    total_count = sum(len(v) for v in domains.values())
    summary_lines = [f"Rusty Capability Matrix ({total_count} total registered tools):"]
    for dom, tools in domains.items():
        summary_lines.append(f"- **{dom}** ({len(tools)} tools): {', '.join(t['name'] for t in tools[:4])}{'...' if len(tools) > 4 else ''}")

    summary_lines.append("\nTip: Call `list_my_tools(category='...')` for a detailed breakdown of any domain.")
    return "\n".join(summary_lines)


def explain_last_action(memory: Any) -> str:
    """Retrieve and explain the most recent action executed by Rusty, including
    its parameters, execution latency, and outcome evidence from the audit log.
    """
    try:
        actions = memory.get_recent_actions(limit=1)
        if not actions:
            return "No previous actions are recorded in my audit log, Sir."

        action = actions[0]
        skill = action.get("skill_name", "unknown")
        args = action.get("args", {})
        result = action.get("result", "")
        status = action.get("status", "success")
        duration = action.get("duration_ms", 0.0)
        ts = action.get("timestamp", datetime.now().isoformat())

        # Redact secrets or sensitive tokens from args preview
        redacted_args = dict(args) if isinstance(args, dict) else {}
        for k in list(redacted_args.keys()):
            if any(s in k.lower() for s in ("token", "key", "password", "secret", "pin")):
                redacted_args[k] = "[REDACTED]"

        res_preview = result[:300].strip() + ("..." if len(result) > 300 else "")

        return (
            f"Last Executed Action Report:\n\n"
            f"- **Tool**: `{skill}`\n"
            f"- **Executed At**: {ts}\n"
            f"- **Duration**: {duration:.2f} ms\n"
            f"- **Status**: {status.upper()}\n"
            f"- **Parameters**: `{json.dumps(redacted_args)}`\n"
            f"- **Outcome**: {res_preview}"
        )
    except Exception as exc:
        return f"Could not inspect last action audit log: {exc}"


def undo_last_action(memory: Any, confirm: bool = False) -> str:
    """Attempt to undo or reverse the most recent action where technically feasible.
    Destructive reversions require explicit `confirm=True`.
    """
    try:
        actions = memory.get_recent_actions(limit=1)
        if not actions:
            return "No previous actions found to undo, Sir."

        action = actions[0]
        skill = action.get("skill_name", "")
        args = action.get("args", {})

        if skill in ("delete_file", "delete_folder"):
            path = args.get("path", "")
            return (
                f"The last action was `{skill}` for '{path}'.\n\n"
                f"Because Rusty enforces safe recycling, items are sent to the Windows Recycle Bin "
                f"rather than permanently wiped. You can restore '{path}' directly from the Windows Recycle Bin, "
                f"or inspect it via File Explorer."
            )

        if skill in ("write_file", "create_word", "create_pdf", "create_excel", "create_ppt"):
            fn = args.get("filename") or args.get("path", "")
            if not confirm:
                return (
                    f"The last action created or modified file '{fn}'.\n\n"
                    f"To remove this newly created file and restore previous state, call `undo_last_action(confirm=True)`."
                )
            # Confirmed file removal
            from .files import delete_file
            res = delete_file(memory, path=fn, permanent=False)
            return f"Undid last action: moved '{fn}' to Recycle Bin ({res})."

        if skill.startswith("cu_") or skill.startswith("ag_"):
            return (
                f"The last action was an interactive UI action (`{skill}`). "
                f"Direct reversal of GUI inputs is not deterministically supported; however, "
                f"you can issue `press_hotkey(keys='ctrl+z')` or focus the target window to revert edits."
            )

        return (
            f"The last action was `{skill}`. This operation cannot be automatically reversed via software undo. "
            f"Check `explain_last_action` for audit parameters."
        )
    except Exception as exc:
        return f"Could not process undo request: {exc}"


SELF_AWARENESS_SKILLS = [
    {
        "name": "list_my_tools",
        "fn": list_my_tools,
        "description": "Enumerate and explain all of Rusty's tools and capabilities grouped by domain (System, Files, Browser, Research, Media, Comms, Assistant, Office, Antigravity, Custom Skills, MCP, Computer Use, Sub-Agents).",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Optional category filter: 'system', 'files', 'browser', 'research', 'media', 'comms', 'assistant', 'office', 'antigravity', 'custom', 'mcp', 'computer_use', 'subagents'",
                }
            },
            "required": [],
        },
    },
    {
        "name": "explain_last_action",
        "fn": explain_last_action,
        "description": "Explain the most recently executed tool, including its exact parameters (secrets redacted), execution duration, timestamp, and result evidence from the audit log.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "undo_last_action",
        "fn": undo_last_action,
        "description": "Attempt to undo or recover from the most recent tool execution (e.g. restoring recycled files, reverting generated files). Destructive reversals require confirm=True.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirm": {"type": "boolean", "description": "Set to true to confirm reversing or removing the last generated asset"}
            },
            "required": [],
        },
    },
]

"""VYRA / Rusty skills package — modular tools registry and dispatcher.

Submodules:
  - common: Path safety, sandbox validation, Win32 window helpers
  - system: Terminal execution, process/window management, volume, hotkeys, input
  - files: File read/write, search, folder listing, safe recycling
  - browser: Web browsing, web search, answer extraction, URL/link memory
  - media: Raaga music playback, audio controls, screen vision, screenshots, imagegen
  - comms: Telegram file delivery, WhatsApp messaging, Google Drive, GitHub CLI
  - assistant: Memory facts, notes, reminders, routines, daily briefings, deep think
"""

from __future__ import annotations

import inspect

from .. import office_skills as _office
from .antigravity_app import (
    ANTIGRAVITY_SKILLS,
    ag_approve,
    ag_build_feature,
    ag_close_window,
    ag_command_palette,
    ag_fix_failing_tests,
    ag_focus,
    ag_install_extension,
    ag_launch,
    ag_cli_launch,
    ag_list_extensions,
    ag_list_open_tabs,
    ag_list_pending_approvals,
    ag_new_window,
    ag_open_file,
    ag_open_folder,
    ag_open_settings,
    ag_open_terminal,
    ag_read_agent_output,
    ag_reject,
    ag_review_changes,
    ag_run_in_terminal,
    ag_save_all,
    ag_screenshot,
    ag_search_workspace,
    ag_selftest,
    ag_send_prompt,
    ag_status,
    ag_stop_agent,
    ag_wait_for_agent,
)
from .skills_manager import (
    CUSTOM_SKILL_TOOLS,
    create_custom_skill,
    delete_custom_skill,
    list_custom_skills,
    read_custom_skill,
)
from .mcp_client import (
    MCP_SKILLS,
    mcp_add_server,
    mcp_call_tool,
    mcp_list_servers,
    mcp_list_tools,
)
from .computer_use import (
    COMPUTER_USE_SKILLS,
    cu_click_app,
    cu_focus_app,
    cu_inspect_app,
    cu_press_key_in_app,
    cu_screenshot_app,
    cu_scroll_app,
    cu_type_in_app,
)
from .research import (
    RESEARCH_SKILLS,
    research_topic,
)
from .self_awareness import (
    SELF_AWARENESS_SKILLS,
    explain_last_action,
    list_my_tools,
    undo_last_action,
)
from .subagents import (
    SUBAGENT_SKILLS,
    cancel_subagent,
    check_subagent,
    list_subagents,
    spawn_subagent,
)
from .projects import (
    PROJECT_SKILLS,
    delete_project_context,
    get_project_context,
    list_project_contexts,
    set_project_context,
)
from .scheduler import (
    SCHEDULER_SKILLS,
    cancel_scheduled_routine,
    list_scheduled_routines,
    schedule_routine,
)

from .assistant import (
    ASSISTANT_SKILLS,
    audit_action_history,
    cancel_reminder,
    daily_briefing,
    deep_think,
    delete_note,
    forget_fact,
    get_datetime,
    list_notes,
    list_reminders,
    list_routines,
    read_clipboard,
    remember,
    run_routine,
    save_note,
    search_memory,
    send_to_claude,
    set_my_name,
    set_reminder,
    write_clipboard,
)
from .browser import (
    BROWSER_SKILLS,
    browser_click,
    browser_close,
    browser_eval_js,
    browser_open,
    browser_read_page,
    browser_scroll,
    browser_type,
    check_stock_crypto,
    check_weather,
    close_browser_tab,
    configure_browser,
    delete_link,
    list_saved_links,
    news_briefing,
    open_saved_link,
    open_url,
    open_youtube,
    real_web_search,
    save_link,
    summarize_webpage,
    web_answer,
    web_search,
)
from .common import (
    FOLDER_SHORTCUTS,
    KNOWN_BROWSERS,
    PROTECTED_PATH_PATTERNS,
    ROOT,
    SYSTEM_PROTECTED,
    _attach_input_desktop,
    _data_dir,
    _get_user_windows,
    _resolve_path,
    focus_window,
    is_path_safe,
)
from .comms import (
    COMMS_SKILLS,
    backup_to_drive,
    git_repo_status,
    github,
    mobile_phone_gateway,
    send_file_to_phone,
    send_whatsapp_message,
)
from .files import (
    FILE_SKILLS,
    delete_file,
    delete_folder,
    empty_recycle_bin,
    list_folder,
    open_file,
    open_folder,
    read_file,
    read_file_tree,
    search_files,
    summarize_document,
    write_file,
)
from .media import (
    MEDIA_SKILLS,
    RAAGA_APP_PATH,
    configure_vision,
    generate_image,
    media_next,
    media_play_pause,
    media_previous,
    play_music,
    save_screenshot,
    see_screen,
)
from .system import (
    APP_ALIASES,
    BLOCKED_COMMAND_PATTERNS,
    DESTRUCTIVE_COMMAND_PATTERNS,
    SYSTEM_SKILLS,
    click_mouse,
    close_active_window,
    close_app,
    close_other_windows,
    emergency_lockdown,
    get_battery_status,
    get_system_info,
    inspect_active_window,
    kill_port,
    list_running_apps,
    lock_pc,
    network_diagnostics,
    open_app,
    press_hotkey,
    run_terminal_command,
    set_brightness,
    sleep_pc,
    switch_mode,
    type_text,
    volume_down,
    volume_mute,
    volume_up,
)

OFFICE_SKILLS = [
    {"name": "create_word", "fn": _office.create_word, "description": "Create a Microsoft Word (.docx) document. BEST way: pass a `title` and a `topic` (what it should cover) and Rusty writes a full, comprehensive, multi-page document itself. Only pass `content` if you've already written the text. Use for reports, notes, study material, resumes.",
     "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "topic": {"type": "string", "description": "What the document should cover / detailed brief — Rusty writes a thorough document from this"}, "content": {"type": "string", "description": "Optional pre-written body ('#'/'##' headings, '- ' bullets, plain text, no markdown emphasis)"}, "filename": {"type": "string"}}, "required": ["title"]}},
    {"name": "create_pdf", "fn": _office.create_pdf, "description": "Create a real PDF (.pdf) — use whenever Jay asks for a PDF (never create_word for that). BEST way: pass a `title` and a `topic` and Rusty writes a full, comprehensive, multi-page document. Only pass `content` if already written.",
     "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "topic": {"type": "string", "description": "What the PDF should cover / detailed brief — Rusty writes a thorough document from this"}, "content": {"type": "string", "description": "Optional pre-written body"}, "filename": {"type": "string"}}, "required": ["title"]}},
    {"name": "create_ppt", "fn": _office.create_ppt, "description": "Create a polished, professionally-designed PowerPoint deck. Just pass a `topic` (a short brief of what the deck is about) and Rusty writes the full, well-structured, themed deck. Optionally choose a theme: midnight, slate, royal, or clean.",
     "parameters": {"type": "object", "properties": {"topic": {"type": "string", "description": "What the presentation is about (a brief, or detailed instructions)"}, "theme": {"type": "string", "description": "midnight (dark blue), slate (dark), royal (purple/gold), or clean (light). Default midnight"}, "filename": {"type": "string"}}, "required": ["topic"]}},
    {"name": "create_excel", "fn": _office.create_excel, "description": "Create an Excel (.xlsx) spreadsheet. Provide the data as CSV text (first row = headers). Use for tables, trackers, budgets, data.",
     "parameters": {"type": "object", "properties": {"title": {"type": "string", "description": "Sheet name"}, "content": {"type": "string", "description": "CSV rows; first row is the header"}, "filename": {"type": "string"}}, "required": ["title", "content"]}},
    {"name": "create_project", "fn": _office.create_project, "description": "Scaffold a code/web project by writing multiple files at once (e.g. a website). YOU write the code for each file; opens index.html if present. Use for building websites/apps or any multi-file deliverable.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Project folder name"}, "files": {"type": "object", "description": "Map of relative filename -> file contents, e.g. {'index.html': '...', 'style.css': '...'}"}}, "required": ["name", "files"]}},
    {"name": "create_website", "fn": _office.create_website, "description": "Build a complete website from a short description and open it — THE reliable way to make a site/landing page/portfolio. Just pass a name and a description of what you want (theme, sections, style); the full HTML is generated and saved. Prefer this over create_project for websites.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Short site name (folder)"}, "description": {"type": "string", "description": "What the site should be: purpose, sections, style/theme (e.g. 'dark-themed developer portfolio with hero, projects, contact')"}}, "required": ["name", "description"]}},
    {"name": "ask_claude_code", "fn": _office.ask_claude_code, "description": "Delegate a heavy coding/engineering task to the Claude Code CLI running on the PC (it can read/edit code in a folder and run commands). Use for complex multi-file coding, refactors, debugging, or building software.",
     "parameters": {"type": "object", "properties": {"task": {"type": "string", "description": "The full task/instructions for Claude Code"}, "folder": {"type": "string", "description": "Project folder to work in (default: the Rusty project)"}}, "required": ["task"]}},
    {"name": "export_note_to_pdf", "fn": _office.export_note_to_pdf, "description": "Export a saved note from memory into a clean, formatted PDF document and open it.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Optional search term for the note (defaults to the most recent note)"}, "filename": {"type": "string", "description": "Optional custom filename"}}, "required": []}},
    {"name": "convert_document", "fn": _office.convert_document, "description": "Convert a text or markdown file into a formatted PDF or Word document.",
     "parameters": {"type": "object", "properties": {"source_path": {"type": "string", "description": "Path to the markdown or text file"}, "target_format": {"type": "string", "description": "'pdf' or 'docx'"}}, "required": ["source_path"]}},
]

SKILLS: list[dict] = (
    SYSTEM_SKILLS
    + FILE_SKILLS
    + BROWSER_SKILLS
    + MEDIA_SKILLS
    + COMMS_SKILLS
    + ASSISTANT_SKILLS
    + OFFICE_SKILLS
    + ANTIGRAVITY_SKILLS
    + CUSTOM_SKILL_TOOLS
    + MCP_SKILLS
    + COMPUTER_USE_SKILLS
    + RESEARCH_SKILLS
    + SELF_AWARENESS_SKILLS
    + SUBAGENT_SKILLS
    + PROJECT_SKILLS
    + SCHEDULER_SKILLS
)



_BY_NAME = {s["name"]: s for s in SKILLS}


def execute(name: str, args: dict, memory, progress_callback=None) -> str:
    """Execute a skill by its unique identifier with parameter unpacking and error containment."""
    skill = _BY_NAME.get(name)
    if not skill:
        return f"(unknown skill: {name})"
    try:
        sig = inspect.signature(skill["fn"])
        call_args = dict(args or {})
        if "progress_callback" in sig.parameters:
            call_args["progress_callback"] = progress_callback
        return skill["fn"](memory, **call_args)
    except TypeError as exc:
        return f"(bad arguments for {name}: {exc})"
    except Exception as exc:  # a skill failing must never crash the assistant
        return f"(error running {name}: {exc})"


def tool_schemas() -> list:
    """Neutral tool schemas (name/description/parameters) formatted for LLM function calling."""
    return [{"name": s["name"], "description": s["description"], "parameters": s["parameters"]} for s in SKILLS]


__all__ = [
    # Metadata & Registries
    "SKILLS",
    "_BY_NAME",
    "execute",
    "tool_schemas",
    "configure_browser",
    "configure_vision",
    "is_path_safe",
    # System
    "run_terminal_command",
    "press_hotkey",
    "click_mouse",
    "type_text",
    "open_app",
    "close_app",
    "close_other_windows",
    "close_active_window",
    "list_running_apps",
    "inspect_active_window",
    "kill_port",
    "network_diagnostics",
    "emergency_lockdown",
    "volume_up",
    "volume_down",
    "volume_mute",
    "lock_pc",
    "sleep_pc",
    "set_brightness",
    "get_system_info",
    "get_battery_status",
    "switch_mode",
    # Files
    "write_file",
    "search_files",
    "open_folder",
    "read_file",
    "read_file_tree",
    "summarize_document",
    "open_file",
    "delete_file",
    "delete_folder",
    "list_folder",
    "empty_recycle_bin",
    # Browser
    "browser_open",
    "browser_click",
    "browser_type",
    "browser_read_page",
    "browser_scroll",
    "browser_eval_js",
    "browser_close",
    "real_web_search",
    "check_weather",
    "check_stock_crypto",
    "news_briefing",
    "summarize_webpage",
    "web_search",
    "web_answer",
    "open_url",
    "open_youtube",
    "close_browser_tab",
    "save_link",
    "open_saved_link",
    "list_saved_links",
    "delete_link",
    # Media
    "media_play_pause",
    "media_next",
    "media_previous",
    "play_music",
    "save_screenshot",
    "see_screen",
    "generate_image",
    # Comms
    "send_whatsapp_message",
    "mobile_phone_gateway",
    "send_file_to_phone",
    "backup_to_drive",
    "git_repo_status",
    "github",
    # Assistant
    "remember",
    "forget_fact",
    "set_my_name",
    "save_note",
    "list_notes",
    "delete_note",
    "search_memory",
    "audit_action_history",
    "read_clipboard",
    "write_clipboard",
    "set_reminder",
    "list_reminders",
    "cancel_reminder",
    "daily_briefing",
    "run_routine",
    "list_routines",
    "send_to_claude",
    "deep_think",
    "get_datetime",
    # Antigravity App Control
    "ag_launch",
    "ag_cli_launch",
    "ag_status",
    "ag_focus",
    "ag_new_window",
    "ag_close_window",
    "ag_screenshot",
    "ag_open_folder",
    "ag_open_file",
    "ag_search_workspace",
    "ag_list_open_tabs",
    "ag_save_all",
    "ag_send_prompt",
    "ag_read_agent_output",
    "ag_wait_for_agent",
    "ag_list_pending_approvals",
    "ag_approve",
    "ag_reject",
    "ag_stop_agent",
    "ag_open_terminal",
    "ag_run_in_terminal",
    "ag_open_settings",
    "ag_list_extensions",
    "ag_install_extension",
    "ag_command_palette",
    "ag_build_feature",
    "ag_fix_failing_tests",
    "ag_review_changes",
    "ag_selftest",
    # Custom Skills (Claude-Desktop SKILL.md format)
    "list_custom_skills",
    "read_custom_skill",
    "create_custom_skill",
    "delete_custom_skill",
    # Model Context Protocol (MCP) Client
    "mcp_list_servers",
    "mcp_list_tools",
    "mcp_call_tool",
    "mcp_add_server",
    # Computer Use & AppProfile
    "cu_focus_app",
    "cu_screenshot_app",
    "cu_click_app",
    "cu_type_in_app",
    "cu_press_key_in_app",
    "cu_scroll_app",
    "cu_inspect_app",
    # Research Mode
    "research_topic",
    # Self-Awareness & Safety
    "list_my_tools",
    "explain_last_action",
    "undo_last_action",
    # Sub-Agents
    "spawn_subagent",
    "check_subagent",
    "cancel_subagent",
    "list_subagents",
    # Per-Project Context
    "set_project_context",
    "get_project_context",
    "list_project_contexts",
    "delete_project_context",
    # Scheduled Routines
    "schedule_routine",
    "list_scheduled_routines",
    "cancel_scheduled_routine",
]




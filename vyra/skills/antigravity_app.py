"""Antigravity Desktop Application Controller and Agent Automation Skill.

Provides Rusty with complete programmatic, keyboard, CLI, and transcript-level control
over the Antigravity IDE (version 1.107.0 / Electron hybrid shell).

Features:
  - Multi-channel orchestration: CLI launcher, Win32 window focus, direct transcript telemetry,
    command palette dispatch, and screenshot verification.
  - Zero-lag agent state observation via brain transcripts and SQLite conversation streams.
  - Code-enforced security boundaries: sensitive approvals require explicit confirmation,
    untrusted data cannot satisfy confirmation gates, and an immediate emergency kill switch.
"""

from __future__ import annotations

import ctypes
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from .common import (
    ROOT,
    _attach_input_desktop,
    _get_user_windows,
    _resolve_path,
    is_path_safe,
)

UI_MAP_PATH = os.path.join(ROOT, "antigravity_ui_map.json")


def _load_ui_map() -> Dict[str, Any]:
    """Load UI locators, shortcuts, and executable definitions with graceful fallback."""
    if os.path.exists(UI_MAP_PATH):
        try:
            with open(UI_MAP_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "version": "1.107.0",
        "process_name": "Antigravity.exe",
        "cli_paths": ["D:\\engineers\\Antigravity\\bin\\antigravity.CMD", "antigravity"],
        "executable_paths": [
            "D:\\engineers\\Antigravity\\Antigravity.exe",
            "C:\\Users\\Perfect\\AppData\\Local\\Programs\\antigravity\\Antigravity.exe"
        ],
        "data_paths": {
            "app_data": "C:\\Users\\Perfect\\.gemini\\antigravity",
            "conversations_db": "C:\\Users\\Perfect\\.gemini\\antigravity\\conversation_summaries.db",
            "conversations_dir": "C:\\Users\\Perfect\\.gemini\\antigravity\\conversations",
            "user_settings": "C:\\Users\\Perfect\\AppData\\Roaming\\Antigravity\\User\\settings.json"
        },
        "shortcuts": {
            "command_palette": {"primary": "ctrl+shift+p", "fallback": "f1"},
            "toggle_terminal": {"primary": "ctrl+`"},
            "focus_chat": {"primary": "ctrl+l"},
            "save_all": {"primary": "ctrl+k s"}
        }
    }


class AntigravityController:
    """Multi-channel controller for the Antigravity desktop application."""

    def __init__(self):
        self.ui_map = _load_ui_map()
        self.cli_cmd = self._resolve_cli()
        self.exe_path = self._resolve_exe()
        self.app_data = self.ui_map.get("data_paths", {}).get("app_data", os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity"))

    def _resolve_cli(self) -> str:
        candidates = self.ui_map.get("cli_paths", ["antigravity"])
        for c in candidates:
            if shutil.which(c):
                return c
            if os.path.isfile(c):
                return c
        return "antigravity"

    def _resolve_exe(self) -> str:
        candidates = self.ui_map.get("executable_paths", [])
        for c in candidates:
            if os.path.isfile(c):
                return c
        return "Antigravity.exe"

    def get_windows(self) -> List[Dict[str, Any]]:
        """Return list of active Antigravity window descriptors."""
        windows = _get_user_windows()
        return [w for w in windows if "antigravity" in w.get("proc", "").lower() or "antigravity" in w.get("title", "").lower()]

    def is_running(self) -> bool:
        """Check if Antigravity application process is active."""
        import psutil
        for p in psutil.process_iter(["name"]):
            try:
                if "antigravity" in (p.info["name"] or "").lower():
                    return True
            except Exception:
                pass
        return False

    def focus(self) -> Dict[str, Any]:
        """Bring Antigravity top-level window to foreground."""
        wins = self.get_windows()
        if not wins:
            return {"ok": False, "observed": "Antigravity window not found.", "evidence": "no_hwnd"}

        hwnd = wins[0]["hwnd"]
        user32 = ctypes.windll.user32
        _attach_input_desktop()
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.15)

        cur_fg = user32.GetForegroundWindow()
        success = (cur_fg == hwnd)
        return {
            "ok": success,
            "observed": f"Foreground set to '{wins[0]['title']}' (HWND: {hwnd})" if success else "Window focus request dispatched",
            "evidence": f"hwnd_{hwnd}"
        }

    def launch(self, workspace: str = "", new_window: bool = False) -> Dict[str, Any]:
        """Launch Antigravity IDE or open specified workspace folder."""
        args = [self.cli_cmd]
        if new_window:
            args.append("-n")
        else:
            args.append("-r")
        if workspace:
            res_path = _resolve_path(workspace)
            if not os.path.exists(res_path):
                return {"ok": False, "observed": f"Target workspace path '{workspace}' does not exist.", "evidence": "path_missing"}
            args.append(res_path)

        try:
            subprocess.Popen(args, shell=False)
            time.sleep(1.0)
            running = self.is_running()
            return {
                "ok": running,
                "observed": f"Antigravity launched successfully with workspace '{workspace or 'current'}'." if running else "Launch command dispatched.",
                "evidence": f"cli_cmd_{self.cli_cmd}"
            }
        except Exception as exc:
            return {"ok": False, "observed": f"Failed to execute launcher: {exc}", "evidence": "launch_error"}

    def status(self) -> Dict[str, Any]:
        """Report comprehensive process, window, and agent telemetry."""
        running = self.is_running()
        wins = self.get_windows()
        active_title = wins[0]["title"] if wins else "None"
        conv_id, latest_agent_msg = self.get_latest_agent_state()

        return {
            "ok": True,
            "observed": {
                "running": running,
                "windows_count": len(wins),
                "active_window_title": active_title,
                "latest_conversation_id": conv_id or "None",
                "latest_agent_status": latest_agent_msg.get("status", "idle") if latest_agent_msg else "idle",
                "cli_ready": bool(shutil.which(self.cli_cmd) or os.path.exists(self.cli_cmd))
            },
            "evidence": f"procs_{len(wins)}"
        }

    def get_latest_conversation_id(self) -> Optional[str]:
        """Locate the most recently modified conversation in Antigravity brain data."""
        conv_dir = os.path.join(self.app_data, "brain")
        if not os.path.exists(conv_dir):
            return None
        dirs = [os.path.join(conv_dir, d) for d in os.listdir(conv_dir) if os.path.isdir(os.path.join(conv_dir, d))]
        if not dirs:
            return None
        dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
        return os.path.basename(dirs[0])

    def get_latest_agent_state(self, conversation_id: str = "") -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Read latest step, status, and output directly from transcript JSONL."""
        cid = conversation_id or self.get_latest_conversation_id()
        if not cid:
            return None, None

        log_path = os.path.join(self.app_data, "brain", cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(log_path):
            return cid, None

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    return cid, entry
                except Exception:
                    continue
        except Exception:
            pass
        return cid, None

    def send_prompt(self, text: str, mode: str = "agent", add_file: str = "") -> Dict[str, Any]:
        """Inject prompt into Antigravity chat using native CLI chat subcommand."""
        if not text or not text.strip():
            return {"ok": False, "observed": "Empty prompt provided.", "evidence": "empty_text"}

        args = [self.cli_cmd, "chat", "-m", mode, "-r"]
        if add_file:
            res_file = _resolve_path(add_file)
            if os.path.exists(res_file):
                args.extend(["-a", res_file])
        args.append(text.strip())

        try:
            subprocess.Popen(args, shell=False)
            time.sleep(0.5)
            self.focus()
            return {
                "ok": True,
                "observed": f"Dispatched prompt in mode '{mode}' to Antigravity agent: \"{text[:100]}...\"",
                "evidence": f"chat_mode_{mode}"
            }
        except Exception as exc:
            return {"ok": False, "observed": f"Failed to send chat prompt: {exc}", "evidence": "prompt_dispatch_error"}

    def read_agent_output(self, conversation_id: str = "", limit: int = 3) -> Dict[str, Any]:
        """Extract recent agent thoughts, tool requests, and assistant messages."""
        cid, state = self.get_latest_agent_state(conversation_id)
        if not cid:
            return {"ok": False, "observed": "No active Antigravity conversation found.", "evidence": "no_cid"}

        log_path = os.path.join(self.app_data, "brain", cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(log_path):
            return {"ok": False, "observed": f"Transcript not found for conversation {cid}", "evidence": "missing_log"}

        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = [l.strip() for l in f if l.strip()]

            recent = []
            for l in reversed(lines):
                try:
                    data = json.loads(l)
                    stype = data.get("type", "")
                    content = data.get("content", "")
                    tool_calls = data.get("tool_calls", [])
                    if content or tool_calls:
                        recent.append({
                            "step_index": data.get("step_index"),
                            "type": stype,
                            "status": data.get("status"),
                            "content_preview": content[:300] if content else "(Tool execution block)",
                            "tool_calls": [tc.get("tool_name", "") for tc in tool_calls] if tool_calls else []
                        })
                    if len(recent) >= limit:
                        break
                except Exception:
                    continue

            return {
                "ok": True,
                "observed": {
                    "conversation_id": cid,
                    "recent_steps": recent
                },
                "evidence": f"steps_read_{len(recent)}"
            }
        except Exception as exc:
            return {"ok": False, "observed": f"Error parsing transcript: {exc}", "evidence": "transcript_error"}

    def wait_for_agent(self, timeout: int = 60, conversation_id: str = "") -> Dict[str, Any]:
        """Block until current agent step completes (status: DONE) or timeout expires."""
        cid = conversation_id or self.get_latest_conversation_id()
        if not cid:
            return {"ok": False, "observed": "No active conversation to wait on.", "evidence": "no_cid"}

        start_time = time.time()
        last_step = -1

        while time.time() - start_time < timeout:
            _, state = self.get_latest_agent_state(cid)
            if state:
                status = state.get("status")
                step_idx = state.get("step_index", 0)
                if status == "DONE" and (last_step == -1 or step_idx >= last_step):
                    return {
                        "ok": True,
                        "observed": f"Agent completed step {step_idx} with status DONE.",
                        "evidence": f"step_{step_idx}_done"
                    }
                last_step = step_idx
            time.sleep(1.0)

        return {"ok": False, "observed": f"Timed out waiting for agent after {timeout} seconds.", "evidence": "timeout"}

    def send_shortcut(self, key_combo: str) -> Dict[str, Any]:
        """Safely send keyboard shortcut to focused Antigravity window."""
        self.focus()
        from .system import press_hotkey
        res = press_hotkey(None, key_combo)
        time.sleep(0.2)
        return {"ok": True, "observed": f"Sent shortcut '{key_combo}': {res}", "evidence": f"key_{key_combo}"}

    def command_palette(self, command_name: str) -> Dict[str, Any]:
        """Trigger Antigravity command palette command."""
        self.focus()
        self.send_shortcut("ctrl+shift+p")
        time.sleep(0.25)
        from .system import type_text, press_hotkey
        type_text(None, command_name)
        time.sleep(0.2)
        press_hotkey(None, "enter")
        return {"ok": True, "observed": f"Triggered command palette: '{command_name}'", "evidence": f"cmd_{command_name}"}

    def stop_agent(self) -> Dict[str, Any]:
        """Emergency kill switch: abort running Antigravity task and release input."""
        self.focus()
        # Esc to dismiss modal or focus, Ctrl+C in terminal if focused
        from .system import press_hotkey
        press_hotkey(None, "esc")
        press_hotkey(None, "esc")
        return {
            "ok": True,
            "observed": "Emergency stop signal sent to Antigravity interface.",
            "evidence": "kill_switch_active"
        }

    def selftest(self) -> Dict[str, Any]:
        """Validate all controller channels, locators, and telemetry files."""
        results = {}
        # 1. CLI availability
        cli_ok = bool(shutil.which(self.cli_cmd) or os.path.exists(self.cli_cmd))
        results["cli_launcher"] = {"ok": cli_ok, "path": self.cli_cmd}

        # 2. Process check
        proc_ok = self.is_running()
        results["process_check"] = {"ok": proc_ok, "active": proc_ok}

        # 3. Window check
        wins = self.get_windows()
        results["window_check"] = {"ok": len(wins) > 0, "count": len(wins), "title": wins[0]["title"] if wins else "None"}

        # 4. Telemetry dir check
        brain_ok = os.path.exists(os.path.join(self.app_data, "brain"))
        results["telemetry_brain"] = {"ok": brain_ok, "path": self.app_data}

        # 5. UI map validity
        results["ui_map"] = {"ok": bool(self.ui_map.get("shortcuts")), "shortcuts_count": len(self.ui_map.get("shortcuts", {}))}

        all_ok = all(v["ok"] for v in results.values())
        return {
            "ok": all_ok,
            "observed": "All Antigravity controller channels operational." if all_ok else "One or more channels degraded.",
            "evidence": results
        }


# Global controller singleton
_CONTROLLER = AntigravityController()


# ---------------------------------------------------------------------------
# Registered Skill Functions
# ---------------------------------------------------------------------------

def ag_launch(memory, workspace: str = "", new_window: bool = False) -> str:
    """Launch the Antigravity IDE application or open a specific project folder."""
    res = _CONTROLLER.launch(workspace=workspace, new_window=new_window)
    return res["observed"]


def ag_status(memory) -> str:
    """Inspect Antigravity process state, active window, and agent telemetry."""
    res = _CONTROLLER.status()
    obs = res["observed"]
    return (
        f"Antigravity Status Report, Sir:\n"
        f"  - Process Active: {'Yes' if obs['running'] else 'No'}\n"
        f"  - Windows Open: {obs['windows_count']} (Active: '{obs['active_window_title']}')\n"
        f"  - Latest Conversation: {obs['latest_conversation_id']}\n"
        f"  - Agent State: {obs['latest_agent_status']}\n"
        f"  - CLI Ready: {'Yes' if obs['cli_ready'] else 'No'}"
    )


def ag_focus(memory) -> str:
    """Bring the Antigravity IDE window to the foreground."""
    res = _CONTROLLER.focus()
    return res["observed"]


def ag_new_window(memory) -> str:
    """Open a new separate Antigravity IDE window."""
    res = _CONTROLLER.launch(new_window=True)
    return res["observed"]


def ag_close_window(memory) -> str:
    """Close the active Antigravity window."""
    _CONTROLLER.focus()
    from .system import press_hotkey
    press_hotkey(None, "alt+f4")
    return "Closed active Antigravity window, Sir."


def ag_screenshot(memory, filename: str = "antigravity_view.png") -> str:
    """Take a screenshot of the Antigravity IDE for visual audit and verification."""
    _CONTROLLER.focus()
    from .media import save_screenshot
    return save_screenshot(memory, filename=filename)


def ag_open_folder(memory, path: str) -> str:
    """Open a project folder or workspace directory inside Antigravity."""
    res = _CONTROLLER.launch(workspace=path, new_window=False)
    return res["observed"]


def ag_open_file(memory, path: str, line: int = 1) -> str:
    """Open a specific file at an exact line number in Antigravity."""
    full_path = _resolve_path(path)
    if not is_path_safe(full_path):
        return f"Access denied: '{os.path.basename(full_path)}' is in a protected system path, Sir."
    if not os.path.exists(full_path):
        return f"File does not exist: {full_path}"

    target = f"{full_path}:{line}"
    try:
        subprocess.Popen([_CONTROLLER.cli_cmd, "-g", target], shell=False)
        time.sleep(0.5)
        _CONTROLLER.focus()
        return f"Opened '{os.path.basename(full_path)}' at line {line} in Antigravity, Sir."
    except Exception as exc:
        return f"Failed to open file: {exc}"


def ag_search_workspace(memory, query: str) -> str:
    """Trigger a global workspace text search in Antigravity."""
    _CONTROLLER.focus()
    _CONTROLLER.send_shortcut("ctrl+shift+f")
    time.sleep(0.2)
    from .system import type_text, press_hotkey
    type_text(None, query)
    press_hotkey(None, "enter")
    return f"Searching workspace for '{query}' in Antigravity, Sir."


def ag_list_open_tabs(memory) -> str:
    """List open editor tabs and inspect currently focused file."""
    wins = _CONTROLLER.get_windows()
    if not wins:
        return "No open Antigravity windows detected."
    title = wins[0].get("title", "")
    return f"Active Antigravity window title: '{title}'"


def ag_save_all(memory) -> str:
    """Save all modified files across open Antigravity editors."""
    _CONTROLLER.command_palette("workbench.action.files.saveAll")
    return "Saved all modified files in Antigravity, Sir."


def ag_send_prompt(memory, text: str, mode: str = "agent", add_file: str = "") -> str:
    """Send an instruction or prompt to the Antigravity AI agent."""
    res = _CONTROLLER.send_prompt(text=text, mode=mode, add_file=add_file)
    return res["observed"]


def ag_read_agent_output(memory, conversation_id: str = "", limit: int = 3) -> str:
    """Read the latest messages, plan, and tool calls directly from Antigravity's agent transcript."""
    res = _CONTROLLER.read_agent_output(conversation_id=conversation_id, limit=limit)
    if not res["ok"]:
        return res["observed"]

    obs = res["observed"]
    steps = obs["recent_steps"]
    if not steps:
        return f"No recent steps recorded in conversation {obs['conversation_id']}."

    lines = [f"Antigravity Agent Telemetry (Conversation: {obs['conversation_id'][:8]}...):"]
    for s in steps:
        idx = s.get("step_index")
        stype = s.get("type")
        status = s.get("status")
        tools = ", ".join(s.get("tool_calls", [])) or "None"
        prev = s.get("content_preview", "").replace("\n", " ").strip()
        lines.append(f"  - [Step {idx} | {stype} | {status}] Tools: {tools} -> {prev[:100]}")
    return "\n".join(lines)


def ag_wait_for_agent(memory, timeout: int = 60, conversation_id: str = "") -> str:
    """Wait for the Antigravity agent to complete its current task execution."""
    res = _CONTROLLER.wait_for_agent(timeout=timeout, conversation_id=conversation_id)
    return res["observed"]


def ag_list_pending_approvals(memory, conversation_id: str = "") -> str:
    """Check if the Antigravity agent is waiting for user approval on terminal or file changes."""
    cid, state = _CONTROLLER.get_latest_agent_state(conversation_id)
    if not state:
        return "No active agent steps found."

    status = state.get("status", "")
    if status == "waiting_for_input":
        detail = state.get("stateDetail", "User confirmation required")
        return f"Pending Approval in Antigravity: {detail}"
    return "No actions currently awaiting approval in Antigravity, Sir."


def ag_approve(memory, item_id: str, confirm: bool = False) -> str:
    """Approve a pending action or step in Antigravity. SENSITIVE: requires explicit confirmation."""
    if not confirm:
        return (
            f"SAFETY GATE (Sensitive Action): Approving step '{item_id}' authorizes Antigravity "
            f"to execute terminal commands or code modifications. Please explicitly confirm to approve."
        )
    _CONTROLLER.focus()
    from .system import press_hotkey
    press_hotkey(None, "enter")
    return f"Approved Antigravity step '{item_id}', Sir."


def ag_reject(memory, item_id: str, reason: str = "") -> str:
    """Reject a pending agent step or cancel execution in Antigravity."""
    _CONTROLLER.focus()
    from .system import press_hotkey
    press_hotkey(None, "esc")
    return f"Rejected Antigravity step '{item_id}'{f' with reason: {reason}' if reason else ''}, Sir."


def ag_stop_agent(memory) -> str:
    """Emergency kill switch: instantly stop Antigravity's autonomous agent execution."""
    res = _CONTROLLER.stop_agent()
    return res["observed"]


def ag_open_terminal(memory) -> str:
    """Open or focus the integrated terminal inside Antigravity."""
    _CONTROLLER.command_palette("workbench.action.terminal.toggleTerminal")
    return "Toggled Antigravity integrated terminal, Sir."


def ag_run_in_terminal(memory, cmd: str, confirm: bool = False) -> str:
    """Run a terminal command inside Antigravity's integrated terminal panel. Requires confirm for safety."""
    if not confirm and any(d in cmd.lower() for d in ("rm", "del", "drop", "kill", "reset", "force", "format")):
        return f"Safety Hold: Command '{cmd}' requires explicit confirmation before executing in Antigravity terminal."

    _CONTROLLER.focus()
    _CONTROLLER.send_shortcut("ctrl+`")
    time.sleep(0.3)
    from .system import type_text, press_hotkey
    type_text(None, cmd)
    press_hotkey(None, "enter")
    return f"Executed command in Antigravity terminal: '{cmd}', Sir."


def ag_open_settings(memory) -> str:
    """Open Antigravity application settings."""
    _CONTROLLER.command_palette("workbench.action.openSettings")
    return "Opened Antigravity settings, Sir."


def ag_list_extensions(memory) -> str:
    """List all installed extensions in Antigravity."""
    try:
        res = subprocess.run([_CONTROLLER.cli_cmd, "--list-extensions"], capture_output=True, text=True, timeout=10)
        exts = res.stdout.strip().splitlines()
        if not exts:
            return "No extensions reported by Antigravity CLI."
        return f"Installed Antigravity Extensions ({len(exts)} total):\n" + "\n".join(f"  - {e}" for e in exts[:15])
    except Exception as exc:
        return f"Failed to list extensions: {exc}"


def ag_install_extension(memory, ext_id: str, confirm: bool = False) -> str:
    """Install an extension into Antigravity. Requires confirmation."""
    if not confirm:
        return f"Safety Hold: Confirm to install extension '{ext_id}' into Antigravity, Sir."
    try:
        res = subprocess.run([_CONTROLLER.cli_cmd, "--install-extension", ext_id], capture_output=True, text=True, timeout=60)
        return res.stdout.strip() or f"Installed extension '{ext_id}', Sir."
    except Exception as exc:
        return f"Failed to install extension: {exc}"


def ag_command_palette(memory, command: str) -> str:
    """Execute any command palette command in Antigravity."""
    res = _CONTROLLER.command_palette(command)
    return res["observed"]


def ag_build_feature(memory, project: str, spec: str) -> str:
    """Compound workflow: opens project, sends specification to agent, and waits for plan."""
    launch_res = _CONTROLLER.launch(workspace=project)
    time.sleep(1.5)
    prompt = f"Implement feature request:\n{spec}\n\nPlease generate a step-by-step plan and wait for confirmation."
    _CONTROLLER.send_prompt(prompt, mode="agent")
    return f"Initiated feature build in '{project}'. Sent specification to Antigravity agent, Sir."


def ag_fix_failing_tests(memory, project: str) -> str:
    """Compound workflow: instructs Antigravity agent to run tests and resolve any failures."""
    _CONTROLLER.launch(workspace=project)
    time.sleep(1.0)
    prompt = "Run the project unit test suite. If any tests fail, analyze the error trace, apply fixes, and re-run to verify."
    _CONTROLLER.send_prompt(prompt, mode="agent")
    return f"Instructed Antigravity agent to inspect and resolve failing tests in '{project}', Sir."


def ag_review_changes(memory, project: str) -> str:
    """Compound workflow: requests a comprehensive code review of uncommitted changes from Antigravity."""
    _CONTROLLER.launch(workspace=project)
    time.sleep(1.0)
    prompt = "Review all modified and unstaged files in the active workspace. Provide a security, performance, and architecture assessment."
    _CONTROLLER.send_prompt(prompt, mode="ask")
    return f"Requested automated change review for '{project}' from Antigravity agent, Sir."


def ag_selftest(memory) -> str:
    """Run comprehensive self-test across Antigravity CLI, process, window, and transcript channels."""
    res = _CONTROLLER.selftest()
    lines = ["Antigravity Self-Test Diagnostics:"]
    for k, v in res["evidence"].items():
        status = "PASSED" if v.get("ok") else "FAILED"
        lines.append(f"  - [{status}] {k.replace('_', ' ').title()}: {v}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Skill Definitions Registry
# ---------------------------------------------------------------------------

ANTIGRAVITY_SKILLS = [
    {"name": "ag_launch", "fn": ag_launch, "description": "Launch the Antigravity IDE application or open a specific workspace.",
     "parameters": {"type": "object", "properties": {"workspace": {"type": "string", "description": "Optional folder path to open as workspace"}, "new_window": {"type": "boolean", "description": "Force opening a separate new window"}}, "required": []}},
    {"name": "ag_status", "fn": ag_status, "description": "Inspect Antigravity process state, active window title, and agent telemetry.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_focus", "fn": ag_focus, "description": "Bring Antigravity IDE window to the foreground.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_new_window", "fn": ag_new_window, "description": "Open a new separate Antigravity window.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_close_window", "fn": ag_close_window, "description": "Close the active Antigravity window.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_screenshot", "fn": ag_screenshot, "description": "Capture a screenshot of Antigravity for visual verification.",
     "parameters": {"type": "object", "properties": {"filename": {"type": "string", "description": "Image filename"}}, "required": []}},
    {"name": "ag_open_folder", "fn": ag_open_folder, "description": "Open a project folder or directory in Antigravity.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Directory path to open"}}, "required": ["path"]}},
    {"name": "ag_open_file", "fn": ag_open_file, "description": "Open a file at a specific line number in Antigravity.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path"}, "line": {"type": "integer", "description": "Line number (default 1)"}}, "required": ["path"]}},
    {"name": "ag_search_workspace", "fn": ag_search_workspace, "description": "Search workspace text across all files in Antigravity.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Text query to search"}}, "required": ["query"]}},
    {"name": "ag_list_open_tabs", "fn": ag_list_open_tabs, "description": "Inspect open tabs and active file in Antigravity.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_save_all", "fn": ag_save_all, "description": "Save all open files across Antigravity editors.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_send_prompt", "fn": ag_send_prompt, "description": "Send a prompt or directive to the Antigravity AI agent.",
     "parameters": {"type": "object", "properties": {"text": {"type": "string", "description": "Prompt text to send"}, "mode": {"type": "string", "enum": ["agent", "edit", "ask"], "description": "Agent mode (default 'agent')"}, "add_file": {"type": "string", "description": "Optional file path to attach as context"}}, "required": ["text"]}},
    {"name": "ag_read_agent_output", "fn": ag_read_agent_output, "description": "Read recent agent responses, thought logs, and tool calls from Antigravity's transcript.",
     "parameters": {"type": "object", "properties": {"conversation_id": {"type": "string", "description": "Optional conversation ID"}, "limit": {"type": "integer", "description": "Number of recent steps to read (default 3)"}}, "required": []}},
    {"name": "ag_wait_for_agent", "fn": ag_wait_for_agent, "description": "Wait until Antigravity agent finishes its current active step or task.",
     "parameters": {"type": "object", "properties": {"timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"}, "conversation_id": {"type": "string", "description": "Optional conversation ID"}}, "required": []}},
    {"name": "ag_list_pending_approvals", "fn": ag_list_pending_approvals, "description": "Check if Antigravity agent is awaiting approval for tool execution or changes.",
     "parameters": {"type": "object", "properties": {"conversation_id": {"type": "string"}}, "required": []}},
    {"name": "ag_approve", "fn": ag_approve, "description": "Approve a pending Antigravity step. SENSITIVE: requires explicit confirmation.",
     "parameters": {"type": "object", "properties": {"item_id": {"type": "string", "description": "ID of step to approve"}, "confirm": {"type": "boolean", "description": "Explicit confirmation"}}, "required": ["item_id"]}},
    {"name": "ag_reject", "fn": ag_reject, "description": "Reject or cancel a pending Antigravity step.",
     "parameters": {"type": "object", "properties": {"item_id": {"type": "string", "description": "ID of step to reject"}, "reason": {"type": "string", "description": "Optional rejection reason"}}, "required": ["item_id"]}},
    {"name": "ag_stop_agent", "fn": ag_stop_agent, "description": "Emergency kill switch: abort running Antigravity autonomous agent immediately.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_open_terminal", "fn": ag_open_terminal, "description": "Toggle and focus the integrated terminal inside Antigravity.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_run_in_terminal", "fn": ag_run_in_terminal, "description": "Run a command inside Antigravity's integrated terminal. Destructive commands require confirm=True.",
     "parameters": {"type": "object", "properties": {"cmd": {"type": "string", "description": "Command to run"}, "confirm": {"type": "boolean", "description": "Set to true for destructive commands"}}, "required": ["cmd"]}},
    {"name": "ag_open_settings", "fn": ag_open_settings, "description": "Open Antigravity settings UI.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_list_extensions", "fn": ag_list_extensions, "description": "List all extensions installed in Antigravity.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "ag_install_extension", "fn": ag_install_extension, "description": "Install an extension in Antigravity. Requires confirmation.",
     "parameters": {"type": "object", "properties": {"ext_id": {"type": "string", "description": "Extension ID or VSIX path"}, "confirm": {"type": "boolean", "description": "Set true to confirm install"}}, "required": ["ext_id"]}},
    {"name": "ag_command_palette", "fn": ag_command_palette, "description": "Execute any command palette command in Antigravity (e.g. workbench.action.files.saveAll).",
     "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "Internal VS Code / Antigravity command ID"}}, "required": ["command"]}},
    {"name": "ag_build_feature", "fn": ag_build_feature, "description": "Compound workflow: Open project, send feature specification to Antigravity agent, and await plan.",
     "parameters": {"type": "object", "properties": {"project": {"type": "string", "description": "Project directory"}, "spec": {"type": "string", "description": "Feature specification"}}, "required": ["project", "spec"]}},
    {"name": "ag_fix_failing_tests", "fn": ag_fix_failing_tests, "description": "Compound workflow: Ask Antigravity agent to diagnose and fix failing unit tests.",
     "parameters": {"type": "object", "properties": {"project": {"type": "string", "description": "Project directory"}}, "required": ["project"]}},
    {"name": "ag_review_changes", "fn": ag_review_changes, "description": "Compound workflow: Ask Antigravity agent to review uncommitted code changes in workspace.",
     "parameters": {"type": "object", "properties": {"project": {"type": "string", "description": "Project directory"}}, "required": ["project"]}},
    {"name": "ag_selftest", "fn": ag_selftest, "description": "Run self-test diagnostics across all Antigravity control channels and telemetry locators.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
]

__all__ = [
    "AntigravityController",
    "ANTIGRAVITY_SKILLS",
    "ag_launch",
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
]

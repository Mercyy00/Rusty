"""General Computer Use Framework and AppProfile Abstraction for Rusty.

Allows Rusty to interact with any Windows application (browser, terminal, editor, office)
using a unified channel strategy: window detection, foreground focusing, screenshot capture,
coordinate clicks, text typing, keyboard combos, and mouse wheel scrolling.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

from .common import _attach_input_desktop, _get_user_windows


class AppProfile:
    """Base application profile abstraction."""

    def __init__(self, name: str, process_names: List[str] = None):
        self.name = name.lower()
        self.process_names = [p.lower() for p in (process_names or [name])]

    def get_windows(self) -> List[Dict[str, Any]]:
        windows = _get_user_windows()
        matches = []
        for w in windows:
            p_name = w.get("proc", "").lower()
            title = w.get("title", "").lower()
            if any(pn in p_name for pn in self.process_names) or self.name in title:
                matches.append(w)
        return matches

    def focus(self) -> Dict[str, Any]:
        wins = self.get_windows()
        if not wins:
            return {"ok": False, "observed": f"No running window found for application '{self.name}'.", "evidence": "no_window"}

        hwnd = wins[0]["hwnd"]
        user32 = ctypes.windll.user32
        _attach_input_desktop()
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.15)
        cur_fg = user32.GetForegroundWindow()
        return {
            "ok": (cur_fg == hwnd),
            "observed": f"Focused application '{self.name}' (HWND: {hwnd}, Title: '{wins[0]['title']}')",
            "evidence": f"hwnd_{hwnd}"
        }

    def inspect(self) -> Dict[str, Any]:
        wins = self.get_windows()
        if not wins:
            return {"ok": False, "observed": f"Application '{self.name}' is not currently running.", "evidence": "offline"}
        return {
            "ok": True,
            "observed": {
                "name": self.name,
                "running": True,
                "windows_count": len(wins),
                "active_window": wins[0]
            },
            "evidence": f"procs_{len(wins)}"
        }

    def click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        self.focus()
        from .system import click_mouse
        res = click_mouse(None, x=x, y=y)
        return {"ok": True, "observed": res, "evidence": "mouse_clicked"}

    def type_text(self, text: str) -> Dict[str, Any]:
        self.focus()
        from .system import type_text
        res = type_text(None, text)
        return {"ok": True, "observed": res, "evidence": "text_typed"}

    def press_key(self, combo: str) -> Dict[str, Any]:
        self.focus()
        from .system import press_hotkey
        res = press_hotkey(None, combo)
        return {"ok": True, "observed": res, "evidence": f"key_{combo}"}

    def scroll(self, direction: str = "down", amount: int = 3) -> Dict[str, Any]:
        self.focus()
        delta = -120 * amount if direction.lower() == "down" else 120 * amount
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, delta, 0)
        return {"ok": True, "observed": f"Scrolled {direction} by {amount} clicks.", "evidence": f"scroll_{direction}"}


class BrowserProfile(AppProfile):
    def __init__(self):
        super().__init__("browser", ["brave.exe", "chrome.exe", "msedge.exe", "firefox.exe", "zen.exe"])


class TerminalProfile(AppProfile):
    def __init__(self):
        super().__init__("terminal", ["windowsterminal.exe", "powershell.exe", "cmd.exe", "wt.exe"])


class AntigravityProfile(AppProfile):
    def __init__(self):
        super().__init__("antigravity", ["antigravity.exe"])


_PROFILES: Dict[str, AppProfile] = {
    "browser": BrowserProfile(),
    "chrome": BrowserProfile(),
    "brave": BrowserProfile(),
    "edge": BrowserProfile(),
    "terminal": TerminalProfile(),
    "powershell": TerminalProfile(),
    "cmd": TerminalProfile(),
    "antigravity": AntigravityProfile(),
}


def get_app_profile(name: str) -> AppProfile:
    clean = (name or "").strip().lower()
    if clean in _PROFILES:
        return _PROFILES[clean]
    profile = AppProfile(clean)
    _PROFILES[clean] = profile
    return profile


# ---------------------------------------------------------------------------
# Registered Computer Use Skill Functions
# ---------------------------------------------------------------------------

def cu_focus_app(memory, app_name: str) -> str:
    """Focus an application window on Windows desktop."""
    profile = get_app_profile(app_name)
    res = profile.focus()
    return res["observed"]


def cu_screenshot_app(memory, app_name: str, filename: str = "") -> str:
    """Capture a screenshot with the target application focused."""
    profile = get_app_profile(app_name)
    profile.focus()
    from .media import save_screenshot
    fn = filename or f"{app_name}_view.png"
    return save_screenshot(memory, filename=fn)


def cu_click_app(memory, app_name: str, x: int = None, y: int = None) -> str:
    """Focus application and click at specified coordinates or current position."""
    profile = get_app_profile(app_name)
    res = profile.click(x=x, y=y)
    return res["observed"]


def cu_type_in_app(memory, app_name: str, text: str) -> str:
    """Focus application and type text into its active input field."""
    profile = get_app_profile(app_name)
    res = profile.type_text(text)
    return res["observed"]


def cu_press_key_in_app(memory, app_name: str, combo: str) -> str:
    """Focus application and send a keyboard shortcut combo."""
    profile = get_app_profile(app_name)
    res = profile.press_key(combo)
    return res["observed"]


def cu_scroll_app(memory, app_name: str, direction: str = "down", amount: int = 3) -> str:
    """Focus application and scroll the mouse wheel up or down."""
    profile = get_app_profile(app_name)
    res = profile.scroll(direction=direction, amount=amount)
    return res["observed"]


def cu_inspect_app(memory, app_name: str) -> str:
    """Inspect application running status, window count, and active title."""
    profile = get_app_profile(app_name)
    res = profile.inspect()
    if not res["ok"]:
        return res["observed"]
    obs = res["observed"]
    win = obs["active_window"]
    return (
        f"Application Telemetry for '{app_name}':\n"
        f"  - Running: Yes (PID: {win['pid']})\n"
        f"  - Active Window Title: '{win['title']}'\n"
        f"  - Window Handle (HWND): {win['hwnd']}"
    )


COMPUTER_USE_SKILLS = [
    {"name": "cu_focus_app", "fn": cu_focus_app, "description": "Focus an application window on Windows desktop.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string", "description": "Target app name (e.g. 'notepad', 'browser', 'spotify')"}}, "required": ["app_name"]}},
    {"name": "cu_screenshot_app", "fn": cu_screenshot_app, "description": "Focus an application and take a visual screenshot.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string", "description": "App name"}, "filename": {"type": "string", "description": "Image filename"}}, "required": ["app_name"]}},
    {"name": "cu_click_app", "fn": cu_click_app, "description": "Focus an application and click mouse at coordinates.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}, "x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["app_name"]}},
    {"name": "cu_type_in_app", "fn": cu_type_in_app, "description": "Focus an application and type text into it.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}, "text": {"type": "string"}}, "required": ["app_name", "text"]}},
    {"name": "cu_press_key_in_app", "fn": cu_press_key_in_app, "description": "Focus application and press keyboard combo (e.g. 'ctrl+s', 'alt+f4', 'enter').",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}, "combo": {"type": "string"}}, "required": ["app_name", "combo"]}},
    {"name": "cu_scroll_app", "fn": cu_scroll_app, "description": "Focus application and scroll the mouse wheel.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}, "direction": {"type": "string", "enum": ["up", "down"]}, "amount": {"type": "integer"}}, "required": ["app_name"]}},
    {"name": "cu_inspect_app", "fn": cu_inspect_app, "description": "Inspect window handle, PID, and title of any application.",
     "parameters": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]}},
]

__all__ = [
    "AppProfile",
    "BrowserProfile",
    "TerminalProfile",
    "AntigravityProfile",
    "get_app_profile",
    "COMPUTER_USE_SKILLS",
    "cu_focus_app",
    "cu_screenshot_app",
    "cu_click_app",
    "cu_type_in_app",
    "cu_press_key_in_app",
    "cu_scroll_app",
    "cu_inspect_app",
]

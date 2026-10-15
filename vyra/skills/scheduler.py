"""Scheduled routines and recurring background tasks for Rusty.

Enables recurring automation (e.g. daily morning briefs, nightly backups,
scheduled system checks) backed by persistent storage.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .common import ROOT

SCHEDULE_STORE = Path(ROOT) / "data" / "scheduled_routines.json"


def _load_schedules() -> List[dict]:
    if SCHEDULE_STORE.exists():
        try:
            return json.loads(SCHEDULE_STORE.read_text("utf-8"))
        except Exception:
            return []
    return []


def _save_schedules(data: List[dict]):
    SCHEDULE_STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SCHEDULE_STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
    tmp.replace(SCHEDULE_STORE)


def schedule_routine(
    memory: Any,
    routine_name: str,
    trigger_time: str,
    description: str = "",
) -> str:
    """Schedule a recurring or timed routine to run automatically (e.g. '08:00', 'every morning at 8', '22:30').

    Args:
        memory: Rusty memory instance.
        routine_name: Name of the routine (e.g. 'start my day', 'focus mode', 'wind down').
        trigger_time: Clock time or frequency (e.g. '08:00', 'daily at 09:00', 'every Monday').
        description: Optional notes or context for the schedule.
    """
    clean_routine = (routine_name or "").strip()
    clean_time = (trigger_time or "").strip()
    if not clean_routine or not clean_time:
        return "Please specify both a routine name and a trigger time (e.g. '08:00'), Sir."

    # Verify routine exists
    from .. import routines
    steps = routines.get_steps(clean_routine)
    if steps is None:
        valid_routines = ", ".join(routines.list_names())
        return f"Routine '{clean_routine}' not found. Available routines: {valid_routines}."

    schedules = _load_schedules()
    sched_id = f"sched-{int(time.time() * 1000) % 1000000:06d}"

    entry = {
        "id": sched_id,
        "routine": clean_routine,
        "time": clean_time,
        "description": description or f"Run routine '{clean_routine}' at {clean_time}",
        "created_at": datetime.now().isoformat(),
        "active": True,
    }
    schedules.append(entry)
    _save_schedules(schedules)

    return (
        f"Scheduled routine `{sched_id}` configured successfully, Sir.\n\n"
        f"- Routine: **{clean_routine}**\n"
        f"- Trigger: **{clean_time}**\n"
        f"- Status: ACTIVE\n"
        f"- Cancel anytime via `cancel_scheduled_routine(schedule_id='{sched_id}')`"
    )


def list_scheduled_routines(memory: Any) -> str:
    """List all scheduled recurring routines and automated tasks."""
    schedules = _load_schedules()
    active_schedules = [s for s in schedules if s.get("active", True)]
    if not active_schedules:
        return "No scheduled routines currently active, Sir. Use `schedule_routine` to configure one."

    lines = [f"Active Scheduled Routines ({len(active_schedules)} items):"]
    for s in active_schedules:
        lines.append(f"  - `{s['id']}`: **{s['routine']}** @ {s['time']} ({s.get('description', '')})")
    return "\n".join(lines)


def cancel_scheduled_routine(memory: Any, schedule_id: str, confirm: bool = False) -> str:
    """Cancel and deactivate a scheduled routine."""
    clean_id = (schedule_id or "").strip()
    if not clean_id:
        return "Please specify a schedule ID to cancel, Sir."

    schedules = _load_schedules()
    target = next((s for s in schedules if s["id"] == clean_id and s.get("active", True)), None)
    if not target:
        return f"No active scheduled routine found with ID '{clean_id}', Sir."

    if not confirm:
        return f"Are you sure you want to cancel scheduled routine `{clean_id}` ({target['routine']} @ {target['time']})? Call with confirm=True to proceed."

    target["active"] = False
    _save_schedules(schedules)
    return f"Scheduled routine `{clean_id}` has been cancelled."


SCHEDULER_SKILLS = [
    {
        "name": "schedule_routine",
        "fn": schedule_routine,
        "description": "Schedule a recurring or timed execution of any saved routine (e.g. 'start my day at 08:00', 'wind down at 22:30').",
        "parameters": {
            "type": "object",
            "properties": {
                "routine_name": {"type": "string", "description": "The routine to execute (e.g. 'start my day', 'focus mode')"},
                "trigger_time": {"type": "string", "description": "Trigger time or interval (e.g. '08:00', 'daily at 09:30')"},
                "description": {"type": "string", "description": "Optional notes or reason"},
            },
            "required": ["routine_name", "trigger_time"],
        },
    },
    {
        "name": "list_scheduled_routines",
        "fn": list_scheduled_routines,
        "description": "List all active scheduled routines and automations.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "cancel_scheduled_routine",
        "fn": cancel_scheduled_routine,
        "description": "Cancel an active scheduled routine by ID. Requires confirm=True.",
        "parameters": {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "description": "Schedule ID (e.g. 'sched-123456')"},
                "confirm": {"type": "boolean", "description": "Explicit confirmation required to cancel"},
            },
            "required": ["schedule_id"],
        },
    },
]

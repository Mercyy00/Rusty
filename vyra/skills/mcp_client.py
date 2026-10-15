"""Model Context Protocol (MCP) Client for Rusty.

Connects to external MCP servers over stdio and HTTP JSON-RPC 2.0, discovers tools,
and exposes them dynamically through Rusty's unified skill registry with code-enforced
risk levels and confirmation safety gates.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from typing import Any, Dict, List, Optional

from .common import ROOT

MCP_CONFIG_PATH = os.path.join(ROOT, "mcp_servers.json")


def _load_mcp_config() -> Dict[str, Any]:
    if os.path.exists(MCP_CONFIG_PATH):
        try:
            with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"mcpServers": {}}


def _save_mcp_config(data: Dict[str, Any]):
    try:
        with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class MCPClient:
    """Lightweight, zero-external-dependency JSON-RPC 2.0 client for stdio & HTTP MCP servers."""

    def __init__(self, config_path: str = MCP_CONFIG_PATH):
        self.config_path = config_path

    def get_servers(self) -> Dict[str, Any]:
        return _load_mcp_config().get("mcpServers", {})

    def call_stdio_jsonrpc(self, command: str, args: List[str], request: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """Execute a single JSON-RPC 2.0 request over a stdio MCP server process."""
        proc = subprocess.Popen(
            [command] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        req_line = json.dumps(request) + "\n"
        try:
            stdout, stderr = proc.communicate(input=req_line, timeout=timeout)
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except Exception:
                    continue
            return {"error": {"message": f"No JSON response from server. Stderr: {stderr[:200]}"}}
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"error": {"message": f"MCP server timed out after {timeout}s."}}
        except Exception as exc:
            return {"error": {"message": str(exc)}}

    def call_http_jsonrpc(self, url: str, request: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """Execute a JSON-RPC 2.0 request over an HTTP/SSE endpoint."""
        body = json.dumps(request).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "Rusty-MCP/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)
        except Exception as exc:
            return {"error": {"message": f"HTTP MCP error: {exc}"}}

    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Query tools/list from a configured MCP server."""
        servers = self.get_servers()
        if server_name not in servers:
            return []

        server = servers[server_name]
        req = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/list",
            "params": {}
        }

        if "url" in server:
            res = self.call_http_jsonrpc(server["url"], req)
        else:
            cmd = server.get("command")
            args = server.get("args", [])
            if not cmd:
                return []
            res = self.call_stdio_jsonrpc(cmd, args, req)

        return res.get("result", {}).get("tools", [])

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke tools/call on an active MCP server."""
        servers = self.get_servers()
        if server_name not in servers:
            return {"error": f"Server '{server_name}' not configured in mcp_servers.json."}

        server = servers[server_name]
        req = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        if "url" in server:
            res = self.call_http_jsonrpc(server["url"], req)
        else:
            cmd = server.get("command")
            args = server.get("args", [])
            res = self.call_stdio_jsonrpc(cmd, args, req)

        if "error" in res:
            return {"error": res["error"].get("message", "Unknown error")}
        return res.get("result", {})


_GLOBAL_MCP = MCPClient()


# ---------------------------------------------------------------------------
# Registered MCP Skill Functions
# ---------------------------------------------------------------------------

def mcp_list_servers(memory) -> str:
    """List all configured Model Context Protocol (MCP) servers."""
    servers = _GLOBAL_MCP.get_servers()
    if not servers:
        return "No MCP servers configured yet in mcp_servers.json, Sir. Use mcp_add_server to register one."
    lines = [f"Configured MCP Servers ({len(servers)} total):"]
    for name, cfg in servers.items():
        if "url" in cfg:
            lines.append(f"  - **{name}** (HTTP): {cfg['url']}")
        else:
            cmd = cfg.get("command", "")
            args = " ".join(cfg.get("args", []))
            lines.append(f"  - **{name}** (stdio): {cmd} {args}")
    return "\n".join(lines)


def mcp_list_tools(memory, server_name: str = "") -> str:
    """Discover tools exposed by a specific MCP server or across all servers."""
    servers = _GLOBAL_MCP.get_servers()
    if not servers:
        return "No MCP servers configured."

    target_servers = [server_name] if server_name and server_name in servers else list(servers.keys())
    lines = []

    for s_name in target_servers:
        tools = _GLOBAL_MCP.list_tools(s_name)
        lines.append(f"Server: {s_name} ({len(tools)} tools discovered):")
        if not tools:
            lines.append("  (no tools or server currently offline)")
        for t in tools:
            lines.append(f"  - `{t.get('name')}`: {t.get('description', 'No description')[:80]}")

    return "\n".join(lines)


def mcp_call_tool(memory, server_name: str, tool_name: str, arguments: dict = None, confirm: bool = False) -> str:
    """Invoke an external tool on an MCP server with confirmation safety checks."""
    t_lower = tool_name.lower()
    if not confirm and any(d in t_lower for d in ("delete", "remove", "drop", "destroy", "kill", "wipe", "exec")):
        return f"SAFETY GATE: MCP tool '{tool_name}' on server '{server_name}' appears destructive. Confirm to execute."

    res = _GLOBAL_MCP.call_tool(server_name, tool_name, arguments or {})
    if "error" in res:
        return f"MCP tool execution failed: {res['error']}"

    content = res.get("content", [])
    if isinstance(content, list):
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and "text" in c]
        if texts:
            return "\n".join(texts)
    return json.dumps(res, indent=2)


def mcp_add_server(memory, name: str, command: str = "", args: list = None, url: str = "") -> str:
    """Add a new MCP server configuration to mcp_servers.json."""
    if not name or not name.strip():
        return "Please provide a valid server name."
    if not command and not url:
        return "Please specify either a command for stdio or a url for HTTP."

    cfg = _load_mcp_config()
    if "mcpServers" not in cfg:
        cfg["mcpServers"] = {}

    entry: Dict[str, Any] = {}
    if url:
        entry["url"] = url.strip()
    else:
        entry["command"] = command.strip()
        entry["args"] = args or []

    cfg["mcpServers"][name.strip()] = entry
    _save_mcp_config(cfg)
    return f"Successfully registered MCP server '{name}' in mcp_servers.json, Sir."


MCP_SKILLS = [
    {"name": "mcp_list_servers", "fn": mcp_list_servers, "description": "List all configured Model Context Protocol (MCP) servers.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "mcp_list_tools", "fn": mcp_list_tools, "description": "List tools available on external MCP servers.",
     "parameters": {"type": "object", "properties": {"server_name": {"type": "string", "description": "Optional specific server name"}}, "required": []}},
    {"name": "mcp_call_tool", "fn": mcp_call_tool, "description": "Execute a tool provided by an external MCP server.",
     "parameters": {"type": "object", "properties": {"server_name": {"type": "string", "description": "MCP server name"}, "tool_name": {"type": "string", "description": "Tool identifier"}, "arguments": {"type": "object", "description": "JSON arguments object"}, "confirm": {"type": "boolean", "description": "Confirm flag for destructive tools"}}, "required": ["server_name", "tool_name"]}},
    {"name": "mcp_add_server", "fn": mcp_add_server, "description": "Register a new MCP server in mcp_servers.json (stdio or HTTP).",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Unique identifier for server"}, "command": {"type": "string", "description": "Executable command for stdio server"}, "args": {"type": "array", "items": {"type": "string"}, "description": "Command line arguments"}, "url": {"type": "string", "description": "HTTP endpoint URL"}}, "required": ["name"]}},
]

__all__ = [
    "MCPClient",
    "MCP_SKILLS",
    "mcp_list_servers",
    "mcp_list_tools",
    "mcp_call_tool",
    "mcp_add_server",
]

# Rusty // Autonomous AI Operating System

A JARVIS-class personal AI assistant and desktop operating system for Windows — engineered for low-latency voice interaction, local whisper transcription, tactical holographic HUD telemetry, system automation, and cross-platform remote phone control.

---

## Architecture Overview

Rusty is built on an asynchronous, modular architecture separating the neural reasoning engine from machine automation and secure interfaces:

```
JARVIS/
├── main.py                     # Interactive terminal REPL
├── config.json                 # Core system configuration
├── requirements.txt            # Dependency specification
├── antigravity_ui_map.json     # UI locators and shortcuts for Antigravity control
├── SECURITY.md                 # Security policy, threat model, and safety gates
├── tests/                      # Automated test suite (96 unit tests, 100% passing)
│   ├── test_config.py          # Config merging and validation
│   ├── test_security.py        # Sandbox & credential protection gates
│   ├── test_memory.py          # Persistent memory and journal tests
│   ├── test_database.py        # SQLite, FTS5 full-text & vector tests
│   ├── test_semantic_memory.py # Vector recall & dynamic context tests
│   ├── test_skills_registry.py # 146-skill schema and integrity tests
│   ├── test_skills_browser.py  # Web intelligence, search, weather & stocks
│   ├── test_skills_power_tools.py # Developer tools, diagnostics, and Protocol Zero
│   ├── test_skills_antigravity.py # Antigravity IDE controller & agent safety tests
│   ├── test_skills_claude_desktop.py # MCP client, custom skills, computer use, subagents, research
│   ├── test_skills_system.py   # System automation and file tests
│   └── test_voice_patience.py  # Speech brevity and adaptive listening silence tests
├── vyra/
│   ├── brain.py                # ReAct think-act loop & multi-hop tool execution
│   ├── config.py               # Layered configuration & environment parser
│   ├── database.py             # SQLite WAL engine with FTS5 & vector storage
│   ├── embeddings.py           # 384-dim dense vectors, cosine & neural hashing
│   ├── gui_server.py           # Aiohttp HUD server & WebSocket bridge
│   ├── llm.py                  # Multi-provider client (Claude / Gemini / OpenRouter)
│   ├── memory.py               # Hybrid SQLite + vector + FTS5 persistent memory
│   ├── office_skills.py        # Comprehensive Office, PDF, PPTX & project generation
│   ├── remote_telegram.py      # Encrypted Telegram bot gateway (voice + commands)
│   ├── voice.py                # Local Faster-Whisper ASR + Neural Edge-TTS engine with conciseness filter
│   ├── wake.py                 # Continuous passive wake word detection
│   └── skills/                 # Modular 146-Skill Dispatcher
│       ├── common.py           # Path resolution, security validation, Win32 desktop API
│       ├── system.py           # Terminal, window management, volume, hotkeys, input
│       ├── files.py            # File I/O, search, listing, and safe recycling
│       ├── browser.py          # Browser automation, tab control, web research, links
│       ├── media.py            # Raaga music app, audio controls, screen vision, screenshots
│       ├── comms.py            # Telegram file transfer, WhatsApp, Drive backup, GitHub CLI
│       ├── assistant.py        # Memory facts, notes, reminders, routines, deep thinking
│       ├── antigravity_app.py  # Antigravity IDE automation, transcript telemetry & safety
│       ├── skills_manager.py   # Custom skill folder loader & manager (SKILL.md format)
│       ├── mcp_client.py       # Model Context Protocol client (stdio/http) & tool dispatcher
│       ├── computer_use.py     # AppProfile computer use abstraction (browser, terminal, app)
│       ├── research.py         # Multi-step deep research mode, citations & report generation
│       ├── self_awareness.py   # Tool capability matrix, audit explanation & safe undo
│       ├── subagents.py        # Asynchronous background worker sub-agent framework
│       ├── projects.py         # Per-project instructions and context management
│       └── scheduler.py        # Scheduled recurring routines and background tasks
└── .github/workflows/
    └── ci.yml                  # Automated continuous integration workflow
```

---

## Core Capabilities (146 Registered Skills)

1. **Antigravity IDE & Multi-Agent Control (28 Skills)**:
   - **Lifecycle & Windows**: Launch IDE workspaces, detect running processes, restore/focus window, screenshot audit, and clean shutdowns (`ag_launch`, `ag_status`, `ag_focus`, `ag_screenshot`).
   - **Zero-Lag Telemetry**: Direct stream reading from `transcript.jsonl` and `conversations/*.db` for 100% faithful extraction of agent thought steps, tool execution requests, and plans without visual OCR errors (`ag_read_agent_output`, `ag_wait_for_agent`).
   - **Agent Directives & Context**: Injects structured prompts directly into the active chat session via CLI chat subcommands, attaching contextual files (`ag_send_prompt`).
   - **Code-Enforced Approval Gates**: Sensitive approval actions (`ag_approve`) require explicit code-level confirmation; untrusted data cannot satisfy confirmation gates. Dedicated kill switch (`ag_stop_agent`) immediately aborts external agent automation.
   - **Workspace Navigation & Terminals**: Opens folders, navigates to precise `file:line` locations, searches workspace text, triggers command palette actions, and manages the integrated terminal panel (`ag_open_file`, `ag_search_workspace`, `ag_command_palette`, `ag_open_terminal`).
   - **Compound Supervised Workflows**: High-level developer routines: `ag_build_feature` (spec-to-plan), `ag_fix_failing_tests` (auto-diagnose), and `ag_review_changes` (code review).
   - **Locator Self-Test**: Automated validation of CLI launchers, UI locators, process health, and telemetry paths (`ag_selftest`).
2. **Hybrid Semantic Memory Engine (SQLite + Vector Embeddings)**:

   - Embedded SQLite storage running in Write-Ahead Logging (`WAL`) mode with foreign keys.
   - Dense 384-dimensional vector embeddings with cosine similarity matching.
   - Dual-tier vector generator: connects to cloud embedding models with an offline-capable deterministic subword n-gram neural hash fallback.
   - SQLite FTS5 lexical search engine with Porter stemming.
   - Seamless, zero-downtime automated migration from legacy JSON memory files on startup.
   - Dynamic memory retrieval automatically injecting relevant facts and notes into prompt context.
2. **Three Operational Modes (`switch_mode`)**:
   - **Tactical (Default)**: Efficient, respectful JARVIS/FRIDAY tone.
   - **Engineer**: Dense, technical, code-first answers with zero conversational pleasantries.
   - **Ghost**: Silent, stealth execution with minimal spoken feedback.
3. **Live Internet & Online Intelligence Superpowers**:
   - `real_web_search`: Direct live search retrieving answers, snippets, and citations into memory context without opening a browser window.
   - `check_weather`: Real-time weather, temperature, humidity, wind, and forecasts via Open-Meteo.
   - `check_stock_crypto`: Live quotes, currency conversions (USD/INR), and 24h percentage changes for stocks and cryptocurrencies via Yahoo Finance and CoinGecko.
   - `news_briefing`: Fetches top technology, world, or business headlines from HackerNews and BBC RSS feeds.
   - `summarize_webpage`: Extracts readable article text from any URL and generates structured executive summaries.
4. **Developer Power Tools, Diagnostics & Emergency Security**:
   - `kill_port`: Instantly frees port 3000, 8000, etc. by identifying and terminating rogue background dev servers.
   - `network_diagnostics`: High-speed network connection check (ping latency to Cloudflare 1.1.1.1, local IP, and public gateway IP).
   - `emergency_lockdown` (**Protocol Zero**): Instantly locks workstation, mutes master audio, minimizes desktop windows, logs the security event, and alerts your phone via Telegram.
   - `read_file_tree`: Generates clean ASCII project folder trees while automatically ignoring build artifacts, git internals, and virtual environments.
   - `summarize_document`: Reads and extracts an executive summary from any PDF, Word, presentation, or code file.
   - `git_repo_status`: Inspects active branch, ahead/behind commit counts, dirty files, and recent commit history.
   - `audit_action_history`: Queries recent tool executions with duration in milliseconds directly from SQLite.
5. **Voice & Hearing Pipeline (Listening Patience & Speech Brevity)**:
   - **Adaptive Listening Patience**: Increased silence detection threshold to 1.8s (with dynamic expansion up to 2.2s during early speech fragments) so users are never cut off prematurely while pausing to think.
   - **Spoken Conciseness Engine (`extract_spoken_summary`)**: Decouples audio speech from screen output. If a response contains 10 lines of lists, tables, markdown files, or code blocks, the complete response is displayed visually in chat/HUD/Telegram, while the voice speaker only reads a crisp 1–2 sentence direct answer/takeaway.
   - Local transcription with **Faster-Whisper** (`small` model on NVIDIA CUDA with CPU fallback).
   - High-fidelity neural voice synthesis via Microsoft Edge-TTS with multi-lingual auto-switching (English + Hindi `hi-IN-MadhurNeural`).
   - Non-blocking continuous wake-word monitoring (`"Rusty"`, `"Friday"`, `"Jarvis"`).
6. **Claude-Desktop-Class Capabilities Framework**:
   - **Custom Skill Folders**: Modular `skills_custom/<name>/SKILL.md` bundles with YAML frontmatter, execution instructions, risk levels, and trigger conditions (`list_custom_skills`, `create_custom_skill`, `read_custom_skill`, `delete_custom_skill`).
   - **Model Context Protocol (MCP) Client**: Full JSON-RPC 2.0 stdio and HTTP client connecting to arbitrary MCP tool servers configured in `mcp_servers.json`, with safety confirmation gates (`mcp_list_servers`, `mcp_list_tools`, `mcp_call_tool`, `mcp_add_server`).
   - **Universal Computer Use (`AppProfile`)**: OS-level app control abstraction supporting browser, terminal, and custom desktop applications (`cu_focus_app`, `cu_screenshot_app`, `cu_click_app`, `cu_type_in_app`, `cu_press_key_in_app`, `cu_scroll_app`, `cu_inspect_app`).
   - **Deep Research Mode**: Multi-step web research protocol deconstructing questions into multiple queries, extracting body text from primary sources, compiling verified citations, and assembling structured reports saved to `.md` or `.docx` (`research_topic`).
   - **Self-Awareness & Introspection**: Full capability matrix breakdown by domain (`list_my_tools`), post-action explanation with secret redaction (`explain_last_action`), and safe recovery/undo using Recycle Bin inspection (`undo_last_action`).
   - **Asynchronous Sub-Agents**: Background worker framework capable of running long-running research or audit jobs with real-time progress event streaming and cancellation tokens (`spawn_subagent`, `check_subagent`, `cancel_subagent`, `list_subagents`).
   - **Per-Project Context Isolation**: Save and manage project-specific architecture rules, coding standards, and key files (`set_project_context`, `get_project_context`, `list_project_contexts`, `delete_project_context`).
   - **Scheduled Routines**: Cron-style persistent task scheduling for automated daily briefs and background maintenance (`schedule_routine`, `list_scheduled_routines`, `cancel_scheduled_routine`).
7. **Tactical Holographic HUD (Stark Industries Interface)**:
   - High-FPS canvas-based Arc Reactor core, real-time audio spectrum, and live hardware telemetry (CPU, RAM, GPU, battery, ping).
   - Borderless desktop PiP application or browser view with real-time spoken and visual task progress updates.
8. **Hardware & Desktop Automation**:
   - Win32 window enumeration, smart tab closing (`Ctrl+W`), process management, master volume control, screen brightness, and lock/sleep triggers.
9. **Autonomous Office & Document Generation**:
   - Generates fully populated, styled Word documents (`.docx`), presentation decks (`.pptx`), Excel sheets (`.xlsx`), and clean formatted PDFs (`reportlab`) with live progress reporting.
10. **Secure Remote Gateway (Phone Control)**:
   - Control your PC from anywhere in the world via Telegram with constant-time HMAC authentication, rate-limiting, and 15-minute brute-force lockout.
   - Send files from PC to phone with a single voice directive.

---

## Security Model & Hardening

Rusty enforces strict security boundaries designed for autonomous systems:
- **Sandbox Validation (`is_path_safe`)**: Blocks access, deletion, or exfiltration of system credentials, `.env`, `.ssh`, AWS keys, GPG keys, and browser session cookies.
- **Terminal Execution Gates**: Catastrophic disk and system commands (`bcdedit`, `bootrec`, `vssadmin`, `iex`, encoded payloads) are blocked at the regex parsing layer. Destructive operations (`rmdir`, `del`, `taskkill /f`, `git reset --hard`) require explicit `confirm=True` validation.
- **Localhost Default**: HUD server binds strictly to `127.0.0.1` by default.
- **HMAC Constant-Time PIN Verification**: Protects against timing attacks on remote endpoints.

---

## Quickstart

### 1. Requirements & Setup
Ensure Python 3.10+ (Python 3.12 recommended) is installed:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy configuration templates and specify your LLM key:

```bash
copy config.example.json config.json
copy .env.example .env
```

Edit `.env`:
```env
VYRA_API_KEY=your_gemini_or_claude_api_key
```

### 3. Launch Rusty

- **Tactical Desktop HUD**:
  ```bash
  .\launch_rusty.bat
  # or: python -m vyra.gui_server
  ```
- **Text Command REPL**:
  ```bash
  python main.py
  ```

---

## Automated Test Suite

Rusty includes a comprehensive 96-test unit testing suite verifying configuration parsing, security boundaries, memory persistence, schema validity, online intelligence, Claude-Desktop capabilities, and tool dispatch:

```bash
python -m unittest discover tests -v
```

All pull requests and pushes are automatically validated via GitHub Actions CI (`.github/workflows/ci.yml`).

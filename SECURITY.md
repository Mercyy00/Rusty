# Security Policy & Threat Model — Rusty // Autonomous AI Operating System

Rusty is an autonomous, tool-calling desktop AI operating system designed for Windows. Because Rusty possesses deep system capabilities (terminal execution, file modification, browser navigation, phone integration, and the ability to supervise other AI agents), rigorous security controls and defensive barriers are enforced directly in code.

---

## 1. Threat Model & Architectural Principles

### 1.1 The Untrusted Data Boundary (Prompt Injection Defense)
Any text originating from outside the verified user prompt is treated as **untrusted data**. This includes:
- Live web search snippets and fetched web page text (`real_web_search`, `summarize_webpage`).
- Content read from local files, documents, and spreadsheets (`read_file`, `summarize_document`).
- Clipboard text (`read_clipboard`).
- OCR or transcript output read from other AI agents (e.g., `ag_read_agent_output`).
- Inbound remote chat messages prior to cryptographic authentication.

**Rule**: Untrusted data can **never** trigger a tool execution, satisfy a confirmation gate, or override a safety boundary.

### 1.2 Multi-Agent Control Security (Antigravity Automation)
When Rusty controls another agent (such as Antigravity):
- **Approvals are never automated**: `ag_approve` is classified as `sensitive`. It requires an explicit user confirmation step enforced in Python code.
- **Visual & Transcript Verification**: Every action must be verified against the live transcript stream or window state before reporting completion.
- **Emergency Kill Switch**: A dedicated kill switch (`ag_stop_agent`) immediately aborts external agent automation and clears focused input.

---

## 2. Security Barriers & Code Gates

### 2.1 File System Sandbox (`is_path_safe`)
All file reads, writes, searches, and recycling operations are filtered through `is_path_safe()`. This prevents path traversal (`..`), symlink redirection, and unauthorized access to:
- Operating system internals (`Windows\System32`, `System32\config\SAM`, drivers, boot configurations).
- User credentials (`.ssh`, `.aws`, `.env`, `.gitconfig`, gcloud tokens).
- Browser profiles and session cookie databases.
- Deletions default to the Windows Recycle Bin (`Microsoft.VisualBasic.FileIO.FileSystem`) rather than permanent removal.

### 2.2 Terminal Execution Gates
- **Hard Deny-List**: Regex parser strictly blocks catastrophic commands (`bcdedit`, `bootrec`, `vssadmin`, `format`, `Invoke-Expression / iex`, encoded Base64 command strings).
- **Code-Level Confirmation Gate**: Destructive or modifying operations (`rmdir`, `del`, `taskkill /f`, `git reset --hard`) require explicit `confirm=True` passed directly to the function.

### 2.3 Remote Interfaces (Telegram Bridge & HUD Server)
- **Localhost Binding**: The local telemetry HUD server binds strictly to `127.0.0.1` by default. Remote phone access is recommended via secure VPN mesh tunnels (Tailscale or WireGuard).
- **Constant-Time Verification**: All remote authentication PINs are compared using `hmac.compare_digest` to prevent side-channel timing attacks.
- **Brute-Force Lockout**: Three consecutive incorrect PIN attempts enforce a mandatory 15-minute lockout period.

---

## 3. Vulnerability Reporting

If you identify a security issue, vulnerability, or bypass in Rusty:
1. Do **not** open a public issue on GitHub.
2. Email details and reproduction steps to the repository owner or submit an encrypted advisory via GitHub Private Vulnerability Reporting.

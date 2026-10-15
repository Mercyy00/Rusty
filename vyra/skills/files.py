"""File system, file search, reading/writing, and recycle bin skills for Rusty."""

from __future__ import annotations

import os
import shutil
import subprocess

from .common import (
    FOLDER_SHORTCUTS,
    _resolve_path,
    is_path_safe,
)


def open_folder(memory, path: str) -> str:
    resolved = os.path.expandvars(FOLDER_SHORTCUTS.get(path.lower().strip(), path))
    if not os.path.exists(resolved):
        return f"That folder doesn't exist: {resolved}"
    subprocess.Popen(["explorer", resolved])
    return f"Opening folder {resolved}."


def open_file(memory, path: str) -> str:
    """Open a file on Jay's computer with its default application or browser.
    Accepts full paths, relative paths, or names of files created under Desktop/Rusty."""
    if not path or not path.strip():
        return "Please specify which file you would like me to open, Sir."
    raw = path.strip().strip('"').strip("'")
    full = _resolve_path(raw)

    # If not found directly, search Desktop/Rusty subdirectories (documents, presentations, sheets, projects)
    if not os.path.exists(full):
        rusty_base = os.path.join(os.path.expandvars(r"%USERPROFILE%\Desktop"), "Rusty")
        if os.path.exists(rusty_base):
            target_name = os.path.basename(raw).lower()
            for root, _, files in os.walk(rusty_base):
                for f in files:
                    if f.lower() == target_name or f.lower().startswith(target_name):
                        full = os.path.join(root, f)
                        break
                if os.path.exists(full):
                    break

    if not os.path.exists(full):
        return f"I couldn't locate '{path}' on your system, Sir."

    if not is_path_safe(full):
        return f"Access denied: '{os.path.basename(full)}' is protected for security, Sir."

    from ..office_skills import _open
    opened = _open(full)
    if opened:
        return f"Opened '{os.path.basename(full)}' for you, Sir."
    return f"Located '{os.path.basename(full)}', but could not launch a viewer on Windows."


def read_file(memory, path: str, max_chars: int = 4000) -> str:
    """Read a text, PDF, Word, or presentation file so Rusty can inspect and discuss it."""
    full = _resolve_path(path)

    # If not found directly, check Desktop/Rusty
    if not os.path.exists(full):
        rusty_base = os.path.join(os.path.expandvars(r"%USERPROFILE%\Desktop"), "Rusty")
        if os.path.exists(rusty_base):
            target_name = os.path.basename(path).lower()
            for root, _, files in os.walk(rusty_base):
                for f in files:
                    if f.lower() == target_name or f.lower().startswith(target_name):
                        full = os.path.join(root, f)
                        break
                if os.path.exists(full):
                    break

    if not is_path_safe(full):
        return f"Access denied: '{os.path.basename(full)}' is protected for system security, Sir."
    if not os.path.exists(full):
        return f"There's no file at {full}."
    if os.path.isdir(full):
        return f"'{full}' is a folder — use list_folder for that."

    low = full.lower()
    # 1. PDF handling via pypdf
    if low.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(full)
            text_parts = []
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                if txt.strip():
                    text_parts.append(f"--- Page {idx + 1} ---\n{txt.strip()}")
                if sum(len(p) for p in text_parts) > max_chars:
                    break
            data = "\n\n".join(text_parts)
            if not data:
                return f"Contents of {os.path.basename(full)}: (empty or scanned image PDF without extractable text)"
        except Exception as exc:
            return f"Error reading PDF '{os.path.basename(full)}': {exc}"
    # 2. Word handling (.docx)
    elif low.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(full)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            data = "\n".join(paras)
        except Exception as exc:
            return f"Error reading Word document '{os.path.basename(full)}': {exc}"
    # 3. PowerPoint handling (.pptx)
    elif low.endswith(".pptx"):
        try:
            import pptx
            prs = pptx.Presentation(full)
            slide_texts = []
            for idx, slide in enumerate(prs.slides, 1):
                bullets = []
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for p in shape.text_frame.paragraphs:
                            if p.text.strip():
                                bullets.append(p.text.strip())
                if bullets:
                    slide_texts.append(f"Slide {idx}:\n" + "\n".join(f"  • {b}" for b in bullets))
            data = "\n\n".join(slide_texts)
        except Exception as exc:
            return f"Error reading PowerPoint presentation '{os.path.basename(full)}': {exc}"
    # 4. Standard text/code file
    else:
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                data = fh.read(max_chars + 1)
        except Exception as exc:
            return f"Couldn't read it: {exc}"

    truncated = len(data) > max_chars
    return f"Contents of {os.path.basename(full)}:\n{data[:max_chars]}" + ("\n...(truncated)" if truncated else "")


def write_file(memory, path: str, content: str) -> str:
    """Create or write content to a text or code file."""
    try:
        full_path = _resolve_path(path)
        if not is_path_safe(full_path):
            return f"Access denied: '{os.path.basename(full_path)}' is in a protected path, Sir."
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Saved file to '{full_path}' ({len(content)} characters)."
    except Exception as exc:
        return f"Failed to write file: {exc}"


def search_files(memory, query: str, folder: str = "", progress_callback=None) -> str:
    """Search for files and directories matching query name."""
    if progress_callback:
        progress_callback(f"Scanning storage directories for '{query}', Sir...", speak=False)
    try:
        target_folder = folder if folder else os.path.expanduser("~")
        root_dir = _resolve_path(target_folder)
        if not os.path.exists(root_dir):
            root_dir = os.path.expanduser("~")
        matches = []
        q_lower = query.lower()
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.venv')]
            for f in files:
                if q_lower in f.lower():
                    matches.append(os.path.join(root, f))
                    if len(matches) >= 15:
                        break
            if len(matches) >= 15:
                break
        if not matches:
            return f"No files found matching '{query}' in {root_dir}."
        res = [f"Found {len(matches)} match(es) for '{query}':"]
        for m in matches:
            res.append(f"  - {m}")
        return "\n".join(res)
    except Exception as exc:
        return f"Error searching files: {exc}"


def delete_file(memory, path: str, permanent: bool = False, confirm: bool = False) -> str:
    """Delete a file. By default moves to Windows Recycle Bin for safety."""
    full_path = _resolve_path(path)
    if not is_path_safe(full_path):
        return f"Access denied: '{os.path.basename(full_path)}' is in a protected system path, Sir."
    if not os.path.exists(full_path):
        return f"File does not exist: {full_path}"
    if os.path.isdir(full_path):
        return f"'{full_path}' is a folder, not a file. Use delete_folder instead."
    
    if permanent:
        if not confirm:
            return f"Safety Hold: Permanent file deletion cannot be undone, Sir. Confirm to permanently delete '{os.path.basename(full_path)}'."
        try:
            os.remove(full_path)
            return f"Permanently deleted '{os.path.basename(full_path)}', Sir."
        except Exception as exc:
            return f"Error deleting file: {exc}"
    else:
        ps_cmd = "param([string]$target) Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($target, 'OnlyErrorDialogs', 'SendToRecycleBin')"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd, "-target", full_path], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Moved '{os.path.basename(full_path)}' to the Windows Recycle Bin."
        return f"Failed to recycle file: {res.stderr.strip()}"


def delete_folder(memory, path: str, permanent: bool = False, confirm: bool = False) -> str:
    """Delete a directory. By default moves to Windows Recycle Bin for safety."""
    full_path = _resolve_path(path)
    if not is_path_safe(full_path):
        return f"Access denied: '{os.path.basename(full_path)}' is in a protected system path, Sir."
    if not os.path.exists(full_path):
        return f"Folder does not exist: {full_path}"
    if not os.path.isdir(full_path):
        return f"'{full_path}' is a file, not a folder. Use delete_file instead."

    if permanent:
        if not confirm:
            return f"Safety Hold: Permanently deleting folder '{os.path.basename(full_path)}' will destroy all its contents, Sir. Please confirm."
        try:
            shutil.rmtree(full_path)
            return f"Permanently deleted folder '{os.path.basename(full_path)}', Sir."
        except Exception as exc:
            return f"Error deleting folder: {exc}"
    else:
        ps_cmd = "param([string]$target) Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($target, 'OnlyErrorDialogs', 'SendToRecycleBin')"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd, "-target", full_path], capture_output=True, text=True)
        if res.returncode == 0:
            return f"Moved folder '{os.path.basename(full_path)}' to the Windows Recycle Bin."
        return f"Failed to recycle folder: {res.stderr.strip()}"


def list_folder(memory, path: str = "downloads") -> str:
    """List files and folders in a directory."""
    full_path = _resolve_path(path)
    if not is_path_safe(full_path):
        return f"Access denied: '{os.path.basename(full_path)}' is in a protected path, Sir."
    if not os.path.exists(full_path):
        return f"Folder does not exist: {full_path}"
    if not os.path.isdir(full_path):
        return f"'{full_path}' is not a directory."
        
    try:
        entries = sorted(os.listdir(full_path))
        if not entries:
            return f"Folder '{os.path.basename(full_path)}' is empty."
        lines = [f"Contents of {os.path.basename(full_path)} ({len(entries)} items):"]
        for item in entries[:20]:
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                lines.append(f"  [DIR]  {item}")
            else:
                size_mb = os.path.getsize(item_path) / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb >= 1.0 else f"{round(size_mb * 1024)} KB"
                lines.append(f"  [FILE] {item} ({size_str})")
        if len(entries) > 20:
            lines.append(f"  ... and {len(entries) - 20} more items.")
        return "\n".join(lines)
    except Exception as exc:
        return f"Could not list folder: {exc}"


def empty_recycle_bin(memory) -> str:
    """Empty the Windows Recycle Bin."""
    res = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
        capture_output=True, text=True
    )
    if res.returncode == 0:
        return "Emptied the Windows Recycle Bin."
    return f"Could not empty Recycle Bin: {res.stderr.strip()}"


IGNORED_TREE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".pytest_cache", ".idea", ".vscode", "dist", "build", ".egg-info"
}


def read_file_tree(memory, folder: str = "", max_depth: int = 3) -> str:
    """Generate a clean ASCII directory tree map of a project folder."""
    from .common import ROOT
    target_dir = _resolve_path(folder) if folder else ROOT
    if not os.path.exists(target_dir):
        return f"Folder not found: {target_dir}, Sir."
    if not os.path.isdir(target_dir):
        return f"'{target_dir}' is a file, not a directory."

    lines = [f"Directory tree of {os.path.basename(target_dir) or target_dir}:"]

    def _walk(current: str, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(current))
        except Exception:
            return

        entries = [e for e in entries if e not in IGNORED_TREE_DIRS and not e.startswith(".")]
        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            full_path = os.path.join(current, entry)
            is_dir = os.path.isdir(full_path)
            lines.append(f"{prefix}{connector}{entry}{'/' if is_dir else ''}")
            if is_dir:
                next_prefix = prefix + ("    " if is_last else "│   ")
                _walk(full_path, next_prefix, depth + 1)

    _walk(target_dir, "", 1)
    if len(lines) > 60:
        lines = lines[:60] + ["  ... (truncated for brevity)"]
    return "\n".join(lines)


def summarize_document(memory, path: str) -> str:
    """Read a document (PDF, Word, presentation, text, or code) and generate an executive summary."""
    content = read_file(memory, path, max_chars=5000)
    if not content or content.startswith(("Error", "Access denied", "There's no file")):
        return content

    fn = os.path.basename(path)
    from .media import _VISION_CONFIG
    cfg = _VISION_CONFIG
    if not cfg:
        try:
            from ..config import load_config
            cfg = load_config().get("llm")
        except Exception:
            cfg = None

    if cfg and cfg.get("api_key"):
        try:
            from ..llm import make_client
            client = make_client({"llm": cfg})
            prompt = (
                f"Document: {fn}\n\nContent:\n{content[:4000]}\n\n"
                "Provide a clear, 3-5 bullet point executive summary highlighting key takeaways, findings, and action items."
            )
            resp = client.complete("You are an expert technical advisor. Summarize clearly and objectively.", [{"role": "user", "content": prompt}], [])
            if resp.text:
                return f"Executive Summary of {fn}:\n\n" + resp.text.strip()
        except Exception:
            pass

    preview = content[:600] + ("..." if len(content) > 600 else "")
    return f"Key extract from {fn}:\n\n{preview}"


FILE_SKILLS = [
    {"name": "write_file", "fn": write_file, "description": "Create or write content to a text or code file on Jay's computer.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path (relative or absolute)"}, "content": {"type": "string", "description": "Text or code content to write"}}, "required": ["path", "content"]}},
    {"name": "search_files", "fn": search_files, "description": "Search for files and folders by name across Jay's workspace or specified directory.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Filename substring or extension to find"}, "folder": {"type": "string", "description": "Root directory to search (optional)"}}, "required": ["query"]}},
    {"name": "open_folder", "fn": open_folder, "description": "Open a folder in File Explorer. Accepts a full path or a shortcut: downloads, documents, desktop, pictures, home.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "read_file", "fn": read_file, "description": "Read a text, code, PDF, Word (.docx), or PowerPoint (.pptx) file so you can inspect and discuss or review it (e.g. desktop/Rusty/documents/python_tips.pdf or downloads/notes.txt).",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path, filename, or shortcut"}}, "required": ["path"]}},
    {"name": "open_file", "fn": open_file, "description": "Open a document, PDF, presentation, spreadsheet, code, or file with its default viewer or browser on Windows. Searches Desktop\\Rusty automatically if only given a filename.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path or name of the file to open (e.g. 'python_tips.pdf', 'World_Dog_Proposal.docx')"}}, "required": ["path"]}},
    {"name": "delete_file", "fn": delete_file, "description": "Delete a file. By default, safely moves it to the Windows Recycle Bin so it can be restored.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "File path or shortcut (e.g. downloads/test.txt)"}, "permanent": {"type": "boolean", "description": "If true, permanently delete instead of moving to Recycle Bin (default false)"}, "confirm": {"type": "boolean", "description": "Explicit confirmation required if permanent is true"}}, "required": ["path"]}},
    {"name": "delete_folder", "fn": delete_folder, "description": "Delete a folder. By default, safely moves it to the Windows Recycle Bin.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Folder path or shortcut (e.g. downloads/old_dir)"}, "permanent": {"type": "boolean", "description": "If true, permanently delete instead of moving to Recycle Bin (default false)"}, "confirm": {"type": "boolean", "description": "Explicit confirmation required if permanent is true"}}, "required": ["path"]}},
    {"name": "list_folder", "fn": list_folder, "description": "List files and subfolders in a directory (e.g. downloads, desktop, documents).",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Folder path or shortcut (default: downloads)"}}, "required": []}},
    {"name": "empty_recycle_bin", "fn": empty_recycle_bin, "description": "Empty the Windows Recycle Bin.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "read_file_tree", "fn": read_file_tree, "description": "Generate an ASCII directory tree diagram of any project folder or current workspace, ignoring virtualenvs and build files.",
     "parameters": {"type": "object", "properties": {"folder": {"type": "string", "description": "Folder path to inspect (defaults to current project root)"}, "max_depth": {"type": "integer", "description": "Maximum folder depth (default 3)"}}, "required": []}},
    {"name": "summarize_document", "fn": summarize_document, "description": "Read and produce an executive summary with key takeaways from any PDF, Word document, PowerPoint presentation, code file, or text document on the PC.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string", "description": "Path or filename of the document to summarize"}}, "required": ["path"]}},
]

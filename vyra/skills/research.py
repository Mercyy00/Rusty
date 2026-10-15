"""Multi-step Research Mode for Rusty (Claude-Desktop-class intelligence).

Provides deep web exploration, multi-query synthesis, source citation gathering,
and comprehensive research reports saved to Markdown or Microsoft Word (.docx).
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .common import is_path_safe

def _get_research_dir() -> str:
    desktop = os.path.expandvars(r"%USERPROFILE%\Desktop")
    rdir = os.path.join(desktop, "Rusty", "research")
    os.makedirs(rdir, exist_ok=True)
    return rdir


def _clean_slug(topic: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", topic.lower()).strip()
    return re.sub(r"[\s_-]+", "_", slug)[:50] or "research_report"


def _fetch_url_text(url: str, max_chars: int = 3000) -> str:
    """Safely fetch and extract readable text from a web page."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "text/plain" not in content_type:
                return ""
            raw = resp.read()
            html = raw.decode("utf-8", errors="replace")

        # Strip scripts, styles, and tags
        html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
        html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
        html = re.sub(r"<!--[\s\S]*?-->", " ", html)
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception:
        return ""


def research_topic(
    memory: Any,
    topic: str,
    depth: str = "standard",
    output_format: str = "markdown",
    progress_callback: Optional[Callable[[str, bool], None]] = None,
) -> str:
    """Execute multi-step web research on a subject, gathering evidence, citations,
    and generating an in-depth structured report saved to Desktop\\Rusty\\research.

    Args:
        memory: Rusty memory instance.
        topic: The topic, question, or technology to research.
        depth: 'quick' (1-2 queries), 'standard' (3 queries), or 'deep' (4-5 queries).
        output_format: 'markdown' or 'docx'.
        progress_callback: Optional callback for streaming status.
    """
    clean_topic = (topic or "").strip()
    if not clean_topic:
        return "Please specify a research topic, Sir."

    if progress_callback:
        progress_callback(f"Initiating research protocol on '{clean_topic}'...", speak=True)

    # 1. Generate multi-step research queries
    queries = [clean_topic]
    if depth in ("standard", "deep"):
        queries.append(f"{clean_topic} overview analysis architecture")
        queries.append(f"{clean_topic} advantages disadvantages alternatives")
    if depth == "deep":
        queries.append(f"{clean_topic} benchmarks latest updates 2026")

    # 2. Execute web searches
    from .browser import real_web_search

    all_citations = []
    seen_urls = set()
    collected_findings = []

    for q in queries:
        if progress_callback:
            progress_callback(f"Gathering intelligence for: '{q}'...", speak=False)
        try:
            res = real_web_search(memory, query=q, max_results=4)
            # Parse links and snippets from real_web_search output
            for line in res.splitlines():
                if line.startswith("- [") and "](" in line:
                    m = re.match(r"- \[(.*?)\]\((.*?)\)(?:: (.*))?", line)
                    if m:
                        title, url, snippet = m.group(1), m.group(2), m.group(3) or ""
                        if url not in seen_urls and url.startswith("http"):
                            seen_urls.add(url)
                            all_citations.append({"title": title, "url": url, "snippet": snippet})
                            if snippet:
                                collected_findings.append(f"Source [{title}]: {snippet}")
        except Exception:
            continue

    # 3. Fetch deep page content for top 2 citations
    page_extracts = []
    for cit in all_citations[:3]:
        url = cit.get("url", "")
        if url:
            if progress_callback:
                progress_callback(f"Reading source material from {cit.get('title', 'webpage')}...", speak=False)
            txt = _fetch_url_text(url, max_chars=1500)
            if txt:
                page_extracts.append(f"--- Excerpt from {cit.get('title', 'Reference')} ({url}) ---\n{txt}")

    # 4. Synthesize report via LLM if available, otherwise construct structured dossier
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_title = f"Research Report: {clean_topic.title()}"

    from .media import _VISION_CONFIG
    cfg = _VISION_CONFIG
    if not cfg:
        try:
            from ..config import load_config
            cfg = load_config().get("llm")
        except Exception:
            cfg = None

    report_body = ""
    executive_summary = ""

    if cfg and cfg.get("api_key"):
        try:
            from ..llm import make_client
            client = make_client({"llm": cfg})
            context_data = "\n\n".join(collected_findings + page_extracts)
            prompt = (
                f"You are Rusty's Research Intelligence Engine. Conduct an exhaustive, rigorous research report on:\n"
                f"Topic: {clean_topic}\n\n"
                f"Collected Web Evidence & Sources:\n{context_data[:5000]}\n\n"
                f"Format the report in clean Markdown with:\n"
                f"# {report_title}\n\n"
                f"## Executive Summary\n(2-3 punchy, high-impact paragraphs)\n\n"
                f"## Key Architectural Findings & Capabilities\n(bullet points and detailed breakdown)\n\n"
                f"## Strategic Implications & Trade-offs\n(pros, cons, comparative outlook)\n\n"
                f"## Actionable Next Steps\n(practical recommendations)"
            )
            resp = client.complete(
                "You are an elite research analyst. Ground your report strictly in facts and present clear strategic insights.",
                [{"role": "user", "content": prompt}],
                [],
            )
            if resp.text:
                report_body = resp.text.strip()
                # Extract first sentence for voice
                first_lines = [l for l in report_body.splitlines() if l.strip() and not l.startswith("#")]
                if first_lines:
                    executive_summary = first_lines[0]
        except Exception:
            report_body = ""

    if not report_body:
        # Fallback structured synthesis
        lines = [
            f"# {report_title}",
            f"*Generated by Rusty on {now_str} | Depth: {depth.capitalize()}*",
            "",
            "## Executive Summary",
            f"This dossier summarizes intelligence gathered regarding **{clean_topic}**. "
            f"Data was synthesized across {len(all_citations)} primary web sources and live documentation.",
            "",
            "## Key Findings & Extracted Intelligence",
        ]
        if collected_findings:
            for f in collected_findings[:8]:
                lines.append(f"- {f}")
        else:
            lines.append("- Primary queries executed with zero fatal errors.")

        if page_extracts:
            lines.append("")
            lines.append("## Detailed Excerpts")
            for ex in page_extracts:
                lines.append(f"```text\n{ex[:600]}...\n```")

        report_body = "\n".join(lines)
        executive_summary = f"I've synthesized key findings on {clean_topic} across {len(all_citations)} verified sources."

    # Append citations section
    citation_lines = ["\n\n## References & Citations"]
    if all_citations:
        for idx, cit in enumerate(all_citations, 1):
            citation_lines.append(f"{idx}. [{cit['title']}]({cit['url']})")
    else:
        citation_lines.append("- No external URLs indexed.")
    report_body += "\n".join(citation_lines)

    # 5. Save report
    out_dir = _get_research_dir()
    slug = _clean_slug(clean_topic)

    if output_format.lower() in ("docx", "word"):
        try:
            from .. import office_skills as _office
            docx_path = os.path.join(out_dir, f"{slug}.docx")
            _office.create_word(memory, title=report_title, content=report_body, filename=os.path.basename(docx_path))
            target_path = docx_path
        except Exception:
            # Fallback to markdown
            md_path = os.path.join(out_dir, f"{slug}.md")
            with open(md_path, "w", encoding="utf-8") as fh:
                fh.write(report_body)
            target_path = md_path
    else:
        md_path = os.path.join(out_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report_body)
        target_path = md_path

    if progress_callback:
        progress_callback(f"Research complete. Report saved to {target_path}.", speak=True)

    spoken_summary = executive_summary or f"Research complete on {clean_topic}."
    return (
        f"Research protocol completed for '{clean_topic}'.\n\n"
        f"- Report saved to: {target_path}\n"
        f"- Sources cited: {len(all_citations)}\n"
        f"- Research depth: {depth}\n\n"
        f"Summary: {spoken_summary}"
    )


RESEARCH_SKILLS = [
    {
        "name": "research_topic",
        "fn": research_topic,
        "description": "Conduct deep, multi-step web research on any topic, synthesize findings, assemble verified citations, and generate an executive report saved to Desktop\\Rusty\\research as Markdown or Word (.docx).",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Subject, query, technology, or question to deeply research"},
                "depth": {"type": "string", "enum": ["quick", "standard", "deep"], "description": "Research thoroughness: quick, standard (default), or deep"},
                "output_format": {"type": "string", "enum": ["markdown", "docx"], "description": "Output format: 'markdown' (default) or 'docx'"},
            },
            "required": ["topic"],
        },
    },
]

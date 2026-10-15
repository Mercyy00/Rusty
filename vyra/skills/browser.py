"""Browser automation, link management, tab handling, real-time web search, and online intelligence for Rusty."""

from __future__ import annotations

import ctypes
import html
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from .common import (
    KNOWN_BROWSERS,
    _get_user_windows,
    focus_window,
)

_BROWSER = None  # preferred browser (e.g. "brave"); None = system default


def configure_browser(browser):
    global _BROWSER
    _BROWSER = browser or None


def _open_in_browser(url: str):
    if _BROWSER:
        try:
            subprocess.Popen([_BROWSER, url])
            return
        except Exception:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", _BROWSER, url])
                return
            except Exception:
                pass
    webbrowser.open(url)


def _send_ctrl_w():
    """Send Ctrl+W key combination using native Win32 keybd_event."""
    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_W = 0x57
    KEYEVENTF_KEYUP = 0x0002
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_W, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(VK_W, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def close_browser_tab(memory, query: str = "") -> str:
    """Close a specific tab by title/website (or the active tab) in the browser (Ctrl+W)."""
    wins = _get_user_windows()
    browser_wins = [w for w in wins if any(b in w['proc'] for b in KNOWN_BROWSERS)]
    if not browser_wins:
        return "No active browser window found to close tabs from, Sir."

    q_clean = query.lower().strip() if query else ""
    for prefix in ("the ", "a ", "my "):
        if q_clean.startswith(prefix):
            q_clean = q_clean[len(prefix):].strip()
    if q_clean.endswith(" tab") or q_clean.endswith(" page"):
        q_clean = q_clean.rsplit(" ", 1)[0].strip()

    # If the user specifically said "browser", "all tabs", or "window", terminate the browser process
    if q_clean in ("browser", "all", "all tabs", "window", "close browser"):
        target_proc = browser_wins[0]['proc']
        subprocess.run(["taskkill", "/F", "/T", "/IM", target_proc], capture_output=True)
        b_name = target_proc.replace('.exe', '').capitalize()
        return f"Closed {b_name} browser and all open tabs, Sir."

    target_win = None
    if q_clean:
        for w in browser_wins:
            if q_clean in w['title'].lower():
                target_win = w
                break
        if not target_win:
            for w in wins:
                if q_clean in w['title'].lower():
                    target_win = w
                    break

    if not target_win:
        target_win = browser_wins[0]

    # Focus the browser window and send Ctrl+W
    focus_window(target_win['hwnd'])
    time.sleep(0.12)
    _send_ctrl_w()

    b_name = target_win['proc'].replace('.exe', '').capitalize()
    if q_clean and q_clean in target_win['title'].lower():
        return f"Closed the '{target_win['title']}' tab in {b_name}, Sir."
    return f"Closed the active tab in {b_name}, Sir."


def web_search(memory, query: str) -> str:
    """Open a Google search visually in the browser."""
    _open_in_browser(f"https://www.google.com/search?q={quote_plus(query)}")
    return f"Searching Google for '{query}'."


def open_url(memory, url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    _open_in_browser(url)
    return f"Opening {url}."


def open_youtube(memory, query: str = None) -> str:
    if query:
        _open_in_browser(f"https://www.youtube.com/results?search_query={quote_plus(query)}")
        return f"Searching YouTube for '{query}'."
    _open_in_browser("https://www.youtube.com")
    return "Opening YouTube."


def save_link(memory, name: str, url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    memory.save_link(name, url)
    return f"Saved '{name}'. Say \"open {name}\" anytime."


def open_saved_link(memory, name: str) -> str:
    url = memory.get_link(name)
    if not url:
        saved = ", ".join(memory.list_links().keys()) or "nothing yet"
        return f"I don't have a link called '{name}'. Saved: {saved}."
    _open_in_browser(url)
    return f"Opening {name}."


def list_saved_links(memory) -> str:
    links = memory.list_links()
    if not links:
        return "No saved links yet."
    return "Saved links:\n" + "\n".join(f"  - {n}: {u}" for n, u in links.items())


def delete_link(memory, name: str) -> str:
    """Delete a saved shortcut link from memory."""
    ok = memory.delete_link(name)
    return f"Removed the link for '{name}', Sir." if ok else f"I couldn't find a saved link named '{name}', Sir."


# --- Live Internet & Research Superpowers ---

def _clean_ddg_url(raw_url: str) -> str:
    """Extract destination URL from DuckDuckGo redirect link."""
    if not raw_url:
        return ""
    if "uddg=" in raw_url:
        try:
            target = raw_url.split("uddg=")[1].split("&")[0]
            return urllib.parse.unquote(target)
        except Exception:
            pass
    if raw_url.startswith("//"):
        return "https:" + raw_url
    return raw_url


def _query_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Retrieve structured search results from DuckDuckGo Instant Answer and web index."""
    results = []
    clean_q = query.strip()
    if not clean_q:
        return []

    # 1. Instant Answer API
    try:
        api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(api_url, headers={"User-Agent": "RustyAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", clean_q),
                    "snippet": data["AbstractText"],
                    "url": data.get("AbstractURL", "")
                })
    except Exception:
        pass

    # 2. HTML Web Search
    try:
        html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
        h_req = urllib.request.Request(
            html_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(h_req, timeout=6) as r:
            raw_html = r.read().decode("utf-8", errors="ignore")

        snippets = re.findall(r'<a[^>]+class="result__snippet[^>]*>(.*?)</a>', raw_html, re.DOTALL)
        url_matches = re.findall(r'<a[^>]+class="result__url[^>]*href="([^"]+)"[^>]*>(.*?)</a>', raw_html, re.DOTALL)

        for i, snip in enumerate(snippets):
            if len(results) >= max_results:
                break
            clean_snip = html.unescape(re.sub(r"<[^>]+>", "", snip).strip())
            dest_url = _clean_ddg_url(url_matches[i][0]) if i < len(url_matches) else ""
            title_text = html.unescape(re.sub(r"<[^>]+>", "", url_matches[i][1]).strip()) if i < len(url_matches) else clean_q
            if clean_snip and not any(r["snippet"] == clean_snip for r in results):
                results.append({
                    "title": title_text or clean_q,
                    "snippet": clean_snip,
                    "url": dest_url
                })
    except Exception:
        pass

    return results


def real_web_search(memory, query: str, max_results: int = 5) -> str:
    """Direct search engine query without opening a browser window."""
    results = _query_duckduckgo(query, max_results=max_results)
    if not results:
        return f"No search results found for '{query}', Sir."

    lines = [f"Search results for '{query}':"]
    for i, r in enumerate(results, 1):
        url_part = f" ({r['url']})" if r.get('url') else ""
        lines.append(f"{i}. {r['title']}{url_part}\n   {r['snippet']}")
    return "\n\n".join(lines)


WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}


def check_weather(memory, location: str = "") -> str:
    """Fetch live weather, temperature, humidity, and condition for any city (default: current city)."""
    loc_clean = (location or "").strip()
    lat, lon, city_name = None, None, loc_clean

    if not loc_clean:
        try:
            req = urllib.request.Request("http://ip-api.com/json/", headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req, timeout=4) as r:
                ip_data = json.loads(r.read())
                lat = ip_data.get("lat")
                lon = ip_data.get("lon")
                city_name = ip_data.get("city") or "Current location"
        except Exception:
            pass

    if lat is None or lon is None:
        if not loc_clean:
            loc_clean = "London"
            city_name = "London"
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(loc_clean)}&count=1&language=en&format=json"
            req = urllib.request.Request(geo_url, headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                geo_data = json.loads(r.read())
                hits = geo_data.get("results", [])
                if not hits:
                    return f"Could not find coordinates for '{loc_clean}', Sir."
                lat = hits[0]["latitude"]
                lon = hits[0]["longitude"]
                city_name = f"{hits[0].get('name')}, {hits[0].get('country', '')}".strip(", ")
        except Exception as exc:
            return f"Weather lookup failed: {exc}"

    try:
        w_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto"
        )
        req = urllib.request.Request(w_url, headers={"User-Agent": "RustyAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            w = json.loads(r.read())

        cur = w.get("current", {})
        temp = cur.get("temperature_2m")
        feels = cur.get("apparent_temperature")
        humidity = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")
        code = cur.get("weather_code", 0)
        cond = WMO_WEATHER_CODES.get(code, "Clear")

        daily = w.get("daily", {})
        high = daily.get("temperature_2m_max", [None])[0]
        low = daily.get("temperature_2m_min", [None])[0]
        rain_prob = daily.get("precipitation_probability_max", [None])[0]

        parts = [f"Weather for {city_name}: {cond}, {temp:.1f}°C (feels like {feels:.1f}°C)."]
        extra = []
        if humidity is not None:
            extra.append(f"Humidity {humidity}%")
        if wind is not None:
            extra.append(f"Wind {wind:.1f} km/h")
        if high is not None and low is not None:
            extra.append(f"Day's range {low:.1f}°C to {high:.1f}°C")
        if rain_prob is not None:
            extra.append(f"{rain_prob}% rain chance")
        if extra:
            parts.append(" | ".join(extra) + ".")
        return " ".join(parts)
    except Exception as exc:
        return f"Unable to fetch weather data: {exc}"


CRYPTO_ALIASES = {
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "eth": "ethereum", "ethereum": "ethereum",
    "sol": "solana", "solana": "solana",
    "doge": "dogecoin", "dogecoin": "dogecoin",
    "ada": "cardano", "xrp": "ripple"
}


def check_stock_crypto(memory, symbol: str) -> str:
    """Fetch real-time price and 24h change for a stock ticker (e.g. NVDA, AAPL) or cryptocurrency (e.g. BTC, ETH)."""
    sym = (symbol or "").strip().lower()
    if not sym:
        return "Please specify a stock ticker or cryptocurrency (e.g., 'NVDA', 'BTC', 'AAPL')."

    # 1. Check Crypto via CoinGecko
    if sym in CRYPTO_ALIASES:
        coin_id = CRYPTO_ALIASES[sym]
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,inr&include_24hr_change=true"
            req = urllib.request.Request(url, headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            c_data = data.get(coin_id, {})
            if c_data:
                usd = c_data.get("usd")
                inr = c_data.get("inr")
                change = c_data.get("usd_24h_change", 0.0)
                sign = "+" if change >= 0 else ""
                name_cap = coin_id.capitalize()
                return (f"{name_cap} ({sym.upper()}): ${usd:,.2f} USD (₹{inr:,.0f} INR), "
                        f"24h change: {sign}{change:.2f}%.")
        except Exception:
            pass

    # 2. Check Stock or Crypto via Yahoo Finance
    ticker = sym.upper()
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?interval=1d&range=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        res = data.get("chart", {}).get("result", [])
        if not res:
            return f"No market data found for ticker '{ticker}', Sir."
        meta = res[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        curr = meta.get("currency", "USD")
        change_pct = ((price - prev) / prev * 100.0) if prev and price else 0.0
        sign = "+" if change_pct >= 0 else ""
        sym_name = meta.get("shortName") or meta.get("symbol") or ticker
        return f"{sym_name} ({ticker}): {price:,.2f} {curr}, 24h change: {sign}{change_pct:.2f}%."
    except Exception as exc:
        return f"Could not retrieve market quote for '{symbol}': {exc}"


def news_briefing(memory, category: str = "technology") -> str:
    """Fetch top headlines and brief summaries (categories: technology, world, business)."""
    cat = (category or "").lower().strip()
    articles = []

    if "tech" in cat or "ai" in cat or "hacker" in cat:
        try:
            req = urllib.request.Request("https://hacker-news.firebaseio.com/v0/topstories.json", headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                story_ids = json.loads(r.read())[:6]
            for sid in story_ids:
                try:
                    s_req = urllib.request.Request(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", headers={"User-Agent": "RustyAI/1.0"})
                    with urllib.request.urlopen(s_req, timeout=4) as sr:
                        item = json.loads(sr.read())
                        if item and item.get("title"):
                            articles.append({
                                "title": item["title"],
                                "score": item.get("score", 0),
                                "url": item.get("url", "")
                            })
                except Exception:
                    continue
        except Exception:
            pass

    if not articles:
        rss_url = "http://feeds.bbci.co.uk/news/technology/rss.xml" if "tech" in cat else "http://feeds.bbci.co.uk/news/world/rss.xml"
        try:
            req = urllib.request.Request(rss_url, headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req, timeout=6) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:5]:
                title = item.findtext("title")
                desc = item.findtext("description")
                if title:
                    articles.append({"title": title, "desc": desc or ""})
        except Exception:
            pass

    if not articles:
        return "Unable to fetch news headlines at the moment, Sir."

    lines = [f"Top {cat.title()} Headlines:"]
    for i, a in enumerate(articles[:5], 1):
        if "score" in a:
            lines.append(f"{i}. {a['title']} ({a['score']} points)")
        else:
            lines.append(f"{i}. {a['title']}")
    return "\n".join(lines)


def summarize_webpage(memory, url: str) -> str:
    """Fetch article or page content from a URL and generate an executive summary."""
    clean_url = (url or "").strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    try:
        req = urllib.request.Request(
            clean_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            raw_html = r.read().decode("utf-8", errors="replace")

        # Extract title
        title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
        title = html.unescape(title_match.group(1).strip()) if title_match else ""

        # Strip scripts, styles, nav, footer, header
        text = re.sub(r"<(script|style|svg|noscript|nav|footer|header)[^>]*>.*?</\1>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return f"Could not extract readable text from {url}, Sir."

        snippet = text[:3500]

        from .media import _VISION_CONFIG
        cfg = _VISION_CONFIG
        if not cfg:
            try:
                from ..config import load_config
                cfg = load_config().get("llm")
            except Exception:
                cfg = None

        if cfg and cfg.get("api_key"):
            from ..llm import make_client
            client = make_client({"llm": cfg})
            prompt = (
                f"Document Title: {title}\nURL: {clean_url}\n\nContent:\n{snippet}\n\n"
                "Provide a clear, 3-5 bullet point executive summary highlighting key takeaways and facts."
            )
            resp = client.complete("You are an expert research analyst. Summarize clearly and objectively.", [{"role": "user", "content": prompt}], [])
            if resp.text:
                return f"Summary of {title or clean_url}:\n\n" + resp.text.strip()

        preview = text[:600] + ("..." if len(text) > 600 else "")
        return f"Content extract from {title or clean_url}:\n\n{preview}"
    except Exception as exc:
        return f"Failed to fetch webpage at {url}: {exc}"


def web_answer(memory, query: str, progress_callback=None) -> str:
    """Look something up and answer concisely using live search and encyclopedic reference."""
    if progress_callback:
        progress_callback(f"Researching '{query[:40]}' across live web sources, Sir...", speak=True)
    
    context_parts = []

    # 1. Query DuckDuckGo search & Instant Answer
    search_hits = _query_duckduckgo(query, max_results=3)
    if search_hits:
        for h in search_hits:
            context_parts.append(f"- {h['title']}: {h['snippet']}")

    # 2. Wikipedia Summary fallback/enrichment
    try:
        s = ("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json"
             "&srlimit=1&srsearch=" + urllib.parse.quote(query))
        req = urllib.request.Request(s, headers={"User-Agent": "RustyAI/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            sr = json.loads(response.read())
        hits = sr.get("query", {}).get("search", [])
        if hits:
            title = hits[0]["title"].replace(" ", "_")
            su = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title)
            req2 = urllib.request.Request(su, headers={"User-Agent": "RustyAI/1.0"})
            with urllib.request.urlopen(req2, timeout=6) as resp2:
                sd = json.loads(resp2.read())
            extract = (sd.get("extract") or "")[:1500]
            if extract:
                context_parts.append(f"Wikipedia reference: {extract}")
    except Exception:
        pass

    context = "\n".join(context_parts)

    from .media import _VISION_CONFIG
    cfg = _VISION_CONFIG
    if not cfg:
        try:
            from ..config import load_config
            cfg = load_config().get("llm")
        except Exception:
            cfg = None
    if not cfg or not cfg.get("api_key"):
        return context[:400] if context else "I couldn't look that up right now, Sir."
    try:
        from ..llm import make_client
        client = make_client({"llm": cfg})
        sysmsg = ("You are Rusty. Answer in one or two crisp spoken sentences. Ground your answer in the "
                  "provided live reference if relevant; otherwise answer accurately and concisely.")
        user = f"Question: {query}" + (f"\n\nLive References:\n{context}" if context else "")
        resp = client.complete(sysmsg, [{"role": "user", "content": user}], [])
        return (resp.text or "").strip() or (context[:400] if context else "I'm not certain on that one, Sir.")
    except Exception:
        return context[:400] if context else "I couldn't look that up right now, Sir."


BROWSER_SKILLS = [
    {"name": "real_web_search", "fn": real_web_search, "description": "Search the live web directly and return top answers, snippets, and source links without opening a browser window. Use for current facts, research, news, and queries.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "The search terms or question"}, "max_results": {"type": "integer", "description": "Number of results to retrieve (default 5)"}}, "required": ["query"]}},
    {"name": "check_weather", "fn": check_weather, "description": "Check live local weather, temperature, humidity, and forecast for any city or current location without needing an API key.",
     "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City or location name (e.g. 'London', 'New York', 'Mumbai'). Leave empty for current location."}}, "required": []}},
    {"name": "check_stock_crypto", "fn": check_stock_crypto, "description": "Fetch real-time price, currency, and 24-hour percentage change for any stock ticker (e.g. 'NVDA', 'AAPL', 'TSLA') or cryptocurrency (e.g. 'BTC', 'ETH', 'SOL').",
     "parameters": {"type": "object", "properties": {"symbol": {"type": "string", "description": "Stock ticker or crypto symbol/name"}}, "required": ["symbol"]}},
    {"name": "news_briefing", "fn": news_briefing, "description": "Fetch top news headlines and bullet summaries for technology, world news, or business.",
     "parameters": {"type": "object", "properties": {"category": {"type": "string", "description": "'technology', 'world', or 'business' (default: 'technology')"}}, "required": []}},
    {"name": "summarize_webpage", "fn": summarize_webpage, "description": "Fetch the readable article or documentation content from any URL and generate an executive bullet-point summary.",
     "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "Full HTTP or HTTPS URL to read and summarize"}}, "required": ["url"]}},
    {"name": "web_search", "fn": web_search, "description": "Open a Google search visually in the user's browser. For spoken or direct answers, prefer real_web_search or web_answer.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "web_answer", "fn": web_answer, "description": "Search the web and give Jay a concise spoken answer using real search results and encyclopedic reference.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "What to look up"}}, "required": ["query"]}},
    {"name": "open_url", "fn": open_url, "description": "Open a specific URL in the browser.",
     "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "open_youtube", "fn": open_youtube, "description": "Open YouTube, optionally searching for something.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Optional search terms"}}, "required": []}},
    {"name": "close_browser_tab", "fn": close_browser_tab, "description": "Close a specific tab by title/site (e.g. 'youtube', 'meet', 'google', 'whatsapp') or the active tab in the browser (Ctrl+W). Focuses the browser first.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "Optional tab title or website name to close (e.g. 'youtube', 'meet', 'reddit')"}}, "required": []}},
    {"name": "save_link", "fn": save_link, "description": "Save a named link/shortcut for later (e.g. a Google Meet link).",
     "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "url": {"type": "string"}}, "required": ["name", "url"]}},
    {"name": "open_saved_link", "fn": open_saved_link, "description": "Open a link previously saved with save_link, by its name.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "url": {"type": "string"}}, "required": ["name"]}},
    {"name": "list_saved_links", "fn": list_saved_links, "description": "List all saved named links.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "delete_link", "fn": delete_link, "description": "Delete a saved named link/shortcut from memory.",
     "parameters": {"type": "object", "properties": {"name": {"type": "string", "description": "Name of the link to remove"}}, "required": ["name"]}},
]

"""Unit tests for live web intelligence, search, weather, market data, and browser skills."""

import unittest
from unittest.mock import MagicMock, patch

from vyra import skills


class TestSkillsBrowser(unittest.TestCase):
    def setUp(self):
        self.mock_memory = MagicMock()

    def test_real_web_search_structure(self):
        """Verify real_web_search returns formatted results or graceful fallback without crashing."""
        output = skills.execute("real_web_search", {"query": "python programming language"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertTrue(len(output) > 10)
        self.assertTrue("python" in output.lower() or "search results" in output.lower())

    def test_check_weather_with_location(self):
        """Verify check_weather returns real temperature and conditions for a valid city."""
        output = skills.execute("check_weather", {"location": "London"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertTrue("London" in output)
        self.assertTrue("°C" in output)

    def test_check_weather_invalid_location(self):
        """Verify check_weather handles non-existent locations gracefully."""
        output = skills.execute("check_weather", {"location": "xyznonexistentcity12345"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertIn("Could not find coordinates", output)

    def test_check_stock_crypto_crypto(self):
        """Verify check_stock_crypto handles major cryptocurrencies (BTC, ETH)."""
        output = skills.execute("check_stock_crypto", {"symbol": "BTC"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertTrue("Bitcoin" in output or "BTC" in output)
        self.assertTrue("$" in output or "USD" in output)

    def test_check_stock_crypto_stocks(self):
        """Verify check_stock_crypto handles stock tickers (e.g. NVDA, AAPL)."""
        output = skills.execute("check_stock_crypto", {"symbol": "NVDA"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertIn("NVDA", output)
        self.assertTrue("24h change" in output or "USD" in output)

    def test_check_stock_crypto_empty(self):
        """Verify check_stock_crypto handles empty symbol gracefully."""
        output = skills.execute("check_stock_crypto", {"symbol": ""}, self.mock_memory)
        self.assertIn("Please specify a stock ticker", output)

    def test_news_briefing_tech(self):
        """Verify news_briefing returns top technology headlines."""
        output = skills.execute("news_briefing", {"category": "technology"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertTrue("Headlines" in output or "news" in output.lower())
        self.assertTrue(len(output.splitlines()) >= 2)

    def test_summarize_webpage_live(self):
        """Verify summarize_webpage extracts title and readable body from a URL."""
        output = skills.execute("summarize_webpage", {"url": "https://example.com"}, self.mock_memory)
        self.assertIsInstance(output, str)
        self.assertTrue("Example Domain" in output or "example" in output.lower())

    def test_close_browser_tab_no_browsers(self):
        """When no browser window is open, close_browser_tab returns a graceful message."""
        with patch("vyra.skills.browser._get_user_windows", return_value=[]):
            output = skills.execute("close_browser_tab", {"query": "youtube"}, self.mock_memory)
            self.assertIn("No active browser window found", output)

    def test_browser_automation_skills_registered(self):
        """Verify all interactive browser control skills are registered and callable."""
        for skill_name in ["browser_open", "browser_click", "browser_type", "browser_read_page", "browser_scroll", "browser_eval_js", "browser_close"]:
            self.assertIn(skill_name, skills._BY_NAME)
            self.assertTrue(callable(skills._BY_NAME[skill_name]["fn"]))

    def test_browser_actions_graceful_when_no_session(self):
        """Verify browser actions handle uninitialized or closed browser gracefully."""
        res_click = skills.execute("browser_click", {"target": "Submit"}, self.mock_memory)
        self.assertIn("No interactive browser window", res_click)

        res_read = skills.execute("browser_read_page", {}, self.mock_memory)
        self.assertIn("No interactive browser window", res_read)

        res_type = skills.execute("browser_type", {"text": "hello"}, self.mock_memory)
        self.assertIn("No interactive browser window", res_type)

        res_scroll = skills.execute("browser_scroll", {}, self.mock_memory)
        self.assertIn("No interactive browser window", res_scroll)

        res_eval = skills.execute("browser_eval_js", {"script": "1+1"}, self.mock_memory)
        self.assertIn("No interactive browser window", res_eval)


if __name__ == "__main__":
    unittest.main()

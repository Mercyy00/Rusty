"""Unit tests verifying speech conciseness and voice patience thresholds."""

import unittest
from vyra.voice import DEFAULT_TRAIL_SILENCE, extract_spoken_summary


class TestVoicePatienceAndConciseness(unittest.TestCase):
    def test_extract_spoken_summary_ten_line_response(self):
        """10-line responses must be distilled into a punchy 1-2 sentence spoken answer."""
        long_response = """
Here is the status of your services, Sir:
1. Docker daemon is running on port 2375.
2. PostgreSQL database has 12 active client connections.
3. Redis cache memory usage is at 42MB.
4. Celery background workers are waiting for tasks.
5. All 77 automated test suites completed with 0 errors.
6. The webpack build succeeded in 1.4s.
7. Web application is serving traffic on localhost:3000.
8. Git repository working directory is clean.
9. System storage has 380GB free space available.
10. Battery level is 94% and connected to AC power.
"""
        spoken = extract_spoken_summary(long_response)
        self.assertNotIn("10.", spoken)
        self.assertNotIn("7.", spoken)
        self.assertTrue(len(spoken.split()) <= 45, f"Summary was too long ({len(spoken.split())} words): {spoken}")
        self.assertIn("status of your services", spoken)

    def test_extract_spoken_summary_strips_code_blocks(self):
        """Code blocks must not be spoken aloud word-for-word."""
        code_response = """
Here is the solution for your algorithm:
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)
```
You can paste this into your project now.
"""
        spoken = extract_spoken_summary(code_response)
        self.assertNotIn("def fibonacci", spoken)
        self.assertNotIn("return n", spoken)
        self.assertIn("Here is the solution", spoken)

    def test_extract_spoken_summary_pure_code_fallback(self):
        """Responses that contain only code blocks get a polite executive spoken message."""
        pure_code = """
```python
import os
print(os.getcwd())
```
"""
        spoken = extract_spoken_summary(pure_code)
        self.assertIn("generated the code for you on screen", spoken)

    def test_extract_spoken_summary_short_text_unchanged(self):
        """Short 1-sentence responses remain intact."""
        short = "Volume set to 40%, Sir."
        spoken = extract_spoken_summary(short)
        self.assertEqual(spoken, short)

    def test_voice_patience_silence_threshold(self):
        """Voice silence threshold must be at least 1.8s to give the speaker room to pause."""
        self.assertGreaterEqual(DEFAULT_TRAIL_SILENCE, 1.8)


if __name__ == "__main__":
    unittest.main()

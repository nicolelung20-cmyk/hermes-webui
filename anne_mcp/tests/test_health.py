import unittest
from unittest.mock import patch

from anne_mcp.health import probe_http


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        return b'{"models": []}'


class HealthProbeTests(unittest.TestCase):
    def test_reports_json_from_reachable_service(self):
        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            result = probe_http("http://127.0.0.1:11434/api/tags")
        self.assertTrue(result["reachable"])
        self.assertEqual(result["json"], {"models": []})

    def test_reports_unreachable_service_without_leaking_exception_text(self):
        with patch("urllib.request.urlopen", side_effect=OSError("secret path /private/token")):
            result = probe_http("http://127.0.0.1:8787")
        self.assertFalse(result["reachable"])
        self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()

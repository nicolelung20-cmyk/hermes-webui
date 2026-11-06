import unittest
from unittest.mock import patch
import poe_bridge

class PoeBridgeTests(unittest.TestCase):
    def test_payload_is_openai_compatible_and_non_streaming(self):
        payload = poe_bridge.build_payload("ExampleBot", "Create a workflow")
        self.assertEqual(payload["model"], "ExampleBot")
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertFalse(payload["stream"])
    def test_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            poe_bridge.build_payload("ExampleBot", " ")
    def test_rejects_invalid_token_limit(self):
        with self.assertRaises(ValueError):
            poe_bridge.build_payload("ExampleBot", "hello", 0)
    def test_requires_api_key_before_network(self):
        with self.assertRaisesRegex(ValueError, "POE_API_KEY"):
            poe_bridge.call_poe({"model": "x"}, "")
    @patch("poe_bridge.urlopen")
    def test_call_returns_json(self, mocked):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"choices":[{"message":{"content":"ok"}}]}'
        mocked.return_value = Response()
        result = poe_bridge.call_poe({"model": "x"}, "not-a-real-key")
        self.assertEqual(result["choices"][0]["message"]["content"], "ok")
        self.assertTrue(mocked.called)

if __name__ == "__main__":
    unittest.main()

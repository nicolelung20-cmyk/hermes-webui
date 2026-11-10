import unittest

from api.anne_connectors import (
    Connector,
    ConnectorPolicyError,
    ConnectorRegistry,
    openapi_operation_methods,
    validate_base_url,
)


class ConnectorPolicyTests(unittest.TestCase):
    def test_public_https_origin_is_accepted(self):
        self.assertEqual(validate_base_url("https://api.example.com/"), "https://api.example.com")

    def test_private_host_requires_explicit_approval(self):
        with self.assertRaises(ConnectorPolicyError):
            validate_base_url("http://100.86.4.13")
        self.assertEqual(
            validate_base_url("http://100.86.4.13", private_network_approved=True),
            "http://100.86.4.13",
        )

    def test_base_url_rejects_embedded_credentials_and_paths(self):
        for value in ("https://user:pass@example.com", "https://api.example.com/v1"):
            with self.subTest(value=value), self.assertRaises(ConnectorPolicyError):
                validate_base_url(value)

    def test_read_is_allowed_and_write_requires_approval(self):
        registry = ConnectorRegistry()
        registry.register(Connector("internal_api", "Internal API", "https://api.example.com"))
        self.assertTrue(registry.authorize_operation("internal_api", "GET").allowed)
        denied = registry.authorize_operation("internal_api", "POST")
        self.assertFalse(denied.allowed)
        self.assertTrue(denied.requires_approval)
        self.assertTrue(registry.authorize_operation(
            "internal_api", "POST", explicit_approval=True
        ).allowed)

    def test_disabled_connector_is_denied(self):
        registry = ConnectorRegistry()
        registry.register(Connector("disabled_api", "Disabled", "https://api.example.com", enabled=False))
        self.assertFalse(registry.authorize_operation("disabled_api", "GET").allowed)

    def test_openapi_method_extraction(self):
        methods = openapi_operation_methods({
            "paths": {"/health": {"get": {}, "post": {}}, "/events": {"delete": {}}}
        })
        self.assertEqual(methods, {"/health": ("GET", "POST"), "/events": ("DELETE",)})


if __name__ == "__main__":
    unittest.main()

"""ANNE API connector policy registry.

This module is deliberately transport-free: it validates connector metadata and
authorizes proposed operations, but never makes network requests or stores
secret values. A future route/MCP adapter must call authorize_operation before
executing any request.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit


_SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{1,47}$")
_SAFE_ENV = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_TAILSCALE_NET = ipaddress.ip_network("100.64.0.0/10")


class ConnectorPolicyError(ValueError):
    """Raised when connector metadata or an operation violates policy."""


@dataclass(frozen=True)
class Connector:
    connector_id: str
    name: str
    base_url: str
    credential_env: str | None = None
    private_network_approved: bool = False
    enabled: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OperationDecision:
    allowed: bool
    requires_approval: bool
    reason: str


def validate_base_url(url: str, *, private_network_approved: bool = False) -> str:
    """Validate an origin URL; private hosts require explicit local approval."""
    if not isinstance(url, str) or not url.strip():
        raise ConnectorPolicyError("A base URL is required")
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ConnectorPolicyError("Base URL must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConnectorPolicyError("Credentials, query strings, and fragments are not allowed in base URLs")
    if parsed.path not in {"", "/"}:
        raise ConnectorPolicyError("Use an origin only; put API paths in operation definitions")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost"} or host.endswith(".localhost") or host.endswith(".local"):
        if not private_network_approved:
            raise ConnectorPolicyError("Local-network hosts require explicit private-network approval")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None:
        is_private = (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address in _TAILSCALE_NET
        )
        if is_private and not private_network_approved:
            raise ConnectorPolicyError("Private or link-local IPs require explicit private-network approval")
        if not is_private and not address.is_global:
            raise ConnectorPolicyError("Non-global IP address is not an allowed public endpoint")
    if parsed.scheme == "http" and not private_network_approved:
        raise ConnectorPolicyError("Public connectors must use HTTPS")
    return f"{parsed.scheme}://{parsed.netloc}"


class ConnectorRegistry:
    """In-memory registry; persistence and transport are intentionally external."""

    def __init__(self) -> None:
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> Connector:
        if not _SAFE_ID.fullmatch(connector.connector_id):
            raise ConnectorPolicyError("Connector ID must be 2-48 lowercase letters, digits, '_' or '-'")
        if not connector.name.strip():
            raise ConnectorPolicyError("Connector name is required")
        if connector.credential_env and not _SAFE_ENV.fullmatch(connector.credential_env):
            raise ConnectorPolicyError("Credential reference must be an environment-variable name")
        normalized_url = validate_base_url(
            connector.base_url,
            private_network_approved=connector.private_network_approved,
        )
        normalized = Connector(
            connector_id=connector.connector_id,
            name=connector.name.strip(),
            base_url=normalized_url,
            credential_env=connector.credential_env,
            private_network_approved=connector.private_network_approved,
            enabled=connector.enabled,
            tags=tuple(connector.tags),
        )
        self._connectors[normalized.connector_id] = normalized
        return normalized

    def get(self, connector_id: str) -> Connector:
        try:
            return self._connectors[connector_id]
        except KeyError as exc:
            raise ConnectorPolicyError("Unknown connector") from exc

    def list(self) -> tuple[Connector, ...]:
        return tuple(self._connectors[key] for key in sorted(self._connectors))

    def authorize_operation(
        self,
        connector_id: str,
        method: str,
        *,
        explicit_approval: bool = False,
    ) -> OperationDecision:
        connector = self.get(connector_id)
        if not connector.enabled:
            return OperationDecision(False, False, "Connector is disabled")
        verb = method.upper()
        if verb in _READ_METHODS:
            return OperationDecision(True, False, "Read-only operation allowed")
        if verb in _WRITE_METHODS:
            if explicit_approval:
                return OperationDecision(True, False, "Write operation approved for this action")
            return OperationDecision(False, True, "Explicit user approval is required for write operations")
        return OperationDecision(False, False, "HTTP method is not supported by connector policy")


def openapi_operation_methods(spec: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Extract HTTP methods from an already-provided OpenAPI document.

    This function does not retrieve remote specs or execute any operation.
    """
    if not isinstance(spec, dict) or not isinstance(spec.get("paths"), dict):
        raise ConnectorPolicyError("OpenAPI document must contain a paths object")
    result: dict[str, tuple[str, ...]] = {}
    for path, item in spec["paths"].items():
        if not isinstance(path, str) or not isinstance(item, dict):
            continue
        methods = tuple(sorted(
            key.upper() for key in item
            if isinstance(key, str) and key.lower() in (_READ_METHODS | _WRITE_METHODS)
        ))
        if methods:
            result[path] = methods
    return result

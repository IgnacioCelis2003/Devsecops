# app/clients/__init__.py
from .wazuh_client import (
    fetch_all_vulns,
    test_connection,
    is_safe_url,
    get_auth_header,
    VULN_INDEX,
    VERIFY_SSL,
    DOMAINS_ALLOWLIST,
)

__all__ = [
    "fetch_all_vulns",
    "test_connection",
    "is_safe_url",
    "get_auth_header",
    "VULN_INDEX",
    "VERIFY_SSL",
    "DOMAINS_ALLOWLIST",
]

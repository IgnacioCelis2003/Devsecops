# app/services/__init__.py
from .wazuh_sync_service import process_wazuh_vulnerabilities

__all__ = ["process_wazuh_vulnerabilities"]

# app/models/__init__.py
from .user import User
from .user_interaction import UserInteraction
from .wazuh_connection import WazuhConnection
from .wazuh_vulnerability import WazuhVulnerability
from .vulnerability_history import VulnerabilityHistory

__all__ = [
    "User",
    "UserInteraction",
    "WazuhConnection",
    "WazuhVulnerability",
    "VulnerabilityHistory",
]

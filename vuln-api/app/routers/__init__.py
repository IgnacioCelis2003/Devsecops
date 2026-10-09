# app/routers/__init__.py
from . import auth_router, users_router, wazuh_router, vulns_router

__all__ = [
    "auth_router",
    "users_router",
    "wazuh_router",
    "vulns_router",
]

# app/routers/__init__.py
from .auth_router import router as auth_router
from .users_router import router as users_router
from .wazuh_router import router as wazuh_router
from .vulns_router import router as vulns_router

__all__ = [
    "auth_router",
    "users_router",
    "wazuh_router",
    "vulns_router",
]

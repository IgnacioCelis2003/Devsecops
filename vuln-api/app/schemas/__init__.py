# app/schemas/__init__.py
from .auth_schemas import ChangePasswordRequest
from .user_schemas import NewUserRequest
from .wazuh_schemas import WazuhConnectionRequest, WazuhConnectionResponse

__all__ = [
    "ChangePasswordRequest",
    "NewUserRequest",
    "WazuhConnectionRequest",
    "WazuhConnectionResponse",
]

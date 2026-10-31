# app/schemas/user_schemas.py
from typing import Optional, List
from pydantic import BaseModel


class NewUserRequest(BaseModel):
    username: str
    password: str
    tags: Optional[List[str]] = []
    role: Optional[str] = "viewer"


class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

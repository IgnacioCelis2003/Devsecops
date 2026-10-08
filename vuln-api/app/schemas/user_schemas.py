# app/schemas/user_schemas.py
from pydantic import BaseModel


class NewUserRequest(BaseModel):
    username: str
    password: str

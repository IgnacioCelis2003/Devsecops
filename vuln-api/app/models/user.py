# app/models/user.py
from sqlalchemy import Column, Integer, Boolean, String, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    is_default_password = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    tags = Column(JSON, nullable=False, default=list)

    interactions = relationship("UserInteraction", back_populates="user")

# app/models/wazuh_connection.py
from sqlalchemy import Column, Integer, Boolean, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db import Base


class WazuhConnection(Base):
    __tablename__ = "wazuh_connections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    indexer_url = Column(String, nullable=False)
    wazuh_user = Column(String, nullable=False)
    wazuh_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tested = Column(Boolean, default=False)
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_ok = Column(Boolean, nullable=True)

    vulnerabilities = relationship(
        "WazuhVulnerability",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

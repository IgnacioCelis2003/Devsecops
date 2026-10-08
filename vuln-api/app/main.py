# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .db import Base, engine, ensure_schema_compatibility, SessionLocal
from .models import User, WazuhVulnerability, WazuhConnection, VulnerabilityHistory
from .auth import hash_password
from .wazuh_client import fetch_all_vulns, test_connection
from .crypto import encrypt, decrypt
from .seed_data import seed_database
from .services.wazuh_sync_service import process_wazuh_vulnerabilities

from .routers.auth_router import router as auth_router
from .routers.users_router import router as users_router
from .routers.wazuh_router import router as wazuh_router
from .routers.vulns_router import router as vulns_router

# Schemas Pydantic reexportados para retrocompatibilidad
from .schemas import (
    WazuhConnectionRequest,
    WazuhConnectionResponse,
    ChangePasswordRequest,
    NewUserRequest,
)

Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

CONNECTION_NOT_FOUND = "Conexión no encontrada"
DOMAINS_ALLOWLIST = [
    domain.strip()
    for domain in os.getenv("DOMAINS_ALLOWLIST", "localhost").split(",")
    if domain.strip()
]
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost,http://127.0.0.1,https://localhost,https://127.0.0.1",
    ).split(",")
    if origin.strip()
]


def create_default_admin():
    db = SessionLocal()
    try:
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
            print("Creando usuario admin default...")
            default_admin = User(
                username="admin", 
                password_hash=hash_password("admin"), 
                is_active=True,
                is_default_password=True,
            )
            db.add(default_admin)
            db.commit()
    finally:
        db.close()


create_default_admin()


def seed_example_data_on_startup():
    if os.getenv("SEED_EXAMPLE_DATA", "false").lower() != "true":
        return
    with SessionLocal() as db:
        if db.query(WazuhVulnerability).first() is not None:
            return
    seed_database()


app = FastAPI(title="Vulnerability Aggregator API", root_path="/api")


@app.on_event("startup")
def load_example_data_if_enabled():
    seed_example_data_on_startup()


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers modulares
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(wazuh_router, prefix="/wazuh-connections", tags=["wazuh"])
app.include_router(vulns_router, prefix="/vulns", tags=["vulns"])
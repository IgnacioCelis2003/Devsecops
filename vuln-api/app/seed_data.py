import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from .crypto import encrypt
from .db import Base, engine, ensure_schema_compatibility
from .models import (
    User,
    UserInteraction,
    VulnerabilityHistory,
    WazuhConnection,
    WazuhVulnerability,
)

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = APP_DIR / "datos_wazuh.json"


def parse_datetime(dt_str: str | None):
    if not dt_str:
        return None
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def normalize_tags(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        if "name" in value:
            return [str(value["name"])]
        if "key" in value and "value" in value:
            return [f"{value['key']}={value['value']}"]
        return [f"{key}={item}" for key, item in value.items()]
    if isinstance(value, (list, tuple, set)):
        tags = []
        for item in value:
            tags.extend(normalize_tags(item))
        return list(dict.fromkeys(tag for tag in tags if tag))
    return [str(value)]


def encrypted_password(value: str) -> str:
    return value if value.startswith("gAAAA") else encrypt(value)


def seed_database(json_path: str | Path = DEFAULT_DATA_PATH, replace: bool = False):
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility()

    with Path(json_path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    with Session(engine) as session:
        user_ids = {}
        connection_ids = {}

        if replace:
            session.query(VulnerabilityHistory).delete()
            session.query(WazuhVulnerability).delete()
            session.query(UserInteraction).delete()
            session.query(WazuhConnection).delete()
            session.flush()

        for item in data.get("users", []):
            user = session.query(User).filter_by(username=item["username"]).first()
            if user is None:
                user = User(username=item["username"])
                session.add(user)
            user.password_hash = item["password_hash"]
            user.is_active = item.get("is_active", False)
            user.is_default_password = item.get("is_default_password", True)
            user.created_at = parse_datetime(item.get("created_at"))
            session.flush()
            user_ids[item["id"]] = user.id

        for item in data.get("wazuh_connections", []):
            connection = session.query(WazuhConnection).filter_by(
                name=item["name"]
            ).first()
            if connection is None:
                connection = WazuhConnection(name=item["name"])
                session.add(connection)
            connection.indexer_url = item["indexer_url"]
            connection.wazuh_user = item["wazuh_user"]
            connection.wazuh_password = encrypted_password(item["wazuh_password"])
            connection.is_active = item.get("is_active", True)
            connection.tested = item.get("tested", False)
            connection.last_test_ok = item.get("last_test_ok")
            connection.created_at = parse_datetime(item.get("created_at"))
            connection.last_tested_at = parse_datetime(item.get("last_tested_at"))

        session.flush()
        for item in data.get("wazuh_connections", []):
            connection = session.query(WazuhConnection).filter_by(
                name=item["name"]
            ).one()
            connection_ids[item["id"]] = connection.id

        for item in data.get("user_interactions", []):
            if session.get(UserInteraction, item.get("id")) is None:
                session.add(UserInteraction(
                    id=item.get("id"),
                    user_id=user_ids[item["user_id"]],
                    endpoint=item.get("endpoint"),
                    method=item.get("method"),
                    details=item.get("details"),
                    timestamp=parse_datetime(item.get("timestamp")),
                ))

        for item in data.get("wazuh_vulnerabilities", []):
            vulnerability = session.get(WazuhVulnerability, item.get("id"))
            if vulnerability is None:
                vulnerability = WazuhVulnerability(id=item.get("id"))
                session.add(vulnerability)
            vulnerability.connection_id = connection_ids[item["connection_id"]]
            vulnerability.status = item.get("status", "ACTIVE")
            vulnerability.agent_id = item["agent_id"]
            vulnerability.agent_name = item.get("agent_name")
            vulnerability.tags = normalize_tags(item.get("tags"))
            vulnerability.os_full = item.get("os_full")
            vulnerability.os_platform = item.get("os_platform")
            vulnerability.os_version = item.get("os_version")
            vulnerability.package_name = item.get("package_name")
            vulnerability.package_version = item.get("package_version")
            vulnerability.package_type = item.get("package_type")
            vulnerability.package_arch = item.get("package_arch")
            vulnerability.cve_id = item["cve_id"]
            vulnerability.severity = item.get("severity")
            vulnerability.score_base = item.get("score_base")
            vulnerability.score_version = item.get("score_version")
            vulnerability.detected_at = parse_datetime(item.get("detected_at"))
            vulnerability.published_at = parse_datetime(item.get("published_at"))
            vulnerability.description = item.get("description")
            vulnerability.reference = item.get("reference")
            vulnerability.scanner_vendor = item.get("scanner_vendor")
            vulnerability.first_seen = parse_datetime(item.get("first_seen"))
            vulnerability.last_seen = parse_datetime(item.get("last_seen"))

        session.flush()
        for item in data.get("vulnerability_history", []):
            if session.get(VulnerabilityHistory, item.get("id")) is None:
                session.add(VulnerabilityHistory(
                    id=item.get("id"),
                    vulnerability_id=item["vulnerability_id"],
                    action=item["action"],
                    details=item.get("details"),
                    timestamp=parse_datetime(item.get("timestamp")),
                ))

        session.commit()

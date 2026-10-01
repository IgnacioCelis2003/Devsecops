import json
from datetime import datetime
from sqlalchemy.orm import Session

# Ajusta las importaciones según la estructura de tu proyecto
from app.db import Base, engine
from app.models import (
    User,
    UserInteraction,
    VulnerabilityHistory,
    WazuhConnection,
    WazuhVulnerability,
)


def parse_datetime(dt_str: str):
    """Convierte cadenas ISO-8601 a objetos datetime de Python."""
    if not dt_str:
        return None
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    return datetime.fromisoformat(dt_str)


def seed_database(json_path: str = "seed_data.json"):
    """Carga los datos del archivo JSON e inserta los registros en la base de datos."""
    # Crea las tablas si aún no existen
    Base.metadata.create_all(bind=engine)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with Session(engine) as session:
        print("Cargando usuarios...")
        for item in data.get("users", []):
            user = User(
                id=item.get("id"),
                username=item["username"],
                password_hash=item["password_hash"],
                is_active=item.get("is_active", False),
                is_default_password=item.get("is_default_password", True),
                created_at=parse_datetime(item.get("created_at")),
            )
            session.add(user)

        print("Cargando conexiones Wazuh...")
        for item in data.get("wazuh_connections", []):
            conn = WazuhConnection(
                id=item.get("id"),
                name=item["name"],
                indexer_url=item["indexer_url"],
                wazuh_user=item["wazuh_user"],
                wazuh_password=item["wazuh_password"],
                is_active=item.get("is_active", True),
                tested=item.get("tested", False),
                last_test_ok=item.get("last_test_ok"),
                created_at=parse_datetime(item.get("created_at")),
                last_tested_at=parse_datetime(item.get("last_tested_at")),
            )
            session.add(conn)

        # Se realiza flush para garantizar la existencia de las llaves primarias de usuarios y conexiones
        session.flush()

        print("Cargando interacciones de usuario...")
        for item in data.get("user_interactions", []):
            interaction = UserInteraction(
                id=item.get("id"),
                user_id=item["user_id"],
                endpoint=item.get("endpoint"),
                method=item.get("method"),
                details=item.get("details"),
                timestamp=parse_datetime(item.get("timestamp")),
            )
            session.add(interaction)

        print("Cargando vulnerabilidades Wazuh...")
        for item in data.get("wazuh_vulnerabilities", []):
            vuln = WazuhVulnerability(
                id=item.get("id"),
                connection_id=item["connection_id"],
                status=item.get("status", "ACTIVE"),
                agent_id=item["agent_id"],
                agent_name=item.get("agent_name"),
                os_full=item.get("os_full"),
                os_platform=item.get("os_platform"),
                os_version=item.get("os_version"),
                package_name=item.get("package_name"),
                package_version=item.get("package_version"),
                package_type=item.get("package_type"),
                package_arch=item.get("package_arch"),
                cve_id=item["cve_id"],
                severity=item.get("severity"),
                score_base=item.get("score_base"),
                score_version=item.get("score_version"),
                detected_at=parse_datetime(item.get("detected_at")),
                published_at=parse_datetime(item.get("published_at")),
                description=item.get("description"),
                reference=item.get("reference"),
                scanner_vendor=item.get("scanner_vendor"),
                first_seen=parse_datetime(item.get("first_seen")),
                last_seen=parse_datetime(item.get("last_seen")),
            )
            session.add(vuln)

        session.flush()

        print("Cargando historial de vulnerabilidades...")
        for item in data.get("vulnerability_history", []):
            history = VulnerabilityHistory(
                id=item.get("id"),
                vulnerability_id=item["vulnerability_id"],
                action=item["action"],
                details=item.get("details"),
                timestamp=parse_datetime(item.get("timestamp")),
            )
            session.add(history)

        session.commit()
        print("¡Base de datos poblada exitosamente!")


if __name__ == "__main__":
    seed_database()
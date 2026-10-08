# app/services/wazuh_sync_service.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models import WazuhVulnerability, VulnerabilityHistory


def _extract_wazuh_tags(vuln: dict) -> list[str]:
    """Normalize tags and agent groups from Wazuh documents."""
    agent = vuln.get("agent") or {}
    values = []
    for source in (vuln.get("tags"), agent.get("tags"), agent.get("groups")):
        if isinstance(source, str):
            values.append(source)
        elif isinstance(source, dict):
            if "name" in source:
                values.append(str(source["name"]))
            elif "key" in source and "value" in source:
                values.append(f"{source['key']}={source['value']}")
            else:
                values.extend(f"{key}={value}" for key, value in source.items())
        elif isinstance(source, (list, tuple, set)):
            for item in source:
                if isinstance(item, dict):
                    if "name" in item:
                        values.append(str(item["name"]))
                    elif "key" in item and "value" in item:
                        values.append(f"{item['key']}={item['value']}")
                elif item is not None:
                    values.append(str(item))
    return list(dict.fromkeys(tag for tag in values if tag))


def _handle_existing_vuln(db: Session, existing: WazuhVulnerability, vuln: dict) -> None:
    if existing.status == "RESOLVED":
        existing.status = "ACTIVE"
        db.add(VulnerabilityHistory(
            vulnerability_id=existing.id,
            action="REOPENED",
            details="La vulnerabilidad fue detectada nuevamente por Wazuh",
        ))

    if existing.severity != vuln.get("severity"):
        db.add(VulnerabilityHistory(
            vulnerability_id=existing.id,
            action="SEVERITY_CHANGED",
            details=f"Severidad cambió de {existing.severity} a {vuln.get('severity')}",
        ))
        existing.severity = vuln.get("severity")

    existing.score_base = (vuln.get("score") or {}).get("base")
    existing.last_seen = datetime.now(timezone.utc)


def _resolve_missing_vulns(db: Session, active_vuln_dict: dict, seen_vuln_ids: set) -> None:
    for vuln_id, db_vuln in active_vuln_dict.items():
        if vuln_id not in seen_vuln_ids:
            db_vuln.status = "RESOLVED"
            db.add(VulnerabilityHistory(
                vulnerability_id=vuln_id,
                action="RESOLVED",
                details="Ya no es reportada por el agente (Probablemente parcheada)",
            ))


def process_wazuh_vulnerabilities(db: Session, conn_id: int, raw_vulns: list) -> int:
    count = 0
    seen_vuln_ids = set()

    # Permite filtrar por rangos de tiempo si se desea (ejemplo: solo las de la última semana)
    # Aquí puedes agregar lógica para filtrar por first_seen o last_seen si lo necesitas
    active_vulns_in_db = db.query(WazuhVulnerability).filter_by(connection_id=conn_id, status="ACTIVE").all()
    active_vuln_dict = {v.id: v for v in active_vulns_in_db}

    for v in raw_vulns:
        agent = v.get("agent", {})
        tags = _extract_wazuh_tags(v)
        osinfo = (v.get("host") or {}).get("os") or {}
        pkg = v.get("package", {})
        vuln = v.get("vulnerability", {})

        if not vuln.get("id"):
            continue

        # Permite escalar y buscar eficientemente por first_seen y last_seen
        existing = db.query(WazuhVulnerability).filter_by(
            connection_id=conn_id,
            agent_id=agent.get("id"),
            package_name=pkg.get("name"),
            package_version=pkg.get("version"),
            cve_id=vuln.get("id"),
        ).first()

        if existing:
            seen_vuln_ids.add(existing.id)
            existing.tags = tags
            # Actualiza last_seen para aprovechar la hypertable
            existing.last_seen = datetime.now(timezone.utc)
            _handle_existing_vuln(db, existing, vuln)
        else:
            # detected_at siempre tiene valor (para particionamiento en TimescaleDB)
            # Si no viene de Wazuh, usa ahora
            detected_at = vuln.get("detected_at") or datetime.now(timezone.utc)
            first_seen = detected_at
            new_vuln = WazuhVulnerability(
                connection_id=conn_id,
                status="ACTIVE",
                agent_id=agent.get("id"),
                agent_name=agent.get("name"),
                tags=tags,
                os_full=osinfo.get("full"),
                os_platform=osinfo.get("platform"),
                os_version=osinfo.get("version"),
                package_name=pkg.get("name"),
                package_version=pkg.get("version"),
                package_type=pkg.get("type"),
                package_arch=pkg.get("architecture"),
                cve_id=vuln.get("id"),
                severity=vuln.get("severity"),
                score_base=(vuln.get("score") or {}).get("base"),
                score_version=(vuln.get("score") or {}).get("version"),
                detected_at=detected_at,
                published_at=vuln.get("published_at"),
                description=vuln.get("description"),
                reference=vuln.get("reference"),
                scanner_vendor=(vuln.get("scanner") or {}).get("vendor"),
                first_seen=first_seen,
                last_seen=first_seen,
            )
            db.add(new_vuln)
            db.flush()
            db.add(VulnerabilityHistory(
                vulnerability_id=new_vuln.id,
                action="DETECTED",
                details="Vulnerabilidad identificada por primera vez",
            ))
            seen_vuln_ids.add(new_vuln.id)

        count += 1

    _resolve_missing_vulns(db, active_vuln_dict, seen_vuln_ids)
    return count

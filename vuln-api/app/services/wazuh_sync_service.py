from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import VulnerabilityEvent, VulnerabilityHistory, WazuhVulnerability


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


def vulnerability_key(
    connection_id: int,
    agent_id: str | None,
    package_name: str | None,
    package_version: str | None,
    cve_id: str | None,
) -> tuple:
    return (
        connection_id,
        agent_id,
        package_name,
        package_version,
        cve_id,
    )


def normalize_wazuh_vulnerability(raw: dict) -> dict | None:
    agent = raw.get("agent") or {}
    host = raw.get("host") or {}
    osinfo = host.get("os") or {}
    package = raw.get("package") or {}
    vulnerability = raw.get("vulnerability") or {}

    if not vulnerability.get("id"):
        return None

    return {
        "agent_id": agent.get("id"),
        "agent_name": agent.get("name"),
        "tags": _extract_wazuh_tags(raw),
        "os_full": osinfo.get("full"),
        "os_platform": osinfo.get("platform"),
        "os_version": osinfo.get("version"),
        "package_name": package.get("name"),
        "package_version": package.get("version"),
        "package_type": package.get("type"),
        "package_arch": package.get("architecture"),
        "vulnerability": vulnerability,
    }


def normalize_wazuh_vulnerabilities(raw_vulns: list[dict]) -> list[dict]:
    return [
        normalized
        for raw in raw_vulns
        if (normalized := normalize_wazuh_vulnerability(raw)) is not None
    ]


def _handle_existing_vuln(
    existing: WazuhVulnerability,
    vuln: dict,
    history_rows: list[VulnerabilityHistory],
    event_rows: list[VulnerabilityEvent],
) -> None:
    if existing.status == "RESOLVED":
        previous_status = existing.status
        existing.status = "ACTIVE"
        history_rows.append(
            VulnerabilityHistory(
                vulnerability_id=existing.id,
                action="REOPENED",
                details="La vulnerabilidad fue detectada nuevamente por Wazuh",
            )
        )
        event_rows.append(
            VulnerabilityEvent(
                event_type="REOPENED",
                vulnerability_id=existing.id,
                connection_id=existing.connection_id,
                agent_id=existing.agent_id,
                cve_id=existing.cve_id,
                severity=existing.severity,
                status="ACTIVE",
                details={"previous_status": previous_status},
            )
        )

    new_severity = vuln.get("severity")
    if existing.severity != new_severity:
        previous_severity = existing.severity
        history_rows.append(
            VulnerabilityHistory(
                vulnerability_id=existing.id,
                action="SEVERITY_CHANGED",
                details=(
                    f"Severidad cambió de {previous_severity} "
                    f"a {new_severity}"
                ),
            )
        )
        existing.severity = new_severity
        event_rows.append(
            VulnerabilityEvent(
                event_type="SEVERITY_CHANGED",
                vulnerability_id=existing.id,
                connection_id=existing.connection_id,
                agent_id=existing.agent_id,
                cve_id=existing.cve_id,
                severity=new_severity,
                status=existing.status,
                details={
                    "old_severity": previous_severity,
                    "new_severity": new_severity,
                },
            )
        )

    existing.score_base = (vuln.get("score") or {}).get("base")
    existing.last_seen = datetime.now(timezone.utc)


def process_wazuh_vulnerabilities(
    db: Session,
    conn_id: int,
    raw_vulns: list,
) -> int:
    normalized_vulns = normalize_wazuh_vulnerabilities(raw_vulns)
    unique_vulns = {}
    for item in normalized_vulns:
        key = vulnerability_key(
            conn_id,
            item["agent_id"],
            item["package_name"],
            item["package_version"],
            item["vulnerability"]["id"],
        )
        unique_vulns[key] = item
    normalized_vulns = list(unique_vulns.values())
    existing_rows = (
        db.query(WazuhVulnerability)
        .filter(WazuhVulnerability.connection_id == conn_id)
        .all()
    )
    existing_by_key = {
        vulnerability_key(
            row.connection_id,
            row.agent_id,
            row.package_name,
            row.package_version,
            row.cve_id,
        ): row
        for row in existing_rows
    }

    seen_keys = set()
    new_rows = []
    history_rows = []
    event_rows = []

    for item in normalized_vulns:
        vulnerability = item["vulnerability"]
        key = vulnerability_key(
            conn_id,
            item["agent_id"],
            item["package_name"],
            item["package_version"],
            vulnerability["id"],
        )
        seen_keys.add(key)
        existing = existing_by_key.get(key)

        if existing is not None:
            existing.tags = item["tags"]
            existing.agent_name = item["agent_name"]
            _handle_existing_vuln(
                existing, vulnerability, history_rows, event_rows
            )
            continue

        detected_at = vulnerability.get("detected_at") or datetime.now(timezone.utc)
        new_rows.append(
            WazuhVulnerability(
                connection_id=conn_id,
                status="ACTIVE",
                agent_id=item["agent_id"],
                agent_name=item["agent_name"],
                tags=item["tags"],
                os_full=item["os_full"],
                os_platform=item["os_platform"],
                os_version=item["os_version"],
                package_name=item["package_name"],
                package_version=item["package_version"],
                package_type=item["package_type"],
                package_arch=item["package_arch"],
                cve_id=vulnerability["id"],
                severity=vulnerability.get("severity"),
                score_base=(vulnerability.get("score") or {}).get("base"),
                score_version=(vulnerability.get("score") or {}).get("version"),
                detected_at=detected_at,
                published_at=vulnerability.get("published_at"),
                description=vulnerability.get("description"),
                reference=vulnerability.get("reference"),
                scanner_vendor=(vulnerability.get("scanner") or {}).get("vendor"),
                first_seen=detected_at,
                last_seen=detected_at,
            )
        )

    db.add_all(new_rows)
    db.flush()

    for row in new_rows:
        history_rows.append(
            VulnerabilityHistory(
                vulnerability_id=row.id,
                action="DETECTED",
                details="Vulnerabilidad identificada por primera vez",
            )
        )
        event_rows.append(
            VulnerabilityEvent(
                event_type="DETECTED",
                vulnerability_id=row.id,
                connection_id=row.connection_id,
                agent_id=row.agent_id,
                cve_id=row.cve_id,
                severity=row.severity,
                status="ACTIVE",
                details={
                    "package_name": row.package_name,
                    "package_version": row.package_version,
                },
            )
        )

    for row in existing_rows:
        key = vulnerability_key(
            row.connection_id,
            row.agent_id,
            row.package_name,
            row.package_version,
            row.cve_id,
        )
        if row.status == "ACTIVE" and key not in seen_keys:
            row.status = "RESOLVED"
            history_rows.append(
                VulnerabilityHistory(
                    vulnerability_id=row.id,
                    action="RESOLVED",
                    details="Ya no es reportada por el agente",
                )
            )
            event_rows.append(
                VulnerabilityEvent(
                    event_type="RESOLVED",
                    vulnerability_id=row.id,
                    connection_id=row.connection_id,
                    agent_id=row.agent_id,
                    cve_id=row.cve_id,
                    severity=row.severity,
                    status="RESOLVED",
                    details={"reason": "not_reported"},
                )
            )

    db.add_all(history_rows)
    db.add_all(event_rows)
    return len(normalized_vulns)

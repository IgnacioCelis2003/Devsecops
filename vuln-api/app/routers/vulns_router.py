# app/routers/vulns_router.py
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, WazuhConnection, WazuhVulnerability
from ..auth import get_current_user_enforcing_password_change
from ..clients.wazuh_client import fetch_all_vulns
from ..crypto import decrypt
from ..services.wazuh_sync_service import process_wazuh_vulnerabilities

router = APIRouter()


@router.post("/sync-all")
def sync_all_connections(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user_enforcing_password_change)
):
    conns = db.query(WazuhConnection).filter(WazuhConnection.is_active == True).all()
    results = []

    for conn in conns:
        try:
            raw_vulns = fetch_all_vulns(
                conn.indexer_url,
                conn.wazuh_user,
                decrypt(conn.wazuh_password),
            )

            count = process_wazuh_vulnerabilities(db, conn.id, raw_vulns)
            db.commit()

            results.append({"connection": conn.name, "synced": count, "ok": True})
        except Exception as e:
            db.rollback()
            results.append({"connection": conn.name, "ok": False, "error": str(e)})

    return results


@router.get("")
def list_vulns(
    limit: Optional[int] = None,
    connection_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_enforcing_password_change),
):
    query = db.query(
        WazuhVulnerability,
        (func.extract('epoch', WazuhVulnerability.last_seen - WazuhVulnerability.first_seen) / 86400.0).label("dwell_time_days"),
        (func.extract('epoch', func.now() - WazuhVulnerability.first_seen) / 86400.0).label("total_age_days")
    )
    if connection_id:
        query = query.filter(WazuhVulnerability.connection_id == connection_id)
    if limit is not None:
        query = query.limit(limit)
    results = query.all()
    return [
        {
            "id": v.id,
            "connection_id": v.connection_id,
            "connection_name": v.connection.name if v.connection else None,
            "status": v.status,
            "agent_id": v.agent_id,
            "agent_name": v.agent_name,
            "tags": v.tags or [],
            "os_full": v.os_full,
            "os_platform": v.os_platform,
            "os_version": v.os_version,
            "package_name": v.package_name,
            "package_version": v.package_version,
            "package_type": v.package_type,
            "package_arch": v.package_arch,
            "cve_id": v.cve_id,
            "severity": v.severity,
            "score_base": float(v.score_base) if v.score_base else None,
            "score_version": v.score_version,
            "detected_at": v.detected_at,
            "published_at": v.published_at,
            "description": v.description,
            "reference": v.reference,
            "scanner_vendor": v.scanner_vendor,
            "first_seen": v.first_seen,
            "last_seen": v.last_seen,
            "dwell_time_days": float(dwell) if dwell is not None else None,
            "total_age_days": float(age) if age is not None else None,
            "history": [
                {
                    "id": h.id,
                    "action": h.action,
                    "details": h.details,
                    "timestamp": h.timestamp,
                }
                for h in sorted(v.history, key=lambda h: h.timestamp)
            ],
        }
        for v, dwell, age in results
    ]

# app/routers/vulns_router.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, column, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, joinedload, selectinload

from ..db import engine, get_db
from ..models import (
    User,
    VulnerabilityEvent,
    VulnerabilityHistory,
    WazuhConnection,
    WazuhVulnerability,
)
from ..auth import get_current_user_enforcing_password_change, require_admin
from ..clients.wazuh_client import fetch_all_vulns
from ..crypto import decrypt
from ..services.wazuh_sync_service import process_wazuh_vulnerabilities

router = APIRouter()


@router.post("/sync-all")
def sync_all_connections(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
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
    offset: int = 0,
    limit: int = 50,
    connection_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_enforcing_password_change),
):
    if engine.dialect.name == "postgresql":
        dwell_time_expression = func.fn_calculate_dwell_time(
            WazuhVulnerability.first_seen,
            WazuhVulnerability.last_seen,
        ).label("dwell_time_days")
        age_expression = func.fn_calculate_total_age(
            WazuhVulnerability.first_seen,
        ).label("total_age_days")
    else:
        dwell_time_expression = (
            func.extract(
                "epoch",
                WazuhVulnerability.last_seen - WazuhVulnerability.first_seen,
            )
            / 86400.0
        ).label("dwell_time_days")
        age_expression = (
            func.extract(
                "epoch",
                func.now() - WazuhVulnerability.first_seen,
            )
            / 86400.0
        ).label("total_age_days")

    query = db.query(
        WazuhVulnerability,
        dwell_time_expression,
        age_expression,
    ).options(
        joinedload(WazuhVulnerability.connection),
        selectinload(WazuhVulnerability.history),
    )
    if connection_id is not None:
        query = query.filter(WazuhVulnerability.connection_id == connection_id)
    query = query.order_by(
        WazuhVulnerability.last_seen.desc(),
        WazuhVulnerability.id.desc(),
    ).offset(offset)
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


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _serialize_event(event: VulnerabilityEvent) -> dict:
    return {
        "id": event.id,
        "event_time": event.event_time,
        "event_type": event.event_type,
        "vulnerability_id": event.vulnerability_id,
        "connection_id": event.connection_id,
        "agent_id": event.agent_id,
        "cve_id": event.cve_id,
        "severity": event.severity,
        "status": event.status,
        "details": event.details,
    }


@router.get("/events")
def list_events(
    connection_id: int = None,
    event_type: str = None,
    agent_id: str = None,
    cve_id: str = None,
    from_ts: datetime = Query(None, alias="from"),
    to_ts: datetime = Query(None, alias="to"),
    limit: int = Query(100, ge=0, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_enforcing_password_change),
):
    from_ts = _as_utc(from_ts)
    to_ts = _as_utc(to_ts)

    if engine.dialect.name == "postgresql":
        event_table = func.fn_vulnerability_events_in_range(
            connection_id,
            from_ts,
            to_ts,
        ).table_valued(
            column("id", BigInteger),
            column("event_time", DateTime(timezone=True)),
            column("event_type", String),
            column("vulnerability_id", Integer),
            column("connection_id", Integer),
            column("agent_id", String),
            column("cve_id", Text),
            column("severity", Text),
            column("status", Text),
            column("details", JSONB),
        ).alias("events")
        statement = select(event_table)
        if event_type is not None:
            statement = statement.where(event_table.c.event_type == event_type)
        if agent_id is not None:
            statement = statement.where(event_table.c.agent_id == agent_id)
        if cve_id is not None:
            statement = statement.where(event_table.c.cve_id == cve_id)
        statement = (
            statement.order_by(event_table.c.event_time.desc())
            .offset(offset)
            .limit(limit)
        )
        return [dict(row) for row in db.execute(statement).mappings().all()]

    query = db.query(VulnerabilityEvent)
    if connection_id is not None:
        query = query.filter(VulnerabilityEvent.connection_id == connection_id)
    if event_type is not None:
        query = query.filter(VulnerabilityEvent.event_type == event_type)
    if agent_id is not None:
        query = query.filter(VulnerabilityEvent.agent_id == agent_id)
    if cve_id is not None:
        query = query.filter(VulnerabilityEvent.cve_id == cve_id)
    if from_ts is not None:
        query = query.filter(VulnerabilityEvent.event_time >= from_ts)
    if to_ts is not None:
        query = query.filter(VulnerabilityEvent.event_time < to_ts)
    events = (
        query.order_by(VulnerabilityEvent.event_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_serialize_event(event) for event in events]


@router.get("/{vuln_id}/history")
def get_vuln_history(
    vuln_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_enforcing_password_change),
):
    vulnerability = db.get(WazuhVulnerability, vuln_id)
    if vulnerability is None:
        raise HTTPException(status_code=404, detail="Vulnerabilidad no encontrada")
    history = (
        db.query(VulnerabilityHistory)
        .filter(VulnerabilityHistory.vulnerability_id == vuln_id)
        .order_by(
            VulnerabilityHistory.timestamp.asc(),
            VulnerabilityHistory.id.asc(),
        )
        .all()
    )
    return [
        {
            "id": item.id,
            "action": item.action,
            "details": item.details,
            "timestamp": item.timestamp,
        }
        for item in history
    ]

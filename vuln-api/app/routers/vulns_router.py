# app/routers/vulns_router.py
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    case,
    column,
    exists,
    func,
    or_,
    select,
)
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
from ..services.wazuh_sync_service import (
    persist_vulnerability_events,
    process_wazuh_vulnerabilities,
)

router = APIRouter()


@router.post("/sync-all")
def sync_all_connections(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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

            event_rows: list[dict] = []
            count = process_wazuh_vulnerabilities(
                db, conn.id, raw_vulns, event_sink=event_rows
            )
            db.commit()
            if event_rows:
                background_tasks.add_task(
                    persist_vulnerability_events, db.get_bind(), event_rows
                )

            results.append({"connection": conn.name, "synced": count, "ok": True})
        except Exception as e:
            db.rollback()
            results.append({"connection": conn.name, "ok": False, "error": str(e)})

    return results


@router.get("")
def list_vulns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    connection_id: int | None = None,
    agent_name: list[str] | None = Query(None),
    package_name: list[str] | None = Query(None),
    cve_id: list[str] | None = Query(None),
    tags: list[str] | None = Query(None),
    severity: list[str] | None = Query(None),
    status: list[str] | None = Query(None),
    score_min: float | None = Query(None, ge=0, le=10),
    score_max: float | None = Query(None, ge=0, le=10),
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query("last_seen"),
    sort_dir: Literal["asc", "desc"] = Query("desc"),
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

    filters = []
    user_role = current_user.role or "admin"
    if user_role != "admin" and current_user.tags:
        user_tags = [t for t in current_user.tags if t]
        if user_tags:
            if engine.dialect.name == "postgresql":
                tag_table = func.json_array_elements_text(
                    WazuhVulnerability.tags
                ).table_valued("value").alias("user_tag")
            else:
                tag_table = func.json_each(
                    WazuhVulnerability.tags
                ).table_valued("value").alias("user_tag")
            filters.append(
                exists(
                    select(1)
                    .select_from(tag_table)
                    .where(tag_table.c.value.in_(user_tags))
                )
            )

    if connection_id is not None:
        filters.append(WazuhVulnerability.connection_id == connection_id)
    if agent_name:
        filters.append(WazuhVulnerability.agent_name.in_(agent_name))
    if package_name:
        filters.append(WazuhVulnerability.package_name.in_(package_name))
    if cve_id:
        filters.append(WazuhVulnerability.cve_id.in_(cve_id))
    if tags:
        tag_values = [tag for tag in tags if tag]
        if tag_values:
            if engine.dialect.name == "postgresql":
                tag_table = func.json_array_elements_text(
                    WazuhVulnerability.tags
                ).table_valued("value").alias("tag")
            else:
                tag_table = func.json_each(
                    WazuhVulnerability.tags
                ).table_valued("value").alias("tag")
            filters.append(
                exists(
                    select(1)
                    .select_from(tag_table)
                    .where(tag_table.c.value.in_(tag_values))
                )
            )
    if severity:
        severity_values = [value.lower() for value in severity if value]
        if severity_values:
            filters.append(func.lower(WazuhVulnerability.severity).in_(severity_values))
    if status:
        status_values = [value.lower() for value in status if value]
        if status_values:
            filters.append(func.lower(WazuhVulnerability.status).in_(status_values))
    if score_min is not None:
        filters.append(WazuhVulnerability.score_base >= score_min)
    if score_max is not None:
        filters.append(WazuhVulnerability.score_base <= score_max)
    if search and search.strip():
        term = f"%{_escape_like(search.strip())}%"
        filters.append(
            or_(
                WazuhVulnerability.cve_id.ilike(term, escape="\\"),
                WazuhVulnerability.agent_id.ilike(term, escape="\\"),
                WazuhVulnerability.agent_name.ilike(term, escape="\\"),
                WazuhVulnerability.package_name.ilike(term, escape="\\"),
                WazuhVulnerability.description.ilike(term, escape="\\"),
            )
        )
    date_from = _as_utc(date_from)
    date_to = _as_utc(date_to)
    if date_from is not None:
        filters.append(WazuhVulnerability.detected_at >= date_from)
    if date_to is not None:
        filters.append(WazuhVulnerability.detected_at < date_to)

    severity_rank = case(
        (func.lower(WazuhVulnerability.severity) == "critical", 4),
        (func.lower(WazuhVulnerability.severity) == "high", 3),
        (func.lower(WazuhVulnerability.severity) == "medium", 2),
        (func.lower(WazuhVulnerability.severity) == "low", 1),
        else_=0,
    )
    connection_name = (
        select(WazuhConnection.name)
        .where(WazuhConnection.id == WazuhVulnerability.connection_id)
        .scalar_subquery()
    )
    sort_columns = {
        "last_seen": WazuhVulnerability.last_seen,
        "first_seen": WazuhVulnerability.first_seen,
        "detected_at": WazuhVulnerability.detected_at,
        "published_at": WazuhVulnerability.published_at,
        "severity": severity_rank,
        "score_base": WazuhVulnerability.score_base,
        "cve_id": WazuhVulnerability.cve_id,
        "status": WazuhVulnerability.status,
        "agent_name": WazuhVulnerability.agent_name,
        "agent_id": WazuhVulnerability.agent_id,
        "package_name": WazuhVulnerability.package_name,
        "package_arch": WazuhVulnerability.package_arch,
        "os_full": func.coalesce(
            WazuhVulnerability.os_full,
            WazuhVulnerability.os_platform,
            "",
        ),
        "scanner_vendor": WazuhVulnerability.scanner_vendor,
        "connection_name": connection_name,
        "dwell_time_days": dwell_time_expression,
        "total_age_days": age_expression,
        "tags": func.json_array_length(WazuhVulnerability.tags),
    }
    order_column = sort_columns.get(sort_by)
    if order_column is None:
        raise HTTPException(status_code=422, detail="sort_by inválido")
    order = order_column.asc() if sort_dir == "asc" else order_column.desc()

    total = db.query(WazuhVulnerability).filter(*filters).count()
    results = (
        db.query(
            WazuhVulnerability,
            dwell_time_expression,
            age_expression,
        )
        .options(
            joinedload(WazuhVulnerability.connection),
            selectinload(WazuhVulnerability.history),
        )
        .filter(*filters)
        .order_by(order, WazuhVulnerability.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
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
        ],
    }


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


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

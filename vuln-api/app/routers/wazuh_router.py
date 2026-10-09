# app/routers/wazuh_router.py
import os
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..db import get_db
from ..models import User, WazuhConnection
from ..auth import get_current_user_enforcing_password_change
from ..clients.wazuh_client import test_connection, fetch_all_vulns
from ..crypto import encrypt, decrypt
from ..schemas.wazuh_schemas import WazuhConnectionRequest
from ..services.wazuh_sync_service import process_wazuh_vulnerabilities

router = APIRouter()

CONNECTION_NOT_FOUND = "Conexión no encontrada"
DOMAINS_ALLOWLIST = [
    domain.strip()
    for domain in os.getenv("DOMAINS_ALLOWLIST", "localhost").split(",")
    if domain.strip()
]


@router.get("")
def list_connections(
    current_user: User = Depends(get_current_user_enforcing_password_change), db: Session = Depends(get_db)
):
    conns = db.query(WazuhConnection).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "indexer_url": c.indexer_url,
            "wazuh_user": c.wazuh_user,
            "is_active": c.is_active,
            "tested": c.tested,
            "last_tested_at": c.last_tested_at,
            "last_test_ok": c.last_test_ok,
        }
        for c in conns
    ]


@router.post("", status_code=201)
def create_connection(
    request: WazuhConnectionRequest,
    current_user: User = Depends(get_current_user_enforcing_password_change),
    db: Session = Depends(get_db),
):
    # verify unique name
    if db.query(WazuhConnection).filter(WazuhConnection.name == request.name).first():
        raise HTTPException(
            status_code=400, detail="Ya existe una conexión con ese nombre"
        )

    # verify SSRF
    hostname = urlparse(request.indexer_url).hostname
    if hostname not in DOMAINS_ALLOWLIST:
        raise HTTPException(
            status_code=400, detail="El dominio del indexador no está en la lista de permitidos"
        )

    # try to connect before persisting
    ok = test_connection(request.indexer_url, request.wazuh_user, request.wazuh_password)
    if not ok:
        # do not store invalid configuration
        raise HTTPException(
            status_code=400,
            detail="No se pudo establecer conexión con el indexador Wazuh",
        )

    conn = WazuhConnection(
        name=request.name,
        indexer_url=request.indexer_url,
        wazuh_user=request.wazuh_user,
        wazuh_password=encrypt(request.wazuh_password),
        tested=True,
        last_tested_at=func.now(),
        last_test_ok=True,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return {"message": "Conexión creada", "id": conn.id}


@router.put("/{conn_id}")
def update_connection(
    conn_id: int,
    request: WazuhConnectionRequest,
    current_user: User = Depends(get_current_user_enforcing_password_change),
    db: Session = Depends(get_db),
):
    conn = db.query(WazuhConnection).filter(WazuhConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail=CONNECTION_NOT_FOUND)

    hostname = urlparse(request.indexer_url).hostname
    if hostname not in DOMAINS_ALLOWLIST:
        raise HTTPException(
            status_code=400, detail="El dominio del indexador no está en la lista de permitidos"
        )

    conn.name = request.name
    conn.indexer_url = request.indexer_url
    conn.wazuh_user = request.wazuh_user
    if request.wazuh_password:
        conn.wazuh_password = encrypt(request.wazuh_password)
    db.commit()
    return {"message": "Conexión actualizada"}


@router.delete("/{conn_id}")
def delete_connection(
    conn_id: int,
    current_user: User = Depends(get_current_user_enforcing_password_change),
    db: Session = Depends(get_db),
):
    conn = db.query(WazuhConnection).filter(WazuhConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail=CONNECTION_NOT_FOUND)
    db.delete(conn)
    db.commit()
    return {"message": "Conexión eliminada"}


@router.post("/{conn_id}/test")
def test_wazuh_connection(
    conn_id: int,
    current_user: User = Depends(get_current_user_enforcing_password_change),
    db: Session = Depends(get_db),
):
    conn = db.query(WazuhConnection).filter(WazuhConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail=CONNECTION_NOT_FOUND)

    ok = test_connection(
        conn.indexer_url, conn.wazuh_user, decrypt(conn.wazuh_password)
    )

    conn.tested = True
    conn.last_tested_at = func.now()
    conn.last_test_ok = ok
    db.commit()

    return {"ok": ok, "message": "Conexión exitosa" if ok else "No se pudo conectar"}


@router.post("/{conn_id}/sync")
def sync_connection(
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_enforcing_password_change),
):
    conn = db.query(WazuhConnection).filter(WazuhConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail=CONNECTION_NOT_FOUND)
    if not conn.is_active:
        raise HTTPException(status_code=400, detail="La conexión está inactiva")

    raw_vulns = fetch_all_vulns(
        conn.indexer_url, conn.wazuh_user, decrypt(conn.wazuh_password)
    )

    count = process_wazuh_vulnerabilities(db, conn.id, raw_vulns)
    db.commit()

    return {"synced": count, "connection": conn.name}

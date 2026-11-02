import pytest
import os
from datetime import datetime, timedelta, timezone
os.environ["ENCRYPTION_KEY"] = "V3pXU0Y1ZzV3S09SclpIbmVyeXpZREp3Y0p6S2pYUTQ="
from unittest.mock import patch
from app.models import (
    User,
    VulnerabilityEvent,
    VulnerabilityHistory,
    WazuhConnection,
    WazuhVulnerability,
)
from app.auth import hash_password
from app.crypto import encrypt
from app.services.wazuh_sync_service import persist_vulnerability_events


#helpers

def _create_user(db, username="admin", password="admin", is_active=True, is_default_password=False, role="admin"):
    user = User(username=username, password_hash=hash_password(password), is_active=is_active, is_default_password=is_default_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _get_headers(client, username="admin", password="admin"):
    res = client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_connection(db, name="test-conn", is_active=True):
    conn = WazuhConnection(
        name=name,
        indexer_url="https://wazuh.local:9200",
        wazuh_user="admin",
        wazuh_password=encrypt("secret"),
        is_active=is_active,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def _create_vuln(
    db,
    conn,
    cve,
    severity="High",
    status="ACTIVE",
    agent_id="001",
    agent_name="host-1",
    package_name="pkg",
    package_version="1.0",
    detected_at=None,
    score_base=None,
    tags=None,
):
    detected_at = detected_at or datetime.now(timezone.utc)
    vuln = WazuhVulnerability(
        connection_id=conn.id,
        status=status,
        agent_id=agent_id,
        agent_name=agent_name,
        package_name=package_name,
        package_version=package_version,
        cve_id=cve,
        severity=severity,
        score_base=score_base,
        tags=tags or [],
        detected_at=detected_at,
        first_seen=detected_at,
        last_seen=detected_at,
    )
    db.add(vuln)
    db.commit()
    db.refresh(vuln)
    return vuln


def _raw_vuln(cve="CVE-2023-9999", severity="High"):
    return [{
        "agent": {"id": "001", "name": "host-1", "groups": ["linux"]},
        "host": {"os": {"full": "Ubuntu 22.04", "platform": "ubuntu", "version": "22.04"}},
        "package": {"name": "curl", "version": "7.81", "type": "deb", "architecture": "amd64"},
        "tags": ["prod"],
        "vulnerability": {
            "id": cve, "severity": severity,
            "score": {"base": 6.0, "version": "3.1"},
            "detected_at": None, "published_at": None,
            "description": "desc", "reference": "https://ref",
            "scanner": {"vendor": "wazuh"},
        },
    }]


MOCK_VULN = [
    {
        "agent": {"id": "001", "name": "agent-1"},
        "host": {"os": {"full": "Ubuntu 22.04", "platform": "ubuntu", "version": "22.04"}},
        "package": {"name": "openssl", "version": "1.1.1", "type": "deb", "architecture": "amd64"},
        "vulnerability": {
            "id": "CVE-2023-0001", "severity": "High",
            "score": {"base": 7.5, "version": "3.1"},
            "detected_at": None, "published_at": None,
            "description": "Test vuln", "reference": "https://nvd.nist.gov",
            "scanner": {"vendor": "wazuh"},
        },
    }
]


#auth

def test_login_fail(client):
    response = client.post("/auth/login", data={"username": "wrong", "password": "password"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"

def test_login_inactive_user(client, db_session):
    _create_user(db_session, is_active=False) 
    res = client.post("/auth/login", data={"username": "admin", "password": "admin"})
    assert res.status_code == 400

def test_login_success(client, db_session):
    _create_user(db_session)
    res = client.post("/auth/login", data={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_unknown_user(client):
    res = client.post("/auth/login", data={"username": "ghost", "password": "x"})
    assert res.status_code == 400


def test_protected_route_without_token(client):
    assert client.get("/users/me").status_code == 401


def test_protected_route_invalid_token(client):
    res = client.get("/users/me", headers={"Authorization": "Bearer token.invalido"})
    assert res.status_code == 401


def test_sync_vulnerabilities_unauthorized(client, db_session):
    conn = _create_connection(db_session)
    response = client.post(f"/wazuh-connections/{conn.id}/sync")
    assert response.status_code == 401


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_sync_vulnerabilities_success(mock_fetch, client, db_session):
    from app.auth import hash_password
    test_user = User(username="admin", password_hash=hash_password("admin"), is_active=True, is_default_password=False, role="admin")
    db_session.add(test_user)
    conn = WazuhConnection(
        name="test", indexer_url="https://wazuh.local:9200",
        wazuh_user="admin", wazuh_password=encrypt("secret"), is_active=True,
    )
    db_session.add(conn)
    db_session.commit()

    login_res = client.post("/auth/login", data={"username": "admin", "password": "admin"})
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    mock_fetch.return_value = [{
        "agent": {"id": "001", "name": "test-agent"},
        "host": {"os": {"full": "Ubuntu 22.04", "platform": "ubuntu", "version": "22.04"}},
        "package": {"name": "openssl", "version": "1.1.1", "type": "deb", "architecture": "amd64"},
        "vulnerability": {
            "id": "CVE-2023-1234", "severity": "High",
            "score": {"base": 7.5, "version": "3.1"},
            "detected_at": None, "published_at": None,
            "description": "Test", "reference": "https://nvd.nist.gov",
            "scanner": {"vendor": "wazuh"},
        },
    }]

    sync_res = client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    assert sync_res.status_code == 200
    assert sync_res.json()["synced"] == 1

    get_res = client.get("/vulns", headers=headers)
    payload = get_res.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 50
    assert len(payload["items"]) == 1
    vuln_item = payload["items"][0]
    assert vuln_item["cve_id"] == "CVE-2023-1234"
    # new requirement: response should include origin connection name
    assert vuln_item.get("connection_name") == "test"
    assert [h["action"] for h in vuln_item["history"]] == ["DETECTED"]
    # Verifica que first_seen y last_seen existen y son iguales al crear
    assert vuln_item["first_seen"] is not None
    assert vuln_item["last_seen"] is not None
    assert vuln_item["first_seen"] == vuln_item["last_seen"]


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_sync_vulnerabilities_allows_authenticated_viewer(mock_fetch, client, db_session):
    _create_user(db_session, username="viewer", password="viewer", role="viewer")
    conn = _create_connection(db_session)
    mock_fetch.return_value = _raw_vuln()

    response = client.post(
        f"/wazuh-connections/{conn.id}/sync?agent_id=001",
        headers=_get_headers(client, username="viewer", password="viewer"),
    )

    assert response.status_code == 200
    assert response.json()["agent_id"] == "001"


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_sync_persists_vulnerability_metadata(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))

    db_session.expire_all()
    vuln = db_session.query(WazuhVulnerability).one()
    assert vuln.agent_name == "host-1"
    assert vuln.package_name == "curl"
    assert vuln.package_version == "7.81"
    assert vuln.severity == "High"
    assert float(vuln.score_base) == 6.0
    assert vuln.tags == ["prod", "linux"]
    assert vuln.last_seen is not None


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_sync_updates_existing_metadata(mock_fetch, client, db_session):
    first = _raw_vuln(severity="Low")
    first[0]["agent"]["name"] = "host-before"
    first[0]["tags"] = ["old"]
    mock_fetch.return_value = first
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)

    second = _raw_vuln(severity="Critical")
    second[0]["agent"]["name"] = "host-after"
    second[0]["tags"] = ["new"]
    mock_fetch.return_value = second
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)

    db_session.expire_all()
    vuln = db_session.query(WazuhVulnerability).one()
    assert vuln.agent_name == "host-after"
    assert vuln.severity == "Critical"
    assert float(vuln.score_base) == 6.0
    assert vuln.tags == ["new", "linux"]
    assert db_session.query(WazuhVulnerability).count() == 1


def test_change_password_success(client, db_session):
    _create_user(db_session)
    client.post("/auth/change-password",
                json={"old_password": "admin", "new_password": "Nueva123!", "confirm_password": "Nueva123!"},
                headers=_get_headers(client))
    res = client.post("/auth/login", data={"username": "admin", "password": "Nueva123!"})
    assert res.status_code == 200


def test_change_password_wrong_old(client, db_session):
    _create_user(db_session)
    res = client.post("/auth/change-password",
                      json={"old_password": "incorrecta", "new_password": "Nueva123!", "confirm_password": "Nueva123!"},
                      headers=_get_headers(client))
    assert res.status_code == 400


def test_change_password_same_as_old(client, db_session):
    _create_user(db_session)
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "admin", "confirm_password": "admin"},
                      headers=_get_headers(client))
    assert res.status_code == 400


def test_change_password_unauthenticated(client):
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "Nueva123!", "confirm_password": "Nueva123!"})
    assert res.status_code == 401

def test_change_password_mismatch(client, db_session):
    _create_user(db_session)
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "Nueva123!", "confirm_password": "Otra456!"},
                      headers=_get_headers(client))
    assert res.status_code == 400


def test_login_rate_limiting(client, db_session):
    _create_user(db_session, username="bruteforce_user")
    for _ in range(5):
        client.post("/auth/login", data={"username": "bruteforce_user", "password": "wrong"})
    res = client.post("/auth/login", data={"username": "bruteforce_user", "password": "wrong"})
    assert res.status_code == 429


def test_change_password_weak_password_length(client, db_session):
    _create_user(db_session, username="weak_user")
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "Short1!", "confirm_password": "Short1!"},
                      headers=_get_headers(client, username="weak_user", password="admin"))
    assert res.status_code == 400


def test_change_password_weak_password_no_uppercase(client, db_session):
    _create_user(db_session, username="weak_user2")
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "lowercase1!", "confirm_password": "lowercase1!"},
                      headers=_get_headers(client, username="weak_user2", password="admin"))
    assert res.status_code == 400


def test_change_password_weak_password_no_lowercase(client, db_session):
    _create_user(db_session, username="weak_user3")
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "UPPERCASE1!", "confirm_password": "UPPERCASE1!"},
                      headers=_get_headers(client, username="weak_user3", password="admin"))
    assert res.status_code == 400


def test_change_password_weak_password_no_number(client, db_session):
    _create_user(db_session, username="weak_user4")
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "NoNumberABC!", "confirm_password": "NoNumberABC!"},
                      headers=_get_headers(client, username="weak_user4", password="admin"))
    assert res.status_code == 400


def test_change_password_weak_password_no_special(client, db_session):
    _create_user(db_session, username="weak_user5")
    res = client.post("/auth/change-password",
                      json={"old_password": "admin", "new_password": "NoSpecial123", "confirm_password": "NoSpecial123"},
                      headers=_get_headers(client, username="weak_user5", password="admin"))
    assert res.status_code == 400

#users me

def test_get_me(client, db_session):
    _create_user(db_session)
    res = client.get("/users/me", headers=_get_headers(client))
    assert res.status_code == 200
    assert res.json()["username"] == "admin"
    assert res.json()["is_active"] is True


def test_get_me_is_active_false_after_deactivation(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client) 
    me = client.get("/users/me", headers=headers).json()

    user = db_session.query(User).filter_by(id=me["id"]).first()
    user.is_active = False
    db_session.commit()

    res = client.get("/users/me", headers=headers) 
    assert res.json()["is_active"] is False 


#users crud

def test_create_user(client, db_session):
    _create_user(db_session)
    res = client.post("/users", json={"username": "nuevo", "password": "pass123"},
                      headers=_get_headers(client))
    assert res.status_code == 200


def test_create_user_duplicate(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client)
    client.post("/users", json={"username": "dup", "password": "x"}, headers=headers)
    res = client.post("/users", json={"username": "dup", "password": "y"}, headers=headers)
    assert res.status_code == 400


def test_create_user_unauthenticated(client):
    assert client.post("/users", json={"username": "x", "password": "y"}).status_code == 401


def test_list_users(client, db_session):
    _create_user(db_session)
    res = client.get("/users", headers=_get_headers(client))
    assert res.status_code == 200
    assert any(u["username"] == "admin" for u in res.json())


def test_delete_user(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client)
    client.post("/users", json={"username": "todelete", "password": "x"}, headers=headers)
    users = client.get("/users", headers=headers).json()
    target_id = next(u["id"] for u in users if u["username"] == "todelete")
    assert client.delete(f"/users/{target_id}", headers=headers).status_code == 200


def test_delete_self_forbidden(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client)
    me = client.get("/users/me", headers=headers).json()
    assert client.delete(f"/users/{me['id']}", headers=headers).status_code == 400


def test_delete_nonexistent_user(client, db_session):
    _create_user(db_session)
    assert client.delete("/users/9999", headers=_get_headers(client)).status_code == 404


def test_update_user(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client)
    client.post("/users", json={"username": "toupdate", "password": "x"}, headers=headers)
    users = client.get("/users", headers=headers).json()
    target_id = next(u["id"] for u in users if u["username"] == "toupdate")

    # Update role, tags, is_active
    res = client.put(f"/users/{target_id}", json={"role": "viewer", "tags": ["prod"], "is_active": True}, headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Usuario actualizado exitosamente"

    # Verify updated values
    updated_users = client.get("/users", headers=headers).json()
    updated = next(u for u in updated_users if u["id"] == target_id)
    assert updated["role"] == "viewer"
    assert updated["tags"] == ["prod"]

    # 404 for non-existent user
    assert client.put("/users/9999", json={"role": "viewer"}, headers=headers).status_code == 404



# wazuh connections

def test_list_connections_empty(client, db_session):
    _create_user(db_session)
    res = client.get("/wazuh-connections", headers=_get_headers(client))
    assert res.status_code == 200
    assert res.json() == []


@patch("app.routers.wazuh_router.test_connection", return_value=True)
def test_create_connection(mock_test, client, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.wazuh_router.DOMAINS_ALLOWLIST", ["localhost", "wazuh.local"])
    # the endpoint should automatically verify the Wazuh connection
    _create_user(db_session)
    payload = {"name": "prod", "indexer_url": "https://wazuh.local:9200",
               "wazuh_user": "admin", "wazuh_password": "secret"}
    res = client.post("/wazuh-connections", json=payload, headers=_get_headers(client))
    assert res.status_code == 201
    # verify that test_connection was called with provided credentials
    mock_test.assert_called_once_with(payload["indexer_url"], payload["wazuh_user"], payload["wazuh_password"])


def test_create_connection_duplicate_name(client, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.wazuh_router.DOMAINS_ALLOWLIST", ["localhost", "wazuh.local"])
    _create_user(db_session)
    headers = _get_headers(client)
    payload = {"name": "dup", "indexer_url": "https://wazuh.local:9200", "wazuh_user": "u", "wazuh_password": "p"}
    client.post("/wazuh-connections", json=payload, headers=headers)
    assert client.post("/wazuh-connections", json=payload, headers=headers).status_code == 400

@patch("app.routers.wazuh_router.test_connection", return_value=False)
def test_create_connection_fails_when_unreachable(mock_test, client, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.wazuh_router.DOMAINS_ALLOWLIST", ["localhost", "wazuh.local"])
    _create_user(db_session)
    payload = {"name": "bad", "indexer_url": "https://wazuh.local:9200", "wazuh_user": "u", "wazuh_password": "p"}
    res = client.post("/wazuh-connections", json=payload, headers=_get_headers(client))
    assert res.status_code == 400
    assert "No se pudo establecer conexión" in res.json()["detail"]
    mock_test.assert_called_once()


def test_update_connection(client, db_session, monkeypatch):
    monkeypatch.setattr("app.routers.wazuh_router.DOMAINS_ALLOWLIST", ["localhost", "wazuh.local"])
    _create_user(db_session)
    conn = _create_connection(db_session)
    res = client.put(f"/wazuh-connections/{conn.id}",
                     json={"name": "updated", "indexer_url": "https://wazuh.local:9200",
                           "wazuh_user": "newuser", "wazuh_password": "newpass"},
                     headers=_get_headers(client))
    assert res.status_code == 200


def test_update_nonexistent_connection(client, db_session):
    _create_user(db_session)
    res = client.put("/wazuh-connections/9999",
                     json={"name": "x", "indexer_url": "https://wazuh.local:9200", "wazuh_user": "x", "wazuh_password": "x"},
                     headers=_get_headers(client))
    assert res.status_code == 404


def test_delete_connection(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    assert client.delete(f"/wazuh-connections/{conn.id}", headers=_get_headers(client)).status_code == 200


def test_delete_connection_with_vulnerabilities(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vulns = [
        _create_vuln(db_session, conn, "CVE-2023-0001"),
        _create_vuln(db_session, conn, "CVE-2023-0002", agent_id="002"),
    ]
    for vuln in vulns:
        db_session.add(VulnerabilityHistory(
            vulnerability_id=vuln.id,
            action="DETECTED",
            details="test",
        ))
    db_session.commit()

    res = client.delete(
        f"/wazuh-connections/{conn.id}",
        headers=_get_headers(client),
    )

    assert res.status_code == 200
    assert db_session.query(WazuhVulnerability).count() == 0
    assert db_session.query(VulnerabilityHistory).count() == 0


def test_delete_nonexistent_connection(client, db_session):
    _create_user(db_session)
    assert client.delete("/wazuh-connections/9999", headers=_get_headers(client)).status_code == 404


@patch("app.routers.wazuh_router.test_connection", return_value=True)
def test_test_connection_ok(mock_test, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    res = client.post(f"/wazuh-connections/{conn.id}/test", headers=_get_headers(client))
    assert res.json()["ok"] is True


@patch("app.routers.wazuh_router.test_connection", return_value=False)
def test_test_connection_fail(mock_test, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    res = client.post(f"/wazuh-connections/{conn.id}/test", headers=_get_headers(client))
    assert res.json()["ok"] is False


def test_test_nonexistent_connection(client, db_session):
    _create_user(db_session)
    assert client.post("/wazuh-connections/9999/test", headers=_get_headers(client)).status_code == 404


# sync per conn

@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_sync_connection_success(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    res = client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))
    assert res.status_code == 200
    assert res.json()["synced"] == 1


def test_sync_inactive_connection(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session, is_active=False)
    assert client.post(f"/wazuh-connections/{conn.id}/sync",
                       headers=_get_headers(client)).status_code == 400


def test_sync_nonexistent_connection(client, db_session):
    _create_user(db_session)
    assert client.post("/wazuh-connections/9999/sync",
                       headers=_get_headers(client)).status_code == 404


@patch("app.routers.wazuh_router.fetch_all_vulns", side_effect=Exception("unreachable"))
def test_sync_failure_preserves_existing_vulns(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vuln = _create_vuln(db_session, conn, "CVE-2023-0001")
    headers = _get_headers(client)

    res = client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)

    assert res.status_code == 502
    db_session.refresh(vuln)
    assert vuln.status == "ACTIVE"


@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=[])
def test_sync_empty_payload_preserves_existing_vulns(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vuln = _create_vuln(db_session, conn, "CVE-2023-0001")
    headers = _get_headers(client)

    res = client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)

    assert res.status_code == 409
    db_session.refresh(vuln)
    assert vuln.status == "ACTIVE"


@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=[])
def test_agent_sync_does_not_resolve_other_agents(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    target = _create_vuln(db_session, conn, "CVE-2023-0001", agent_id="001")
    other = _create_vuln(db_session, conn, "CVE-2023-0002", agent_id="002")
    headers = _get_headers(client)

    res = client.post(
        f"/wazuh-connections/{conn.id}/sync?agent_id=001&allow_empty=true",
        headers=headers,
    )

    assert res.status_code == 200
    mock_fetch.assert_called_once_with(
        conn.indexer_url, conn.wazuh_user, "secret", agent_id="001"
    )
    db_session.refresh(target)
    db_session.refresh(other)
    assert target.status == "RESOLVED"
    assert other.status == "ACTIVE"


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_agent_sync_ignores_payload_for_other_agents(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    target = _create_vuln(
        db_session,
        conn,
        "CVE-2023-0001",
        agent_id="001",
        package_name="openssl",
        package_version="1.1.1",
    )
    other = _create_vuln(
        db_session,
        conn,
        "CVE-2023-0002",
        agent_id="002",
        status="RESOLVED",
        package_name="curl",
        package_version="7.81",
    )
    raw_other = _raw_vuln("CVE-2023-0002")
    raw_other[0]["agent"]["id"] = "002"
    raw_other[0]["agent"]["name"] = "host-2"
    mock_fetch.return_value = MOCK_VULN + raw_other

    res = client.post(
        f"/wazuh-connections/{conn.id}/sync?agent_id=001",
        headers=_get_headers(client),
    )

    assert res.status_code == 200
    db_session.refresh(target)
    db_session.refresh(other)
    assert target.status == "ACTIVE"
    assert other.status == "RESOLVED"


@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=[])
def test_sync_empty_payload_without_active_inventory(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vuln = _create_vuln(
        db_session, conn, "CVE-2023-0001", agent_id="001", status="RESOLVED"
    )

    res = client.post(
        f"/wazuh-connections/{conn.id}/sync?agent_id=001",
        headers=_get_headers(client),
    )

    assert res.status_code == 200
    assert res.json()["synced"] == 0
    db_session.refresh(vuln)
    assert vuln.status == "RESOLVED"


@patch(
    "app.routers.wazuh_router.process_wazuh_vulnerabilities",
    side_effect=RuntimeError("boom"),
)
@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_sync_unexpected_error_rolls_back(mock_fetch, mock_process, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vuln = _create_vuln(db_session, conn, "CVE-2023-0001")

    with pytest.raises(RuntimeError, match="boom"):
        client.post(
            f"/wazuh-connections/{conn.id}/sync",
            headers=_get_headers(client),
        )

    db_session.refresh(vuln)
    assert vuln.status == "ACTIVE"


# sync all

@patch("app.routers.vulns_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_sync_all_success(mock_fetch, client, db_session):
    _create_user(db_session)
    _create_connection(db_session, name="conn-1")
    _create_connection(db_session, name="conn-2")
    res = client.post("/vulns/sync-all", headers=_get_headers(client))
    assert len(res.json()) == 2
    assert all(r["ok"] for r in res.json())


@patch("app.routers.vulns_router.fetch_all_vulns", side_effect=Exception("unreachable"))
def test_sync_all_partial_failure(mock_fetch, client, db_session):
    _create_user(db_session)
    _create_connection(db_session)
    result = client.post("/vulns/sync-all", headers=_get_headers(client)).json()[0]
    assert result["ok"] is False


@patch("app.routers.vulns_router.fetch_all_vulns", return_value=[])
def test_sync_all_empty_payload_preserves_inventory(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    vuln = _create_vuln(db_session, conn, "CVE-2023-0001")

    result = client.post("/vulns/sync-all", headers=_get_headers(client)).json()[0]

    assert result["ok"] is False
    db_session.refresh(vuln)
    assert vuln.status == "ACTIVE"


def test_sync_all_skips_inactive(client, db_session):
    _create_user(db_session)
    _create_connection(db_session, is_active=False)
    assert client.post("/vulns/sync-all", headers=_get_headers(client)).json() == []


def test_sync_all_unauthenticated(client):
    assert client.post("/vulns/sync-all").status_code == 401


# vulns list

def test_list_vulns_empty(client, db_session):
    _create_user(db_session)
    assert client.get("/vulns", headers=_get_headers(client)).json() == {
        "total": 0,
        "page": 1,
        "page_size": 50,
        "items": [],
    }


def test_list_vulns_unauthenticated(client):
    assert client.get("/vulns").status_code == 401


@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_list_vulns_paginates(mock_fetch, client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))
    headers = _get_headers(client)

    first = client.get("/vulns?page=1&page_size=1", headers=headers).json()
    second = client.get("/vulns?page=2&page_size=1", headers=headers).json()
    assert first["total"] == 1
    assert len(first["items"]) == 1
    assert len(second["items"]) == 0
    assert client.get("/vulns?page=0", headers=headers).status_code == 422
    assert client.get("/vulns?page_size=501", headers=headers).status_code == 422


def test_list_vulns_filters(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    other = _create_connection(db_session, name="other")
    now = datetime.now(timezone.utc)
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-0001",
        agent_name="host-one",
        package_name="openssl",
        detected_at=now - timedelta(days=2),
    )
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-0002",
        severity="Low",
        agent_name="host-two",
        package_name="curl",
        detected_at=now - timedelta(days=1),
    )
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-0003",
        status="RESOLVED",
        agent_name="host-three",
        package_name="openssl",
        detected_at=now,
    )
    _create_vuln(db_session, other, "CVE-2026-0004", agent_name="host-one")
    headers = _get_headers(client)

    assert client.get("/vulns", headers=headers).json()["total"] == 4
    assert client.get(
        f"/vulns?connection_id={conn.id}", headers=headers
    ).json()["total"] == 3
    assert client.get("/vulns?severity=High", headers=headers).json()["total"] == 3
    assert client.get("/vulns?status=RESOLVED", headers=headers).json()["total"] == 1
    assert client.get("/vulns?search=openssl", headers=headers).json()["total"] == 2
    assert client.get("/vulns?search=host-two", headers=headers).json()["total"] == 1
    cutoff = (now - timedelta(hours=12)).isoformat()
    assert client.get("/vulns", params={"date_from": cutoff}, headers=headers).json()["total"] == 2
    assert client.get("/vulns", params={"date_to": cutoff}, headers=headers).json()["total"] == 2


def test_list_vulns_advanced_filters(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-1001",
        severity="High",
        agent_name="agent-a",
        package_name="openssl",
        score_base=9.8,
        tags=["prod"],
    )
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-1002",
        severity="Low",
        status="RESOLVED",
        agent_name="agent-b",
        package_name="curl",
        score_base=3.1,
        tags=["dev"],
    )
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-1003",
        severity="Medium",
        agent_name="agent-a",
        package_name="curl",
        tags=["prod", "dev"],
    )
    headers = _get_headers(client)

    def total(query):
        return client.get(f"/vulns?{query}", headers=headers).json()["total"]

    assert total("agent_name=agent-a") == 2
    assert total("package_name=curl") == 2
    assert total("cve_id=CVE-2026-1002") == 1
    assert total("tags=prod") == 2
    assert total("tags=prod&tags=dev") == 3
    assert total("severity=HIGH") == 1
    assert total("status=resolved") == 1
    assert total("score_min=8") == 1
    assert total("score_max=5") == 1
    assert total("agent_name=agent-a&package_name=curl") == 1


def test_list_vulns_search_escapes_wildcards(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    _create_vuln(db_session, conn, "CVE-2026-2001", agent_name="host-one")
    _create_vuln(db_session, conn, "CVE-2026-2002", agent_name="host%one")
    _create_vuln(db_session, conn, "CVE-2026-2003", agent_name="host_one")
    headers = _get_headers(client)

    percent = client.get(
        "/vulns", params={"search": "host%one"}, headers=headers
    ).json()
    underscore = client.get(
        "/vulns", params={"search": "host_one"}, headers=headers
    ).json()
    assert percent["total"] == 1
    assert underscore["total"] == 1


def test_list_vulns_sorting(client, db_session):
    _create_user(db_session)
    conn = _create_connection(db_session)
    other = _create_connection(db_session, name="zzz")
    _create_vuln(
        db_session,
        conn,
        "CVE-2026-3001",
        severity="Low",
        score_base=3.0,
    )
    _create_vuln(
        db_session,
        other,
        "CVE-2026-3002",
        severity="Critical",
        score_base=9.0,
    )
    headers = _get_headers(client)

    by_score = client.get(
        "/vulns?sort_by=score_base&sort_dir=desc", headers=headers
    ).json()["items"]
    by_cve = client.get(
        "/vulns?sort_by=cve_id&sort_dir=asc", headers=headers
    ).json()["items"]
    by_severity = client.get(
        "/vulns?sort_by=severity&sort_dir=desc", headers=headers
    ).json()["items"]
    by_connection = client.get(
        "/vulns?sort_by=connection_name&sort_dir=asc", headers=headers
    ).json()["items"]

    assert [item["cve_id"] for item in by_score] == [
        "CVE-2026-3002",
        "CVE-2026-3001",
    ]
    assert [item["cve_id"] for item in by_cve] == [
        "CVE-2026-3001",
        "CVE-2026-3002",
    ]
    assert [item["cve_id"] for item in by_severity] == [
        "CVE-2026-3002",
        "CVE-2026-3001",
    ]
    assert by_connection[0]["connection_name"] == "test-conn"
    assert client.get("/vulns?sort_by=bogus", headers=headers).status_code == 422
    assert client.get("/vulns?sort_dir=sideways", headers=headers).status_code == 422


@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_list_vulns_shows_connection_name(mock_fetch, client, db_session):
    # newly added test ensures connection_name field is returned
    _create_user(db_session)
    conn = _create_connection(db_session, name="myconn")
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))
    res_list = client.get("/vulns", headers=_get_headers(client)).json()
    assert len(res_list["items"]) == 1
    assert res_list["items"][0].get("connection_name") == "myconn"


# fetch vulns

def test_persist_events_empty_is_noop():
    persist_vulnerability_events(object(), [])


@patch("app.services.wazuh_sync_service.Session")
def test_persist_events_failure_is_logged(mock_session):
    db = mock_session.return_value
    db.commit.side_effect = RuntimeError("boom")

    persist_vulnerability_events(object(), [{"event_type": "DETECTED"}])

    db.rollback.assert_called_once()
    db.close.assert_called_once()


@patch("app.routers.wazuh_router.persist_vulnerability_events")
@patch("app.routers.wazuh_router.fetch_all_vulns", return_value=MOCK_VULN)
def test_sync_schedules_event_persistence(
    mock_fetch, mock_persist, client, db_session
):
    _create_user(db_session)
    conn = _create_connection(db_session)

    res = client.post(
        f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client)
    )

    assert res.status_code == 200
    assert mock_persist.call_count == 1
    _, events = mock_persist.call_args.args
    assert events[0]["event_type"] == "DETECTED"


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_new_vuln_creates_detected_history(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))
    actions = [h.action for h in db_session.query(VulnerabilityHistory).all()]
    assert "DETECTED" in actions
    event_types = [
        e.event_type for e in db_session.query(VulnerabilityEvent).all()
    ]
    assert event_types == ["DETECTED"]


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_resolved_vuln_gets_reopened(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    vuln = db_session.query(WazuhVulnerability).first()
    vuln.status = "RESOLVED"
    db_session.commit()
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    db_session.refresh(vuln)
    assert vuln.status == "ACTIVE"
    actions = [h.action for h in db_session.query(VulnerabilityHistory).all()]
    assert "REOPENED" in actions
    event_types = [
        e.event_type for e in db_session.query(VulnerabilityEvent).all()
    ]
    assert event_types.count("REOPENED") == 1
    # Verifica que last_seen se actualiza pero first_seen no cambia
    assert vuln.first_seen is not None
    assert vuln.last_seen is not None
    assert vuln.last_seen >= vuln.first_seen


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_vuln_resolved_when_absent_from_payload(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    mock_fetch.return_value = []
    client.post(
        f"/wazuh-connections/{conn.id}/sync?allow_empty=true",
        headers=headers,
    )
    vuln = db_session.query(WazuhVulnerability).first()
    assert vuln.status == "RESOLVED"
    event_types = [
        e.event_type for e in db_session.query(VulnerabilityEvent).all()
    ]
    assert event_types.count("RESOLVED") == 1


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_severity_change_logged_in_history(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln(severity="Low")
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    mock_fetch.return_value = _raw_vuln(severity="Critical")
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    actions = [h.action for h in db_session.query(VulnerabilityHistory).all()]
    assert "SEVERITY_CHANGED" in actions
    event_types = [
        e.event_type for e in db_session.query(VulnerabilityEvent).all()
    ]
    assert event_types.count("SEVERITY_CHANGED") == 1


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_repeated_sync_does_not_duplicate_events(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    events = db_session.query(VulnerabilityEvent).all()
    assert len(events) == 1
    assert events[0].event_type == "DETECTED"


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_vuln_events_and_history_endpoints(mock_fetch, client, db_session):
    mock_fetch.return_value = _raw_vuln()
    _create_user(db_session)
    conn = _create_connection(db_session)
    headers = _get_headers(client)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    vuln = db_session.query(WazuhVulnerability).first()

    events_res = client.get("/vulns/events", headers=headers)
    assert events_res.status_code == 200
    assert events_res.json()[0]["event_type"] == "DETECTED"

    history_res = client.get(f"/vulns/{vuln.id}/history", headers=headers)
    assert history_res.status_code == 200
    assert history_res.json()[0]["action"] == "DETECTED"

    missing_res = client.get("/vulns/9999/history", headers=headers)
    assert missing_res.status_code == 404


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_vuln_without_cve_id_is_skipped(mock_fetch, client, db_session):
    mock_fetch.return_value = [{
        "agent": {"id": "001", "name": "host-1"},
        "host": {"os": {}},
        "package": {"name": "curl", "version": "7.81"},
        "vulnerability": {"id": None, "severity": "High", "score": {}},
    }]
    _create_user(db_session)
    conn = _create_connection(db_session)
    res = client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client))
    assert res.json()["synced"] == 0
    assert db_session.query(WazuhVulnerability).count() == 0


def test_viewer_role_forbidden_actions(client, db_session):
    _create_user(db_session, username="viewer_user", role="viewer")
    headers = _get_headers(client, username="viewer_user", password="admin")
    
    payload = {"name": "test", "indexer_url": "https://wazuh.local:9200", "wazuh_user": "u", "wazuh_password": "p"}
    res = client.post("/wazuh-connections", json=payload, headers=headers)
    assert res.status_code == 403

    res2 = client.post("/users", json={"username": "new", "password": "123"}, headers=headers)
    assert res2.status_code == 403

    conn = _create_connection(db_session)
    res3 = client.post(f"/wazuh-connections/{conn.id}/sync", headers=headers)
    assert res3.status_code == 403


@patch("app.routers.wazuh_router.fetch_all_vulns")
def test_user_tag_filtering(mock_fetch, client, db_session):
    mock_fetch.return_value = [
        {
            "agent": {"id": "001", "name": "host-dev"},
            "host": {"os": {}},
            "package": {"name": "lib1", "version": "1.0", "type": "deb", "architecture": "amd64"},
            "vulnerability": {"id": "CVE-2023-0001", "severity": "High", "score": {}},
        },
        {
            "agent": {"id": "002", "name": "host-prod"},
            "host": {"os": {}},
            "package": {"name": "lib2", "version": "2.0", "type": "deb", "architecture": "amd64"},
            "vulnerability": {"id": "CVE-2023-0002", "severity": "Medium", "score": {}},
        }
    ]
    _create_user(db_session, username="admin_user", role="admin")
    conn = _create_connection(db_session)
    client.post(f"/wazuh-connections/{conn.id}/sync", headers=_get_headers(client, username="admin_user", password="admin"))

    vulns = db_session.query(WazuhVulnerability).all()
    if len(vulns) >= 2:
        vulns[0].tags = ["dev"]
        vulns[1].tags = ["prod"]
        db_session.commit()

    viewer = _create_user(db_session, username="dev_viewer", role="viewer")
    viewer.tags = ["dev"]
    db_session.commit()

    headers_viewer = _get_headers(client, username="dev_viewer", password="admin")
    res = client.get("/vulns", headers=headers_viewer).json()
    assert res["total"] == 1
    assert res["items"][0]["cve_id"] == "CVE-2023-0001"


def test_vulns_query_filters(client, db_session):
    _create_user(db_session)
    headers = _get_headers(client)
    res = client.get(
        "/vulns?score_min=4.0&score_max=9.5&search=bash&date_from=2026-01-01T00:00:00Z&date_to=2026-12-31T23:59:59Z",
        headers=headers
    )
    assert res.status_code == 200

from fastapi.testclient import TestClient

from auth_context import PrincipalContext
from auth_dependency import current_principal
from identity import Role
from main import app


client = TestClient(app)


def owner_principal():
    return PrincipalContext(
        user_id="user_owner",
        email="owner@example.test",
        organization_id="org_authorized",
        organization_name="Authorized Family Office",
        membership_id="membership_owner",
        role=Role.OWNER,
    )


def viewer_principal():
    return PrincipalContext(
        user_id="user_viewer",
        email="viewer@example.test",
        organization_id="org_authorized",
        organization_name="Authorized Family Office",
        membership_id="membership_viewer",
        role=Role.VIEWER,
    )


def setup_function():
    app.dependency_overrides.clear()


def teardown_function():
    app.dependency_overrides.clear()


def test_audit_requires_authentication():
    response = client.get("/v1/audit/export")

    assert response.status_code == 401


def test_old_tenant_audit_route_is_not_available():
    response = client.get("/v1/audit/export/org_attacker")

    assert response.status_code == 404


def test_viewer_cannot_export_audit():
    app.dependency_overrides[current_principal] = viewer_principal

    response = client.get("/v1/audit/export")

    assert response.status_code == 403


def test_assistant_rejects_client_supplied_tenant_id():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/assistant/query",
        json={
            "tenant_id": "org_attacker",
            "query_text": "Show audit integrity",
        },
    )

    assert response.status_code == 422


def test_assistant_uses_authenticated_organization():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/assistant/query",
        json={
            "query_text": "Show audit integrity",
        },
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "org_authorized"


def test_liquidity_rejects_client_supplied_tenant_id():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/liquidity/overview",
        json={
            "tenant_id": "org_attacker",
            "base_currency": "USD",
        },
    )

    assert response.status_code == 422


def test_liquidity_uses_authenticated_organization():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/liquidity/overview",
        json={
            "base_currency": "USD",
        },
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "org_authorized"


def test_ingestion_requires_ledger_ingest_permission():
    app.dependency_overrides[current_principal] = viewer_principal

    response = client.post(
        "/v1/ingest/statement",
        data={
            "custodian": "Test Custodian",
        },
        files={
            "file": (
                "statement.csv",
                b"timestamp,asset,value\n2026-10-04T00:00:00Z,CASH,100\n",
                "text/csv",
            ),
        },
    )

    assert response.status_code == 403


def test_ingestion_uses_authenticated_organization(monkeypatch):
    app.dependency_overrides[current_principal] = owner_principal

    captured = {}

    async def fake_process_csv_feed(
        tenant_id,
        custodian,
        file_bytes,
    ):
        captured["tenant_id"] = tenant_id
        captured["custodian"] = custodian

        return {
            "tenant_id": tenant_id,
            "custodian": custodian,
            "total_rows_processed": 1,
            "ledger_signatures": [],
            "status": "SECURE_INGESTION_COMPLETE",
        }

    import main

    monkeypatch.setattr(
        main,
        "process_csv_feed",
        fake_process_csv_feed,
    )

    response = client.post(
        "/v1/ingest/statement",
        data={
            "tenant_id": "org_attacker",
            "custodian": "Test Custodian",
        },
        files={
            "file": (
                "statement.csv",
                b"timestamp,asset,value\n2026-10-04T00:00:00Z,CASH,100\n",
                "text/csv",
            ),
        },
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "org_authorized"
    assert captured["tenant_id"] == "org_authorized"


def test_governance_rejects_client_supplied_tenant_id():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/governance/impact-radar",
        json={
            "tenant_id": "org_attacker",
            "jurisdiction": "UAE_DIFC",
            "held_asset_classes": ["ALL"],
        },
    )

    assert response.status_code == 422


def test_governance_uses_authenticated_organization():
    app.dependency_overrides[current_principal] = owner_principal

    response = client.post(
        "/v1/governance/impact-radar",
        json={
            "jurisdiction": "UAE_DIFC",
            "held_asset_classes": ["ALL"],
        },
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "org_authorized"

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

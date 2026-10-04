import aiosqlite
import pytest

from authorization import Permission, authorize
from iam_schema import initialize_iam_schema
from identity import MembershipStatus, Role
from security import generate_session_token, hash_session_token


def test_viewer_cannot_ingest_ledger():
    result = authorize(
        membership_status=MembershipStatus.ACTIVE,
        role=Role.VIEWER,
        permission=Permission.LEDGER_INGEST,
    )

    assert result.allowed is False
    assert result.reason == "permission_denied"


def test_owner_can_manage_security():
    result = authorize(
        membership_status=MembershipStatus.ACTIVE,
        role=Role.OWNER,
        permission=Permission.SECURITY_MANAGE,
    )

    assert result.allowed is True


def test_permission_does_not_bypass_missing_entitlement():
    result = authorize(
        membership_status=MembershipStatus.ACTIVE,
        role=Role.OWNER,
        permission=Permission.ASSISTANT_USE,
        entitlement_enabled=False,
    )

    assert result.allowed is False
    assert result.reason == "entitlement_disabled"


def test_inactive_membership_denied_before_role():
    result = authorize(
        membership_status=MembershipStatus.SUSPENDED,
        role=Role.OWNER,
        permission=Permission.ORGANIZATION_MANAGE,
    )

    assert result.allowed is False
    assert result.reason == "membership_inactive"


def test_session_tokens_are_random_and_only_hash_is_stable():
    first = generate_session_token()
    second = generate_session_token()

    assert first != second
    assert hash_session_token(first) == hash_session_token(first)
    assert hash_session_token(first) != first


@pytest.mark.asyncio
async def test_iam_schema_enforces_membership_uniqueness(tmp_path):
    db_path = tmp_path / "iam.db"

    async with aiosqlite.connect(db_path) as db:
        await initialize_iam_schema(db)

        await db.execute(
            """
            INSERT INTO users (
                id, email, display_name, status, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("user_1", "owner@example.test", "Owner", "active", "2026-10-04T00:00:00Z"),
        )

        await db.execute(
            """
            INSERT INTO organizations (
                id, name, status, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            ("org_1", "Example Family Office", "active", "2026-10-04T00:00:00Z"),
        )

        await db.execute(
            """
            INSERT INTO memberships (
                id, user_id, organization_id, role, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "membership_1",
                "user_1",
                "org_1",
                "owner",
                "active",
                "2026-10-04T00:00:00Z",
            ),
        )

        await db.commit()

        with pytest.raises(aiosqlite.IntegrityError):
            await db.execute(
                """
                INSERT INTO memberships (
                    id, user_id, organization_id, role, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "membership_2",
                    "user_1",
                    "org_1",
                    "viewer",
                    "active",
                    "2026-10-04T00:00:01Z",
                ),
            )

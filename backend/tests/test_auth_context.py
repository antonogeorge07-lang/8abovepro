from datetime import datetime, timedelta, timezone

import aiosqlite
import pytest

from auth_context import (
    AuthenticationError,
    OrganizationAccessDenied,
    OrganizationSelectionRequired,
    resolve_principal_context,
)
from iam_schema import initialize_iam_schema
from security import hash_session_token


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def seed_identity(
    db,
    *,
    token="test-session-token",
    second_org=False,
):
    now = datetime.now(timezone.utc)
    later = now + timedelta(hours=1)

    await db.execute(
        """
        INSERT INTO users (
            id, email, display_name, status, created_at
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            "user_1",
            "owner@example.test",
            "Owner",
            "active",
            iso(now),
        ),
    )

    await db.execute(
        """
        INSERT INTO organizations (
            id, name, status, created_at
        ) VALUES (?, ?, ?, ?)
        """,
        (
            "org_1",
            "Primary Family Office",
            "active",
            iso(now),
        ),
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
            iso(now),
        ),
    )

    if second_org:
        await db.execute(
            """
            INSERT INTO organizations (
                id, name, status, created_at
            ) VALUES (?, ?, ?, ?)
            """,
            (
                "org_2",
                "Secondary Family Office",
                "active",
                iso(now),
            ),
        )

        await db.execute(
            """
            INSERT INTO memberships (
                id, user_id, organization_id, role, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "membership_2",
                "user_1",
                "org_2",
                "viewer",
                "active",
                iso(now),
            ),
        )

    await db.execute(
        """
        INSERT INTO sessions (
            id, user_id, token_hash, status, expires_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "session_1",
            "user_1",
            hash_session_token(token),
            "active",
            iso(later),
            iso(now),
        ),
    )

    await db.commit()


@pytest.mark.asyncio
async def test_valid_session_resolves_single_org(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)
        await seed_identity(db)

        principal = await resolve_principal_context(
            db,
            bearer_token="test-session-token",
        )

        assert principal.user_id == "user_1"
        assert principal.organization_id == "org_1"
        assert principal.role.value == "owner"


@pytest.mark.asyncio
async def test_invalid_session_is_rejected(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)
        await seed_identity(db)

        with pytest.raises(AuthenticationError):
            await resolve_principal_context(
                db,
                bearer_token="wrong-token",
            )


@pytest.mark.asyncio
async def test_multi_org_requires_explicit_selection(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)
        await seed_identity(db, second_org=True)

        with pytest.raises(OrganizationSelectionRequired):
            await resolve_principal_context(
                db,
                bearer_token="test-session-token",
            )


@pytest.mark.asyncio
async def test_valid_org_selection_resolves_membership(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)
        await seed_identity(db, second_org=True)

        principal = await resolve_principal_context(
            db,
            bearer_token="test-session-token",
            requested_organization_id="org_2",
        )

        assert principal.organization_id == "org_2"
        assert principal.role.value == "viewer"


@pytest.mark.asyncio
async def test_cross_org_selection_is_denied(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)
        await seed_identity(db)

        with pytest.raises(OrganizationAccessDenied):
            await resolve_principal_context(
                db,
                bearer_token="test-session-token",
                requested_organization_id="org_attacker",
            )


@pytest.mark.asyncio
async def test_expired_session_is_rejected(tmp_path):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        now = datetime.now(timezone.utc)
        expired = now - timedelta(minutes=1)

        await db.execute(
            """
            INSERT INTO users (
                id, email, display_name, status, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "user_1",
                "owner@example.test",
                "Owner",
                "active",
                iso(now),
            ),
        )

        await db.execute(
            """
            INSERT INTO sessions (
                id, user_id, token_hash, status, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "session_1",
                "user_1",
                hash_session_token("expired-token"),
                "active",
                iso(expired),
                iso(now),
            ),
        )

        await db.commit()

        with pytest.raises(AuthenticationError):
            await resolve_principal_context(
                db,
                bearer_token="expired-token",
            )

from datetime import datetime, timedelta, timezone

import aiosqlite
import pytest

from account_lifecycle import (
    DEFAULT_ENTITLEMENTS,
    InvitationError,
    accept_invitation,
    create_invitation,
    create_organization,
)
from auth_context import PrincipalContext
from iam_schema import initialize_iam_schema
from identity import Role
from identity_context import (
    AuthenticatedIdentity,
    resolve_authenticated_identity,
)
from security import hash_session_token


def iso(dt):
    return dt.astimezone(
        timezone.utc
    ).isoformat().replace("+00:00", "Z")


async def seed_user(
    db,
    *,
    user_id,
    email,
    token,
):
    now = datetime.now(timezone.utc)

    await db.execute(
        """
        INSERT INTO users (
            id,
            email,
            display_name,
            status,
            created_at
        ) VALUES (?, ?, ?, 'active', ?)
        """,
        (
            user_id,
            email,
            email,
            iso(now),
        ),
    )

    await db.execute(
        """
        INSERT INTO sessions (
            id,
            user_id,
            token_hash,
            status,
            expires_at,
            created_at
        ) VALUES (?, ?, ?, 'active', ?, ?)
        """,
        (
            f"session_{user_id}",
            user_id,
            hash_session_token(token),
            iso(now + timedelta(hours=1)),
            iso(now),
        ),
    )

    await db.commit()


@pytest.mark.asyncio
async def test_identity_resolution_does_not_require_membership(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_new",
            email="new@example.test",
            token="new-user-session",
        )

        identity = await resolve_authenticated_identity(
            db,
            bearer_token="new-user-session",
        )

        assert identity.user_id == "user_new"
        assert identity.email == "new@example.test"


@pytest.mark.asyncio
async def test_org_creation_atomically_creates_owner_entitlements_and_onboarding(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        identity = AuthenticatedIdentity(
            user_id="user_owner",
            email="owner@example.test",
        )

        result = await create_organization(
            db,
            identity=identity,
            name="Example Family Office",
        )

        assert result["role"] == "owner"
        assert result["onboarding"]["current_step"] == (
            "first_data_source"
        )

        async with db.execute(
            """
            SELECT role, status
            FROM memberships
            WHERE organization_id = ?
              AND user_id = ?
            """,
            (
                result["organization_id"],
                "user_owner",
            ),
        ) as cursor:
            membership = await cursor.fetchone()

        assert membership == (
            "owner",
            "active",
        )

        async with db.execute(
            """
            SELECT capability
            FROM entitlements
            WHERE organization_id = ?
              AND enabled = 1
            ORDER BY capability
            """,
            (result["organization_id"],),
        ) as cursor:
            capabilities = {
                row[0]
                for row in await cursor.fetchall()
            }

        assert capabilities == set(
            DEFAULT_ENTITLEMENTS
        )

        async with db.execute(
            """
            SELECT status, current_step
            FROM onboarding_states
            WHERE organization_id = ?
            """,
            (result["organization_id"],),
        ) as cursor:
            onboarding = await cursor.fetchone()

        assert onboarding == (
            "in_progress",
            "first_data_source",
        )


@pytest.mark.asyncio
async def test_owner_cannot_be_created_by_invitation(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        identity = AuthenticatedIdentity(
            user_id="user_owner",
            email="owner@example.test",
        )

        org = await create_organization(
            db,
            identity=identity,
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        with pytest.raises(
            InvitationError,
            match="invite_role_not_allowed",
        ):
            await create_invitation(
                db,
                actor=actor,
                email="future-owner@example.test",
                role=Role.OWNER,
            )


@pytest.mark.asyncio
async def test_admin_cannot_invite_another_admin(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        actor = PrincipalContext(
            user_id="admin_1",
            email="admin@example.test",
            organization_id="org_1",
            organization_name="Example",
            membership_id="membership_admin",
            role=Role.ADMIN,
        )

        with pytest.raises(
            InvitationError,
            match="invite_role_not_allowed",
        ):
            await create_invitation(
                db,
                actor=actor,
                email="admin2@example.test",
                role=Role.ADMIN,
            )


@pytest.mark.asyncio
async def test_invite_persists_hash_not_raw_token(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        org = await create_organization(
            db,
            identity=AuthenticatedIdentity(
                user_id="user_owner",
                email="owner@example.test",
            ),
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        invite = await create_invitation(
            db,
            actor=actor,
            email="member@example.test",
            role=Role.MEMBER,
        )

        async with db.execute(
            """
            SELECT token_hash
            FROM invitations
            WHERE id = ?
            """,
            (invite["invitation_id"],),
        ) as cursor:
            row = await cursor.fetchone()

        assert row is not None
        assert row[0] != invite["token"]
        assert row[0] == hash_session_token(
            invite["token"]
        )


@pytest.mark.asyncio
async def test_invite_email_must_match_authenticated_identity(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        org = await create_organization(
            db,
            identity=AuthenticatedIdentity(
                user_id="user_owner",
                email="owner@example.test",
            ),
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        invite = await create_invitation(
            db,
            actor=actor,
            email="member@example.test",
            role=Role.MEMBER,
        )

        with pytest.raises(
            InvitationError,
            match="invite_email_mismatch",
        ):
            await accept_invitation(
                db,
                identity=AuthenticatedIdentity(
                    user_id="attacker",
                    email="attacker@example.test",
                ),
                token=invite["token"],
            )


@pytest.mark.asyncio
async def test_invite_acceptance_is_single_use(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        await seed_user(
            db,
            user_id="user_member",
            email="member@example.test",
            token="member-session",
        )

        org = await create_organization(
            db,
            identity=AuthenticatedIdentity(
                user_id="user_owner",
                email="owner@example.test",
            ),
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        invite = await create_invitation(
            db,
            actor=actor,
            email="member@example.test",
            role=Role.MEMBER,
        )

        member_identity = AuthenticatedIdentity(
            user_id="user_member",
            email="member@example.test",
        )

        accepted = await accept_invitation(
            db,
            identity=member_identity,
            token=invite["token"],
        )

        assert accepted["organization_id"] == (
            org["organization_id"]
        )
        assert accepted["role"] == "member"

        with pytest.raises(
            InvitationError,
            match="invite_already_used",
        ):
            await accept_invitation(
                db,
                identity=member_identity,
                token=invite["token"],
            )


@pytest.mark.asyncio
async def test_onboarding_progresses_in_order(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        identity = AuthenticatedIdentity(
            user_id="user_owner",
            email="owner@example.test",
        )

        org = await create_organization(
            db,
            identity=identity,
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        from account_lifecycle import advance_onboarding

        state = await advance_onboarding(
            db,
            actor=actor,
            completed_step="first_data_source",
        )

        assert state["status"] == "in_progress"
        assert state["current_step"] == "first_value"
        assert "first_data_source" in state["completed_steps"]


@pytest.mark.asyncio
async def test_onboarding_rejects_out_of_order_progress(
    tmp_path,
):
    path = tmp_path / "iam.db"

    async with aiosqlite.connect(path) as db:
        await initialize_iam_schema(db)

        await seed_user(
            db,
            user_id="user_owner",
            email="owner@example.test",
            token="owner-session",
        )

        identity = AuthenticatedIdentity(
            user_id="user_owner",
            email="owner@example.test",
        )

        org = await create_organization(
            db,
            identity=identity,
            name="Example Family Office",
        )

        actor = PrincipalContext(
            user_id="user_owner",
            email="owner@example.test",
            organization_id=org["organization_id"],
            organization_name="Example Family Office",
            membership_id=org["membership_id"],
            role=Role.OWNER,
        )

        from account_lifecycle import advance_onboarding

        with pytest.raises(
            Exception,
            match="onboarding_step_out_of_order",
        ):
            await advance_onboarding(
                db,
                actor=actor,
                completed_step="team_invite",
            )

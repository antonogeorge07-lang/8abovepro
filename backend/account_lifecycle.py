import json
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import aiosqlite

from auth_context import PrincipalContext
from identity import Role
from identity_context import AuthenticatedIdentity
from security import hash_session_token


class AccountLifecycleError(Exception):
    pass


class InvitationError(AccountLifecycleError):
    pass


DEFAULT_ENTITLEMENTS = (
    "audit_export",
    "assistant",
    "governance",
    "ledger_ingest",
    "liquidity",
)


INVITE_ROLE_POLICY = {
    Role.OWNER: {
        Role.ADMIN,
        Role.MANAGER,
        Role.MEMBER,
        Role.VIEWER,
    },
    Role.ADMIN: {
        Role.MANAGER,
        Role.MEMBER,
        Role.VIEWER,
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace(
        "+00:00",
        "Z",
    )


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def create_organization(
    db: aiosqlite.Connection,
    *,
    identity: AuthenticatedIdentity,
    name: str,
) -> dict:
    organization_name = name.strip()

    if len(organization_name) < 2:
        raise AccountLifecycleError(
            "organization_name_invalid"
        )

    now = iso(utc_now())

    organization_id = new_id("org")
    membership_id = new_id("membership")

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("BEGIN IMMEDIATE")

    try:
        await db.execute(
            """
            INSERT INTO organizations (
                id,
                name,
                status,
                created_at
            ) VALUES (?, ?, 'active', ?)
            """,
            (
                organization_id,
                organization_name,
                now,
            ),
        )

        await db.execute(
            """
            INSERT INTO memberships (
                id,
                user_id,
                organization_id,
                role,
                status,
                created_at
            ) VALUES (?, ?, ?, 'owner', 'active', ?)
            """,
            (
                membership_id,
                identity.user_id,
                organization_id,
                now,
            ),
        )

        for capability in DEFAULT_ENTITLEMENTS:
            await db.execute(
                """
                INSERT INTO entitlements (
                    id,
                    organization_id,
                    capability,
                    enabled,
                    limit_value,
                    created_at
                ) VALUES (?, ?, ?, 1, NULL, ?)
                """,
                (
                    new_id("entitlement"),
                    organization_id,
                    capability,
                    now,
                ),
            )

        await db.execute(
            """
            INSERT INTO onboarding_states (
                organization_id,
                status,
                current_step,
                completed_steps_json,
                created_at,
                updated_at
            ) VALUES (?, 'in_progress', ?, ?, ?, ?)
            """,
            (
                organization_id,
                "first_data_source",
                json.dumps(
                    [
                        "organization_created",
                        "owner_membership_created",
                        "entitlements_initialized",
                    ]
                ),
                now,
                now,
            ),
        )

        await db.execute(
            """
            INSERT INTO iam_audit_events (
                organization_id,
                actor_user_id,
                event_type,
                resource_type,
                resource_id,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                organization_id,
                identity.user_id,
                "organization.created",
                "organization",
                organization_id,
                json.dumps(
                    {
                        "owner_membership_id": membership_id,
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return {
        "organization_id": organization_id,
        "organization_name": organization_name,
        "membership_id": membership_id,
        "role": Role.OWNER.value,
        "onboarding": {
            "status": "in_progress",
            "current_step": "first_data_source",
        },
    }


async def get_onboarding_state(
    db: aiosqlite.Connection,
    *,
    organization_id: str,
) -> dict:
    async with db.execute(
        """
        SELECT
            status,
            current_step,
            completed_steps_json,
            created_at,
            updated_at
        FROM onboarding_states
        WHERE organization_id = ?
        """,
        (organization_id,),
    ) as cursor:
        row = await cursor.fetchone()

    if row is None:
        raise AccountLifecycleError(
            "onboarding_state_not_found"
        )

    (
        status,
        current_step,
        completed_steps_json,
        created_at,
        updated_at,
    ) = row

    return {
        "organization_id": organization_id,
        "status": status,
        "current_step": current_step,
        "completed_steps": json.loads(
            completed_steps_json
        ),
        "created_at": created_at,
        "updated_at": updated_at,
    }


async def create_invitation(
    db: aiosqlite.Connection,
    *,
    actor: PrincipalContext,
    email: str,
    role: Role,
    ttl_days: int = 7,
) -> dict:
    normalized_email = normalize_email(email)

    allowed_roles = INVITE_ROLE_POLICY.get(
        actor.role,
        set(),
    )

    if role not in allowed_roles:
        raise InvitationError(
            "invite_role_not_allowed"
        )

    if normalize_email(actor.email) == normalized_email:
        raise InvitationError(
            "cannot_invite_self"
        )

    now_dt = utc_now()
    now = iso(now_dt)
    expires_at = iso(
        now_dt + timedelta(days=ttl_days)
    )

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("BEGIN IMMEDIATE")

    try:
        async with db.execute(
            """
            SELECT id
            FROM invitations
            WHERE organization_id = ?
              AND email = ?
              AND accepted_at IS NULL
              AND expires_at > ?
            LIMIT 1
            """,
            (
                actor.organization_id,
                normalized_email,
                now,
            ),
        ) as cursor:
            pending = await cursor.fetchone()

        if pending is not None:
            raise InvitationError(
                "invite_already_pending"
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_session_token(raw_token)
        invitation_id = new_id("invite")

        await db.execute(
            """
            INSERT INTO invitations (
                id,
                organization_id,
                email,
                role,
                token_hash,
                expires_at,
                accepted_at,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                invitation_id,
                actor.organization_id,
                normalized_email,
                role.value,
                token_hash,
                expires_at,
                now,
            ),
        )

        await db.execute(
            """
            INSERT INTO iam_audit_events (
                organization_id,
                actor_user_id,
                event_type,
                resource_type,
                resource_id,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                actor.organization_id,
                actor.user_id,
                "invitation.created",
                "invitation",
                invitation_id,
                json.dumps(
                    {
                        "email": normalized_email,
                        "role": role.value,
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return {
        "invitation_id": invitation_id,
        "organization_id": actor.organization_id,
        "email": normalized_email,
        "role": role.value,
        "expires_at": expires_at,

        # Returned once to the caller.
        # Only the hash is persisted.
        "token": raw_token,
    }


async def accept_invitation(
    db: aiosqlite.Connection,
    *,
    identity: AuthenticatedIdentity,
    token: str,
) -> dict:
    if not token:
        raise InvitationError(
            "invite_token_required"
        )

    token_hash = hash_session_token(token)

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("BEGIN IMMEDIATE")

    try:
        async with db.execute(
            """
            SELECT
                id,
                organization_id,
                email,
                role,
                expires_at,
                accepted_at
            FROM invitations
            WHERE token_hash = ?
            LIMIT 1
            """,
            (token_hash,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            raise InvitationError(
                "invite_invalid"
            )

        (
            invitation_id,
            organization_id,
            invitation_email,
            role_value,
            expires_at,
            accepted_at,
        ) = row

        if accepted_at is not None:
            raise InvitationError(
                "invite_already_used"
            )

        expiry = datetime.fromisoformat(
            expires_at.replace("Z", "+00:00")
        )

        if expiry <= utc_now():
            raise InvitationError(
                "invite_expired"
            )

        if normalize_email(identity.email) != normalize_email(
            invitation_email
        ):
            raise InvitationError(
                "invite_email_mismatch"
            )

        async with db.execute(
            """
            SELECT status
            FROM organizations
            WHERE id = ?
            """,
            (organization_id,),
        ) as cursor:
            organization = await cursor.fetchone()

        if organization is None or organization[0] != "active":
            raise InvitationError(
                "organization_unavailable"
            )

        async with db.execute(
            """
            SELECT id
            FROM memberships
            WHERE user_id = ?
              AND organization_id = ?
            LIMIT 1
            """,
            (
                identity.user_id,
                organization_id,
            ),
        ) as cursor:
            existing_membership = await cursor.fetchone()

        if existing_membership is not None:
            raise InvitationError(
                "membership_already_exists"
            )

        now = iso(utc_now())
        membership_id = new_id("membership")

        await db.execute(
            """
            INSERT INTO memberships (
                id,
                user_id,
                organization_id,
                role,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, 'active', ?)
            """,
            (
                membership_id,
                identity.user_id,
                organization_id,
                role_value,
                now,
            ),
        )

        cursor = await db.execute(
            """
            UPDATE invitations
            SET accepted_at = ?
            WHERE id = ?
              AND accepted_at IS NULL
            """,
            (
                now,
                invitation_id,
            ),
        )

        if cursor.rowcount != 1:
            raise InvitationError(
                "invite_already_used"
            )

        await db.execute(
            """
            INSERT INTO iam_audit_events (
                organization_id,
                actor_user_id,
                event_type,
                resource_type,
                resource_id,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                organization_id,
                identity.user_id,
                "invitation.accepted",
                "membership",
                membership_id,
                json.dumps(
                    {
                        "invitation_id": invitation_id,
                        "role": role_value,
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return {
        "organization_id": organization_id,
        "membership_id": membership_id,
        "role": role_value,
        "status": "active",
    }


ONBOARDING_STEPS = (
    "first_data_source",
    "first_value",
    "team_invite",
    "completed",
)


async def advance_onboarding(
    db: aiosqlite.Connection,
    *,
    actor: PrincipalContext,
    completed_step: str,
) -> dict:
    if completed_step not in ONBOARDING_STEPS:
        raise AccountLifecycleError(
            "onboarding_step_invalid"
        )

    await db.execute("PRAGMA foreign_keys = ON")
    await db.execute("BEGIN IMMEDIATE")

    try:
        async with db.execute(
            """
            SELECT
                status,
                current_step,
                completed_steps_json
            FROM onboarding_states
            WHERE organization_id = ?
            """,
            (actor.organization_id,),
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            raise AccountLifecycleError(
                "onboarding_state_not_found"
            )

        status_value, current_step, completed_json = row
        completed_steps = json.loads(completed_json)

        if status_value == "completed":
            return await get_onboarding_state(
                db,
                organization_id=actor.organization_id,
            )

        if completed_step != current_step:
            raise AccountLifecycleError(
                "onboarding_step_out_of_order"
            )

        if completed_step not in completed_steps:
            completed_steps.append(completed_step)

        index = ONBOARDING_STEPS.index(
            completed_step
        )

        if completed_step == "completed":
            next_status = "completed"
            next_step = "completed"
        else:
            next_status = "in_progress"
            next_step = ONBOARDING_STEPS[
                index + 1
            ]

        now = iso(utc_now())

        await db.execute(
            """
            UPDATE onboarding_states
            SET
                status = ?,
                current_step = ?,
                completed_steps_json = ?,
                updated_at = ?
            WHERE organization_id = ?
            """,
            (
                next_status,
                next_step,
                json.dumps(completed_steps),
                now,
                actor.organization_id,
            ),
        )

        await db.execute(
            """
            INSERT INTO iam_audit_events (
                organization_id,
                actor_user_id,
                event_type,
                resource_type,
                resource_id,
                details_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                actor.organization_id,
                actor.user_id,
                "onboarding.advanced",
                "organization",
                actor.organization_id,
                json.dumps(
                    {
                        "completed_step": completed_step,
                        "next_step": next_step,
                        "status": next_status,
                    },
                    sort_keys=True,
                ),
                now,
            ),
        )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    return await get_onboarding_state(
        db,
        organization_id=actor.organization_id,
    )

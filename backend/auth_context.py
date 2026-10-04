from dataclasses import dataclass
from datetime import datetime, timezone

import aiosqlite

from authorization import Permission, authorize
from identity import MembershipStatus, Role
from security import hash_session_token


@dataclass(frozen=True)
class PrincipalContext:
    user_id: str
    email: str
    organization_id: str
    organization_name: str
    membership_id: str
    role: Role


class AuthenticationError(Exception):
    pass


class OrganizationSelectionRequired(AuthenticationError):
    pass


class OrganizationAccessDenied(AuthenticationError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def resolve_principal_context(
    db: aiosqlite.Connection,
    *,
    bearer_token: str,
    requested_organization_id: str | None = None,
) -> PrincipalContext:
    if not bearer_token:
        raise AuthenticationError("missing_session")

    token_hash = hash_session_token(bearer_token)

    async with db.execute(
        """
        SELECT
            s.user_id,
            s.status AS session_status,
            s.expires_at,
            u.email,
            u.status AS user_status
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_hash = ?
        LIMIT 1
        """,
        (token_hash,),
    ) as cursor:
        session_row = await cursor.fetchone()

    if session_row is None:
        raise AuthenticationError("invalid_session")

    (
        user_id,
        session_status,
        expires_at,
        email,
        user_status,
    ) = session_row

    if session_status != "active":
        raise AuthenticationError("inactive_session")

    if user_status != "active":
        raise AuthenticationError("inactive_user")

    if expires_at <= utc_now_iso():
        raise AuthenticationError("expired_session")

    params: list[str] = [user_id]

    sql = """
        SELECT
            m.id,
            m.organization_id,
            m.role,
            m.status,
            o.name,
            o.status
        FROM memberships m
        JOIN organizations o ON o.id = m.organization_id
        WHERE m.user_id = ?
          AND m.status = 'active'
          AND o.status = 'active'
    """

    if requested_organization_id is not None:
        sql += " AND m.organization_id = ?"
        params.append(requested_organization_id)

    sql += " ORDER BY m.created_at ASC"

    async with db.execute(sql, tuple(params)) as cursor:
        memberships = await cursor.fetchall()

    if requested_organization_id is not None and not memberships:
        raise OrganizationAccessDenied("organization_access_denied")

    if not memberships:
        raise AuthenticationError("no_active_membership")

    if requested_organization_id is None and len(memberships) > 1:
        raise OrganizationSelectionRequired("organization_selection_required")

    (
        membership_id,
        organization_id,
        role,
        _membership_status,
        organization_name,
        _organization_status,
    ) = memberships[0]

    return PrincipalContext(
        user_id=user_id,
        email=email,
        organization_id=organization_id,
        organization_name=organization_name,
        membership_id=membership_id,
        role=Role(role),
    )


def require_permission(
    context: PrincipalContext,
    permission: Permission,
    *,
    entitlement_enabled: bool = True,
    policy_satisfied: bool = True,
    quota_available: bool = True,
) -> None:
    decision = authorize(
        membership_status=MembershipStatus.ACTIVE,
        role=context.role,
        permission=permission,
        entitlement_enabled=entitlement_enabled,
        policy_satisfied=policy_satisfied,
        quota_available=quota_available,
    )

    if not decision.allowed:
        raise OrganizationAccessDenied(decision.reason)

from dataclasses import dataclass

import aiosqlite

from authorization import Permission, authorize
from identity import MembershipStatus, Role
from identity_context import (
    AuthenticatedIdentity,
    AuthenticationError,
    resolve_authenticated_identity,
)


@dataclass(frozen=True)
class PrincipalContext:
    user_id: str
    email: str
    organization_id: str
    organization_name: str
    membership_id: str
    role: Role


class OrganizationSelectionRequired(AuthenticationError):
    pass


class OrganizationAccessDenied(AuthenticationError):
    pass


async def resolve_principal_context(
    db: aiosqlite.Connection,
    *,
    bearer_token: str,
    requested_organization_id: str | None = None,
) -> PrincipalContext:
    identity: AuthenticatedIdentity = await resolve_authenticated_identity(
        db,
        bearer_token=bearer_token,
    )

    params: list[str] = [identity.user_id]

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
        raise OrganizationAccessDenied(
            "organization_access_denied"
        )

    if not memberships:
        raise AuthenticationError(
            "no_active_membership"
        )

    if requested_organization_id is None and len(memberships) > 1:
        raise OrganizationSelectionRequired(
            "organization_selection_required"
        )

    (
        membership_id,
        organization_id,
        role,
        _membership_status,
        organization_name,
        _organization_status,
    ) = memberships[0]

    return PrincipalContext(
        user_id=identity.user_id,
        email=identity.email,
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
        raise OrganizationAccessDenied(
            decision.reason
        )

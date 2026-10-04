from dataclasses import dataclass
from enum import StrEnum

from identity import MembershipStatus, Role


class Permission(StrEnum):
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_MANAGE = "organization.manage"

    MEMBERS_READ = "members.read"
    MEMBERS_INVITE = "members.invite"
    MEMBERS_MANAGE = "members.manage"

    PORTFOLIO_READ = "portfolio.read"
    PORTFOLIO_CREATE = "portfolio.create"
    PORTFOLIO_MANAGE = "portfolio.manage"

    LEDGER_READ = "ledger.read"
    LEDGER_INGEST = "ledger.ingest"

    AUDIT_READ = "audit.read"
    AUDIT_EXPORT = "audit.export"

    ASSISTANT_USE = "assistant.use"

    INTEGRATIONS_MANAGE = "integrations.manage"

    BILLING_READ = "billing.read"
    BILLING_MANAGE = "billing.manage"

    SECURITY_MANAGE = "security.manage"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),

    Role.ADMIN: frozenset({
        Permission.ORGANIZATION_READ,
        Permission.ORGANIZATION_MANAGE,
        Permission.MEMBERS_READ,
        Permission.MEMBERS_INVITE,
        Permission.MEMBERS_MANAGE,
        Permission.PORTFOLIO_READ,
        Permission.PORTFOLIO_CREATE,
        Permission.PORTFOLIO_MANAGE,
        Permission.LEDGER_READ,
        Permission.LEDGER_INGEST,
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        Permission.ASSISTANT_USE,
        Permission.INTEGRATIONS_MANAGE,
        Permission.BILLING_READ,
        Permission.SECURITY_MANAGE,
    }),

    Role.MANAGER: frozenset({
        Permission.ORGANIZATION_READ,
        Permission.MEMBERS_READ,
        Permission.PORTFOLIO_READ,
        Permission.PORTFOLIO_CREATE,
        Permission.PORTFOLIO_MANAGE,
        Permission.LEDGER_READ,
        Permission.LEDGER_INGEST,
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        Permission.ASSISTANT_USE,
    }),

    Role.MEMBER: frozenset({
        Permission.ORGANIZATION_READ,
        Permission.PORTFOLIO_READ,
        Permission.LEDGER_READ,
        Permission.AUDIT_READ,
        Permission.ASSISTANT_USE,
    }),

    Role.VIEWER: frozenset({
        Permission.ORGANIZATION_READ,
        Permission.PORTFOLIO_READ,
        Permission.LEDGER_READ,
        Permission.AUDIT_READ,
    }),
}


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


def authorize(
    *,
    membership_status: MembershipStatus,
    role: Role,
    permission: Permission,
    entitlement_enabled: bool = True,
    policy_satisfied: bool = True,
    quota_available: bool = True,
) -> AuthorizationDecision:
    if membership_status is not MembershipStatus.ACTIVE:
        return AuthorizationDecision(False, "membership_inactive")

    if not has_permission(role, permission):
        return AuthorizationDecision(False, "permission_denied")

    if not entitlement_enabled:
        return AuthorizationDecision(False, "entitlement_disabled")

    if not policy_satisfied:
        return AuthorizationDecision(False, "policy_unsatisfied")

    if not quota_available:
        return AuthorizationDecision(False, "quota_exhausted")

    return AuthorizationDecision(True, "allowed")

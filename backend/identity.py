from enum import StrEnum

from pydantic import BaseModel, EmailStr


class UserStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class MembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class UserIdentity(BaseModel):
    id: str
    email: EmailStr
    display_name: str | None = None
    status: UserStatus = UserStatus.ACTIVE


class Organization(BaseModel):
    id: str
    name: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE


class Membership(BaseModel):
    id: str
    user_id: str
    organization_id: str
    role: Role
    status: MembershipStatus = MembershipStatus.ACTIVE

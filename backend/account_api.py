import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from account_lifecycle import (
    AccountLifecycleError,
    InvitationError,
    accept_invitation,
    advance_onboarding,
    create_invitation,
    create_organization,
    get_onboarding_state,
)
from auth_context import PrincipalContext
from auth_dependency import (
    current_identity,
    permission_required,
)
from authorization import Permission
from database import DB_PATH
from identity import Role
from identity_context import AuthenticatedIdentity


router = APIRouter(prefix="/v1")


class OrganizationCreateRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=120,
    )


class OnboardingProgressRequest(BaseModel):
    completed_step: str = Field(
        min_length=2,
        max_length=64,
    )


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: Role


class InvitationAcceptRequest(BaseModel):
    token: str = Field(
        min_length=20,
        max_length=512,
    )


def lifecycle_http_error(
    exc: AccountLifecycleError,
) -> HTTPException:
    detail = str(exc)

    conflict_errors = {
        "invite_already_pending",
        "invite_already_used",
        "membership_already_exists",
    }

    forbidden_errors = {
        "invite_role_not_allowed",
        "cannot_invite_self",
        "invite_email_mismatch",
    }

    gone_errors = {
        "invite_expired",
    }

    if detail in conflict_errors:
        code = status.HTTP_409_CONFLICT
    elif detail in forbidden_errors:
        code = status.HTTP_403_FORBIDDEN
    elif detail in gone_errors:
        code = status.HTTP_410_GONE
    else:
        code = status.HTTP_400_BAD_REQUEST

    return HTTPException(
        status_code=code,
        detail=detail,
    )


@router.post("/onboarding/organization")
async def bootstrap_organization(
    request: OrganizationCreateRequest,
    identity: AuthenticatedIdentity = Depends(
        current_identity
    ),
):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await create_organization(
                db,
                identity=identity,
                name=request.name,
            )

    except AccountLifecycleError as exc:
        raise lifecycle_http_error(exc)


@router.get("/onboarding/state")
async def onboarding_state(
    principal: PrincipalContext = Depends(
        permission_required(
            Permission.ORGANIZATION_READ
        )
    ),
):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await get_onboarding_state(
                db,
                organization_id=principal.organization_id,
            )

    except AccountLifecycleError as exc:
        raise lifecycle_http_error(exc)


@router.post("/onboarding/progress")
async def update_onboarding_progress(
    request: OnboardingProgressRequest,
    principal: PrincipalContext = Depends(
        permission_required(
            Permission.ORGANIZATION_MANAGE
        )
    ),
):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await advance_onboarding(
                db,
                actor=principal,
                completed_step=request.completed_step,
            )

    except AccountLifecycleError as exc:
        raise lifecycle_http_error(exc)


@router.post("/organization/invitations")
async def issue_invitation(
    request: InvitationCreateRequest,
    principal: PrincipalContext = Depends(
        permission_required(
            Permission.MEMBERS_INVITE
        )
    ),
):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await create_invitation(
                db,
                actor=principal,
                email=str(request.email),
                role=request.role,
            )

    except InvitationError as exc:
        raise lifecycle_http_error(exc)


@router.post("/invitations/accept")
async def redeem_invitation(
    request: InvitationAcceptRequest,
    identity: AuthenticatedIdentity = Depends(
        current_identity
    ),
):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await accept_invitation(
                db,
                identity=identity,
                token=request.token,
            )

    except InvitationError as exc:
        raise lifecycle_http_error(exc)

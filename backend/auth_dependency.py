import aiosqlite
from fastapi import Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends

from auth_context import (
    AuthenticationError,
    OrganizationAccessDenied,
    OrganizationSelectionRequired,
    PrincipalContext,
    resolve_principal_context,
)
from database import DB_PATH


bearer_scheme = HTTPBearer(auto_error=False)


async def current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    organization_id: str | None = Header(
        default=None,
        alias="X-Organization-ID",
    ),
) -> PrincipalContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
        )

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            return await resolve_principal_context(
                db,
                bearer_token=credentials.credentials,
                requested_organization_id=organization_id,
            )

    except OrganizationSelectionRequired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="organization_selection_required",
        )

    except OrganizationAccessDenied:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="organization_access_denied",
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_session",
        )

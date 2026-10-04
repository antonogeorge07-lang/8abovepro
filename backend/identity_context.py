from dataclasses import dataclass
from datetime import datetime, timezone

import aiosqlite

from security import hash_session_token


class AuthenticationError(Exception):
    pass


@dataclass(frozen=True)
class AuthenticatedIdentity:
    user_id: str
    email: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def resolve_authenticated_identity(
    db: aiosqlite.Connection,
    *,
    bearer_token: str,
) -> AuthenticatedIdentity:
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
        row = await cursor.fetchone()

    if row is None:
        raise AuthenticationError("invalid_session")

    (
        user_id,
        session_status,
        expires_at,
        email,
        user_status,
    ) = row

    if session_status != "active":
        raise AuthenticationError("inactive_session")

    if user_status != "active":
        raise AuthenticationError("inactive_user")

    if expires_at <= utc_now_iso():
        raise AuthenticationError("expired_session")

    return AuthenticatedIdentity(
        user_id=user_id,
        email=email,
    )

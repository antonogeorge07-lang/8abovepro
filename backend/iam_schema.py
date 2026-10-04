import aiosqlite


async def initialize_iam_schema(db: aiosqlite.Connection) -> None:
    await db.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            display_name TEXT,
            status TEXT NOT NULL
                CHECK(status IN ('invited', 'active', 'suspended', 'deactivated')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL
                CHECK(status IN ('active', 'suspended', 'closed')),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memberships (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            organization_id TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK(role IN ('owner', 'admin', 'manager', 'member', 'viewer')),
            status TEXT NOT NULL
                CHECK(status IN ('invited', 'active', 'suspended')),
            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE CASCADE,

            UNIQUE(user_id, organization_id)
        );

        CREATE TABLE IF NOT EXISTS entitlements (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            capability TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
                CHECK(enabled IN (0, 1)),
            limit_value INTEGER,
            created_at TEXT NOT NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE CASCADE,

            UNIQUE(organization_id, capability)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL
                CHECK(status IN ('active', 'revoked', 'expired')),
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS invitations (
            id TEXT PRIMARY KEY,
            organization_id TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK(role IN ('admin', 'manager', 'member', 'viewer')),
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            accepted_at TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS iam_audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id TEXT,
            actor_user_id TEXT,
            event_type TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details_json TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY(organization_id)
                REFERENCES organizations(id)
                ON DELETE SET NULL,

            FOREIGN KEY(actor_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_memberships_user
            ON memberships(user_id);

        CREATE INDEX IF NOT EXISTS idx_memberships_org
            ON memberships(organization_id);

        CREATE INDEX IF NOT EXISTS idx_sessions_user
            ON sessions(user_id);

        CREATE INDEX IF NOT EXISTS idx_entitlements_org
            ON entitlements(organization_id);
        """
    )

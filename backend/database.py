import aiosqlite
import os

from iam_schema import initialize_iam_schema

DB_PATH = os.getenv("SOVEREIGN_DB_PATH", "sovereign_ledger.db")

class SovereignDBPool:
    @staticmethod
    async def initialize():
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    custodian TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL UNIQUE,
                    verified INTEGER DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    logged_at TEXT NOT NULL
                )
            """)

            await initialize_iam_schema(db)

            await db.commit()

    @staticmethod
    async def close():
        pass

import os
import aiosqlite
from typing import Optional
import contextlib
import re

DB_PATH = "sovereign_ledger.db"

class AsyncPGConnectionAdapter:
    """Adapts aiosqlite to mimic asyncpg: converts $1->$?, strips ::type casts, unpacks params."""
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    def _convert_sql(self, query: str) -> str:
        # 1. Remove PostgreSQL type casts like ::jsonb, ::text, ::timestamp, etc.
        clean_query = re.sub(r'::[a-zA-Z_][a-zA-Z0-9_]*(?:\[\])?', '', query)
        # 2. Convert PostgreSQL $1, $2, ... placeholders to SQLite ? placeholders
        sqlite_query = re.sub(r'\$\d+', '?', clean_query)
        return sqlite_query

    async def execute(self, query: str, *args):
        sqlite_query = self._convert_sql(query)
        if len(args) == 1 and isinstance(args[0], (tuple, list)):
            params = args[0]
        elif len(args) == 1 and isinstance(args[0], dict):
            params = args[0]
        else:
            params = args
            
        async with self._conn.execute(sqlite_query, params) as cursor:
            await self._conn.commit()
            return f"UPDATE {cursor.rowcount}"

class SovereignDBPool:
    _conn: Optional[aiosqlite.Connection] = None

    @classmethod
    async def initialize(cls):
        if not cls._conn:
            cls._conn = await aiosqlite.connect(DB_PATH)
            cls._conn.row_factory = aiosqlite.Row
            
            # Create the asset_ledger table automatically on startup
            await cls._conn.execute("""
                CREATE TABLE IF NOT EXISTS asset_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    custodian_source TEXT NOT NULL,
                    account_hash TEXT NOT NULL,
                    canonical_payload TEXT NOT NULL,
                    row_signature TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await cls._conn.commit()
            print("Successfully connected to SQLite Sovereign SSOT!")

    @classmethod
    async def close(cls):
        if cls._conn:
            await cls._conn.close()
            cls._conn = None

    @classmethod
    @contextlib.asynccontextmanager
    async def acquire(cls):
        if not cls._conn:
            await cls.initialize()
        yield AsyncPGConnectionAdapter(cls._conn)

    @classmethod
    async def get_connection(cls):
        if not cls._conn:
            await cls.initialize()
        return cls

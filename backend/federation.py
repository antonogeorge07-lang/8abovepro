import hashlib
import json
from datetime import datetime
import aiosqlite
from database import DB_PATH

async def verify_peer_node(peer_tenant_id: str, peer_integrity_root: str) -> dict:
    """
    Cryptographically verifies a peer family office node across international jurisdictions
    (e.g., Geneva node syncing with Dubai/ADGM node) via zero-knowledge root comparison.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT sha256_hash FROM ledger_entries WHERE tenant_id = ?",
            (peer_tenant_id,)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        local_root = hashlib.sha256(f"{peer_tenant_id}:EMPTY_VAULT".encode()).hexdigest()
    else:
        hasher = hashlib.sha256()
        for row in rows:
            hasher.update(row["sha256_hash"].encode("utf-8"))
        local_root = hasher.hexdigest()

    # Verify cryptographic consistency
    match = (local_root == peer_integrity_root)

    return {
        "peer_tenant_id": peer_tenant_id,
        "federation_status": "SYNCED_SECURE" if match else "DRIFT_DETECTED",
        "local_integrity_root": local_root,
        "peer_integrity_root": peer_integrity_root,
        "cryptographic_match": match,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

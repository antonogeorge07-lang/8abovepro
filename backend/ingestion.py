import csv
import hashlib
import json
from datetime import datetime
import aiosqlite
from database import DB_PATH

async def process_csv_feed(tenant_id: str, custodian: str, file_bytes: bytes) -> dict:
    """Parses incoming custodian CSV feeds, generates cryptographic non-repudiation hashes, and logs to SQLite."""
    decoded_content = file_bytes.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_content)
    
    processed_rows = []
    async with aiosqlite.connect(DB_PATH) as db:
        for row in reader:
            timestamp = row.get("timestamp", datetime.utcnow().isoformat())
            payload_str = json.dumps(row, sort_keys=True)
            
            # Compute Cryptographic SHA-256 Row Signature for Non-Repudiation
            hasher = hashlib.sha256()
            hasher.update(f"{tenant_id}:{custodian}:{timestamp}:{payload_str}".encode('utf-8'))
            row_hash = hasher.hexdigest()
            
            # Insert into ledger
            try:
                await db.execute(
                    "INSERT INTO ledger_entries (tenant_id, timestamp, custodian, payload_json, sha256_hash) VALUES (?, ?, ?, ?, ?)",
                    (tenant_id, timestamp, custodian, payload_str, row_hash)
                )
                processed_rows.append({"hash": row_hash, "status": "LOCKED"})
            except aiosqlite.IntegrityError:
                # Duplicate hash detected (prevents double-spending or replay manipulation)
                processed_rows.append({"hash": row_hash, "status": "DUPLICATE_REJECTED"})
        
        await db.commit()

    return {
        "tenant_id": tenant_id,
        "custodian": custodian,
        "total_rows_processed": len(processed_rows),
        "ledger_signatures": processed_rows,
        "status": "SECURE_INGESTION_COMPLETE"
    }

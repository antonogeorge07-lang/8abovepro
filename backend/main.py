import hashlib
import json
import os
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from database import SovereignDBPool

app = FastAPI(
    title="8above.pro Sovereign Core API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

@app.on_event("startup")
async def startup_event():
    await SovereignDBPool.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await SovereignDBPool.close()

class Holding(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)
    shares: float = Field(..., gt=0)
    price: float = Field(..., ge=0)

class CustodianPayload(BaseModel):
    account_id: str = Field(..., min_length=5)
    base_currency: str = Field(..., min_length=3, max_length=3)
    total_valuation: float = Field(..., ge=0)
    holdings: List[Holding]
    as_of_timestamp: str

class IngestionRequest(BaseModel):
    tenant_id: str
    custodian_source: str
    payload: CustodianPayload

def generate_immutable_hash(tenant_id: str, payload_dict: dict) -> str:
    canonical_payload = json.dumps(payload_dict, sort_keys=True)
    tenant_salt = os.getenv(f"SALT_{tenant_id}", "DEFAULT_SOVEREIGN_ROOT_SALT")
    signature_string = f"{tenant_salt}::{canonical_payload}"
    return hashlib.sha256(signature_string.encode('utf-8')).hexdigest()

@app.post("/v1/ingest/ledger", status_code=status.HTTP_201_CREATED)
async def ingest_custodian_data(data: IngestionRequest):
    try:
        payload_dict = data.payload.dict()
        account_hash = hashlib.sha256(data.payload.account_id.encode('utf-8')).hexdigest()
        row_signature = generate_immutable_hash(data.tenant_id, payload_dict)
        
        pool = await SovereignDBPool.get_connection()
        
        async with pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO asset_ledger (tenant_id, custodian_source, account_hash, canonical_payload, row_signature)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                """,
                data.tenant_id,
                data.custodian_source,
                account_hash,
                json.dumps(payload_dict),
                row_signature
            )

        return {
            "status": "VERIFIED_AND_LOCKED_IN_SSOT",
            "ledger_receipt": {
                "tenant_id": data.tenant_id,
                "custodian": data.custodian_source,
                "cryptographic_proof": row_signature[:16] + "...",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingestion pipeline halted: {str(e)}"
        )

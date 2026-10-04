import hashlib
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import SovereignDBPool
from ingestion import process_csv_feed
from legislation_engine import JurisdictionMonitor

app = FastAPI(
    title="8above.pro Sovereign Core & Law-Adapter API",
    version="2.0.0",
    description="Institutional Sovereign Asset Ledger with Autonomous Legislative Impact Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

legislative_monitor = JurisdictionMonitor()

@app.on_event("startup")
async def startup_event():
    await SovereignDBPool.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await SovereignDBPool.close()

class TenantProfileCheck(BaseModel):
    tenant_id: str
    jurisdiction: str = Field(..., description="e.g. CH_SWITZERLAND, UAE_DIFC, IN_SEBI")
    held_asset_classes: List[str]

@app.get("/v1/health")
async def health_check():
    return {"status": "ONLINE", "mode": "SOVEREIGN_AIR_GAPPED", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.post("/v1/governance/impact-radar")
async def check_legislative_impact(profile: TenantProfileCheck):
    """Dynamically scans pipeline and enacted laws, returning Good/Moderate/Bad/Worse impact flags."""
    try:
        exposures = legislative_monitor.evaluate_tenant_exposure(profile.jurisdiction, profile.held_asset_classes)
        return {
            "tenant_id": profile.tenant_id,
            "monitored_jurisdiction": profile.jurisdiction,
            "total_alerts": len(exposures),
            "impact_assessment_matrix": exposures,
            "audit_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impact radar failure: {str(e)}")

@app.post("/v1/ingest/statement")
async def ingest_statement(
    tenant_id: str = Form(...),
    custodian: str = Form(...),
    file: UploadFile = File(...)
):
    """Ingests multi-custodian CSV statements with SHA-256 cryptographic non-repudiation."""
    try:
        file_bytes = await file.read()
        result = await process_csv_feed(tenant_id, custodian, file_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline error: {str(e)}")

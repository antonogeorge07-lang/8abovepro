from account_api import router as account_router
import hashlib
import json
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from database import SovereignDBPool
from auth_context import PrincipalContext
from authorization import Permission
from auth_dependency import current_principal, permission_required
from fastapi import Depends
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

app.include_router(account_router)

@app.on_event("startup")
async def startup_event():
    await SovereignDBPool.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await SovereignDBPool.close()

class TenantProfileCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jurisdiction: str = Field(
        ...,
        description="e.g. CH_SWITZERLAND, UAE_DIFC, IN_SEBI",
    )
    held_asset_classes: List[str]



@app.get("/v1/me")
async def get_current_identity(
    principal: PrincipalContext = Depends(current_principal),
):
    return {
        "user_id": principal.user_id,
        "email": principal.email,
        "organization": {
            "id": principal.organization_id,
            "name": principal.organization_name,
        },
        "membership_id": principal.membership_id,
        "role": principal.role.value,
    }


@app.get("/v1/health")
async def health_check():
    return {"status": "ONLINE", "mode": "SOVEREIGN_AIR_GAPPED", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.post("/v1/governance/impact-radar")
async def check_legislative_impact(
    profile: TenantProfileCheck,
    principal: PrincipalContext = Depends(
        permission_required(Permission.PORTFOLIO_READ)
    ),
):
    """Evaluates legislative exposure for the authenticated organization."""
    try:
        exposures = legislative_monitor.evaluate_tenant_exposure(
            profile.jurisdiction,
            profile.held_asset_classes,
        )

        return {
            "tenant_id": principal.organization_id,
            "monitored_jurisdiction": profile.jurisdiction,
            "total_alerts": len(exposures),
            "impact_assessment_matrix": exposures,
            "audit_timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="impact_radar_failure",
        )

@app.post("/v1/ingest/statement")
async def ingest_statement(
    custodian: str = Form(...),
    file: UploadFile = File(...),
    principal: PrincipalContext = Depends(
        permission_required(Permission.LEDGER_INGEST)
    ),
):
    """Ingests statements into the authenticated organization's ledger."""
    try:
        file_bytes = await file.read()

        result = await process_csv_feed(
            principal.organization_id,
            custodian,
            file_bytes,
        )

        return result

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="ingestion_pipeline_error",
        )

from audit_exporter import generate_zk_audit_package

@app.get("/v1/audit/export")
async def export_audit_package(
    principal: PrincipalContext = Depends(
        permission_required(Permission.AUDIT_EXPORT)
    ),
):
    """Generates an audit package scoped to the authenticated organization."""
    try:
        package = await generate_zk_audit_package(
            principal.organization_id
        )
        return package
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="audit_package_generation_failed",
        )

from federation import verify_peer_node
from pydantic import BaseModel

class PeerSyncRequest(BaseModel):
    peer_tenant_id: str
    peer_integrity_root: str

@app.post("/v1/federation/verify-peer")
async def verify_peer(req: PeerSyncRequest):
    """Handshake endpoint for cross-border sovereign node synchronization."""
    try:
        result = await verify_peer_node(req.peer_tenant_id, req.peer_integrity_root)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Federation verification failed: {str(e)}")

from dispatcher import SovereignAlert, dispatch_sovereign_alert

@app.post("/v1/dispatch/alert")
async def send_sovereign_alert(alert: SovereignAlert):
    """Dispatches real-time autonomous security and legislative alerts to private channels."""
    try:
        result = await dispatch_sovereign_alert(alert)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert dispatch failed: {str(e)}")

from assistant import ExecutiveQuery, process_executive_query

@app.post("/v1/assistant/query")
async def executive_assistant_query(
    q: ExecutiveQuery,
    principal: PrincipalContext = Depends(
        permission_required(Permission.ASSISTANT_USE)
    ),
):
    """Natural-language intelligence scoped to the authenticated organization."""
    try:
        result = await process_executive_query(
            principal.organization_id,
            q.query_text,
        )
        return result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="executive_query_processing_failed",
        )

from liquidity import LiquidityOverviewRequest, calculate_sovereign_liquidity

@app.post("/v1/liquidity/overview")
async def sovereign_liquidity_overview(
    req: LiquidityOverviewRequest,
    principal: PrincipalContext = Depends(
        permission_required(Permission.PORTFOLIO_READ)
    ),
):
    """Liquidity overview scoped to the authenticated organization."""
    try:
        result = await calculate_sovereign_liquidity(
            principal.organization_id,
            req.base_currency,
        )
        return result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="liquidity_calculation_failed",
        )

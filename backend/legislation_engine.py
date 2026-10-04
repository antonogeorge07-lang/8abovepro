from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class LegislativeItem(BaseModel):
    bill_id: str
    jurisdiction: str = Field(..., description="e.g., CH_SWITZERLAND, UAE_DIFC, IN_SEBI")
    title: str
    status: str = Field(..., description="IN_DISCUSSION, PIPELINE, DECIDED")
    summary: str
    impact_level: str = Field(..., description="GOOD, MODERATE, BAD, WORSE")
    affected_asset_classes: List[str]
    statutory_reference: str

class JurisdictionMonitor:
    def __init__(self):
        self.active_pipeline: List[LegislativeItem] = [
            LegislativeItem(
                bill_id="CH-FADP-2026-03",
                jurisdiction="CH_SWITZERLAND",
                title="Cross-Border Data Residency & Non-Coercion Act Update",
                status="PIPELINE",
                summary="Tightens cross-border data transfer parameters for non-tenant cloud storage holding multi-custodian assets.",
                impact_level="BAD",
                affected_asset_classes=["EQUITIES", "BULLION", "PRIVATE_EQUITY"],
                statutory_reference="Swiss FADP Art. 16 / Revised Banking Act Guidance"
            ),
            LegislativeItem(
                bill_id="DIFC-AI-2026-01",
                jurisdiction="UAE_DIFC",
                title="AI-Native Financial Center Autonomous Systems Mandate",
                status="DECIDED",
                summary="Mandates explicit cryptographic audit trails and Autonomous Systems Officer (ASO) oversight for automated wealth ledgers.",
                impact_level="GOOD",
                affected_asset_classes=["ALL"],
                statutory_reference="DIFC Data Protection Reg 10 / Amendment Law No. 1 of 2025"
            )
        ]

    def evaluate_tenant_exposure(self, tenant_jurisdiction: str, asset_classes: List[str]) -> List[Dict]:
        exposures = []
        for item in self.active_pipeline:
            if item.jurisdiction == tenant_jurisdiction or item.jurisdiction == "GLOBAL":
                if "ALL" in item.affected_asset_classes or any(ac in item.affected_asset_classes for ac in asset_classes):
                    exposures.append({
                        "bill_id": item.bill_id,
                        "title": item.title,
                        "status": item.status,
                        "impact_tier": item.impact_level,
                        "actionable_notice": item.summary,
                        "statutory_reference": item.statutory_reference,
                        "flagged_at": datetime.utcnow().isoformat()
                    })
        return exposures

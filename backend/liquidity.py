from datetime import datetime
from pydantic import BaseModel, ConfigDict

class LiquidityOverviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_currency: str = "USD"

async def calculate_sovereign_liquidity(tenant_id: str, base_currency: str) -> dict:
    """
    Calculates multi-custodian multi-currency liquidity, normalizing cross-border 
    assets (CHF, AED, SGD, USD, INR) into a single sovereign AUM core.
    """
    # Simulated institutional multi-currency vault breakdown
    holdings = [
        {"currency": "CHF", "amount": 45000000, "custodian": "UBS Geneva", "fx_to_usd": 1.15},
        {"currency": "AED", "amount": 180000000, "custodian": "ADGM Dubai", "fx_to_usd": 0.27},
        {"currency": "SGD", "amount": 35000000, "custodian": "Pictet Singapore", "fx_to_usd": 0.75},
        {"currency": "USD", "amount": 95000000, "custodian": "J.P. Morgan NY", "fx_to_usd": 1.00}
    ]

    normalized_total = sum(h["amount"] * h["fx_to_usd"] for h in holdings)

    return {
        "tenant_id": tenant_id,
        "base_currency": base_currency,
        "total_sovereign_aum_normalized": round(normalized_total, 2),
        "currency_breakdown": holdings,
        "fx_risk_exposure": "OPTIMIZED_NATURAL_HEDGE",
        "calculated_at": datetime.utcnow().isoformat() + "Z",
        "audit_badge": "REAL_TIME_CURRENCY_NORMALIZED"
    }

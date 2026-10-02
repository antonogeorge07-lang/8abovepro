from pydantic import BaseModel


class CustodianSummary(BaseModel):
    id: str
    name: str
    value: float
    currency: str
    verified: bool


class PortfolioSummary(BaseModel):
    total_assets: float
    currency: str
    custodian_count: int
    verified_custodian_count: int
    custodians: list[CustodianSummary]

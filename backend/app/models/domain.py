from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    CASH = "cash"
    EQUITY = "equity"
    BOND = "bond"
    FUND = "fund"
    DIGITAL_ASSET = "digital_asset"
    COMMODITY = "commodity"
    OTHER = "other"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


class LedgerEntryType(str, Enum):
    POSITION_CREATED = "position_created"
    POSITION_UPDATED = "position_updated"
    VALUATION_UPDATED = "valuation_updated"
    VERIFICATION_COMPLETED = "verification_completed"


class Asset(BaseModel):
    id: str
    name: str
    symbol: Optional[str] = None
    asset_type: AssetType
    currency: str = "USD"


class Custodian(BaseModel):
    id: str
    name: str
    jurisdiction: Optional[str] = None
    verified: bool = False


class Account(BaseModel):
    id: str
    portfolio_id: str
    custodian_id: str
    name: str
    currency: str = "USD"


class Position(BaseModel):
    id: str
    account_id: str
    asset_id: str
    quantity: float = Field(ge=0)
    unit_price: float = Field(ge=0)
    currency: str = "USD"

    @property
    def market_value(self) -> float:
        return self.quantity * self.unit_price


class VerificationRecord(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    status: VerificationStatus
    checksum: str
    verified_at: Optional[datetime] = None


class LedgerEntry(BaseModel):
    id: str
    entry_type: LedgerEntryType
    entity_type: str
    entity_id: str
    checksum: str
    created_at: datetime


class Portfolio(BaseModel):
    id: str
    name: str
    base_currency: str = "USD"

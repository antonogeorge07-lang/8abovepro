from fastapi import APIRouter

from app.models.portfolio import PortfolioSummary
from app.services.portfolio import get_portfolio_summary

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=PortfolioSummary)
def portfolio_summary() -> PortfolioSummary:
    return get_portfolio_summary()

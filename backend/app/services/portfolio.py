from app.models.portfolio import CustodianSummary, PortfolioSummary


def get_portfolio_summary() -> PortfolioSummary:
    custodians = [
        CustodianSummary(
            id="swiss-custody-a",
            name="Swiss Custody A",
            value=64_120_000,
            currency="USD",
            verified=True,
        ),
        CustodianSummary(
            id="difc-regional-hub",
            name="DIFC Regional Hub",
            value=51_430_420,
            currency="USD",
            verified=True,
        ),
        CustodianSummary(
            id="liquid-yield-reserves",
            name="Liquid Yield / Reserves",
            value=27_300_000,
            currency="USD",
            verified=True,
        ),
    ]

    total_assets = sum(item.value for item in custodians)

    return PortfolioSummary(
        total_assets=total_assets,
        currency="USD",
        custodian_count=len(custodians),
        verified_custodian_count=sum(1 for item in custodians if item.verified),
        custodians=custodians,
    )

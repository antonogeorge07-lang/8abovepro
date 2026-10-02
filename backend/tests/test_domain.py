from app.models.domain import (
    Asset,
    AssetType,
    Custodian,
    Position,
)


def test_position_market_value():
    position = Position(
        id="pos-1",
        account_id="account-1",
        asset_id="asset-1",
        quantity=100,
        unit_price=25.5,
        currency="USD",
    )

    assert position.market_value == 2550


def test_asset_model():
    asset = Asset(
        id="asset-1",
        name="Cash Reserve",
        symbol="USD",
        asset_type=AssetType.CASH,
        currency="USD",
    )

    assert asset.asset_type == AssetType.CASH


def test_custodian_model():
    custodian = Custodian(
        id="custodian-1",
        name="Swiss Custody A",
        jurisdiction="CH",
        verified=True,
    )

    assert custodian.verified is True

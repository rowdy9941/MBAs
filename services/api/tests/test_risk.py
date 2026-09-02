from app.main import RISK_LEVELS


def test_refunds_are_red_risk():
    assert RISK_LEVELS["payment.refund"] == "red"


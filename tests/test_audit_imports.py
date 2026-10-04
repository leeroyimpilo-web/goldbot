from app.audit import record_heartbeat, record_order_attempt, record_risk_snapshot


def test_audit_functions_exist():
    assert callable(record_heartbeat)
    assert callable(record_risk_snapshot)
    assert callable(record_order_attempt)

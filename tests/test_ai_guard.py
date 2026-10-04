from app.ai_guard import evaluate_ai_gate


def test_unapproved_ai_cannot_block_rule_strategy():
    result = evaluate_ai_gate(0.1, model_approved=False)
    assert result.allowed is True
    assert result.reason == "ai_observer_only"


def test_approved_ai_can_filter_low_probability():
    result = evaluate_ai_gate(0.4, threshold=0.58, model_approved=True)
    assert result.allowed is False

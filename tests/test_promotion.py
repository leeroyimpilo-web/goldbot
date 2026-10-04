from app.promotion import evaluate_demo_to_live, evaluate_research_to_demo


def test_research_candidate_must_pass_all_gates():
    result = evaluate_research_to_demo(
        oos_profit_factor=1.3,
        oos_expectancy_r=0.08,
        oos_max_drawdown_pct=6.5,
        stress_profit_factor=1.05,
        profitable_years=3,
        parameter_stable=True,
        best_trades_dependency_ok=True,
    )
    assert result.approved is True
    assert result.target_stage == "demo"


def test_weak_candidate_stays_in_research():
    result = evaluate_research_to_demo(
        oos_profit_factor=1.05,
        oos_expectancy_r=-0.01,
        oos_max_drawdown_pct=12.0,
        stress_profit_factor=0.9,
        profitable_years=1,
        parameter_stable=False,
        best_trades_dependency_ok=False,
    )
    assert result.approved is False
    assert result.target_stage == "research"
    assert len(result.reasons) >= 5


def test_demo_requires_minimum_evidence():
    result = evaluate_demo_to_live(
        demo_trading_days=60,
        demo_trades=100,
        risk_rule_violations=0,
        unexplained_position_mismatches=0,
        slippage_model_compatible=True,
        kill_switch_tests_passed=True,
        restart_recovery_passed=True,
    )
    assert result.approved is True
    assert result.target_stage == "small_live"

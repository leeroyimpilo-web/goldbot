from app.experiments import make_experiment, parameter_hash


def test_parameter_hash_is_stable():
    a = parameter_hash({"adx": 22, "atr": 1.2})
    b = parameter_hash({"atr": 1.2, "adx": 22})
    assert a == b


def test_experiment_contains_reproducibility_fields():
    e = make_experiment(
        strategy_name="mtf_breakout",
        strategy_version="mtf_breakout_v1",
        stage="research",
        parameters={"adx": 22},
        metrics={"profit_factor": 1.2},
    )
    assert e.experiment_id
    assert e.parameter_hash
    assert e.stage == "research"

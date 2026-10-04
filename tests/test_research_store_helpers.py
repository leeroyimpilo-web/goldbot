from app.experiments import make_experiment


def test_experiment_shape_for_persistence():
    experiment = make_experiment(
        strategy_name="mtf_breakout",
        strategy_version="mtf_breakout_v1",
        stage="research",
        parameters={"adx": 22},
        metrics={"profit_factor": 1.25},
    )
    payload = experiment.to_dict()
    assert payload["parameter_hash"]
    assert payload["stage"] == "research"

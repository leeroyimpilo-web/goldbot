from app.runner import load_state


def test_missing_state_file_is_safe(monkeypatch, tmp_path):
    import app.runner as runner
    monkeypatch.setattr(runner, "STATE_PATH", tmp_path / "missing.json")
    assert load_state() == {}

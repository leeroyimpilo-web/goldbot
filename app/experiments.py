from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    created_at: str
    strategy_name: str
    strategy_version: str
    stage: str
    parameters: dict
    parameter_hash: str
    metrics: dict
    notes: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def parameter_hash(parameters: dict) -> str:
    canonical = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def make_experiment(
    *,
    strategy_name: str,
    strategy_version: str,
    stage: str,
    parameters: dict,
    metrics: dict,
    notes: str | None = None,
) -> Experiment:
    return Experiment(
        experiment_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        strategy_name=strategy_name,
        strategy_version=strategy_version,
        stage=stage,
        parameters=parameters,
        parameter_hash=parameter_hash(parameters),
        metrics=metrics,
        notes=notes,
    )

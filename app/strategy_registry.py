from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal, StrategyVersion


def get_strategy(version: str) -> dict | None:
    with SessionLocal() as session:
        row = session.scalar(
            select(StrategyVersion).where(StrategyVersion.version == version)
        )
        if row is None:
            return None
        return {
            "id": row.id,
            "name": row.name,
            "version": row.version,
            "stage": row.stage,
            "parameters": row.parameters,
            "metrics": row.metrics,
            "live_approved": row.live_approved,
        }


def is_strategy_approved(version: str, trading_mode: str) -> bool:
    record = get_strategy(version)
    if record is None:
        return False

    stage = str(record["stage"]).lower()
    mode = trading_mode.lower()

    if mode == "demo":
        return stage in {"demo", "small_live", "live"}
    if mode == "live":
        return stage in {"small_live", "live"} and bool(record["live_approved"])
    return False


def register_strategy(
    *,
    name: str,
    version: str,
    stage: str = "research",
    parameters: dict | None = None,
    metrics: dict | None = None,
    live_approved: bool = False,
) -> dict:
    if live_approved and stage not in {"small_live", "live"}:
        raise ValueError("live_approved requires small_live or live stage")

    with SessionLocal() as session:
        row = session.scalar(
            select(StrategyVersion).where(StrategyVersion.version == version)
        )
        if row is None:
            row = StrategyVersion(
                name=name,
                version=version,
                stage=stage,
                parameters=parameters or {},
                metrics=metrics or {},
                live_approved=live_approved,
            )
            session.add(row)
        else:
            row.name = name
            row.stage = stage
            row.parameters = parameters or row.parameters
            row.metrics = metrics or row.metrics
            row.live_approved = live_approved

        session.commit()
        session.refresh(row)
        return {
            "id": row.id,
            "name": row.name,
            "version": row.version,
            "stage": row.stage,
            "live_approved": row.live_approved,
            "parameters": row.parameters,
            "metrics": row.metrics,
        }

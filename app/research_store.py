from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select

from app.database import BacktestRun, ExperimentRecord, ResearchNote, SessionLocal
from app.experiments import Experiment


def save_backtest(
    *,
    strategy_version: str,
    data_source: str,
    parameters: dict,
    metrics: dict,
    assumptions: dict,
    data_start: datetime | None = None,
    data_end: datetime | None = None,
) -> int:
    with SessionLocal() as session:
        row = BacktestRun(
            strategy_version=strategy_version,
            data_source=data_source,
            data_start=data_start,
            data_end=data_end,
            parameters=parameters,
            metrics=metrics,
            assumptions=assumptions,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def save_experiment(
    experiment: Experiment,
    *,
    score: float | None = None,
    promotion_decision: dict | None = None,
) -> int:
    with SessionLocal() as session:
        row = ExperimentRecord(
            experiment_id=experiment.experiment_id,
            strategy_name=experiment.strategy_name,
            strategy_version=experiment.strategy_version,
            stage=experiment.stage,
            parameter_hash=experiment.parameter_hash,
            parameters=experiment.parameters,
            metrics=experiment.metrics,
            score=score,
            promotion_decision=promotion_decision or {},
            notes=experiment.notes,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def save_research_note(
    *,
    category: str,
    title: str,
    observation: str,
    evidence: dict,
    recommendation: str | None = None,
    strategy_version: str | None = None,
) -> int:
    with SessionLocal() as session:
        row = ResearchNote(
            category=category,
            title=title,
            observation=observation,
            evidence=evidence,
            recommendation=recommendation,
            strategy_version=strategy_version,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def recent_experiments(limit: int = 50) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(ExperimentRecord).order_by(desc(ExperimentRecord.created_at)).limit(limit)
        ).all()
        return [
            {
                "id": r.id,
                "experiment_id": r.experiment_id,
                "created_at": r.created_at.isoformat(),
                "strategy_name": r.strategy_name,
                "strategy_version": r.strategy_version,
                "stage": r.stage,
                "parameter_hash": r.parameter_hash,
                "parameters": r.parameters,
                "metrics": r.metrics,
                "score": r.score,
                "promotion_decision": r.promotion_decision,
                "notes": r.notes,
            }
            for r in rows
        ]


def recent_research_notes(limit: int = 50) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        rows = session.scalars(
            select(ResearchNote).order_by(desc(ResearchNote.created_at)).limit(limit)
        ).all()
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "strategy_version": r.strategy_version,
                "category": r.category,
                "title": r.title,
                "observation": r.observation,
                "evidence": r.evidence,
                "recommendation": r.recommendation,
                "status": r.status,
            }
            for r in rows
        ]

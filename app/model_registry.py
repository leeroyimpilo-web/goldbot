from __future__ import annotations

from sqlalchemy import desc, select

from app.database import ModelVersion, SessionLocal
from app.ml_meta import FEATURE_COLUMNS


def register_model(
    *,
    name: str,
    version: str,
    stage: str,
    artifact_path: str,
    metrics: dict,
    approved_for_filtering: bool = False,
) -> dict:
    if approved_for_filtering and stage not in {"validated", "demo", "live"}:
        raise ValueError("AI filtering approval requires validated/demo/live stage")

    with SessionLocal() as session:
        row = session.scalar(select(ModelVersion).where(ModelVersion.version == version))
        if row is None:
            row = ModelVersion(
                name=name,
                version=version,
                stage=stage,
                artifact_path=artifact_path,
                feature_columns={"columns": FEATURE_COLUMNS},
                metrics=metrics,
                approved_for_filtering=approved_for_filtering,
            )
            session.add(row)
        else:
            row.name = name
            row.stage = stage
            row.artifact_path = artifact_path
            row.metrics = metrics
            row.approved_for_filtering = approved_for_filtering

        session.commit()
        session.refresh(row)
        return {
            "id": row.id,
            "name": row.name,
            "version": row.version,
            "stage": row.stage,
            "artifact_path": row.artifact_path,
            "metrics": row.metrics,
            "approved_for_filtering": row.approved_for_filtering,
        }


def latest_approved_model() -> dict | None:
    with SessionLocal() as session:
        row = session.scalar(
            select(ModelVersion)
            .where(ModelVersion.approved_for_filtering.is_(True))
            .order_by(desc(ModelVersion.created_at))
            .limit(1)
        )
        if row is None:
            return None
        return {
            "name": row.name,
            "version": row.version,
            "stage": row.stage,
            "artifact_path": row.artifact_path,
            "metrics": row.metrics,
            "approved_for_filtering": row.approved_for_filtering,
        }

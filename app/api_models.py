from pydantic import BaseModel, Field


class StrategyRegistrationRequest(BaseModel):
    name: str
    version: str
    stage: str = "research"
    parameters: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    live_approved: bool = False


class MetaTrainingRequest(BaseModel):
    version: str
    rows: list[dict]
    stage: str = "observer"


class EconomicEventRequest(BaseModel):
    name: str
    scheduled_at: str
    impact: str = "high"
    currency: str = "USD"
    source: str | None = None
    external_id: str | None = None

from pydantic import BaseModel, Field


class StrategyRegistrationRequest(BaseModel):
    name: str
    version: str
    stage: str = "research"
    parameters: dict = Field(default_factory=dict)
    metrics: dict = Field(default_factory=dict)
    live_approved: bool = False

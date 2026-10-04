from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AIGateDecision:
    allowed: bool
    probability: float | None
    threshold: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_ai_gate(
    probability: float | None,
    *,
    threshold: float = 0.58,
    model_approved: bool = False,
) -> AIGateDecision:
    if not model_approved:
        return AIGateDecision(
            allowed=True,
            probability=probability,
            threshold=threshold,
            reason="ai_observer_only",
        )

    if probability is None:
        return AIGateDecision(
            allowed=False,
            probability=None,
            threshold=threshold,
            reason="approved_ai_model_missing_prediction",
        )

    return AIGateDecision(
        allowed=probability >= threshold,
        probability=probability,
        threshold=threshold,
        reason="ai_probability_passed" if probability >= threshold else "ai_probability_below_threshold",
    )

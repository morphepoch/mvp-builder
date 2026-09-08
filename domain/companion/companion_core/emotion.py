"""Deterministic emotion state and response-policy engine.

The model may extract an EmotionSignal, but only this module mutates state and
decides response constraints. This separation makes behaviour testable and
portable across model vendors.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from math import exp, log, isfinite
from uuid import uuid4


VALID_NEEDS = {"listen", "reassure", "celebrate", "problem_solve", "space", "safety"}
VALID_RISKS = {"none", "low", "high", "urgent"}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class EmotionSignal:
    primary: str = "neutral"
    valence: float = 0.0       # -1 unpleasant, +1 pleasant
    arousal: float = 0.0       # 0 calm, 1 activated
    intensity: float = 0.0     # 0 weak, 1 strong
    confidence: float = 0.0
    need: str = "listen"
    risk: str = "none"
    cues: tuple[str, ...] = ()

    def normalized(self) -> "EmotionSignal":
        if not all(isfinite(x) for x in (self.valence, self.arousal, self.intensity, self.confidence)):
            raise ValueError("Emotion scores must be finite numbers")
        return replace(
            self,
            primary=(self.primary or "neutral").strip().lower(),
            valence=_clamp(self.valence, -1.0, 1.0),
            arousal=_clamp(self.arousal, 0.0, 1.0),
            intensity=_clamp(self.intensity, 0.0, 1.0),
            confidence=_clamp(self.confidence, 0.0, 1.0),
            need=self.need if self.need in VALID_NEEDS else "listen",
            risk=self.risk if self.risk in VALID_RISKS else "high",
            cues=tuple(cue[:120] for cue in self.cues[:5]),
        )


@dataclass(frozen=True)
class EmotionState:
    primary: str = "neutral"
    valence: float = 0.0
    arousal: float = 0.0
    intensity: float = 0.0
    confidence: float = 0.0
    need: str = "listen"
    risk: str = "none"
    negative_streak: int = 0
    positive_streak: int = 0
    episode_id: str = ""
    updated_at: datetime | None = None


@dataclass(frozen=True)
class EmotionPolicy:
    half_life_hours: float = 8.0
    update_gain: float = 0.72
    switch_margin: float = 0.12
    episode_threshold: float = 0.55
    low_confidence_floor: float = 0.35

    def __post_init__(self) -> None:
        if self.half_life_hours <= 0 or not isfinite(self.half_life_hours):
            raise ValueError("half_life_hours must be positive and finite")
        if not all(isfinite(x) and 0 <= x <= 1 for x in (self.update_gain, self.switch_margin, self.episode_threshold, self.low_confidence_floor)):
            raise ValueError("Emotion thresholds must be in [0, 1]")


@dataclass(frozen=True)
class EmotionDecision:
    mode: str
    max_sentences: int
    advice_allowed: bool
    ask_one_question: bool
    follow_up_after_minutes: int | None
    proactive_eligible: bool
    safety_escalation: bool


def _decay(value: float, hours: float, half_life: float) -> float:
    if half_life <= 0:
        return 0.0
    return value * exp(-log(2) * max(0.0, hours) / half_life)


def reduce_emotion(
    previous: EmotionState,
    raw_signal: EmotionSignal,
    *,
    now: datetime | None = None,
    policy: EmotionPolicy = EmotionPolicy(),
) -> tuple[EmotionState, EmotionDecision]:
    """Reduce one extracted signal into durable state and response constraints."""
    signal = raw_signal.normalized()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must have a timezone")
    elapsed_hours = 0.0
    if previous.updated_at is not None:
        if previous.updated_at.tzinfo is None or previous.updated_at.utcoffset() is None:
            raise ValueError("updated_at must have a timezone")
        if now < previous.updated_at:
            raise ValueError("Reject out-of-order emotion events")
        elapsed_hours = max(0.0, (now - previous.updated_at).total_seconds() / 3600)

    old_intensity = _decay(previous.intensity, elapsed_hours, policy.half_life_hours)
    weight = policy.update_gain * signal.confidence
    intensity = _clamp(old_intensity * (1 - weight) + signal.intensity * weight, 0, 1)
    valence = _clamp(_decay(previous.valence, elapsed_hours, policy.half_life_hours) * (1 - weight) + signal.valence * weight, -1, 1)
    arousal = _clamp(_decay(previous.arousal, elapsed_hours, policy.half_life_hours) * (1 - weight) + signal.arousal * weight, 0, 1)

    can_switch = (
        signal.confidence >= policy.low_confidence_floor
        and signal.intensity >= max(old_intensity + policy.switch_margin, policy.episode_threshold)
    )
    primary = signal.primary if can_switch or (previous.primary == "neutral" and signal.confidence >= policy.low_confidence_floor) else previous.primary
    new_episode = primary != previous.primary and intensity >= policy.episode_threshold
    episode_id = str(uuid4()) if new_episode or not previous.episode_id else previous.episode_id

    negative = valence < -0.2
    positive = valence > 0.2
    state = EmotionState(
        primary=primary,
        valence=valence,
        arousal=arousal,
        intensity=intensity,
        confidence=signal.confidence,
        need=signal.need,
        risk=signal.risk,
        negative_streak=previous.negative_streak + 1 if negative else 0,
        positive_streak=previous.positive_streak + 1 if positive else 0,
        episode_id=episode_id,
        updated_at=now,
    )

    # Durable state is deliberately smoothed, while the current reply must react
    # immediately to a high-confidence strong signal.
    response_intensity = max(intensity, signal.intensity * signal.confidence)

    if signal.risk in {"high", "urgent"} or previous.risk in {"high", "urgent"}:
        # Clearing a safety episode is the host's explicit responsibility.
        state = replace(state, risk="urgent" if "urgent" in (signal.risk, previous.risk) else "high")
        decision = EmotionDecision("safety", 5, False, True, None, False, True)
    elif signal.need == "space":
        decision = EmotionDecision("give_space", 2, False, False, None, False, False)
    elif signal.confidence < policy.low_confidence_floor:
        decision = EmotionDecision("natural", 4, False, False, None, False, False)
    elif signal.valence > 0.2 and response_intensity >= 0.55:
        decision = EmotionDecision("celebrate", 4, False, True, None, False, False)
    elif signal.valence < -0.2 and response_intensity >= 0.75:
        decision = EmotionDecision("contain", 4, False, True, 60, True, False)
    elif signal.valence < -0.2 and response_intensity >= 0.5:
        decision = EmotionDecision("support", 5, signal.need == "problem_solve", True, 180, True, False)
    else:
        decision = EmotionDecision("natural", 6, signal.need == "problem_solve", False, None, False, False)
    return state, decision

"""Portable primitives for AI companion products."""

from .emotion import EmotionDecision, EmotionPolicy, EmotionSignal, EmotionState, reduce_emotion
from .fallback import FailureKind, FallbackDecision, FallbackPolicy
from .frequency import ContactCandidate, ContactContext, ContactDecision, ContactPolicy, evaluate_contact
from .prompt_stack import PromptLayer, PromptStack, PreparedTurn

__all__ = [
    "ContactCandidate",
    "ContactContext",
    "ContactDecision",
    "ContactPolicy",
    "EmotionDecision",
    "EmotionPolicy",
    "EmotionSignal",
    "EmotionState",
    "FailureKind",
    "FallbackDecision",
    "FallbackPolicy",
    "PreparedTurn",
    "PromptLayer",
    "PromptStack",
    "evaluate_contact",
    "reduce_emotion",
]

"""Deterministic outbound-contact budget and frequency gate."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from hashlib import sha256


class ContactDecision(str, Enum):
    SEND = "send"
    DEFER = "defer"
    SILENCE = "silence"


@dataclass(frozen=True)
class ContactCandidate:
    key: str
    due_at: datetime
    reason: str
    hard: bool = False
    user_requested: bool = False
    expires_at: datetime | None = None


@dataclass(frozen=True)
class ContactContext:
    now: datetime
    contact_enabled: bool = True
    soft_contact_opt_in: bool = False
    already_delivered: bool = False
    last_user_message_at: datetime | None = None
    last_outbound_at: datetime | None = None
    outbound_today: int = 0
    outbound_this_week: int = 0
    consecutive_unanswered: int = 0
    active_conversation: bool = False


@dataclass(frozen=True)
class ContactPolicy:
    quiet_start: time = time(22, 30)
    quiet_end: time = time(9, 0)
    daily_soft_limit: int = 2
    weekly_soft_limit: int = 5
    minimum_gap: timedelta = timedelta(hours=6)
    active_chat_suppression: timedelta = timedelta(minutes=30)
    unanswered_backoff_days: tuple[int, ...] = (3, 7, 14, 30)
    spread_minutes: int = 59

    def __post_init__(self) -> None:
        if self.daily_soft_limit < 0 or self.weekly_soft_limit < 0:
            raise ValueError("Contact budgets must be non-negative")
        if self.minimum_gap.total_seconds() < 0 or self.active_chat_suppression.total_seconds() < 0:
            raise ValueError("Contact intervals must be non-negative")
        if not self.unanswered_backoff_days or any(d <= 0 for d in self.unanswered_backoff_days):
            raise ValueError("Backoff must contain positive day intervals")


@dataclass(frozen=True)
class FrequencyResult:
    decision: ContactDecision
    reason: str
    next_at: datetime | None = None


def deterministic_spread(user_id: str, key: str, max_minutes: int = 59) -> int:
    if max_minutes <= 0:
        return 0
    digest = sha256(f"{user_id}:{key}".encode()).digest()
    return int.from_bytes(digest[:4], "big") % (max_minutes + 1)


def _in_quiet_hours(value: time, policy: ContactPolicy) -> bool:
    if policy.quiet_start <= policy.quiet_end:
        return policy.quiet_start <= value < policy.quiet_end
    return value >= policy.quiet_start or value < policy.quiet_end


def _next_allowed_morning(now: datetime, policy: ContactPolicy) -> datetime:
    candidate = now.replace(
        hour=policy.quiet_end.hour,
        minute=policy.quiet_end.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def evaluate_contact(
    candidate: ContactCandidate,
    context: ContactContext,
    *,
    policy: ContactPolicy = ContactPolicy(),
) -> FrequencyResult:
    """Gate a due outbound message before invoking the expensive conversation model."""
    now = context.now
    for value in (now, candidate.due_at, candidate.expires_at, context.last_user_message_at, context.last_outbound_at):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Use timezone-aware datetimes; context.now must be in the user's timezone")
    if not context.contact_enabled:
        return FrequencyResult(ContactDecision.SILENCE, "contact_disabled")
    if context.already_delivered:
        return FrequencyResult(ContactDecision.SILENCE, "already_delivered")
    if candidate.hard and not candidate.user_requested:
        return FrequencyResult(ContactDecision.SILENCE, "unverified_hard_commitment")
    if candidate.expires_at and now > candidate.expires_at:
        return FrequencyResult(ContactDecision.SILENCE, "candidate_expired")
    if now < candidate.due_at:
        return FrequencyResult(ContactDecision.DEFER, "not_due", candidate.due_at)

    # Explicit reminders/promises are hard: send at the requested time, even in quiet hours.
    if candidate.hard and candidate.user_requested:
        return FrequencyResult(ContactDecision.SEND, "explicit_user_commitment")

    if not context.soft_contact_opt_in and not candidate.user_requested:
        return FrequencyResult(ContactDecision.SILENCE, "soft_contact_not_enabled")

    if _in_quiet_hours(now.timetz().replace(tzinfo=None), policy):
        return FrequencyResult(ContactDecision.DEFER, "quiet_hours", _next_allowed_morning(now, policy))
    if context.active_conversation:
        return FrequencyResult(ContactDecision.DEFER, "conversation_active", now + policy.active_chat_suppression)
    if context.last_user_message_at and now - context.last_user_message_at < policy.active_chat_suppression:
        return FrequencyResult(ContactDecision.DEFER, "recent_user_activity", context.last_user_message_at + policy.active_chat_suppression)
    if context.outbound_today >= policy.daily_soft_limit:
        return FrequencyResult(ContactDecision.SILENCE, "daily_budget_exhausted")
    if context.outbound_this_week >= policy.weekly_soft_limit:
        return FrequencyResult(ContactDecision.SILENCE, "weekly_budget_exhausted")
    if context.last_outbound_at and now - context.last_outbound_at < policy.minimum_gap:
        return FrequencyResult(ContactDecision.DEFER, "minimum_gap", context.last_outbound_at + policy.minimum_gap)
    if context.last_outbound_at and context.consecutive_unanswered:
        index = min(context.consecutive_unanswered - 1, len(policy.unanswered_backoff_days) - 1)
        allowed = context.last_outbound_at + timedelta(days=policy.unanswered_backoff_days[index])
        if now < allowed:
            return FrequencyResult(ContactDecision.DEFER, "unanswered_backoff", allowed)
    return FrequencyResult(ContactDecision.SEND, "within_budget")

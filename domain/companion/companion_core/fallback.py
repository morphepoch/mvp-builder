"""Typed fallback decisions for companion chat delivery boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureKind(str, Enum):
    MODERATION_BLOCK = "moderation_block"
    KNOWN_USER_ERROR = "known_user_error"
    IDENTITY_UNAVAILABLE = "identity_unavailable"
    MODEL_TIMEOUT = "model_timeout"
    MODEL_INVALID_OUTPUT = "model_invalid_output"
    TOOL_FAILURE = "tool_failure"
    DELIVERY_FAILURE = "delivery_failure"
    CRASH_RECOVERY = "crash_recovery"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FallbackDecision:
    user_message: str | None
    retry_now: bool
    mark_input_processed: bool
    persist_as_assistant: bool
    alert_operator: bool
    expose_error_detail: bool = False


class FallbackPolicy:
    """Central policy: never let a model invent operational fallback behaviour."""

    GENERIC = "刚才这里出了点问题，你可以再发一次，我会重新接住。"
    RECOVERY = "刚才的回复被意外打断了，麻烦把那句话再发我一次。"
    IDENTITY = "我现在暂时没能连上这段对话，请稍后再试一次。"
    MODERATION = "这部分内容我不能继续处理，我们可以换个安全的方向聊。"

    def decide(self, kind: FailureKind, *, known_message: str = "") -> FallbackDecision:
        if kind is FailureKind.MODERATION_BLOCK:
            return FallbackDecision(self.MODERATION, False, True, False, False)
        if kind is FailureKind.KNOWN_USER_ERROR:
            return FallbackDecision(known_message or self.GENERIC, False, True, False, False)
        if kind is FailureKind.IDENTITY_UNAVAILABLE:
            return FallbackDecision(self.IDENTITY, False, True, False, True)
        if kind is FailureKind.DELIVERY_FAILURE:
            # Avoid duplicate companion messages when delivery acknowledgement is ambiguous.
            return FallbackDecision(None, False, True, False, True)
        if kind is FailureKind.CRASH_RECOVERY:
            return FallbackDecision(self.RECOVERY, False, True, False, True)
        if kind is FailureKind.TOOL_FAILURE:
            # Return the failure to the model as a tool result; let it state what was not done.
            return FallbackDecision(None, False, False, False, False)
        return FallbackDecision(self.GENERIC, False, True, False, True)

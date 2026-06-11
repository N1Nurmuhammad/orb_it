"""Verification sender factory.

Resolves a delivery channel by registry key. Only the console sender ships here;
email/SMS implementations would register the same way (one line in the mapping
below) and be selected by passing their key to `get_sender`.
"""

from functools import lru_cache

from .base import Sender, generate_code
from .console import ConsoleSender
from .store import OTPStore, get_otp_store

_SENDERS = {
    "console": ConsoleSender,
}


@lru_cache
def get_sender(sender: str | None = None) -> Sender:
    """Return a verification sender (cached per key).

    `sender=None` (the default) yields the dev `ConsoleSender`. A non-None key
    is looked up in `_SENDERS`; unknown keys also fall back to the console sender.
    """
    if sender is None:
        return ConsoleSender()
    sender_cls = _SENDERS.get(sender, ConsoleSender)
    return sender_cls()


__all__ = [
    "OTPStore",
    "Sender",
    "generate_code",
    "get_otp_store",
    "get_sender",
]

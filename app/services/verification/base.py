"""Abstract verification-code sender interface.

Every delivery channel (console, email/SMTP, SMS/Twilio, ...) implements
`Sender`. The rest of the app depends only on this interface, so swapping or
adding a channel is a one-file change — mirroring the LLM-provider pattern.
"""

import secrets
from abc import ABC, abstractmethod

CODE_LENGTH = 6


def generate_code() -> str:
    """Generate a cryptographically-random 6-digit numeric code."""
    return "".join(secrets.choice("0123456789") for _ in range(CODE_LENGTH))


class Sender(ABC):
    """Interface every verification-code delivery channel must implement."""

    @abstractmethod
    async def send_code(self, email: str, code: str) -> None:
        """Deliver `code` to the user identified by `email`.

        Implementations must not raise on the happy path. A real email/SMS
        provider would perform an HTTP/SMTP call here without leaking secrets
        into exceptions.
        """
        raise NotImplementedError

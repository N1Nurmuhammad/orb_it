"""Development verification sender: logs the code to the console.

This is the dev/test channel mandated by the spec ("in dev можно фиктивно
выводить в консоль"). In production you would implement `Sender` with an SMTP
client (email) or an SMS gateway such as Twilio — same interface, registered in
`_SENDERS` and selected by key (see __init__.get_sender).
"""

import logging

from .base import Sender

logger = logging.getLogger("verification")


class ConsoleSender(Sender):
    """Prints the verification code instead of actually emailing/SMSing it."""

    async def send_code(self, email: str, code: str) -> None:
        logger.warning("[VERIFICATION] code for %s: %s", email, code)
        # Also print so it shows up plainly in `docker compose logs`.
        print(f"[VERIFICATION] code for {email}: {code}", flush=True)

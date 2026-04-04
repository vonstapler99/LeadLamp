"""
SMS notifications via Twilio.

WHY a dedicated module/class:
- HTTP route handlers stay thin (validate → call service → return JSON).
- Outbound messaging is one responsibility you can unit-test or mock.
- Later you can add voice, email, or queue-backed delivery without rewriting routes.
"""

from __future__ import annotations

import asyncio
import logging

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.core.config import settings

# Module-level logger: log messages are tagged with this name in the output.
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Sends outbound notifications. For now: SMS via Twilio.

    We keep a single Twilio Client on the instance so we do not rebuild
    HTTP client state for every text (cheaper and simpler).
    """

    def __init__(self) -> None:
        # Client is synchronous; we wrap calls in asyncio.to_thread in async methods
        # so FastAPI's event loop is not blocked while waiting on Twilio's API.
        self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    def _send_sms_sync(self, to_number: str, body: str) -> str:
        """
        Perform the blocking Twilio REST call.

        Returns the Twilio Message SID (string) on success.
        The parameter is named `from_` because `from` is a Python keyword.
        """
        message = self._client.messages.create(
            to=to_number,
            from_=settings.twilio_from_number,
            body=body,
        )
        return message.sid

    async def send_sms_notification(self, phone_number: str, message: str) -> bool:
        """
        Send one SMS. Returns True if Twilio accepted the send, False otherwise.

        WHY async even though Twilio's SDK is sync:
        - FastAPI runs many requests on one thread; long blocking I/O would stall everyone.
        - asyncio.to_thread runs the blocking call in a thread pool so the event loop
          can keep serving other requests while Twilio responds.

        WHY try/except (fault tolerance):
        - Network blips, invalid numbers, auth errors, or rate limits should not
          crash the whole process. We log, return False, and let the caller decide
          (e.g. mark lead FAILED, retry, alert operations).
        """
        try:
            sid = await asyncio.to_thread(self._send_sms_sync, phone_number, message)
            logger.info("SMS sent successfully sid=%s to=%s", sid, phone_number)
            return True
        except TwilioRestException as exc:
            # Twilio-specific failure: status code and message help you debug quickly.
            logger.error(
                "Twilio SMS failed to=%s code=%s status=%s msg=%s",
                phone_number,
                exc.code,
                exc.status,
                exc.msg,
            )
            return False
        except Exception:
            # Anything else (DNS, SSL, unexpected SDK errors): full traceback in logs.
            logger.exception("Unexpected error sending SMS to=%s", phone_number)
            return False

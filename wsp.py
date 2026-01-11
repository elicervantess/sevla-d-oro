"""Module to send messages using Twilio Messaging API."""

import logging
from base64 import b64encode
from json import dumps
from typing import Dict

import requests
from twilio.rest import Client  # pyright: ignore [reportMissingTypeStubs]

from env import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_NUMBER

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

logger = logging.getLogger(__name__)


def send_message(to_number: str, body_text: str) -> None:
    """Send a message to a phone number using Twilio API."""
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        message = client.messages.create(
            from_=f"whatsapp:{TWILIO_NUMBER}",
            body=body_text,
            to=to_number,
        )
        logger.info("Message sent to %s: %s", to_number, message.body)
    except Exception:
        logger.exception("Error sending message to %s", to_number)


def send_template_message(
    to_number: str,
    template_sid: str,
    content_variables: Dict[str, str],
    messaging_service_sid: str,
) -> None:
    """Send a message to a phone number using Twilio API."""
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    try:
        message = client.messages.create(
            from_=f"whatsapp:{TWILIO_NUMBER}",
            to=to_number,
            content_variables=dumps(content_variables),
            content_sid=template_sid,
            messaging_service_sid=messaging_service_sid,
        )
        logger.info("Message sent to %s: %s", to_number, message.body)
    except Exception:
        logger.exception("Error sending message to %s", to_number)


# get the media url with secure http
def get_media_url(secure_media_url: str) -> str:
    """Get the media url with secure http."""
    auth_str = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = b64encode(auth_bytes).decode("utf-8")
    headers = {"Authorization": "Basic " + auth_b64}
    response = requests.get(secure_media_url, headers=headers, timeout=10)  # type: ignore[misc]
    return response.url  # type: ignore[return-value]

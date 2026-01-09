"""Sample test module."""

from env import TWILIO_MESSAGING_SERVICE_SID
from wsp import send_message, send_template_message

TEST_NUMBER = "+51984724707"

TEMPLATE_SID = "HX268d42f3d35cd684ba0a64f31cd233cf"


def test_send_hello_message() -> None:
    """Send a hello message to a phone number."""
    send_message(TEST_NUMBER, "Hello, World!")
    assert True


def test_send_template_message() -> None:
    """Send a template message to a phone number."""
    content_variables = {"1": "21"}
    send_template_message(
        TEST_NUMBER,
        TEMPLATE_SID,
        content_variables,
        TWILIO_MESSAGING_SERVICE_SID,
    )

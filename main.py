"""Main API module for the chatbot."""

# ruff: noqa: N803 (Twilio API requires Capitalized variable names)
# ruff: noqa: B008 (fastapi makes use of reusable default function calls)

from typing import Optional

from fastapi import FastAPI, Form, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ai import get_response, identify_image
from utils import logger
from wsp import send_message

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logger.error(f"{request}: {exc_str}")
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"msg": "up & running"}


@app.post("/message")
def reply(
    From: str = Form(),
    Body: Optional[str] = Form(None),
    MediaUrl0: Optional[str] = Form(None),
) -> str:
    """Reply to a WhatsApp message from the user."""
    user_message = Body
    image_url = MediaUrl0
    if not image_url and not user_message:
        logger.error("No image or message provided")
        return "failure"

    if not image_url and user_message:
        logger.info("Replying to text message only.")
        chat_response = get_response(user_message, phone=From)

        if chat_response is None:
            logger.error("Failed to get a response from the chat system")
            return "failure"
        send_message(From, chat_response)
        return "success"

    if image_url:
        if not user_message:
            logger.info("Replying to image only.")
            user_message = "analyze the image by its url and describe it"
        chat_response = identify_image(user_message, image_url, phone=From)

        if chat_response is None:
            logger.error("Failed to get a response from the chat system")
            return ""

        send_message(From, chat_response)
        return "success"

    return "failure"

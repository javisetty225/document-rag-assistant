import json
import logging
import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from ragflow_sdk import RAGFlow

from src.backend.server_schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    SessionMessageResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAGFLOW_API_KEY = os.getenv("API_KEY", "ragflow-A-EBXidE3iswvFgie-5F-uPqKT4yH17aAd2ZUAdx3QE")
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "http://localhost:9380")
RAGFLOW_CHAT_NAME = os.getenv("CHAT_NAME", "test")

if not RAGFLOW_API_KEY:
    raise RuntimeError("Missing required environment variable: API_KEY")

# RAGFlow client initialization
ragflow_client = RAGFlow(
    api_key=RAGFLOW_API_KEY,
    base_url=RAGFLOW_BASE_URL,
)


def get_chat_assistant():
    """
    Retrieve the configured RAGFlow assistant by name.

    Raises:
        HTTPException: If no assistant with the given name exists.
    """
    assistants = ragflow_client.list_chats(name=RAGFLOW_CHAT_NAME)

    if not assistants:
        logger.error("No assistant found with name '%s'", RAGFLOW_CHAT_NAME)
        raise HTTPException(status_code=500, detail="Chat assistant not found")

    return assistants[0]


def get_chat_session(assistant, session_id: str):
    """
    Retrieve a chat session by ID.

    Raises:
        HTTPException: If the session does not exist.
    """
    session = assistant.list_sessions(id=session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session



def register_chatbot_routes(app: FastAPI):
    """
    Register chatbot-related REST endpoints on the FastAPI app.
    """

    @app.post("/session", response_model=SessionMessageResponse)
    def create_chat_session():
        """
        Create a new chat session and return the initial chatbot greeting and session id.
        """
        try:
            assistant = get_chat_assistant()

            session_name = f"session_{uuid4()}"
            session = assistant.create_session(name=session_name)

            chatbot_greeting = session.messages[0]["content"]

            return SessionMessageResponse(
                session_id=session.id,
                chatbot_greeting=chatbot_greeting,
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to create chat session")
            raise HTTPException(
                status_code=500,
                detail="Failed to create chat session",
            ) from exc

    @app.post("/answer", response_model=ChatMessageResponse)
    def send_chat_message(request: ChatMessageRequest):
        """
        Send a user message to an existing chat session and return the answer.
        """
        try:
            assistant = get_chat_assistant()
            session = get_chat_session(assistant, request.session_id)[0]

            response = session._ask_chat(
                question=request.user_query,
                stream=False,
            )

            try:
                response_payload = json.loads(response.text)
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON response from RAGFlow: %s", response.text)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to parse response from chat service",
                ) from exc

            answer = response_payload.get("data", {}).get("answer", "")

            return ChatMessageResponse(answer=answer)

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to process chat message")
            raise HTTPException(
                status_code=500,
                detail="Failed to process chat message",
            ) from exc

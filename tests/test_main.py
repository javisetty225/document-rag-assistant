from fastapi.testclient import TestClient
from src.backend.main import create_app
from pytest_mock import MockerFixture


client = TestClient(create_app())


def test_success_session_creation(mocker: MockerFixture):
    # Mock session
    mock_session = mocker.Mock()
    mock_session.id = "mock-session-id"
    mock_session.messages = [
        {"content": "Hi! I'm your assistant. What can I do for you?"}
    ]

    # Mock assistant
    mock_assistant = mocker.Mock()
    mock_assistant.create_session.return_value = mock_session

    # Patch helper function
    mocker.patch(
        "src.backend.server_endpoints.get_chat_assistant",
        return_value=mock_assistant,
    )

    response = client.post("/session")

    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == "mock-session-id"
    assert data["chatbot_greeting"] == (
        "Hi! I'm your assistant. What can I do for you?"
    )


def test_chat_message_success(mocker: MockerFixture):
    # Mock RAGFlow response
    mock_ragflow_response = mocker.Mock()
    mock_ragflow_response.text = (
        '{"data": {"answer": "This is a mocked answer"}}'
    )

    # Mock session
    mock_session = mocker.Mock()
    mock_session._ask_chat.return_value = mock_ragflow_response

    # Mock assistant
    mock_assistant = mocker.Mock()
    mock_assistant.list_sessions.return_value = mock_session

    # Patch assistant getter
    mocker.patch(
        "src.backend.server_endpoints.get_chat_assistant",
        return_value=mock_assistant,
    )

    response = client.post(
        "/answer",
        json={
            "session_id": "mock-session-id",
            "user_query": "Hello",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "This is a mocked answer"





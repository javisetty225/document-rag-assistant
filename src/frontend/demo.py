import gradio as gr
import requests

BACKEND_BASE_URL = "http://localhost:8000"
SESSION_ENDPOINT = f"{BACKEND_BASE_URL}/session"
CHAT_ENDPOINT = f"{BACKEND_BASE_URL}/answer"


def assistant_message(text: str):
    return {"role": "assistant", "content": text}

def user_message(text: str):
    return {"role": "user", "content": text}

def start_chat_session():
    response = requests.post(SESSION_ENDPOINT, timeout=10)
    response.raise_for_status()

    data = response.json()
    session_id = data["session_id"]
    greeting = data["chatbot_greeting"]

    return (
        session_id,
        [assistant_message(greeting)],
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(visible=False),
    )


def send_message(message, session_id, chat_history):
    payload = {
        "session_id": session_id,
        "user_query": message,
    }

    response = requests.post(CHAT_ENDPOINT, json=payload, timeout=200)
    response.raise_for_status()

    answer = response.json()["answer"]

    chat_history.append(user_message(message))
    chat_history.append(assistant_message(answer))

    return "", chat_history


with gr.Blocks(title="Chatbot") as demo:

    session_state = gr.State(value=None)
    start_screen = gr.Column(visible=True)

    with start_screen:
        gr.Markdown(
            """
            <div style="text-align:center">
                <h1>🤖 Document Rag Assistant</h1>
            </div>
            """
        )
        start_button = gr.Button("Start Chat Session", size="lg")

    chat_screen = gr.Column(visible=False)

    with chat_screen:
        chatbot = gr.Chatbot(height=450)
        user_input = gr.Textbox(
            placeholder="Type your message...",
            show_label=False,
        )

    start_button.click(
        fn=start_chat_session,
        outputs=[
            session_state,
            chatbot,
            chat_screen,
            user_input,
            start_screen,
        ],
    )

    user_input.submit(
        fn=send_message,
        inputs=[user_input, session_state, chatbot],
        outputs=[user_input, chatbot],
    )


if __name__ == "__main__":
    demo.launch(server_port=7860)

import gradio as gr
from app.agents.assistant import run_assistant


def _format_chat_history(history: list[dict[str, str]] | None, user_message: str) -> list[dict[str, str]]:
    history = history or []
    if user_message:
        history.append({"role": "user", "content": user_message})
    return history


def process_message(history: list[dict[str, str]] | None, user_message: str) -> tuple[list[dict[str, str]], str]:
    if not user_message.strip():
        return history or [], ""

    history = _format_chat_history(history, user_message)
    response = run_assistant(user_message)
    history.append({"role": "assistant", "content": response.answer})

    return history, ""


def create_gradio_app() -> gr.Blocks:
    with gr.Blocks(title="AutoMate AI Car Assistant") as demo:
        gr.Markdown(
            "# AutoMate — AI Car Assistant\n"
            "Ask natural questions about cars, compare models, and get buyer guidance backed by verified CSV data."
        )

        chatbot = gr.Chatbot(value=[], label="AutoMate Chat")
        user_input = gr.Textbox(
            placeholder="Ask about car specs, comparisons, or recommendations...",
            label="Your question",
            lines=2,
        )
        submit = gr.Button("Send")

        submit.click(
            fn=process_message,
            inputs=[chatbot, user_input],
            outputs=[chatbot, user_input],
        )

    return demo

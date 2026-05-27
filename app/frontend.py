import gradio as gr
from app.agents.assistant import run_assistant_stream
from app.models import ChatMessage


def _format_chat_history(history: list[dict[str, str]] | None, user_message: str) -> list[dict[str, str]]:
    history = history or []
    if user_message:
        history.append({"role": "user", "content": user_message})
    return history


async def process_message(history: list[dict[str, str]] | None, user_message: str):
    if not user_message.strip():
        yield history or [], ""
        return

    # Prepare context for the assistant (history before the current message)
    chat_history = [ChatMessage(role=m["role"], content=m["content"]) for m in (history or [])]

    # Add user message to UI history
    history = _format_chat_history(history, user_message)

    # Initialize assistant response in UI
    history.append({"role": "assistant", "content": ""})
    yield history, ""

    # Stream real chunks from the assistant
    full_response = ""
    async for chunk in run_assistant_stream(user_message, history=chat_history):
        full_response += chunk
        history[-1]["content"] = full_response
        yield history, ""

    # Ensure the final state is yielded
    history[-1]["content"] = full_response
    yield history, ""


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
        
        # Required for streaming and async functions
        demo.queue()

    return demo


if __name__ == "__main__":
    demo = create_gradio_app()
    demo.launch(share=True)

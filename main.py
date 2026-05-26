import gradio as gr
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.routes import router
from app.config import logger
from app.frontend import create_gradio_app

app = FastAPI(
    title="AutoMate AI Car Assistant",
    description=(
        "A production-style AI automotive assistant that answers car questions, compares models, "
        "and offers buyer recommendations backed by verified CSV data."
    ),
    version="0.1.0",
)
app.include_router(router, prefix="/api")
app = gr.mount_gradio_app(app, create_gradio_app(), path="/chat")


@app.on_event("startup")
def startup_event() -> None:
    logger.info("AutoMate backend is starting")


@app.get("/")
def redirect_to_chat() -> RedirectResponse:
    return RedirectResponse(url="/chat")

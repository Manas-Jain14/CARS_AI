import gradio as gr
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api.routes import router
from app.config import logger
from app.frontend import create_gradio_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoMate backend is starting")
    yield


app = FastAPI(
    title="AutoMate AI Car Assistant",
    description=(
        "A production-style AI automotive assistant that answers car questions, compares models, "
        "and offers buyer recommendations backed by verified CSV data."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router, prefix="/api")

# Create the Gradio demo and launch it with sharing enabled
# This generates the public URL while allowing it to be mounted to FastAPI
demo = create_gradio_app()
demo.launch(share=True, prevent_thread_lock=True)

app = gr.mount_gradio_app(app, demo, path="/chat")


@app.get("/")
def redirect_to_chat() -> RedirectResponse:
    return RedirectResponse(url="/chat")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

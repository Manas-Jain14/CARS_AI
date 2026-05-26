# AutoMate AI Car Assistant

A production-style AI automotive assistant built with FastAPI, Gradio, PydanticAI, and Gemini. The assistant answers car questions, compares models, explains pros and cons, and recommends cars based on verified CSV data.

## Quick Start

1. Activate your virtual environment.
2. Ensure `.env` contains `GEMINI_API_KEY`.
3. Run the app:

```bash
uvicorn main:app --reload
```

4. Open `http://127.0.0.1:8000/chat`.

## Project Structure

- `main.py` — FastAPI application and Gradio frontend mount.
- `app/agents/assistant.py` — Agent and tool definitions.
- `app/services/car_data.py` — CSV-backed car database service.
- `app/api/routes.py` — REST endpoints for chat and car queries.
- `app/models.py` — Pydantic validation models.
- `data/cars.csv` — Source of truth for car specifications.

## Notes

- The agent is configured to use `google:gemini-1.5-flash`.
- Car data is loaded from CSV and used as the source of truth for all specifications.
- The assistant uses tools whenever a car data lookup is needed.

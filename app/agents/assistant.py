from typing import List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from app.config import GEMINI_MODEL, logger
from app.models import AgentResponse, CarSpec, ChatMessage
from app.services.car_data import car_data_service

SYSTEM_PROMPT = (
    "You are AutoMate, a professional automotive assistant for buyers. "
    "Always answer with verified car data from the CSV database. "
    "Do not invent specifications, prices, or features. "
    "When presenting prices, always show the amount in Indian Rupees (INR) first, using 1 USD = 95 INR. "
    "You may optionally include the USD equivalent in parentheses, but INR must appear as the primary currency. "
    "If the user asks about a car or comparison, use the database tools and return a concise, professional answer. "
    "Where appropriate, provide pros and cons, clear recommendations, and budget-aware advice. "
    "When data is unavailable, admit the limit and offer the closest factual guidance."
)

agent = Agent(
    GEMINI_MODEL,
    system_prompt=SYSTEM_PROMPT,
    tool_timeout=12,
    metadata={"assistant": "AI Car Assistant"},
)

logger.info("Using Gemini model: %s", GEMINI_MODEL)


def _validated_car_name(name: str) -> str:
    return name.strip()


@agent.tool(
    description="Search cars in the CSV database by name, feature, budget, or use case and return a short list of verified matches."
)
def search_cars(ctx: RunContext, query: str, limit: int = 5) -> List[CarSpec]:
    return car_data_service.search_cars(query, limit=limit)


@agent.tool(
    description="Lookup a car by name and return the full specification record from the CSV database."
)
def lookup_car_specs(ctx: RunContext, car_name: str) -> CarSpec:
    car = car_data_service.get_car_specs(_validated_car_name(car_name))
    if not car:
        raise ValueError(f"No car matching '{car_name}' was found in the database.")
    return car


@agent.tool(
    description="Compare two cars from the CSV database and return verified differences, strengths, and clarity for a buyer."
)
def compare_cars(ctx: RunContext, car_a: str, car_b: str) -> dict[str, object]:
    return car_data_service.compare_cars(_validated_car_name(car_a), _validated_car_name(car_b))


@agent.tool(
    description="Recommend cars from the CSV database based on the customer budget and use case."
)
def recommend_cars(
    ctx: RunContext,
    budget_usd: float | None = None,
    use_case: str | None = None,
    limit: int = 3,
) -> List[CarSpec]:
    return car_data_service.recommend_cars(budget_usd=budget_usd, use_case=use_case, limit=limit)


def _format_tool_error(error: Exception) -> AgentResponse:
    message = str(error)
    if isinstance(error, ValueError) and "No car matching" in message:
        return AgentResponse(
            answer=(
                f"I couldn't find that car in the database: {message}. "
                "Please try a different car name or ask about one of the supported cars."
            ),
            source="database",
            tool_used=False,
        )

    return AgentResponse(
        answer=(
            "I’m sorry, I encountered an internal issue while processing your request. "
            "Please try again or ask a simpler car question."
        ),
        source="internal",
        tool_used=False,
    )


async def run_assistant_stream(user_message: str, history: Optional[List[ChatMessage]] = None):
    try:
        logger.info("Assistant streaming received message: %s", user_message)

        model_messages: List[ModelMessage] = []
        if history:
            for msg in history:
                if msg.role == "user":
                    model_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
                elif msg.role == "assistant":
                    model_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        async with agent.run_stream(user_message, message_history=model_messages) as result:
            async for message in result.stream_text(delta=True):
                yield message
    except Exception as error:
        logger.exception("Assistant streaming error")
        yield _format_tool_error(error).answer


def run_assistant(user_message: str, history: Optional[List[ChatMessage]] = None) -> AgentResponse:
    try:
        logger.info("Assistant received message: %s", user_message)

        model_messages: List[ModelMessage] = []
        if history:
            for msg in history:
                if msg.role == "user":
                    model_messages.append(ModelRequest(parts=[UserPromptPart(content=msg.content)]))
                elif msg.role == "assistant":
                    model_messages.append(ModelResponse(parts=[TextPart(content=msg.content)]))

        result = agent.run_sync(user_message, message_history=model_messages)
        output = getattr(result, "output", None) or getattr(result, "data", None)
        if isinstance(output, AgentResponse):
            return output
        return AgentResponse(answer=str(output), source="database", tool_used=True)
    except Exception as error:
        logger.exception("Assistant error")
        return _format_tool_error(error)

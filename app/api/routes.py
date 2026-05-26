from fastapi import APIRouter, HTTPException, Query
from app.agents.assistant import run_assistant
from app.models import AgentResponse, CarSpec, ChatRequest
from app.services.car_data import car_data_service

router = APIRouter()


@router.post("/assistant/chat", response_model=AgentResponse)
def assistant_chat(request: ChatRequest) -> AgentResponse:
    return run_assistant(request.message)


@router.get("/cars", response_model=list[CarSpec])
def list_cars(query: str | None = Query(None, description="Search term for cars."), limit: int = 10) -> list[CarSpec]:
    return car_data_service.search_cars(query or "", limit=limit)


@router.get("/cars/specs", response_model=CarSpec)
def get_car_specs(car_name: str = Query(..., description="Full car name, such as '2024 Toyota Corolla' or 'Toyota Corolla'.")) -> CarSpec:
    car = car_data_service.get_car_specs(car_name)
    if not car:
        raise HTTPException(status_code=404, detail=f"Car '{car_name}' not found.")
    return car


@router.get("/cars/compare")
def compare_cars(car_a: str = Query(...), car_b: str = Query(...)) -> dict:
    try:
        return car_data_service.compare_cars(car_a, car_b)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.get("/cars/recommend", response_model=list[CarSpec])
def recommend_cars(
    budget_usd: float | None = Query(None, description="Maximum purchase budget in USD."),
    use_case: str | None = Query(None, description="Desired use case or priority, such as family, efficiency, or performance."),
) -> list[CarSpec]:
    return car_data_service.recommend_cars(budget_usd=budget_usd, use_case=use_case, limit=5)

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field, root_validator, validator

USD_TO_INR = 95.0


def parse_int(value: Optional[str] | int) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else None


def parse_float(value: Optional[str] | float) -> float | None:
    if value is None:
        return None
    if isinstance(value, float):
        return value
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


class CarSpec(BaseModel):
    make: str
    model: str
    year: int
    price_usd: int
    mileage_city: Optional[int] = None
    mileage_highway: Optional[int] = None
    engine: str
    fuel_type: str
    transmission: str
    seating: int
    horsepower: Optional[int] = None
    drive_type: str = Field(alias="drive_type")
    safety_rating: Optional[float] = None
    features: List[str] = Field(default_factory=list)
    body_type: Optional[str] = None

    @computed_field
    def price_inr(self) -> int:
        return int(round(self.price_usd * USD_TO_INR))

    @validator("features", pre=True)
    def split_features(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(";") if item.strip()]
        return value or []

    @validator("year", "price_usd", "mileage_city", "mileage_highway", "seating", "horsepower", pre=True)
    def normalize_ints(cls, value):
        return parse_int(value)

    @validator("safety_rating", pre=True)
    def normalize_float(cls, value):
        return parse_float(value)

    @root_validator(pre=True)
    def normalize_fields(cls, values):
        values["make"] = str(values.get("make", "")).strip()
        values["model"] = str(values.get("model", "")).strip()
        return values

    def display_name(self) -> str:
        return f"{self.year} {self.make} {self.model}"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat message for the car assistant.")


class AgentResponse(BaseModel):
    answer: str = Field(..., description="Assistant response text.")
    source: str = Field("database", description="Source of the answer. Always use CSV truth when available.")
    tool_used: bool = Field(
        True,
        description="Indicates whether the assistant used a tool to retrieve car data."
    )


class ComparisonRequest(BaseModel):
    car_a: str = Field(..., description="First car name for comparison.")
    car_b: str = Field(..., description="Second car name for comparison.")


class RecommendationRequest(BaseModel):
    budget_usd: Optional[float] = Field(None, description="User budget in USD.")
    use_case: Optional[str] = Field(None, description="Intended use case or priority for the car.")

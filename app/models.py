from __future__ import annotations
from typing import Any, List, Optional
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from app.config import USD_TO_INR


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
    drive_type: str
    safety_rating: Optional[float] = None
    features: List[str] = Field(default_factory=list)
    body_type: Optional[str] = None

    @computed_field
    def price_inr(self) -> int:
        return int(round(self.price_usd * USD_TO_INR))

    @field_validator("features", mode="before")
    @classmethod
    def split_features(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(";") if item.strip()]
        return value or []

    @field_validator("year", "price_usd", "mileage_city", "mileage_highway", "seating", "horsepower", mode="before")
    @classmethod
    def normalize_ints(cls, value):
        return parse_int(value)

    @field_validator("safety_rating", mode="before")
    @classmethod
    def normalize_float(cls, value):
        return parse_float(value)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        if isinstance(values, dict):
            values["make"] = str(values.get("make", "")).strip()
            values["model"] = str(values.get("model", "")).strip()
        return values

    def display_name(self) -> str:
        return f"{self.year} {self.make} {self.model}"


class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender (user or assistant).")
    content: Any = Field(..., description="The content of the message. Can be a string or a list of parts from Gradio.")

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, v):
        if isinstance(v, list):
            # Extract text from Gradio's complex message format if needed
            parts = []
            for part in v:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            return "\n".join(parts) if parts else str(v)
        return str(v) if v is not None else ""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User chat message for the car assistant.")
    history: List[ChatMessage] = Field(default_factory=list, description="Previous conversation history.")


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

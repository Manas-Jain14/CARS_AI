from __future__ import annotations
import csv
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import List
from app.models import CarSpec
from app.config import logger

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "cars.csv"


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


class CarDataService:
    def __init__(self, csv_path: Path = DATA_PATH):
        self.csv_path = csv_path
        self._cars = self._load_cars()
        self._index = {normalize_text(car.display_name()): car for car in self._cars}
        logger.info("Loaded %d cars from %s", len(self._cars), csv_path)

    def _load_cars(self) -> List[CarSpec]:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Car data CSV not found at {self.csv_path}")

        cars: List[CarSpec] = []
        with self.csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    car = CarSpec.model_validate(row)
                    cars.append(car)
                except Exception as exc:
                    logger.warning("Skipping invalid row in CSV: %s (%s)", row, exc)
        return cars

    def get_all_cars(self) -> List[CarSpec]:
        return self._cars

    def _find_exact(self, query: str) -> CarSpec | None:
        normalized = normalize_text(query)
        return self._index.get(normalized)

    def _find_closest_match(self, query: str, threshold: float = 0.55) -> CarSpec | None:
        normalized_query = normalize_text(query)
        best: tuple[float, CarSpec] | None = None

        for car in self._cars:
            text = normalize_text(car.display_name())
            ratio = SequenceMatcher(None, normalized_query, text).ratio()
            if best is None or ratio > best[0]:
                best = (ratio, car)

        if best and best[0] >= threshold:
            return best[1]
        return None

    def search_cars(self, query: str, limit: int = 5) -> List[CarSpec]:
        logger.info("Tool search_cars called with query: '%s'", query)
        if not query:
            return self._cars[:limit]

        normalized = normalize_text(query)
        results: List[CarSpec] = []
        for car in self._cars:
            score_text = " ".join([
                car.display_name(),
                car.engine,
                car.fuel_type,
                car.transmission,
                car.body_type or "",
                " ".join(car.features),
            ])
            if normalized in normalize_text(score_text):
                results.append(car)

        if not results:
            tokens = normalized.split()
            for car in self._cars:
                text = normalize_text(" ".join([car.make, car.model, car.engine, car.fuel_type, car.body_type or ""]))
                if all(token in text for token in tokens):
                    results.append(car)

        if not results:
            closest = self._find_closest_match(query)
            if closest:
                results.append(closest)

        return results[:limit]

    def get_car_specs(self, car_name: str) -> CarSpec | None:
        logger.info("Tool get_car_specs called for: '%s'", car_name)
        car = self._find_exact(car_name)
        if car:
            return car
        results = self.search_cars(car_name, limit=1)
        return results[0] if results else None

    def compare_cars(self, car_a: str, car_b: str) -> dict[str, object]:
        logger.info("Tool compare_cars called for: '%s' and '%s'", car_a, car_b)
        first = self.get_car_specs(car_a)
        second = self.get_car_specs(car_b)
        if not first or not second:
            raise ValueError("One or both cars could not be found in the database.")

        comparison = {
            "car_a": first.display_name(),
            "car_b": second.display_name(),
            "summary": self._build_comparison_summary(first, second),
            "differences": self._build_differences(first, second),
        }
        return comparison

    def recommend_cars(
        self,
        budget_usd: float | None = None,
        use_case: str | None = None,
        off_road_only: bool = False,
        budget_category: str | None = None,
        limit: int = 3,
    ) -> List[CarSpec]:
        logger.info(
            "Tool recommend_cars called with budget: %s, use_case: '%s', off_road_only: %s, budget_category: '%s'",
            budget_usd, use_case, off_road_only, budget_category,
        )
        candidates = self._cars
        if budget_usd is not None:
            candidates = [car for car in candidates if car.price_usd <= budget_usd]
        if off_road_only:
            candidates = [car for car in candidates if car.off_road_capable]
        if budget_category:
            normalized_category = normalize_text(budget_category)
            candidates = [
                car for car in candidates
                if car.budget_category and normalize_text(car.budget_category) == normalized_category
            ]
        if use_case:
            phrase = normalize_text(use_case)
            candidates = [
                car
                for car in candidates
                if phrase
                in normalize_text(
                    " ".join(
                        filter(
                            None,
                            [
                                car.body_type or "",
                                " ".join(car.features),
                                car.engine,
                                car.fuel_type,
                            ],
                        )
                    )
                )
            ]
        if not candidates:
            candidates = self._cars
        ranked = sorted(candidates, key=lambda car: (abs((budget_usd or car.price_usd) - car.price_usd), car.price_usd))
        return ranked[:limit]

    def _build_comparison_summary(self, first: CarSpec, second: CarSpec) -> str:
        return (
            f"{first.display_name()} is stronger on {self._primary_strength(first, second)}, "
            f"while {second.display_name()} stands out with {self._primary_strength(second, first)}."
        )

    def _primary_strength(self, base: CarSpec, other: CarSpec) -> str:
        if base.price_usd < other.price_usd:
            return "value and lower ownership cost"
        if base.horsepower and other.horsepower and base.horsepower > other.horsepower:
            return "performance and horsepower"
        if base.seating > other.seating:
            return "passenger comfort and cabin flexibility"
        return "a balanced feature set"

    def _build_differences(self, first: CarSpec, second: CarSpec) -> dict[str, str]:
        return {
            "price": f"${first.price_usd:,} vs ${second.price_usd:,}",
            "engine": f"{first.engine} vs {second.engine}",
            "fuel_type": f"{first.fuel_type} vs {second.fuel_type}",
            "transmission": f"{first.transmission} vs {second.transmission}",
            "seating": f"{first.seating} vs {second.seating}",
            "horsepower": f"{first.horsepower or 'N/A'} vs {second.horsepower or 'N/A'}",
        }


car_data_service = CarDataService()

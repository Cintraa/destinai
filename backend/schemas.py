from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel


class TripRequest(BaseModel):
    """Trip form submitted by the frontend (camelCase JSON)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    destination: str = "Miami"
    departure_city: str = Field(min_length=1)
    start_date: date
    end_date: date
    budget_usd: float = Field(alias="budgetUSD", gt=0)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str = ""
    travelers: int = Field(default=1, ge=1, le=9)
    interests: list[str] = []

    @field_validator("departure_city", "destination", mode="before")
    @classmethod
    def _strip(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("age", mode="before")
    @classmethod
    def _blank_age_is_none(cls, value):
        return None if value == "" else value

    @model_validator(mode="after")
    def _check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("endDate must be on or after startDate")
        return self


class ItineraryRequest(BaseModel):
    form: TripRequest
    weather: dict | None = None
    flights: dict | None = None
    hotels: list[dict] | None = None
    places: list[dict] | None = None

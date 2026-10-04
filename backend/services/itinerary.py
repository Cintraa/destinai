import logging
import os
import textwrap
import time

from google import genai
from google.genai import types as genai_types

from ..schemas import TripRequest

logger = logging.getLogger(__name__)

FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite"]
MAX_OUTPUT_TOKENS = 16384
BUSY_MESSAGE = "The AI is busy right now"


def _build_prompt(
    trip: TripRequest,
    weather: dict | None,
    flights: dict | None,
    hotels: list[dict] | None,
    places: list[dict] | None,
) -> str:
    prices = [f["price"] for f in (flights or {}).get("items", []) if f.get("price")]
    cheapest = f"${min(prices)}" if prices else "unknown"

    weather_label = f" - {weather['label']}" if weather and weather.get("label") else ""
    weather_days = weather["days"] if weather else "unavailable; assume typical Miami weather for the season"

    if places:
        place_list = [
            {"interest": g["interest"], "places": [(p["title"], p["address"]) for p in g["places"]]}
            for g in places
        ]
    else:
        place_list = "none; suggest well-known Miami spots"

    interests = ", ".join(trip.interests) or "general sightseeing"
    return textwrap.dedent(f"""\
        Write a day-by-day Miami itinerary in markdown for {trip.start_date} to {trip.end_date}.
        Traveler: age {trip.age}, {trip.travelers} traveler(s), budget ${trip.budget_usd:g} USD total.
        Interests: {interests}.
        Weather (F){weather_label}: {weather_days}
        Flight options: {flights['items'] if flights else 'unavailable'}
        Cheapest round-trip flight (Google Flights quote for {trip.travelers} adult(s)): {cheapest} - use this real number in the budget breakdown
        Hotel options: {hotels or 'unavailable'}
        Real places to include (use these by name in the plan where they fit, grouped by interest): {place_list}
        Take the weather into account (e.g. indoor plans on rainy days) and keep within budget.
        Return only markdown.""")


def get_itinerary(
    trip: TripRequest,
    weather: dict | None,
    flights: dict | None,
    hotels: list[dict] | None,
    places: list[dict] | None = None,
) -> tuple[str | None, str | None]:
    """Generate a markdown itinerary. Returns (text, None) on success or (None, error_message)."""
    prompt = _build_prompt(trip, weather, flights, hotels, places)
    models = [os.getenv("GEMINI_MODEL", "gemini-3.8-flash"), *FALLBACK_MODELS]
    config = genai_types.GenerateContentConfig(max_output_tokens=MAX_OUTPUT_TOKENS)

    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    except ValueError as e:
        logger.error("Gemini client could not be created: %s", e)
        return None, BUSY_MESSAGE

    for attempt, model in enumerate(models, start=1):
        delay = 4 * attempt
        try:
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            text = (response.text or "").strip()
            if text:
                return text, None
            logger.warning("Gemini attempt %d (%s) returned no text", attempt, model)
        except Exception as e:
            logger.warning("Gemini attempt %d (%s) failed: %s", attempt, model, e)
            if getattr(e, "code", None) == 429:
                delay = 10

        if attempt < len(models):
            time.sleep(delay)

    return None, BUSY_MESSAGE

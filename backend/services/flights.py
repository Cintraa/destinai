import logging
import os
import unicodedata
from datetime import date

import requests

from .cache import CACHE_DIR, cache_get, cache_set

logger = logging.getLogger(__name__)

FLIGHTS_CACHE = CACHE_DIR / "flights.json"
FLIGHTS_TTL = 24 * 3600

ALIASES = {
    "new york": "JFK",
    "nyc": "JFK",
    "lima": "LIM",
    "paris": "CDG",
    "london": "LHR",
    "sao paulo": "GRU",
    "mexico city": "MEX",
    "cdmx": "MEX",
    "bogota": "BOG",
    "buenos aires": "EZE",
    "rio": "GIG",
    "madrid": "MAD",
    "barcelona": "BCN",
    "tokyo": "NRT",
}


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return " ".join(stripped.split())


def _iata(city: str) -> str | None:
    """Resolve a city name to an IATA code via local aliases, then the public autocomplete API."""
    term = city.strip()
    if len(term) == 3 and term.isalpha():
        return term.upper()
    alias = ALIASES.get(_normalize(term))
    if alias:
        return alias

    r = requests.get(
        "https://autocomplete.travelpayouts.com/places2",
        params=[("term", term), ("locale", "en"), ("types[]", "city"), ("types[]", "airport")],
        timeout=12,
    )
    r.raise_for_status()
    for item in r.json():
        if item.get("code"):
            return item["code"].upper()
    return None


def _format_duration(minutes) -> str | None:
    try:
        hours, mins = divmod(int(minutes), 60)
    except (TypeError, ValueError):
        return None
    return f"{hours}h {mins}m"


def _clock_time(timestamp: str | None) -> str | None:
    """Extract HH:MM from a SerpAPI timestamp such as '2026-10-05 08:15'."""
    return timestamp.split(" ")[-1] if timestamp else None


def _search_flights(origin: str, start: str, end: str, adults: int, api_key: str) -> dict | None:
    r = requests.get(
        "https://serpapi.com/search",
        params={
            "engine": "google_flights",
            "type": 1,
            "departure_id": origin,
            "arrival_id": "MIA",
            "outbound_date": start,
            "return_date": end,
            "adults": adults,
            "currency": "USD",
            "hl": "en",
            "api_key": api_key,
        },
        timeout=40,
    )
    r.raise_for_status()
    data = r.json()

    options = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    options = sorted((o for o in options if o.get("price")), key=lambda o: o["price"])[:6]

    items = []
    for option in options:
        legs = option.get("flights") or []
        if not legs:
            continue
        first, last = legs[0], legs[-1]
        departure = first.get("departure_airport") or {}
        arrival = last.get("arrival_airport") or {}
        items.append({
            "airline": first.get("airline"),
            "logo": option.get("airline_logo") or first.get("airline_logo"),
            "flight_numbers": ", ".join(leg["flight_number"] for leg in legs if leg.get("flight_number")),
            "dep_airport": departure.get("id"),
            "dep_time": _clock_time(departure.get("time")),
            "arr_airport": arrival.get("id"),
            "arr_time": _clock_time(arrival.get("time")),
            "stops": len(legs) - 1,
            "duration": _format_duration(option.get("total_duration")),
            "price": option["price"],
        })
    if not items:
        return None

    url = (data.get("search_metadata") or {}).get("google_flights_url")
    return {"items": items, "url": url}


def get_flights(origin_city: str, start: date, end: date, adults: int = 1) -> dict | None:
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        logger.warning("SERPAPI_KEY is not set; skipping flights")
        return None

    try:
        origin = _iata(origin_city)
    except (requests.RequestException, ValueError) as e:
        logger.warning("IATA lookup failed for %r: %s", origin_city, e)
        return None
    if not origin:
        logger.warning("Could not resolve IATA code for %r", origin_city)
        return None

    cache_key = f"{origin}|{start}|{end}|{adults}"
    cached = cache_get(FLIGHTS_CACHE, cache_key, FLIGHTS_TTL)
    if cached:
        return cached

    try:
        result = _search_flights(origin, start.isoformat(), end.isoformat(), adults, api_key)
    except requests.RequestException as e:
        logger.warning("Flight search failed (status %s)", getattr(e.response, "status_code", None))
        return None
    except ValueError:
        logger.warning("Flight search returned invalid JSON")
        return None
    if result:
        cache_set(FLIGHTS_CACHE, cache_key, result)
    return result

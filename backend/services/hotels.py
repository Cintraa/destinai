import logging
import os
from datetime import date

import requests

logger = logging.getLogger(__name__)


def get_hotels(start: date, end: date, adults: int) -> list[dict] | None:
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        logger.warning("SERPAPI_KEY is not set; skipping hotels")
        return None

    try:
        r = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_hotels",
                "q": "Miami, FL",
                "check_in_date": start.isoformat(),
                "check_out_date": end.isoformat(),
                "adults": adults,
                "currency": "USD",
                "api_key": api_key,
            },
            timeout=30,
        )
        r.raise_for_status()
        properties = r.json().get("properties", [])
    except requests.RequestException as e:
        logger.warning("Hotel search failed (status %s)", getattr(e.response, "status_code", None))
        return None
    except ValueError:
        logger.warning("Hotel search returned invalid JSON")
        return None

    hotels = []
    for prop in properties[:5]:
        rate = prop.get("rate_per_night") or {}
        rating = prop.get("overall_rating")
        hotels.append({
            "name": prop.get("name"),
            "price": rate.get("lowest") if isinstance(rate, dict) else rate,
            "rating": round(rating, 1) if isinstance(rating, (int, float)) else rating,
            "link": prop.get("link"),
        })
    return hotels or None

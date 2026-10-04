import logging
import os

import requests

from .cache import CACHE_DIR, cache_get, cache_set

logger = logging.getLogger(__name__)

PLACES_CACHE = CACHE_DIR / "places.json"
PLACES_TTL = 7 * 24 * 3600
MAX_INTERESTS = 4
PLACES_PER_QUERY = 3

PLACE_QUERIES = {
    "Theme Parks/Amusement Parks": "theme parks amusement parks Miami",
    "Nightclubs/Dance Venues": "best nightclubs Miami",
    "Live Music/Concerts": "best live music venues Miami",
    "Theater/Musicals/Shows": "theaters musicals shows Miami",
    "Casinos/Gambling": "casinos Miami",
    "Ancient Ruins/Archaeology": "archaeological sites historic ruins Miami",
    "Historical Architecture": "historic architecture landmarks Miami",
    "Modern Architecture": "modern architecture landmarks Miami",
    "Museums - Art": "best art museums Miami",
    "Museums - History/Science": "history and science museums Miami",
    "Local Festivals/Events": "cultural festivals event venues Miami",
    "Fine Dining/Gourmet Restaurants": "best fine dining restaurants Miami",
    "Street Food/Food Trucks": "best street food food trucks Miami",
    "Fast Food": "popular fast food Miami",
    "Cooking Classes": "cooking classes Miami",
    "Winery/Brewery Tours": "breweries wineries tours Miami",
    "Coffee Culture": "best specialty coffee shops Miami",
    "Swimming/Sunbathing": "best beaches Miami",
    "Water Sports": "water sports rentals Miami",
    "Hiking/Trekking": "nature trails hiking Miami",
    "Skiing/Snowboarding": "indoor skiing snowboarding near Miami",
    "Wildlife Watching/Safaris": "wildlife zoo nature reserve Miami",
    "Botanical Gardens/Arboretums": "botanical gardens Miami",
    "Extreme Sports": "extreme sports adventure activities Miami",
    "Road Trip/Scenic Driving": "scenic drives viewpoints Miami",
    "Attending Sports Games": "sports arenas stadiums Miami",
    "Soccer": "soccer stadium Miami",
    "Football": "football stadium Miami",
    "Basketball": "basketball arena Miami",
    "Tennis": "tennis courts clubs Miami",
    "Golf": "best golf courses Miami",
    "Luxury Shopping": "luxury shopping Miami",
    "Thrift/Vintage Shopping": "vintage thrift stores Miami",
    "Local Markets/Bazaars": "local markets bazaars Miami",
    "Spa/Wellness Retreats": "best spas wellness Miami",
    "Yoga/Meditation": "yoga studios meditation Miami",
    "Photography Spots": "best photography spots Miami",
    "Glamping/Boutique Hotels": "boutique hotels Miami",
}


def _search_places(query: str, api_key: str) -> list[dict]:
    r = requests.get(
        "https://serpapi.com/search",
        params={
            "engine": "google_maps",
            "type": "search",
            "q": query,
            "ll": "@25.7617,-80.1918,12z",
            "hl": "en",
            "api_key": api_key,
        },
        timeout=30,
    )
    r.raise_for_status()

    places = []
    for result in r.json().get("local_results", [])[:PLACES_PER_QUERY]:
        rating = result.get("rating")
        place_id = result.get("place_id")
        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else None
        places.append({
            "title": result.get("title"),
            "rating": round(rating, 1) if isinstance(rating, (int, float)) else None,
            "reviews": result.get("reviews"),
            "address": result.get("address"),
            "thumbnail": result.get("thumbnail"),
            "link": result.get("website") or maps_url,
        })
    return places


def get_places(interests: list[str]) -> list[dict] | None:
    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        logger.warning("SERPAPI_KEY is not set; skipping places")
        return None

    chosen = [i for i in interests if i in PLACE_QUERIES][:MAX_INTERESTS]
    queries = [(i, PLACE_QUERIES[i]) for i in chosen] or [("Top Attractions", "top attractions Miami")]

    groups = []
    for interest, query in queries:
        places = cache_get(PLACES_CACHE, query, PLACES_TTL)
        if not places:
            try:
                places = _search_places(query, api_key)
            except requests.RequestException as e:
                logger.warning("Place search for %r failed (status %s)", query, getattr(e.response, "status_code", None))
                continue
            except ValueError:
                logger.warning("Place search for %r returned invalid JSON", query)
                continue
            if places:
                cache_set(PLACES_CACHE, query, places)
        if places:
            groups.append({"interest": interest, "places": places})
    return groups or None

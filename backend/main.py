import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .schemas import ItineraryRequest, TripRequest
from .services.flights import get_flights
from .services.hotels import get_hotels
from .services.itinerary import get_itinerary
from .services.places import get_places
from .services.weather import get_weather

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="DestinAI")


@app.post("/api/itinerary")
def itinerary_only(body: ItineraryRequest):
    text, error = get_itinerary(body.form, body.weather, body.flights, body.hotels, body.places)
    return {"itinerary": text, "itinerary_error": error}


@app.post("/api/plan")
def plan(trip: TripRequest):
    weather = get_weather(trip.start_date, trip.end_date)
    flights = get_flights(trip.departure_city, trip.start_date, trip.end_date, trip.travelers)
    hotels = get_hotels(trip.start_date, trip.end_date, trip.travelers)
    places = get_places(trip.interests)
    text, error = get_itinerary(trip, weather, flights, hotels, places)
    return {
        "places": places,
        "weather": weather,
        "flights": flights,
        "hotels": hotels,
        "itinerary": text,
        "itinerary_error": error,
    }


app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")

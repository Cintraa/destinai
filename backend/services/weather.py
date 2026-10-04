import logging
from datetime import date, timedelta

import requests

logger = logging.getLogger(__name__)

MIAMI_LAT, MIAMI_LON = 25.7617, -80.1918
FORECAST_DAYS = 15


def get_weather(start: date, end: date) -> dict | None:
    today = date.today()
    if end < today:
        return None

    params = {
        "latitude": MIAMI_LAT,
        "longitude": MIAMI_LON,
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    }
    label = None
    if start > today + timedelta(days=FORECAST_DAYS):
        label = "Current Miami forecast (trip is beyond forecast range)"
        params["forecast_days"] = 7
    else:
        params["start_date"] = max(start, today).isoformat()
        params["end_date"] = min(end, today + timedelta(days=FORECAST_DAYS)).isoformat()

    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=12)
        r.raise_for_status()
        daily = r.json()["daily"]
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.warning("Weather lookup failed: %s", e)
        return None

    days = [
        {"date": d, "max": hi, "min": lo, "precip": rain}
        for d, hi, lo, rain in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
        )
    ]
    return {"label": label, "days": days} if days else None

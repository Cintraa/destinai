# DestinAI

**Plan your vacation with AI.** DestinAI turns a short form into a complete, personalized trip plan. It gathers real flight prices, hotel options, the weather forecast and top-rated places that match your interests, then uses Google Gemini to write a day-by-day itinerary that fits your dates and budget.

> **Prototype scope:** the destination is currently fixed to **Miami, FL**.

> [!NOTE]
> **Repository Notice:** This repository is an archive/personal mirror and is not the original development repository.

---

## Demo

https://github.com/user-attachments/assets/ed7504d3-7361-406c-b991-37df3b1032e9

*From an empty form to a full Miami trip plan in under a minute.*

### Screenshots

| Trip form | Trip plan |
|:---------:|:---------:|
| <img src="https://github.com/user-attachments/assets/e1c17696-f5db-4ea7-b62a-dba4a228bdae" alt="img-form" width="450" /> | <img src="https://github.com/user-attachments/assets/26226104-3ee4-43d8-9033-8934d78720f3" alt="img-plan" width="450" /> |

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Caching](#caching)
- [Error Handling and Fallbacks](#error-handling-and-fallbacks)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Team](#team)
- [License](#license)

---

## Features

- **Three-step trip form:** where and when, who you are, and what you love (38 interests in 6 categories).
- **Real flight quotes:** round-trip options to Miami from Google Flights (via SerpAPI), sorted by price, with airline, times, stops, duration and flight numbers.
- **Hotel options:** up to 5 Miami hotels for your dates, with nightly rate, rating and link.
- **Weather forecast:** daily highs, lows and precipitation from Open-Meteo, with a fallback to the current forecast when the trip is too far in the future.
- **Places for you:** top-rated Google Maps results for up to 4 of your selected interests.
- **AI itinerary:** a day-by-day markdown plan from Google Gemini that uses the real data above, accounts for the weather and stays within budget.
- **Graceful degradation:** if any data source fails, the page still renders, with links to search Google Flights, Hotels or Maps directly. If the itinerary fails, a **Try again** button regenerates it without refetching everything else.
- **Safe rendering:** all external data is HTML-escaped, and the AI-generated markdown is sanitized with DOMPurify.

---

## How It Works

```
 ┌──────────────┐   POST /api/plan    ┌───────────────────────────────────────┐
 │  form.html   │ ──────────────────▶ │            FastAPI backend            │
 │  (script.js) │                     │                                       │
 └──────────────┘                     │  1. Weather   → Open-Meteo            │
        │                             │  2. Flights   → Travelpayouts (IATA)  │
        │ plan saved to               │                + SerpAPI Google Flights│
        │ sessionStorage              │  3. Hotels    → SerpAPI Google Hotels │
        ▼                             │  4. Places    → SerpAPI Google Maps   │
 ┌──────────────┐                     │  5. Itinerary → Google Gemini         │
 │ output.html  │ ◀────── JSON ────── │                                       │
 │ (output.js)  │                     └───────────────────────────────────────┘
 └──────────────┘
        │ "Try again" (itinerary only)
        └──────────── POST /api/itinerary ───▶ Gemini, reusing the data already fetched
```

1. The user fills out `form.html`. `script.js` validates the dates and budget and sends the form to `POST /api/plan`.
2. The backend collects weather, flights, hotels and places, then builds a prompt with all of that data and asks Gemini for an itinerary.
3. The response and the form data are stored in `sessionStorage`, and the browser goes to `output.html`.
4. `output.js` renders each section. If the itinerary failed, the user can retry through `POST /api/itinerary`, which reuses the data already collected.

---

## Tech Stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Requests, python-dotenv |
| AI       | Google Gemini via the `google-genai` SDK |
| Frontend | Plain HTML, CSS and JavaScript (no build step) |
| Frontend libraries (CDN) | marked (markdown rendering), DOMPurify (sanitization), Font Awesome, Google Fonts (Poppins) |
| External data | SerpAPI (Google Flights, Hotels, Maps), Open-Meteo (weather), Travelpayouts autocomplete (city → IATA code) |

---

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI app: API routes + serves the frontend
│   ├── schemas.py           # Pydantic request models (TripRequest, ItineraryRequest)
│   └── services/
│       ├── cache.py         # Simple JSON file cache with TTL
│       ├── flights.py       # City → IATA lookup + Google Flights search
│       ├── hotels.py        # Google Hotels search
│       ├── itinerary.py     # Prompt building + Gemini call with model fallbacks
│       ├── places.py        # Interest → Google Maps place search
│       └── weather.py       # Open-Meteo daily forecast
├── docs/
│   └── images/              # README screenshots and demo thumbnail
├── frontend/
│   ├── index.html           # Landing page
│   ├── form.html            # Trip form
│   ├── output.html          # Results page
│   ├── css/
│   │   ├── style.css        # Landing page + form styles
│   │   └── output.css       # Results page styles
│   ├── js/
│   │   ├── script.js        # Form handling and submission
│   │   └── output.js        # Results rendering, itinerary retry, read more/less
│   └── img/                 # Logo, banner, step images, favicon
├── .env.example             # Template for required API keys
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10 or newer** (the code uses `X | None` type syntax)
- A **Google Gemini API key**: create one in [Google AI Studio](https://aistudio.google.com/apikey)
- A **SerpAPI key**: find it in your [SerpAPI dashboard](https://serpapi.com/manage-api-key)

Open-Meteo and the Travelpayouts autocomplete endpoint are public and need no key.

### 1. Clone the repository

```bash
git clone <your-repo-url> destinai
cd destinai
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API keys

```bash
cp .env.example .env
```

Then open `.env` and fill in your keys (see [Configuration](#configuration)).

### 5. Run the app

Run this from the **project root** (not from inside `backend/`), because the backend uses package-relative imports:

```bash
uvicorn backend.main:app --reload
```

### 6. Open it in your browser

Go to **http://127.0.0.1:8000**. FastAPI serves the frontend and the API from the same server, so there is nothing else to start.

---

## Configuration

All settings are read from a `.env` file in the project root.

| Variable         | Required | Description |
|------------------|----------|-------------|
| `GOOGLE_API_KEY` | Yes      | Google Gemini API key, used to generate the itinerary. |
| `SERPAPI_KEY`    | Yes      | SerpAPI key, used for flights, hotels and places. Without it, those three sections are skipped and fallback search links are shown. |
| `GEMINI_MODEL`   | No       | Primary Gemini model to try first. Defaults to `gemini-3.8-flash`. The app falls back to `gemini-3.5-flash` and then `gemini-3.5-flash-lite` if it fails. |

Example `.env`:

```env
GOOGLE_API_KEY=your-gemini-key
SERPAPI_KEY=your-serpapi-key
# GEMINI_MODEL=gemini-3.8-flash
```

> Never commit your `.env` file. It is already listed in `.gitignore`.

---

## API Reference

The API accepts and returns JSON. Request fields use **camelCase**, and the backend converts them to snake_case automatically.

### `POST /api/plan`

Fetches all trip data and generates an itinerary.

**Request body**

| Field           | Type            | Required | Rules |
|-----------------|-----------------|----------|-------|
| `departureCity` | string          | Yes      | Not empty. A city name (e.g. `"New York"`) or a 3-letter IATA code (e.g. `"JFK"`). |
| `startDate`     | date (`YYYY-MM-DD`) | Yes  | |
| `endDate`       | date (`YYYY-MM-DD`) | Yes  | Must be on or after `startDate`. |
| `budgetUSD`     | number          | Yes      | Greater than 0. Total trip budget. |
| `age`           | integer         | No       | 0–120. An empty string is treated as not provided. |
| `gender`        | string          | No       | |
| `travelers`     | integer         | No       | 1–9. Defaults to 1. |
| `interests`     | string[]        | No       | Values from the form's interest list (e.g. `"Coffee Culture"`). |
| `destination`   | string          | No       | Defaults to `"Miami"`. |

**Example request**

```json
{
  "departureCity": "New York",
  "startDate": "2026-11-12",
  "endDate": "2026-11-16",
  "budgetUSD": 2000,
  "age": 29,
  "gender": "Female",
  "travelers": 2,
  "interests": ["Swimming/Sunbathing", "Coffee Culture", "Museums - Art"]
}
```

**Response**

```json
{
  "weather":   { "label": null, "days": [{ "date": "2026-11-12", "max": 82.1, "min": 71.4, "precip": 0.0 }] },
  "flights":   { "items": [{ "airline": "...", "logo": "...", "flight_numbers": "...", "dep_airport": "JFK", "dep_time": "08:15", "arr_airport": "MIA", "arr_time": "11:20", "stops": 0, "duration": "3h 5m", "price": 312 }], "url": "https://www.google.com/travel/flights/..." },
  "hotels":    [{ "name": "...", "price": "$189", "rating": 4.4, "link": "https://..." }],
  "places":    [{ "interest": "Coffee Culture", "places": [{ "title": "...", "rating": 4.7, "reviews": 1234, "address": "...", "thumbnail": "https://...", "link": "https://..." }] }],
  "itinerary": "# Your Miami Trip\n\n## Day 1 ...",
  "itinerary_error": null
}
```

Any of `weather`, `flights`, `hotels`, `places` or `itinerary` can be `null` if that source was unavailable. When `itinerary` is `null`, `itinerary_error` contains a user-facing message.

Invalid input (for example `endDate` before `startDate`) returns FastAPI's standard **422** validation error.

### `POST /api/itinerary`

Regenerates only the itinerary, reusing data already fetched. The results page uses this for **Try again**.

**Request body**

```json
{
  "form":    { "...same fields as /api/plan..." },
  "weather": { "...": "..." },
  "flights": { "...": "..." },
  "hotels":  [ "..." ],
  "places":  [ "..." ]
}
```

Only `form` is required. The other fields can be `null`.

**Response**

```json
{ "itinerary": "...markdown...", "itinerary_error": null }
```

### Interactive docs

While the server is running, FastAPI's auto-generated docs are at **http://127.0.0.1:8000/docs**.

---

## Caching

To save API quota, some results are cached as JSON files in `backend/cache/`, which is created automatically and ignored by Git.

| Data    | File           | Cache key                              | Lifetime |
|---------|----------------|----------------------------------------|----------|
| Flights | `flights.json` | origin + start date + end date + adults | 24 hours |
| Places  | `places.json`  | search query                           | 7 days   |

Weather, hotels and itineraries are not cached. To clear the cache, delete the `backend/cache/` folder.

---

## Error Handling and Fallbacks

DestinAI is built so that one failing service never breaks the whole page.

- **Missing `SERPAPI_KEY`:** flights, hotels and places are skipped with a log warning.
- **Failed external request or bad JSON:** the section returns `null`, and the results page shows "Not available" with a link to search Google Flights, Google Hotels or Google Maps directly.
- **City not recognized:** the departure city is resolved through a built-in alias list (e.g. `nyc` → `JFK`, `cdmx` → `MEX`), then the Travelpayouts autocomplete API. Accents and capitalization are ignored, so `São Paulo` and `sao paulo` both work.
- **Trip beyond the forecast window (15 days):** the current 7-day Miami forecast is shown instead, with a label saying so.
- **Gemini failures:** the app tries up to three models in order, waiting 4s, then 8s between attempts, or 10s after a rate-limit (429) error. If all fail, the user sees "The AI is busy right now" and a **Try again** button.
- **API keys in logs:** for SerpAPI requests, only the HTTP status code is logged, because the full error would include the request URL and the API key.

---

## Known Limitations

- **Miami only.** The destination, hotel search, places search and weather coordinates are all hard-coded to Miami.
- **Gender** is collected by the form but is not currently used in the itinerary prompt.
- **Places** are fetched for at most 4 interests (3 places each). If no supported interest is selected, "Top Attractions" is used.
- **Flights** show the 6 cheapest round-trip options. **Hotels** show the first 5 results.
- **Requests are synchronous.** `/api/plan` calls each service one after another, so generating a plan can take several seconds.
- **No user accounts or saved trips.** Plans live in the browser's `sessionStorage` and disappear when the tab is closed.

---

## Troubleshooting

**`ImportError: attempted relative import with no known parent package`**
You ran the server from inside `backend/` or with `python main.py`. Run `uvicorn backend.main:app --reload` from the project root.

**Flights, hotels and places all say "Not available"**
Check that `SERPAPI_KEY` is set in `.env` and that your SerpAPI account has searches left. The server log will show a warning explaining which call failed.

**The itinerary always says "The AI is busy right now"**
Check that `GOOGLE_API_KEY` is valid. If you set `GEMINI_MODEL`, make sure the model name exists. The server log shows the error for each attempt.

**Flights are missing for my city**
Try entering the airport's 3-letter IATA code directly (for example `LIM` instead of `Lima`).

**Old results keep showing up**
Flights and places are cached. Delete `backend/cache/` to force fresh results.

---

## Contributors
@AndresVZ23
@Salvacb

---

## License

All rights reserved. No license has been granted for use, copying or distribution of this project.

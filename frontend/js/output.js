const NETWORK_ERROR_MESSAGE = 'Could not reach the server. Please try again.';
const ITIN_LIMIT = 350;
const COLLAPSE_THRESHOLD = ITIN_LIMIT + 40;
const READ_MORE_LABEL = 'Read more ▾';
const READ_LESS_LABEL = 'Show less ▴';

function loadStored(key) {
  try {
    return JSON.parse(sessionStorage.getItem(key) || '{}');
  } catch (e) {
    console.error(`Failed to parse stored "${key}":`, e);
    return {};
  }
}

const plan = loadStored('plan');
const form = loadStored('destinai_form_data');

const flightsFallbackUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(
  `Flights from ${form.departureCity || ''} to Miami on ${form.startDate || ''} returning ${form.endDate || ''}`
)}`;
const hotelsFallbackUrl = `https://www.google.com/travel/hotels/Miami?checkin=${encodeURIComponent(
  form.startDate || ''
)}&checkout=${encodeURIComponent(form.endDate || '')}`;

const itin = document.getElementById('itinerary');
const itinWrap = document.getElementById('itinWrap');
const itinBtn = document.getElementById('itinToggle');

const HTML_ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };

function esc(value) {
  return String(value ?? '—').replace(/[&<>"]/g, (c) => HTML_ESCAPES[c]);
}

function isHttpUrl(value) {
  return /^https?:\/\//.test(value || '');
}

function formatShortDate(iso) {
  if (!iso) return '';
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function externalLink(url, label, cssClass = '') {
  const classAttr = cssClass ? ` class="${cssClass}"` : '';
  return `<a${classAttr} href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a>`;
}

function renderUnavailable(url, label) {
  return `<p class="muted">Not available</p>${externalLink(url, label, 'btn ghost')}`;
}

function renderWeather(data) {
  if (!data || !data.days || !data.days.length) {
    return '<p class="muted">Not available</p>';
  }
  const label = data.label ? `<p class="helper">${esc(data.label)}</p>` : '';
  const days = data.days
    .map(
      (day) => `
        <div class="weather-day">
          <b>${esc(formatShortDate(day.date))}</b><br>
          ${esc(Math.round(day.max))}° / ${esc(Math.round(day.min))}°F<br>
          ${esc(day.precip)} mm
        </div>`
    )
    .join('');
  return `${label}<div class="row">${days}</div>`;
}

function renderFlightCard(flight) {
  const time = flight.dep_time || '';
  let route = `${esc(flight.dep_airport || '')} ${esc(time)}`;
  if (flight.arr_airport) {
    route += ` → ${esc(flight.arr_airport)} ${esc(flight.arr_time || '')}`;
  }

  const logo = isHttpUrl(flight.logo) ? `<img src="${esc(flight.logo)}" alt="">` : '';

  let stops = '';
  if (flight.stops === 0) {
    stops = 'Nonstop';
  } else if (flight.stops != null) {
    stops = `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`;
  }
  const details = [flight.duration, stops, flight.flight_numbers].filter(Boolean).map(esc).join(' · ');

  return `
    <div class="item flight-card">
      <div class="row">
        <span class="row flight-airline">${logo}<b>${esc(flight.airline)}</b></span>
        <span class="flight-price"><b>$${esc(flight.price)}</b><div class="muted">round trip</div></span>
      </div>
      <div class="flight-route">${route}</div>
      <div class="muted">${details}</div>
    </div>`;
}

function renderFlights(data) {
  if (!data || !data.items || !data.items.length) {
    return renderUnavailable(flightsFallbackUrl, 'Search Google Flights');
  }
  const travelers = Number(form.travelers) || 1;
  const header = `Round trip · ${formatShortDate(form.startDate)} → ${formatShortDate(form.endDate)} · ${travelers} adult${travelers > 1 ? 's' : ''}`;
  const url = isHttpUrl(data.url) ? data.url : flightsFallbackUrl;
  return `
    <p class="helper">${esc(header)}</p>
    <div class="list">${data.items.map(renderFlightCard).join('')}</div>
    <p>${externalLink(url, 'See all on Google Flights', 'btn ghost')}</p>`;
}

function renderHotels(data) {
  if (!data || !data.length) {
    return renderUnavailable(hotelsFallbackUrl, 'Search Google Hotels');
  }
  const cards = data
    .map(
      (hotel) => `
        <div class="item">
          <div class="row"><span><b>${esc(hotel.name)}</b></span><span>${esc(hotel.price)} / night</span></div>
          <div class="muted">Rating: ${esc(hotel.rating)}</div>
          ${isHttpUrl(hotel.link) ? externalLink(hotel.link, 'View') : ''}
        </div>`
    )
    .join('');
  return `
    <div class="list">${cards}</div>
    <p>${externalLink(hotelsFallbackUrl, 'More on Google Hotels', 'btn ghost')}</p>`;
}

function renderPlaceCard(place) {
  const thumbnail = isHttpUrl(place.thumbnail) ? `<img src="${esc(place.thumbnail)}" alt="">` : '';
  const rating = place.rating != null ? `★ ${Number(place.rating).toFixed(1)}` : 'No rating';
  const reviews = place.reviews ? ` (${esc(place.reviews)})` : '';
  return `
    <div class="item place-card">
      ${thumbnail}
      <b>${esc(place.title)}</b>
      <div class="muted">${rating}${reviews}</div>
      <div class="muted">${esc(place.address)}</div>
      ${isHttpUrl(place.link) ? externalLink(place.link, 'View') : ''}
    </div>`;
}

function renderPlaces(data) {
  if (!data || !data.length) {
    return renderUnavailable('https://www.google.com/maps/search/things+to+do+in+Miami', 'Search Google Maps');
  }
  return data
    .map(
      (group) => `
        <h3 class="place-group-title">${esc(group.interest)}</h3>
        <div class="row stretch">${group.places.map(renderPlaceCard).join('')}</div>`
    )
    .join('');
}

function renderItinerary() {
  itinWrap.className = 'itin-wrap';
  itinWrap.style.maxHeight = '';
  itinBtn.hidden = true;
  itinBtn.textContent = READ_MORE_LABEL;
  itinBtn.onclick = null;

  if (plan.itinerary) {
    itin.className = 'itinerary';
    itin.innerHTML = DOMPurify.sanitize(marked.parse(plan.itinerary));
    setupCollapse();
    return;
  }

  itin.className = '';
  itinWrap.classList.add('short');
  itinWrap.style.maxHeight = 'none';
  itin.innerHTML = `<p class="muted">${esc(plan.itinerary_error || NETWORK_ERROR_MESSAGE)}</p><button type="button" class="btn" id="itinRetry">Try again</button>`;
  document.getElementById('itinRetry').onclick = retryItinerary;
}

async function retryItinerary() {
  const retryBtn = document.getElementById('itinRetry');
  retryBtn.disabled = true;
  retryBtn.textContent = 'Generating...';
  try {
    const resp = await fetch('/api/itinerary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        form,
        weather: plan.weather,
        flights: plan.flights,
        hotels: plan.hotels,
        places: plan.places,
      }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const result = await resp.json();
    plan.itinerary = result.itinerary;
    plan.itinerary_error = result.itinerary_error;
    try {
      sessionStorage.setItem('plan', JSON.stringify(plan));
    } catch (e) {
      console.error('Failed to persist plan:', e);
    }
  } catch (e) {
    console.error('Itinerary retry failed:', e);
    plan.itinerary_error = NETWORK_ERROR_MESSAGE;
  }
  renderItinerary();
}

function setupCollapse() {
  if (itin.scrollHeight <= COLLAPSE_THRESHOLD) {
    itinWrap.classList.add('short');
    itinWrap.style.maxHeight = 'none';
    return;
  }
  itinBtn.hidden = false;
  itinBtn.onclick = () => {
    const opening = !itinWrap.classList.contains('open');
    if (opening) {
      itinWrap.classList.add('open');
      itinWrap.style.maxHeight = `${itinWrap.scrollHeight}px`;
      const onTransitionEnd = (ev) => {
        if (ev.propertyName !== 'max-height') return;
        itinWrap.removeEventListener('transitionend', onTransitionEnd);
        if (itinWrap.classList.contains('open')) itinWrap.style.maxHeight = 'none';
      };
      itinWrap.addEventListener('transitionend', onTransitionEnd);
    } else {
      itinWrap.style.maxHeight = `${itinWrap.scrollHeight}px`;
      void itinWrap.offsetHeight; // force reflow so the collapse animates
      itinWrap.classList.remove('open');
      itinWrap.style.maxHeight = `${ITIN_LIMIT}px`;
      itinWrap.closest('.card').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    itinBtn.textContent = opening ? READ_LESS_LABEL : READ_MORE_LABEL;
  };
}

renderItinerary();
document.getElementById('weather').innerHTML = renderWeather(plan.weather);
document.getElementById('places').innerHTML = renderPlaces(plan.places);
document.getElementById('flights').innerHTML = renderFlights(plan.flights);
document.getElementById('hotels').innerHTML = renderHotels(plan.hotels);

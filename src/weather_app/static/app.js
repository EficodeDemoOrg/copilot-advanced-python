/**
 * Weather Dashboard — client-side application logic.
 *
 * Fetches data from the FastAPI backend and renders the dashboard
 * using vanilla JavaScript and Chart.js for forecast visualization.
 */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let forecastChart = null;
let currentLat = null;
let currentLon = null;

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

const latInput = document.getElementById("lat-input");
const lonInput = document.getElementById("lon-input");
const unitsSelect = document.getElementById("units-select");
const searchBtn = document.getElementById("search-btn");
const saveBtn = document.getElementById("save-btn");
const searchError = document.getElementById("search-error");
const locationsList = document.getElementById("locations-list");
const currentWeatherCard = document.getElementById("current-weather");
const alertsSection = document.getElementById("alerts-section");
const alertsList = document.getElementById("alerts-list");
const forecastSection = document.getElementById("forecast-section");

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiGet(url) {
    const response = await fetch(url);
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `API error: ${response.status}`);
    }
    return response.json();
}

async function apiPost(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `API error: ${response.status}`);
    }
    return response.json();
}

async function apiDelete(url) {
    const response = await fetch(url, { method: "DELETE" });
    if (!response.ok && response.status !== 204) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `API error: ${response.status}`);
    }
}

// ---------------------------------------------------------------------------
// Weather display
// ---------------------------------------------------------------------------

function unitSymbol(units) {
    switch (units) {
        case "fahrenheit": return "°F";
        case "kelvin": return "K";
        default: return "°C";
    }
}

function showCurrentWeather(data) {
    const symbol = unitSymbol(data.units);

    document.getElementById("location-name").textContent = data.location_name;
    document.getElementById("weather-icon").src =
        `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
    document.getElementById("weather-icon").alt = data.description;
    document.getElementById("weather-desc").textContent = data.description;
    document.getElementById("temperature").textContent =
        `${data.temperature}${symbol}`;
    document.getElementById("feels-like").textContent =
        `${data.feels_like}${symbol}`;
    document.getElementById("humidity").textContent = `${data.humidity}%`;
    document.getElementById("pressure").textContent = `${data.pressure} hPa`;
    document.getElementById("wind").textContent =
        `${data.wind_speed} m/s (${data.wind_direction}°)`;

    currentWeatherCard.classList.remove("hidden");
}

function showAlerts(alerts) {
    alertsList.innerHTML = "";
    if (alerts.length === 0) {
        alertsSection.classList.add("hidden");
        return;
    }
    alerts.forEach((alert) => {
        const li = document.createElement("li");
        li.className = `severity-${alert.severity}`;
        li.textContent = alert.message;
        alertsList.appendChild(li);
    });
    alertsSection.classList.remove("hidden");
}

function showForecast(data) {
    if (!data.days || data.days.length === 0) {
        forecastSection.classList.add("hidden");
        return;
    }

    const symbol = unitSymbol(data.units);
    const labels = data.days.map((d) => d.forecast_date);
    const highs = data.days.map((d) => d.temp_max);
    const lows = data.days.map((d) => d.temp_min);

    if (forecastChart) {
        forecastChart.destroy();
    }

    const ctx = document.getElementById("forecast-chart").getContext("2d");
    forecastChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: `High (${symbol})`,
                    data: highs,
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    fill: "+1",
                    tension: 0.3,
                },
                {
                    label: `Low (${symbol})`,
                    data: lows,
                    borderColor: "#3b82f6",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: false,
                    tension: 0.3,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top" },
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: `Temperature (${symbol})`,
                    },
                },
            },
        },
    });

    forecastSection.classList.remove("hidden");
}

// ---------------------------------------------------------------------------
// Locations
// ---------------------------------------------------------------------------

async function loadLocations() {
    try {
        const locations = await apiGet("/api/locations");
        locationsList.innerHTML = "";
        locations.forEach((loc) => {
            const li = document.createElement("li");
            li.innerHTML = `
                <div>
                    <div class="loc-name">${loc.name}</div>
                    <div class="loc-coords">${loc.coordinates.lat.toFixed(2)}, ${loc.coordinates.lon.toFixed(2)}</div>
                </div>
                <button class="delete-btn" title="Delete">&times;</button>
            `;
            li.querySelector(".loc-name").addEventListener("click", () => {
                latInput.value = loc.coordinates.lat;
                lonInput.value = loc.coordinates.lon;
                fetchWeather(loc.coordinates.lat, loc.coordinates.lon);
            });
            li.querySelector(".delete-btn").addEventListener("click", async (e) => {
                e.stopPropagation();
                await apiDelete(`/api/locations/${loc.id}`);
                loadLocations();
            });
            locationsList.appendChild(li);
        });
    } catch (err) {
        console.error("Failed to load locations:", err);
    }
}

// ---------------------------------------------------------------------------
// Search & fetch
// ---------------------------------------------------------------------------

async function fetchWeather(lat, lon) {
    const units = unitsSelect.value;
    currentLat = lat;
    currentLon = lon;

    searchError.classList.add("hidden");

    try {
        const [weather, forecast, alerts] = await Promise.all([
            apiGet(`/api/weather/current?lat=${lat}&lon=${lon}&units=${units}`),
            apiGet(`/api/weather/forecast?lat=${lat}&lon=${lon}&units=${units}`),
            apiGet(`/api/weather/alerts?lat=${lat}&lon=${lon}`),
        ]);

        showCurrentWeather(weather);
        showForecast(forecast);
        showAlerts(alerts);
    } catch (err) {
        searchError.textContent = err.message;
        searchError.classList.remove("hidden");
    }
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

searchBtn.addEventListener("click", () => {
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(lonInput.value);
    if (isNaN(lat) || isNaN(lon)) {
        searchError.textContent = "Please enter valid latitude and longitude.";
        searchError.classList.remove("hidden");
        return;
    }
    fetchWeather(lat, lon);
});

saveBtn.addEventListener("click", async () => {
    if (currentLat === null || currentLon === null) {
        searchError.textContent = "Search for a location first.";
        searchError.classList.remove("hidden");
        return;
    }
    const name = prompt("Enter a name for this location:");
    if (!name) return;

    try {
        await apiPost("/api/locations", {
            name,
            lat: currentLat,
            lon: currentLon,
        });
        loadLocations();
    } catch (err) {
        searchError.textContent = err.message;
        searchError.classList.remove("hidden");
    }
});

// Allow Enter key to trigger search
[latInput, lonInput].forEach((input) => {
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") searchBtn.click();
    });
});

// ---------------------------------------------------------------------------
// Initialize
// ---------------------------------------------------------------------------

loadLocations();

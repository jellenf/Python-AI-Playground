const form = document.querySelector("#search-form");
const input = document.querySelector("#place-input");
const emptyState = document.querySelector("#empty-state");
const image = document.querySelector("#map-image");
const loading = document.querySelector("#map-loading");
const error = document.querySelector("#map-error");
const status = document.querySelector("#map-status");
const placeName = document.querySelector("#place-name");
const placeRegion = document.querySelector("#place-region");
const coordinates = document.querySelector("#place-coordinates");
let activeRequest = false;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const place = input.value.trim();
  if (!place || activeRequest) return;

  activeRequest = true;
  form.querySelector("button").disabled = true;
  emptyState.hidden = true;
  image.hidden = true;
  error.hidden = true;
  loading.hidden = false;
  status.textContent = "SEARCHING";

  try {
    const response = await fetch(`/api/map?q=${encodeURIComponent(place)}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Map lookup failed.");

    image.src = result.image;
    image.alt = `Street and geographic overview map of ${result.name}`;
    placeName.textContent = result.name;
    placeRegion.textContent = result.region || "";
    coordinates.textContent = `${result.coordinates.lat.toFixed(4)}°  ${result.coordinates.lon.toFixed(4)}°`;
    status.textContent = "MAP READY";
    image.hidden = false;
  } catch (lookupError) {
    error.textContent = lookupError.message || "Unable to load this map. Try again.";
    error.hidden = false;
    status.textContent = "LOOKUP FAILED";
  } finally {
    loading.hidden = true;
    form.querySelector("button").disabled = false;
    activeRequest = false;
  }
});
// Extract and register Alpine data
document.addEventListener("alpine:init", () => {
  const jsonEl = document.getElementById("preferences-data");
  let data = {};

  if (jsonEl) {
    try {
      data = JSON.parse(jsonEl.textContent);
      window._preferences = data;
    } catch (e) {
      console.error("Failed to parse preferences data", e);
    }
  }

  Alpine.data("preferences", () => data);
});

// Handle DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  // Get CSRF token
  const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

  // Load artist selection
  const artistSelect = document.getElementById("artist-select");
  if (!artistSelect) {
    return;
  }

  // Constants for localStorage cache key and max age
  const CACHE_KEY = "artistList";
  const CACHE_MAX_AGE = 24 * 60 * 60 * 1000; // 1 day in milliseconds

  // Try to use cached data
  const cached = localStorage.getItem(CACHE_KEY);

  if (cached) {
    // Parse the cached JSON object
    const parsed = JSON.parse(cached);
    const age = Date.now() - parsed.timestamp;

    // If cached data is still fresh, use it
    if (age < CACHE_MAX_AGE) {
      initArtistSelect(parsed.data);
      return;
    } else {
      // Otherwise, remove stale cache
      localStorage.removeItem(CACHE_KEY);
    }
  }

  // Fetch artists from API
  fetch("/api/artists", { headers: { "X-CSRFToken": csrfToken } })
    .then((response) => response.json())
    .then((artists) => {
      // Store fetched data in localStorage with a timestamp
      localStorage.setItem(
        CACHE_KEY,
        JSON.stringify({
          data: artists,
          timestamp: Date.now(),
        })
      );

      // Initialize the dropdown with fetched data
      initArtistSelect(artists);
    })
    .catch((error) => console.error("Error loading artists:", error));

  // Function to initialize artist dropdown
  function initArtistSelect(artists) {
    // Map artist names into Tom Select format
    const options = artists.map((artist) => ({
      value: artist,
      text: artist,
    }));

    // Get preferred artists from Alpine.js state
    let selected_items = [];
    const preferred_artists = getAlpineDataProperty("artists");
    if (Array.isArray(preferred_artists)) {
      selected_items = preferred_artists;
    }

    // Initialize Tom Select
    new TomSelect(artistSelect, {
      options: options,
      items: selected_items,
      maxOptions: 1000,
      searchField: "text",
      placeholder: "Search for an artist...",
      persist: false,
      create: false,
      clearAfterSelect: true,
      closeAfterSelect: true,
      plugins: ["remove_button"],
    });
  }

  // Function to get a property from Alpine.js state
  function getAlpineDataProperty(propName) {
    const el = document.querySelector("[x-data]");
    return el?._x_dataStack?.[0]?.[propName];
  }
});

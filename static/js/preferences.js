document.addEventListener("DOMContentLoaded", () => {
  // Load artist selection
  const artistSelect = document.getElementById("artist-select");
  if (!artistSelect) {
    return;
  }

  // Fetch artists from API
  fetch("/api/artists")
    .then((response) => response.json())
    .then((artists) => {
      // Map artist names into Tom Select format
      const options = artists.map((artist) => ({
        value: artist,
        text: artist,
      }));

      // Initialize Tom Select
      new TomSelect(artistSelect, {
        options: options,
        maxOptions: 1000,
        searchField: "text",
        placeholder: "Search for an artist...",
        persist: false,
        create: false,
        clearAfterSelect: true,
        closeAfterSelect: true,
        plugins: ["remove_button"],
      });
    })
    .catch((error) => console.error("Error loading artists:", error));
});

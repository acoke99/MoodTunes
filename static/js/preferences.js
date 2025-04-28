document.addEventListener("DOMContentLoaded", () => {
  // Load artist selection
  const artistSelect = document.getElementById("artist-select");
  if (!artistSelect) {
    return;
  }

  const choices = new Choices(artistSelect, {
    removeItemButton: true,
  });

  // Fetch artists from API
  fetch("/api/artists")
    .then((response) => response.json())
    .then((artists) => {
      // Map artist names into Choices.js format
      const artistChoices = artists.map((artist) => ({
        value: artist,
        label: artist,
      }));

      // Load into Choices.js
      choices.setChoices(artistChoices, "value", "label", true);
    })
    .catch((error) => console.error("Error loading artists:", error));
});

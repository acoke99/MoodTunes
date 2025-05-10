document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("queue-form");
  const button = document.getElementById("queue-btn");
  const messageDiv = document.getElementById("custom-messages");

  const newSongsBtn = document.getElementById("new-songs");
  const newMoodBtn = document.getElementById("new-mood");

  const pauseBtn = document.getElementById("pause-btn");
  const playBtn = document.getElementById("play-btn");
  const nextBtn = document.getElementById("next-btn");
  const previousBtn = document.getElementById("previous-btn");

  const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

  // Add handler for button to queue tracks
  if (form && button && messageDiv) {
    form.addEventListener("submit", async function (e) {
      // Prevent default form submission
      e.preventDefault();
      button.disabled = true;
      messageDiv.innerHTML = "";

      // Gather selected tracks
      const formData = new FormData(form);
      const selectedTracks = formData.getAll("selected_tracks");

      // Validate selection
      if (selectedTracks.length === 0) {
        showToast("Please select at least one track.", "warning");
        button.disabled = false;
        return;
      }

      // Call API
      // Leave "queue tracks" button disabled after successful call
      try {
        const response = await fetch("/api/queue", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
          body: JSON.stringify(selectedTracks),
        });
        const result = await response.json();
        if (response.ok) {
          showToast(result.message, "success");

          // Hide the "queue tracks" button
          button.classList.add("hidden");

          // Disable all selected_tracks checkboxes
          document.querySelectorAll('input[name="selected_tracks"]').forEach((cb) => (cb.disabled = true));

          // Show the "new mood" button
          if (newMoodBtn) {
            newMoodBtn.classList.remove("hidden");
          }
        } else {
          showToast(result.error, "error");
          button.disabled = false;
        }
      } catch (error) {
        showToast("Unable to connect. Please try again.", "error");
        button.disabled = false;
      }
    });
  }

  // Navigation handlers for "new songs" and "new mood" buttons
  if (newSongsBtn) {
    newSongsBtn.addEventListener("click", () => {
      window.location.href = "/recommendations";
    });
  }
  if (newMoodBtn) {
    newMoodBtn.addEventListener("click", () => {
      window.location.href = "/mood";
    });
  }

  // Playback control handlers
  if (pauseBtn) {
    pauseBtn.addEventListener("click", function () {
      fetch("/api/pause", { method: "POST", headers: { "X-CSRFToken": csrfToken } });
    });
  }
  if (playBtn) {
    playBtn.addEventListener("click", function () {
      fetch("/api/play", { method: "POST", headers: { "X-CSRFToken": csrfToken } });
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function () {
      fetch("/api/next", { method: "POST", headers: { "X-CSRFToken": csrfToken } });
    });
  }
  if (previousBtn) {
    previousBtn.addEventListener("click", function () {
      fetch("/api/previous", { method: "POST", headers: { "X-CSRFToken": csrfToken } });
    });
  }
});

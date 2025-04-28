document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("queue-form");
  const button = document.getElementById("queue-btn");
  const messageDiv = document.getElementById("custom-messages");
  const postQueueButtons = document.getElementById("post-queue-buttons");
  const newSongsBtn = document.getElementById("new-songs");
  const newMoodBtn = document.getElementById("new-mood");

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
        showMessage("Please select at least one track.", "warning");
        button.disabled = false;
        return;
      }

      // Call API
      // Leave button disabled after successful call
      try {
        const response = await fetch("/api/queue", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(selectedTracks),
        });
        const result = await response.json();
        if (response.ok) {
          showMessage(result.message, "success");

          // Hide the queue button
          button.style.display = "none";

          // Show the row of buttons for "new songs" and "new mood"
          if (postQueueButtons) {
            postQueueButtons.classList.remove("hidden");
          }
        } else {
          showMessage(result.error, "error");
          button.disabled = false;
        }
      } catch (error) {
        showMessage("Unable to connect. Please try again.", "error");
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

  // Show custom message
  // type: "success", "warning", "error", "info"
  function showMessage(msg, type) {
    messageDiv.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
  }
});

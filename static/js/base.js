document.addEventListener("DOMContentLoaded", () => {
  // Add handler for the menu toggle
  const toggle = document.getElementById("menu-toggle");
  const menu = document.getElementById("menu");

  if (toggle) {
    toggle.addEventListener("click", function () {
      this.classList.toggle("is-active");

      if (menu.style.maxHeight) {
        menu.style.maxHeight = null;
      } else {
        menu.style.maxHeight = menu.scrollHeight + "px";
      }
    });
  }

  // Read and show Flask flash messages as toasts (from data attribute)
  const flashEl = document.getElementById("server-flash-data");
  if (flashEl) {
    const flashes = JSON.parse(flashEl.dataset.flashes);
    flashes.forEach(([category, message]) => {
      showToast(category, message);
    });
  }
});

// Show toast notification
// type: "success", "warning", "error", "info"
function showToast(message, type = "info", duration = 5000) {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, duration + 500); // allow fade-out to complete
}

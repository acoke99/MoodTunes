document.addEventListener("DOMContentLoaded", () => {
  // Add handler for the menu toggle
  const toggle = document.getElementById("menu-toggle");
  const menu = document.getElementById("menu");

  toggle.addEventListener("click", function () {
    this.classList.toggle("is-active");

    if (menu.style.maxHeight) {
      menu.style.maxHeight = null;
    } else {
      menu.style.maxHeight = menu.scrollHeight + "px";
    }
  });
});

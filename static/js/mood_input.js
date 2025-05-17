document.addEventListener("DOMContentLoaded", function () {
  const valence = document.getElementById("valence");
  const energy = document.getElementById("energy");
  const valenceEmoji = document.getElementById("valence-emoji");
  const energyEmoji = document.getElementById("energy-emoji");

  function getEmoji(value, type) {
    const index = Math.min(4, Math.floor(value / 20));
    const emojiSets = {
      valence: ["\u{1F622}", "\u{1F641}", "\u{1F610}", "\u{1F642}", "\u{1F601}"], // 😢🙁😐🙂😁
      energy: ["\u{1F4A4}", "\u{1F634}", "\u{1F636}", "\u{1F603}", "\u{26A1}"], // 💤😴😶😃⚡
    };
    return emojiSets[type][index];
  }

  function updateEmoji() {
    valenceEmoji.innerHTML = getEmoji(valence.value, "valence");
    energyEmoji.innerHTML = getEmoji(energy.value, "energy");
  }

  valence.addEventListener("input", updateEmoji);
  energy.addEventListener("input", updateEmoji);

  updateEmoji(); // initialize
});

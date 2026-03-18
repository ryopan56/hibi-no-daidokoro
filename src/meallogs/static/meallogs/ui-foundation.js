(function () {
  const copies = [
    "今日はこれでいい。",
    "ここに来たこと自体で、もう十分です。",
    "急がなくて大丈夫。ひとつずつで大丈夫です。",
  ];

  function hideLayer(layer) {
    layer.dataset.state = "hidden";
    window.setTimeout(() => {
      layer.hidden = true;
    }, 260);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const layer = document.querySelector("[data-startup-layer]");
    const text = document.querySelector("[data-startup-copy-text]");
    if (!layer || !text) {
      return;
    }

    if (window.sessionStorage.getItem("startup-copy-seen") === "1") {
      layer.remove();
      return;
    }

    window.sessionStorage.setItem("startup-copy-seen", "1");
    text.textContent = copies[Math.floor(Math.random() * copies.length)];
    layer.hidden = false;
    layer.dataset.state = "visible";
    window.setTimeout(() => hideLayer(layer), 1400);
  });
})();

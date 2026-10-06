document.addEventListener("DOMContentLoaded", () => {
  for (const image of document.querySelectorAll("article img")) {
    if (image.closest("a, button")) continue;
    const link = document.createElement("a");
    link.href = image.currentSrc || image.src;
    link.className = "pq-figure-link";
    link.setAttribute("aria-label", `Open figure at full size: ${image.alt}`);
    image.before(link);
    link.append(image);
  }
});

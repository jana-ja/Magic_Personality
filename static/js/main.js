/**
 * HTMX-Ergänzung fürs Fünfeck (Task 1.8, D-24).
 *
 * Die Fünfeck-Ecken sind <a>-Elemente *innerhalb* eines <svg> (Task
 * 1.5/1.6) — das macht sie zu SVGAElement, nicht zu HTMLAnchorElement.
 * HTMX entscheidet in seiner shouldCancel()-Logik aber ausdrücklich
 * über `instanceof HTMLAnchorElement`, ob es die native Navigation per
 * preventDefault() unterbindet. Für ein SVG-<a> trifft das nie zu —
 * HTMX feuert zwar korrekt seinen eigenen AJAX-Request, lässt daneben
 * aber den Browser dem href ganz normal folgen: zwei identische
 * Requests, und am Ende gewinnt der echte Seitenwechsel statt des
 * Panel-Swaps (im Browser nachgestellt und über einen pagehide-
 * Listener nachgewiesen — siehe die Verifikation zu Task 1.8).
 *
 * Ein normales HTML-<a> (z. B. "Reset selection" in der Info-Box)
 * braucht das nicht: HTMX erkennt es korrekt selbst.
 */
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[hx-get]");
  if (link instanceof SVGAElement) {
    event.preventDefault();
  }
});

/**
 * Tastatur und Barrierefreiheit fürs Fünfeck (Task 1.9, FR-C5, FR-C8,
 * NFR-5). Bleibt bewusst dünn: jede Aktion läuft am Ende über
 * .click() auf den ohnehin vorhandenen, server-gerenderten <a>-Link
 * — keine eigene URL-Logik in JS, der href bleibt die einzige Quelle
 * der Wahrheit dafür, wohin ein Klick führt.
 */

const COLOR_KEYS = "WUBRG";

function isTypingTarget(target) {
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

// SVGAElement (die Fünfeck-Ecken, s. o.) hat anders als HTMLAnchorElement
// gar keine .click()-Methode — derselbe HTML/SVG-Unterschied wie oben,
// diesmal nicht bei der Navigation, sondern beim programmatischen
// Auslösen eines Klicks. Ein manuell konstruiertes MouseEvent
// funktioniert für beide Elementtypen gleichermaßen.
function simulateClick(element) {
  if (typeof element.click === "function") {
    element.click();
  } else {
    element.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
  }
}

// W/U/B/R/G schalten die jeweilige Farbe um, Esc setzt zurück
// (FR-C8, FR-C5). Modifier-Tasten werden ignoriert — sonst würde z. B.
// Ctrl+W ("Tab schließen") durch das eigene preventDefault() blockiert.
document.addEventListener("keydown", (event) => {
  if (!document.getElementById("colors-panel")) return;
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (isTypingTarget(event.target)) return;

  if (event.key === "Escape") {
    const reset = document.getElementById("reset-selection");
    if (reset) simulateClick(reset);
    return;
  }

  const key = event.key.toUpperCase();
  if (key.length === 1 && COLOR_KEYS.includes(key)) {
    const vertex = document.querySelector(`.pentagon__vertex[data-color="${key}"]`);
    if (vertex) {
      event.preventDefault();
      simulateClick(vertex);
    }
  }
});

// Leertaste aktiviert role="button"-Elemente (NFR-5) — Browser tun das
// von sich aus nur bei echten <button>-Elementen, nicht bei Links mit
// role="button" (betrifft die Fünfeck-Ecken und den Reset-Link).
document.addEventListener("keydown", (event) => {
  if (event.key !== " " && event.key !== "Spacebar") return;
  const target = event.target.closest('a[role="button"]');
  if (!target) return;
  event.preventDefault();
  simulateClick(target);
});

// Optimistische Hervorhebung: die Markierung schaltet sofort um, bevor
// die HTMX-Antwort da ist — der tatsächliche Server-Zustand korrigiert
// das gleich danach beim Swap (ARCHITECTURE.md §4.3). Liest den
// *aktuellen* Zustand direkt aus aria-pressed statt ihn separat
// mitzuführen, damit neben dem server-gerenderten HTML keine zweite
// Quelle der Wahrheit entsteht.
document.addEventListener("click", (event) => {
  const vertex = event.target.closest(".pentagon__vertex");
  const isReset = event.target.closest("#reset-selection");
  if (!vertex && !isReset) return;

  const vertices = document.querySelectorAll(".pentagon__vertex");
  const selected = new Set(
    [...vertices]
      .filter((v) => v.getAttribute("aria-pressed") === "true")
      .map((v) => v.dataset.color)
  );

  if (isReset) {
    selected.clear();
  } else if (selected.has(vertex.dataset.color)) {
    selected.delete(vertex.dataset.color);
  } else {
    selected.add(vertex.dataset.color);
  }

  const hasSelection = selected.size > 0;
  vertices.forEach((v) => {
    const isSelected = selected.has(v.dataset.color);
    v.setAttribute("aria-pressed", isSelected ? "true" : "false");
    v.classList.toggle("pentagon__vertex--selected", hasSelection && isSelected);
    v.classList.toggle("pentagon__vertex--unselected", hasSelection && !isSelected);
  });
});

// Live-Region (NFR-5): nach jedem Panel-Swap den neuen Kombinations-
// namen ansagen. #colors-live-region bleibt über jeden Swap hinweg
// bestehen (liegt außerhalb von #colors-panel, siehe index.html) —
// nur so kündigen Screenreader Änderungen daran zuverlässig an.
document.body.addEventListener("htmx:afterSwap", (event) => {
  if (event.target.id !== "colors-panel") return;
  const liveRegion = document.getElementById("colors-live-region");
  if (!liveRegion) return;
  const title = event.target.querySelector(".info-box__title");
  liveRegion.textContent = title ? title.textContent : liveRegion.dataset.emptyText;
});

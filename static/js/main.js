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

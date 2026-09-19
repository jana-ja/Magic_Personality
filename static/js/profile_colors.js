/**
 * Farbwahl im Profil als Fünfeck (Task 4.6, FR-P13, D-74).
 *
 * Bleibt bewusst dünn: die echten Kontrollkästchen (name="colors") sind die
 * Quelle der Wahrheit, das Fünfeck schaltet sie nur um und spiegelt ihren
 * Zustand. Ohne dieses Skript bleiben die Kästchen sichtbar und das Formular
 * funktioniert unverändert. Ereignisse laufen über Delegation, damit auch ein
 * per HTMX nachgeladenes Formular ohne Neuinitialisierung funktioniert.
 */
document.documentElement.classList.add("js");

function checkboxFor(vertex) {
  const form = vertex.closest("form");
  return form.querySelector(`input[name="colors"][value="${vertex.dataset.color}"]`);
}

// Spiegelt den Zustand der Kästchen ins Fünfeck; wie in den Color Infos ist
// bei leerer Auswahl nichts zurückgenommen (FR-C6).
function sync(form) {
  const vertices = form.querySelectorAll(".color-field__vertex");
  const hasSelection = [...vertices].some((vertex) => checkboxFor(vertex).checked);
  vertices.forEach((vertex) => {
    const checked = checkboxFor(vertex).checked;
    vertex.setAttribute("aria-checked", checked ? "true" : "false");
    vertex.classList.toggle("pentagon__vertex--selected", hasSelection && checked);
    vertex.classList.toggle("pentagon__vertex--unselected", hasSelection && !checked);
  });
}

function toggle(vertex) {
  const box = checkboxFor(vertex);
  box.checked = !box.checked;
  // Wer am Fünfeck klickt, will die Farben selbst wählen.
  const manual = vertex.closest("form").querySelector('input[name="choice"][value="manual"]');
  if (manual) manual.checked = true;
  sync(vertex.closest("form"));
}

document.addEventListener("click", (event) => {
  const vertex = event.target.closest(".color-field__vertex");
  if (vertex) toggle(vertex);
});

document.addEventListener("keydown", (event) => {
  if (event.key !== " " && event.key !== "Enter") return;
  const vertex = event.target.closest?.(".color-field__vertex");
  if (!vertex) return;
  event.preventDefault();
  toggle(vertex);
});

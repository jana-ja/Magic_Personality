/**
 * Fokus und Ansage nach dem Austausch eines Profil-Bereichs per HTMX
 * (Task 4.9, NFR-5, D-73).
 *
 * Nickname, Bio und Farben tauschen sich an Ort und Stelle zwischen Anzeige und
 * Formular. Beim Öffnen fokussiert das Formular sein erstes Feld selbst
 * (autofocus); hier kommt der Rest dazu: nach Speichern oder Abbrechen springt
 * der Fokus zurück auf den "Edit"-Link (sonst ginge er mit dem ersetzten Element
 * verloren), und die Live-Region sagt an, was passiert ist — wie bei den Color
 * Infos (Task 1.9). Ohne JavaScript ändert sich nichts: jede Adresse ist eine
 * normale Seite.
 */
const SECTIONS = ["profile-bio", "profile-colors", "profile-name"];

document.body.addEventListener("htmx:afterSettle", (event) => {
  const id = event.detail.target && event.detail.target.id;
  if (!SECTIONS.includes(id)) return;

  // Bei outerHTML ist das alte Element weg; die id findet das neue.
  const section = document.getElementById(id);
  const live = document.getElementById("profile-live-region");
  if (!section || !live) return;

  if (section.querySelector("form")) {
    live.textContent = live.dataset.editingText;
    return;
  }

  const link = section.querySelector(".profile-edit-link");
  if (link) link.focus();
  const saved = event.detail.requestConfig && event.detail.requestConfig.verb === "post";
  live.textContent = saved ? live.dataset.savedText : live.dataset.cancelledText;
});

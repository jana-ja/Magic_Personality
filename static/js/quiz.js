/**
 * Live-Fortschritt beim Testdurchlauf (Task 2.8, FR-T9: "Fortschritt
 * ist sichtbar"). Ohne dieses Skript bleibt die statische Zahl aus
 * dem Server-Rendering stehen ("30 questions in total") — die Seite
 * funktioniert also auch ohne JavaScript, nur ohne Live-Update
 * (ARCHITECTURE.md §4, Progressive Enhancement).
 */
(function () {
  const form = document.querySelector("[data-quiz-form]");
  const progress = document.querySelector("[data-quiz-progress]");
  if (!form || !progress) return;

  const total = parseInt(progress.dataset.total, 10);
  const template = progress.dataset.template;

  // Eine Frage gilt als beantwortet, wenn alle ihre Ränge gewählt sind
  // (v1: eine Auswahl, v2: beste und zweitbeste Antwort, D-65).
  function update() {
    let answered = 0;
    form.querySelectorAll("[data-quiz-question]").forEach((question) => {
      const picks = parseInt(question.dataset.picks, 10);
      if (question.querySelectorAll("input[type=radio]:checked").length === picks) {
        answered += 1;
      }
    });
    progress.textContent = template.replace("{answered}", answered).replace("{total}", total);
  }

  form.addEventListener("change", update);
  update();
})();

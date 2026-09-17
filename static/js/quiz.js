/**
 * Live-Fortschritt beim Testdurchlauf (Task 2.8, FR-T9: "Fortschritt
 * ist sichtbar"). Ohne dieses Skript bleibt die statische Zahl aus
 * dem Server-Rendering stehen ("20 questions in total") — die Seite
 * funktioniert also auch ohne JavaScript, nur ohne Live-Update
 * (ARCHITECTURE.md §4, Progressive Enhancement).
 */
(function () {
  const form = document.querySelector("[data-quiz-form]");
  const progress = document.querySelector("[data-quiz-progress]");
  if (!form || !progress) return;

  const total = parseInt(progress.dataset.total, 10);
  const template = progress.dataset.template;

  function update() {
    const answeredQuestions = new Set();
    form.querySelectorAll("input[type=radio]:checked").forEach((input) => {
      answeredQuestions.add(input.name);
    });
    progress.textContent = template
      .replace("{answered}", answeredQuestions.size)
      .replace("{total}", total);
  }

  form.addEventListener("change", update);
  update();
})();

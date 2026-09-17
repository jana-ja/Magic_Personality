/**
 * Übernimmt ein im Browser zwischengespeichertes anonymes Testergebnis
 * nach Login/Registrierung (Task 2.11, FR-T16). Läuft auf jeder Seite
 * (siehe base.html): Login und Registrierung leiten nicht auf eine
 * bestimmte Zielseite (LOGIN_REDIRECT_URL) — die Übernahme passiert
 * deshalb beim nächsten Seitenaufruf danach, ganz gleich wo er landet.
 *
 * Ein echter, unsichtbarer Formular-POST statt fetch(): die Antwort
 * ist eine vollständige HTML-Seite (dieselbe Ergebnisseite wie direkt
 * nach dem Test, Task 2.10) — der Browser soll dorthin navigieren,
 * nicht sie als Text empfangen.
 */
(function () {
  if (document.body.dataset.authenticated !== "true") return;

  let token;
  try {
    token = localStorage.getItem("mp_pending_quiz_result");
    if (token) localStorage.removeItem("mp_pending_quiz_result");
  } catch (error) {
    return;
  }
  if (!token) return;

  const csrfToken = JSON.parse(document.body.getAttribute("hx-headers"))["X-CSRFToken"];

  const form = document.createElement("form");
  form.method = "post";
  form.action = "/quiz/results/claim/";
  form.style.display = "none";
  form.innerHTML = '<input name="csrfmiddlewaretoken"><input name="token">';
  form.elements.csrfmiddlewaretoken.value = csrfToken;
  form.elements.token.value = token;

  document.body.appendChild(form);
  form.submit();
})();

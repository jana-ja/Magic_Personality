"""
Views der Social-App: fremde Profile ansehen (Task 3.1, FR-S1), nach
Nickname suchen (Task 3.2, FR-S2), nach Farbkombination suchen
(Task 3.3, FR-S3) und Freundschaften (Task 3.4, FR-S4).

Freundeslisten und Graph (3.5) kommen mit dem eigenen Task hinzu.
"""

from dataclasses import dataclass

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.models import Profile
from apps.colors import pentagon, selection
from apps.colors.models import Color

from . import friendships, profile_page
from .decorators import owner_only
from .models import Friendship


def _current_profile(request):
    """Wie `apps.accounts.views.profile`: `get_object_or_404` statt
    `request.user.profile` direkt, damit ein per `createsuperuser`
    angelegter Account ohne Profil eine klare 404 statt eines
    Serverfehlers auslöst."""
    return get_object_or_404(Profile, user=request.user)


@login_required
@require_GET
def profile_detail(request, nickname):
    """
    FR-S1: Nickname, Profilbild, Bio, Farben — **nicht** Testhistorie,
    **nicht** E-Mail. `nickname__iexact` passend zur Eindeutigkeit
    case-insensitiv (FR-P2, `Profile.Meta.constraints`).

    `login_required` genügt für "nur für eingeloggte Nutzende
    sichtbar" — die Zugangssperre (D-09) gilt davor ohnehin für jede
    URL, das hier ist die zusätzliche Login-Pflicht aus FR-S1.

    Seit Task 4.1 (FR-P9, D-73) ist das auch die Seite der eigenen
    Person: derselbe View, `is_owner` im Kontext schaltet die
    Bearbeiten-Zugänge und die privaten Bereiche ein
    (`profile_page.profile_context`). Der frühere Redirect des eigenen
    Profils auf `/accounts/profile/` entfällt — die Richtung ist jetzt
    umgekehrt.

    Seit Task 4.3 (FR-P11) ist das der Tab „Pinboard" (Standardtab);
    die Freundesliste steht im Tab „Friends" (`profile_friends`).
    Weiterhin je Profil: Freundschaftsstatus (FR-S4, Task 3.4) im Kopf
    und die Punkte des übernommenen Testergebnisses (D-70).
    """
    profile = get_object_or_404(Profile, nickname__iexact=nickname)
    viewer_profile = _current_profile(request)
    context = profile_page.profile_context(profile, viewer_profile)
    return render(request, "social/profile_detail.html", context)


@login_required
@require_GET
def profile_friends(request, nickname):
    """
    Tab „Friends" (Task 4.3, FR-P11, FR-S5, FR-S6): die Freundesliste
    **dieses** Profils, unabhängig von der Beziehung der ansehenden Person
    dazu (FR-S6: keine Einschränkung auf gemeinsame Freunde) — jeder
    Eintrag verlinkt wieder auf ein Profil, der Graph lässt sich beliebig
    weiterklicken (Task 3.5-DoD). Die eigene Person sieht hier zusätzlich
    ihre offenen Anfragen (FR-S4); bei fremden Profilen erscheinen die
    offenen Anfragen dieser Person nirgends.
    """
    profile = get_object_or_404(Profile, nickname__iexact=nickname)
    viewer_profile = _current_profile(request)
    context = profile_page.profile_context(profile, viewer_profile, tab=profile_page.FRIENDS)
    return render(request, "social/profile_friends.html", context)


@owner_only
@require_GET
def profile_history(request, profile):
    """
    Tab „Test history" (Task 4.4, FR-P6, FR-P7, D-19): nur für die eigene
    Person; jede andere Person wird von `owner_only` auf das öffentliche
    Profil weitergeleitet, bevor dieser View läuft.
    """
    context = profile_page.profile_context(profile, profile, tab=profile_page.HISTORY)
    return render(request, "social/profile_history.html", context)


@owner_only
@require_GET
def profile_settings(request, profile):
    """Tab „Settings" (Task 4.4): Passwort ändern und Account löschen, nur
    für die eigene Person (`owner_only`)."""
    context = profile_page.profile_context(profile, profile, tab=profile_page.SETTINGS)
    return render(request, "social/profile_settings.html", context)


@owner_only
@require_http_methods(["GET", "POST"])
def edit_profile_section(request, profile, section):
    """
    Nickname oder Bio einzeln bearbeiten (Task 4.5, FR-P12, D-73). Jeder
    Bereich hat sein eigenes Formular und speichert nur sich selbst; die
    Adresse ist nur für die eigene Person erreichbar (`owner_only`, jede
    andere wird weitergeleitet, auch bei POST).

    GET zeigt dieselbe Profilseite wie sonst, nur mit diesem einen Bereich
    im Bearbeiten-Modus — ohne JavaScript ist das die "eigene Seite" mit
    dem Formular, mit HTMX holt sich der Bereich per `hx-select` genau sein
    Stück daraus und tauscht es an Ort und Stelle (D-24). Erfolgreiches
    Speichern leitet auf das Profil weiter — bei geändertem Nickname auf
    die neue Adresse; Fehler (z. B. vergebener Nickname) erscheinen im
    Formular.
    """
    if request.method == "POST":
        form = profile_page.edit_form_for(section, profile, request.POST)
        if form.is_valid():
            form.save()
            return redirect(profile)
    else:
        form = profile_page.edit_form_for(section, profile)

    context = profile_page.profile_context(profile, profile, editing=section, edit_form=form)
    return render(request, "social/profile_detail.html", context)


@login_required
@require_GET
def search(request):
    """
    FR-S2: Teilstring-Suche nach Nickname, Groß-/Kleinschreibung egal.
    `login_required` aus demselben Grund wie bei `profile_detail` —
    Profile anderer (und damit auch ihre Nicknames) sind FR-S1 zufolge
    nur für Angemeldete sichtbar, die Suche macht davon keine Ausnahme.

    Leere oder fehlende Suchanfrage liefert keine Treffer statt aller
    Profile — ein leeres Suchfeld soll nicht versehentlich jeden
    Nickname auflisten.
    """
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = Profile.objects.filter(nickname__icontains=query).order_by("nickname")

    context = {"query": query, "results": results}
    return render(request, "social/search.html", context)


@dataclass(frozen=True)
class ColorToggle:
    """
    Eine Fünfeck-Ecke als Auswahl-Link für die Farbsuche, analog zu
    `apps.colors.views.VertexLink` — eigene, kleine Klasse statt eines
    Imports von dort: die Suche braucht nur Vertex, Ziel-URL und
    Auswahlstatus, keine der übrigen Farb-Inhalte (Theme/Pole-Labels,
    Info-Box), die dort mit dranhängen (Task 3.3).
    """

    vertex: pentagon.Vertex
    toggle_url: str
    is_selected: bool


def _search_colors_url(url_code):
    """Die URL für eine (bereits kanonische) Auswahl-URL-Form, analog
    zu `apps.colors.views._url_for`."""
    if not url_code:
        return reverse("social:search_colors")
    return reverse("social:search_colors_combination", kwargs={"code": url_code})


def _color_pentagon_context(selected_colors):
    """
    Kontext für `social/_color_pentagon.html`. Nutzt dieselbe Geometrie
    wie das Fünfeck aus `apps.colors` (`pentagon.vertices()`,
    `pentagon.outline_points()`/`star_points()`/`view_box()`) — Task
    3.3s DoD verlangt ausdrücklich dieselbe Darstellung. Anders als
    `apps.colors.views.pentagon_context()` ohne Theme-/Pole-Labels: die
    Suche zeigt keine Kombinations-Inhalte, nur die Auswahl selbst.
    """
    vertices = pentagon.vertices(Color.objects.all())
    vertex_links = [
        ColorToggle(
            vertex=vertex,
            toggle_url=_search_colors_url(
                selection.canonical_url_code(selection.toggled(selected_colors, vertex.code))
            ),
            is_selected=vertex.code in selected_colors,
        )
        for vertex in vertices
    ]
    return {
        "vertex_links": vertex_links,
        "outline_points": pentagon.outline_points(vertices),
        "star_points": pentagon.star_points(vertices),
        "view_box": pentagon.view_box(vertices),
        "name_size": pentagon.NAME_SIZE,
        "has_selection": bool(selected_colors),
        "reset_url": reverse("social:search_colors"),
    }


def _profiles_with_all_colors(selected_colors):
    """
    FR-S3/D-21: alle Profile, deren Farben die gesuchte Kombination
    **enthalten** — eine Kette von Buchstaben-Prüfungen auf
    `ColorCombination.code` (ARCHITECTURE.md §6.2). Alle Bedingungen
    in einem einzigen `filter()`-Aufruf verknüpft, statt ihn je
    Buchstabe erneut aufzurufen: so muss derselbe zugeordnete
    Kombinations-Datensatz alle Buchstaben tragen, nicht nur
    irgendeine Zeile der Relation.
    """
    conditions = Q()
    for color in selected_colors:
        conditions &= Q(color_assignments__combination__code__contains=color)
    return Profile.objects.filter(conditions).distinct().order_by("nickname")


@login_required
@require_GET
def search_by_colors(request, code=""):
    """
    FR-S3: Suche nach Farbkombination. Selektion und URL-Form
    (kanonisch, kleingeschrieben, Redirect bei falscher Schreibweise,
    404 bei ungültigem Code) laufen exakt wie beim Fünfeck selbst
    (Task 1.6) über `apps.colors.selection` — dieselben reinen
    Funktionen, keine zweite Auswahl-Logik im System.

    Wie `profile_detail`/`search`: `login_required` zusätzlich zur
    Zugangssperre (D-09), weil Profile anderer FR-S1 zufolge nur für
    Angemeldete sichtbar sind.
    """
    if code:
        selected_colors = selection.parse_url_code(code)
        if selected_colors is None:
            raise Http404("Not a valid color combination.")

        canonical = selection.canonical_url_code(selected_colors)
        if code != canonical:
            return redirect(_search_colors_url(canonical), permanent=True)
    else:
        selected_colors = set()

    context = _color_pentagon_context(selected_colors)
    context["results"] = _profiles_with_all_colors(selected_colors) if selected_colors else []
    return render(request, "social/search_colors.html", context)


@login_required
@require_POST
def send_friend_request(request, nickname):
    """
    FR-S4: Anfrage senden — vom fremden Profil aus (`/u/<nickname>/`).
    Eine bereits bestehende Anfrage/Freundschaft (`friendships.send_request`
    wirft dafür eine `ValidationError`) wird stillschweigend
    übergangen: der reguläre UI-Pfad zeigt den "Anfrage senden"-Knopf
    ohnehin nur, wenn noch keine Beziehung besteht (Roadmap-Test:
    "Anfrage kann nicht doppelt gestellt werden" prüft nur, dass keine
    zweite Zeile entsteht, nicht eine bestimmte Fehlerdarstellung).
    """
    target = get_object_or_404(Profile, nickname__iexact=nickname)
    requester = _current_profile(request)
    try:
        friendships.send_request(requester, target)
    except ValidationError:
        pass
    return redirect("social:profile_detail", nickname=target.nickname)


def _redirect_to_other(friendship, acting_profile):
    other = friendship.other_profile(acting_profile)
    return redirect("social:profile_detail", nickname=other.nickname)


@login_required
@require_POST
def accept_friend_request(request, pk):
    """
    FR-S4: Anfrage annehmen. `friendships.accept_request` wirft
    `PermissionDenied`, wenn eine unbeteiligte Person oder die
    anfragende Person selbst annimmt — Django beantwortet das
    serienmäßig mit 403 (Roadmap-Test: "nicht von Dritten angenommen
    werden").
    """
    friendship = get_object_or_404(Friendship, pk=pk)
    acting_profile = _current_profile(request)
    try:
        friendships.accept_request(friendship, acting_profile)
    except ValidationError:
        pass
    return _redirect_to_other(friendship, acting_profile)


@login_required
@require_POST
def decline_friend_request(request, pk):
    """FR-S4: Anfrage ablehnen — durch die Empfängerin oder, als
    Rückzug der eigenen Anfrage, durch die anfragende Person selbst."""
    friendship = get_object_or_404(Friendship, pk=pk)
    acting_profile = _current_profile(request)
    other = friendship.other_profile(acting_profile)
    try:
        friendships.decline_request(friendship, acting_profile)
    except ValidationError:
        pass
    return redirect("social:profile_detail", nickname=other.nickname)


@login_required
@require_POST
def remove_friendship(request, pk):
    """FR-S4: bestehende Freundschaft auflösen — durch jede der beiden
    Seiten."""
    friendship = get_object_or_404(Friendship, pk=pk)
    acting_profile = _current_profile(request)
    other = friendship.other_profile(acting_profile)
    try:
        friendships.dissolve(friendship, acting_profile)
    except ValidationError:
        pass
    return redirect("social:profile_detail", nickname=other.nickname)

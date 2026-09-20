"""
Decorator für „nur die Autorin bzw. der Autor"-Seiten eines Beitrags
(Task 5.3, FR-B4, D-78) — wie `apps.social.decorators.owner_only` für private
Profil-Adressen, hier mit dem Beitrag statt dem Profil als Schlüssel.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.accounts.models import Profile

from .models import Post


def current_profile(request):
    """Das Profil der angemeldeten Person; ein Account ohne Profil (z. B. ein per
    `createsuperuser` angelegter Admin) bekommt 404 statt eines Serverfehlers."""
    return get_object_or_404(Profile, user=request.user)


def author_only(view):
    """
    Umhüllt einen View `view(request, post, profile, ...)`, der unter einer
    Adresse mit `<pk>` hängt. Reihenfolge: Gäste zum Login, unbekannter oder
    nicht sichtbarer Beitrag 404 (`visible_to`, die einzige Lesestelle),
    jede **andere** Person 302 auf die Beitragsseite — ohne etwas zu ändern,
    auch bei POST. Nur die Autorin bzw. der Autor erreicht den View.
    """

    @wraps(view)
    @login_required
    def wrapper(request, pk, *args, **kwargs):
        profile = current_profile(request)
        post = get_object_or_404(Post.objects.visible_to(profile).select_related("author"), pk=pk)
        if post.author_id != profile.pk:
            return redirect("posts:detail", pk=post.pk)
        return view(request, post, profile, *args, **kwargs)

    return wrapper

"""Fixtures, die mehrere Test-Dateien in apps/posts/tests/ teilen."""

import pytest

from apps.accounts.models import Profile, User


@pytest.fixture
def make_profile(db):
    """Legt ein Profil samt Account an; jeder Aufruf mit eigenem Nickname."""

    def make(nickname):
        user = User.objects.create_user(
            email=f"{nickname}@example.com", password="a-long-enough-password"
        )
        return Profile.objects.create(user=user, nickname=nickname)

    return make


@pytest.fixture
def author(make_profile):
    return make_profile("alex")

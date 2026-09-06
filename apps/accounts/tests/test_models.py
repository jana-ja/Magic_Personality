"""
Tests für das eigene User-Modell (Task 0.2).

Deckt genau die Punkte aus der Definition of Done in docs/ROADMAP.md ab:
E-Mail als Anmeldefeld, kein username, eindeutige E-Mail, Argon2 als
aktiver Hasher, funktionierender create_superuser.
"""

import pytest
from django.db import IntegrityError
from django.db.utils import DataError

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_email_is_the_username_field():
    assert User.USERNAME_FIELD == "email"
    assert User.REQUIRED_FIELDS == []


def test_user_has_no_username_field():
    field_names = {field.name for field in User._meta.get_fields()}
    assert "username" not in field_names


def test_create_user_requires_an_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password="a-long-enough-password")


def test_email_addresses_are_unique():
    User.objects.create_user(email="alex@example.com", password="a-long-enough-password")

    with pytest.raises((IntegrityError, DataError)):
        User.objects.create_user(email="alex@example.com", password="a-different-password")


def test_create_user_hashes_the_password_with_argon2():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")

    # Argon2-kodierte Hashes beginnen mit diesem Präfix (Django-Konvention,
    # siehe PASSWORD_HASHERS in config/settings/base.py).
    assert user.password.startswith("argon2$")
    assert user.check_password("a-long-enough-password")


def test_create_user_defaults_to_a_non_staff_non_superuser_account():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")

    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_active is True


def test_create_superuser_sets_staff_and_superuser_flags():
    user = User.objects.create_superuser(
        email="admin@example.com", password="a-long-enough-password"
    )

    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True


@pytest.mark.parametrize("field,value", [("is_staff", False), ("is_superuser", False)])
def test_create_superuser_rejects_conflicting_flags(field, value):
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin@example.com",
            password="a-long-enough-password",
            **{field: value},
        )


def test_string_representation_is_the_email_address():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")

    assert str(user) == "alex@example.com"

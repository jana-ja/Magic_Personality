"""
Tests für das Django-Admin (D-71): jede registrierte Modell-Liste und
die Formulare des angepassten User-Admins laden ohne Fehler, und ohne
`is_staff` kommt niemand hinein.
"""

import pytest
from django.contrib import admin
from django.urls import reverse

from apps.accounts.models import Profile, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def superuser(db):
    user = User.objects.create_superuser(email="root@example.com", password="a-long-enough-pw")
    Profile.objects.create(user=user, nickname="root")
    return user


def _registered_models():
    return [
        model
        for model in admin.site._registry
        if model._meta.app_label in {"accounts", "colors", "quiz", "social", "core"}
    ]


@pytest.mark.parametrize("model", _registered_models(), ids=lambda m: m._meta.label)
def test_changelist_loads(gated_client, superuser, model):
    gated_client.force_login(superuser)

    response = gated_client.get(
        reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist")
    )

    assert response.status_code == 200


def test_all_project_models_are_registered():
    from django.apps import apps

    project_models = {
        model
        for label in ("accounts", "colors", "quiz", "social", "core")
        for model in apps.get_app_config(label).get_models()
    }

    assert project_models == set(_registered_models())


def test_user_change_and_add_forms_load(gated_client, superuser):
    gated_client.force_login(superuser)

    assert gated_client.get(reverse("admin:accounts_user_add")).status_code == 200
    assert (
        gated_client.get(reverse("admin:accounts_user_change", args=[superuser.pk])).status_code
        == 200
    )


def test_a_normal_account_cannot_use_the_admin(gated_client):
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-pw")
    gated_client.force_login(user)

    response = gated_client.get(reverse("admin:index"))

    assert response.status_code == 302
    assert "/admin/login/" in response.url

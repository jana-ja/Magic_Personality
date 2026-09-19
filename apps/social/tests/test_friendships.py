"""
Tests für Freundschaften (Task 3.4, FR-S4, D-20, D-22).

Die beiden Fälle aus der Definition of Done in docs/ROADMAP.md stehen
wörtlich drin: eine Anfrage kann nicht doppelt gestellt und nicht von
Dritten angenommen werden.
"""

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Profile, User
from apps.social import friendships
from apps.social.models import Friendship

pytestmark = pytest.mark.django_db


@pytest.fixture
def alex():
    user = User.objects.create_user(email="alex@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="alex")


@pytest.fixture
def jamie():
    user = User.objects.create_user(email="jamie@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="jamie")


@pytest.fixture
def taylor():
    user = User.objects.create_user(email="taylor@example.com", password="a-long-enough-password")
    return Profile.objects.create(user=user, nickname="taylor")


# Modell-Constraints -----------------------------------------------------


def test_cannot_create_a_friendship_with_oneself(alex):
    with pytest.raises(IntegrityError):
        Friendship.objects.create(profile_a=alex, profile_b=alex, requested_by=alex)


def test_cannot_create_the_reversed_pair_once_one_exists(alex, jamie):
    low, high = sorted([alex, jamie], key=lambda p: p.pk)
    Friendship.objects.create(profile_a=low, profile_b=high, requested_by=alex)

    with pytest.raises(IntegrityError), transaction.atomic():
        Friendship.objects.create(profile_a=high, profile_b=low, requested_by=jamie)


def test_requested_by_must_be_a_participant(alex, jamie, taylor):
    low, high = sorted([alex, jamie], key=lambda p: p.pk)

    with pytest.raises(IntegrityError):
        Friendship.objects.create(profile_a=low, profile_b=high, requested_by=taylor)


# apps.social.friendships -------------------------------------------------


def test_send_request_creates_a_pending_friendship(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    assert friendship.status == Friendship.Status.PENDING
    assert friendship.requested_by == alex
    assert friendship.involves(alex)
    assert friendship.involves(jamie)


def test_send_request_to_oneself_is_rejected(alex):
    with pytest.raises(ValidationError):
        friendships.send_request(alex, alex)


def test_send_request_twice_does_not_create_a_second_row(alex, jamie):
    """Aus der DoD wörtlich: Anfrage kann nicht doppelt gestellt werden."""

    friendships.send_request(alex, jamie)

    with pytest.raises(ValidationError):
        friendships.send_request(alex, jamie)

    assert Friendship.objects.count() == 1


def test_the_other_side_can_also_not_send_a_second_request(alex, jamie):
    """Dieselbe Regel gilt auch für die umgekehrte Richtung."""

    friendships.send_request(alex, jamie)

    with pytest.raises(ValidationError):
        friendships.send_request(jamie, alex)

    assert Friendship.objects.count() == 1


def test_recipient_can_accept(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    friendships.accept_request(friendship, jamie)

    friendship.refresh_from_db()
    assert friendship.status == Friendship.Status.ACCEPTED


def test_requester_cannot_accept_their_own_request(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    with pytest.raises(PermissionDenied):
        friendships.accept_request(friendship, alex)

    friendship.refresh_from_db()
    assert friendship.status == Friendship.Status.PENDING


def test_a_third_party_cannot_accept_a_request(alex, jamie, taylor):
    """Aus der DoD wörtlich: nicht von Dritten angenommen werden."""

    friendship = friendships.send_request(alex, jamie)

    with pytest.raises(PermissionDenied):
        friendships.accept_request(friendship, taylor)

    friendship.refresh_from_db()
    assert friendship.status == Friendship.Status.PENDING


def test_recipient_can_decline(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    friendships.decline_request(friendship, jamie)

    assert not Friendship.objects.filter(pk=friendship.pk).exists()


def test_requester_can_withdraw_their_own_request(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    friendships.decline_request(friendship, alex)

    assert not Friendship.objects.filter(pk=friendship.pk).exists()


def test_a_third_party_cannot_decline_a_request(alex, jamie, taylor):
    friendship = friendships.send_request(alex, jamie)

    with pytest.raises(PermissionDenied):
        friendships.decline_request(friendship, taylor)

    assert Friendship.objects.filter(pk=friendship.pk).exists()


def test_either_side_can_dissolve_an_accepted_friendship(alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    friendships.accept_request(friendship, jamie)

    friendships.dissolve(friendship, alex)

    assert not Friendship.objects.filter(pk=friendship.pk).exists()


def test_a_third_party_cannot_dissolve_a_friendship(alex, jamie, taylor):
    friendship = friendships.send_request(alex, jamie)
    friendships.accept_request(friendship, jamie)

    with pytest.raises(PermissionDenied):
        friendships.dissolve(friendship, taylor)

    assert Friendship.objects.filter(pk=friendship.pk).exists()


def test_pending_request_cannot_be_dissolved(alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    with pytest.raises(ValidationError):
        friendships.dissolve(friendship, alex)


# Views --------------------------------------------------------------------


def test_sending_a_request_requires_login(gated_client, jamie):
    response = gated_client.post("/u/jamie/friend-request/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_send_request_view_creates_a_pending_friendship(gated_client, alex, jamie):
    gated_client.force_login(alex.user)

    response = gated_client.post("/u/jamie/friend-request/")

    assert response.status_code == 302
    friendship = Friendship.objects.get()
    assert friendship.status == Friendship.Status.PENDING
    assert friendship.requested_by == alex


def test_send_request_view_twice_does_not_create_a_second_row(gated_client, alex, jamie):
    gated_client.force_login(alex.user)
    gated_client.post("/u/jamie/friend-request/")

    response = gated_client.post("/u/jamie/friend-request/")

    assert response.status_code == 302
    assert Friendship.objects.count() == 1


def test_accept_request_view_requires_login(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)

    response = gated_client.post(f"/friends/{friendship.pk}/accept/")

    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_recipient_can_accept_via_view(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    gated_client.force_login(jamie.user)

    response = gated_client.post(f"/friends/{friendship.pk}/accept/")

    assert response.status_code == 302
    friendship.refresh_from_db()
    assert friendship.status == Friendship.Status.ACCEPTED


def test_third_party_cannot_accept_via_view(gated_client, alex, jamie, taylor):
    """Aus der DoD wörtlich: nicht von Dritten angenommen werden."""
    friendship = friendships.send_request(alex, jamie)
    gated_client.force_login(taylor.user)

    response = gated_client.post(f"/friends/{friendship.pk}/accept/")

    assert response.status_code == 403
    friendship.refresh_from_db()
    assert friendship.status == Friendship.Status.PENDING


def test_recipient_can_decline_via_view(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    gated_client.force_login(jamie.user)

    response = gated_client.post(f"/friends/{friendship.pk}/decline/")

    assert response.status_code == 302
    assert not Friendship.objects.filter(pk=friendship.pk).exists()


def test_remove_friendship_view(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    friendships.accept_request(friendship, jamie)
    gated_client.force_login(alex.user)

    response = gated_client.post(f"/friends/{friendship.pk}/remove/")

    assert response.status_code == 302
    assert not Friendship.objects.filter(pk=friendship.pk).exists()


# Sichtbarkeit im eigenen Profil (Task 3.4-DoD) -----------------------------


def test_pending_requests_are_visible_on_the_recipients_own_profile(gated_client, alex, jamie):
    friendships.send_request(alex, jamie)
    gated_client.force_login(jamie.user)

    response = gated_client.get("/u/jamie/")

    html = response.content.decode()
    assert 'href="/u/alex/"' in html


def test_pending_requests_are_visible_on_the_senders_own_profile(gated_client, alex, jamie):
    friendships.send_request(alex, jamie)
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/alex/")

    html = response.content.decode()
    assert 'href="/u/jamie/"' in html


def test_accepted_friendship_is_not_listed_as_an_open_request(gated_client, alex, jamie):
    friendship = friendships.send_request(alex, jamie)
    friendships.accept_request(friendship, jamie)
    gated_client.force_login(alex.user)

    response = gated_client.get("/u/alex/")

    html = response.content.decode()
    assert "No open friend requests." in html

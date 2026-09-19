from django.urls import path

from . import views

app_name = "social"

urlpatterns = [
    path("search/", views.search, name="search"),
    # Wie apps/colors/urls.py: <str:code> verlangt mindestens ein
    # Zeichen, deshalb ein eigenes Pattern für die leere Auswahl.
    path("search/colors/", views.search_by_colors, name="search_colors"),
    path("search/colors/<str:code>/", views.search_by_colors, name="search_colors_combination"),
    path("u/<str:nickname>/", views.profile_detail, name="profile_detail"),
    path("u/<str:nickname>/friends/", views.profile_friends, name="profile_friends"),
    path("u/<str:nickname>/friend-request/", views.send_friend_request, name="send_friend_request"),
    path("friends/<int:pk>/accept/", views.accept_friend_request, name="accept_friend_request"),
    path("friends/<int:pk>/decline/", views.decline_friend_request, name="decline_friend_request"),
    path("friends/<int:pk>/remove/", views.remove_friendship, name="remove_friendship"),
]

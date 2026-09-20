from django.urls import path

from . import views

app_name = "colors"

urlpatterns = [
    path("colors/", views.index, name="index"),
    # <str:code> verlangt mindestens ein Zeichen, deshalb ein eigenes
    # Pattern statt eines optionalen Parameters am obigen (Task 1.6).
    path("colors/<str:code>/", views.index, name="combination"),
    path("colors/<str:code>/posts/", views.combination_posts, name="posts"),
]

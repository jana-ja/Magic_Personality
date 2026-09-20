from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("posts/new/", views.new_post, name="new"),
    path("posts/<int:pk>/", views.post_detail, name="detail"),
    path("posts/<int:pk>/edit/", views.edit_post, name="edit"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete"),
]

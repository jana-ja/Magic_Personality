from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("posts/new/", views.new_post, name="new"),
    path("posts/<int:pk>/", views.post_detail, name="detail"),
    path("posts/<int:pk>/edit/", views.edit_post, name="edit"),
    path("posts/<int:pk>/delete/", views.delete_post, name="delete"),
    path("posts/<int:pk>/report/", views.report_post, name="report"),
    path("posts/<int:pk>/report/thanks/", views.report_thanks, name="report_thanks"),
    path("posts/<int:pk>/comment/", views.add_comment, name="comment"),
    path(
        "posts/<int:post_pk>/comments/<int:pk>/delete/",
        views.delete_comment,
        name="comment_delete",
    ),
    path(
        "posts/<int:post_pk>/comments/<int:pk>/report/",
        views.report_comment,
        name="comment_report",
    ),
    path(
        "posts/<int:post_pk>/comments/<int:pk>/report/thanks/",
        views.comment_report_thanks,
        name="comment_report_thanks",
    ),
]

from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("quiz/", views.take_test, name="take_test"),
]

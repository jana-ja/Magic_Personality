from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("quiz/", views.take_test, name="take_test"),
    path("quiz/results/<int:pk>/adopt/", views.adopt_result, name="adopt_result"),
    path("quiz/results/claim/", views.claim_anonymous_result, name="claim_anonymous_result"),
]

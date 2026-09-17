"""
URLs der Accounts-App (Task 2.2, Task 2.3).

Login/Logout/Passwortänderung nutzen Djangos eigene View-Klassen direkt
— nur Templates und Redirect-Ziele sind projektspezifisch. Bewusst
**nicht** eingebunden: Djangos Passwort-Reset-URLs (FR-U7, D-10) und
jede Form von E-Mail-Versand.
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change_form.html",
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path("delete/", views.delete_account, name="delete_account"),
]

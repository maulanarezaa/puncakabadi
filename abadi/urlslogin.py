# myapp/urls.py
from django.urls import path
from . import viewslogin

urlpatterns = [
    path("login/", viewslogin.login_view, name="login"),
    path("logout/", viewslogin.logout_view, name="logout"),
    path("register/", viewslogin.register_view, name="register"),
]

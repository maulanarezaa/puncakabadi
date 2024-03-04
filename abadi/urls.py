from django.urls import path
from . import views

urlpatterns = [
    path("artikel", views.views_artikel, name="views_artikel"),
    path("tambahdataartikel", views.tambahdataartikel, name="tambahdataartikel"),
    path("updateartikel/<str:id>", views.updatedataartikel, name="update_artikel"),
    path("deleteartikel/<str:id>", views.deleteartikel, name="delete_artikel"),
]

from django.urls import path
from . import views

urlpatterns = [
    path("artikel", views.views_artikel, name="views_artikel"),
    path("tambahdataartikel", views.tambahdataartikel, name="tambahdataartikel"),
    path("updateartikel/<str:id>", views.updatedataartikel, name="update_artikel"),
    path("deleteartikel/<str:id>", views.deleteartikel, name="delete_artikel"),
    path("penyusunartikel", views.views_penyusun, name="penyusun_artikel"),
    path(
        "tambahdatapenyusun/<str:id>",
        views.tambahdatapenyusun,
        name="tambah_data_penyusun",
    ),
    path("konversi", views.konversi, name="konversi"),
    path(
        "Updatekonversi/<str:id>",
        views.konversimaster_update,
        name="update_data_konversi_master",
    ),
    path(
        "Deletekonversi/<str:id>",
        views.konversimaster_delete,
        name="delete_data_konversi_master",
    ),
]

from django.urls import path
from . import views

urlpatterns = [
    path("artikel", views.views_artikel, name="views_artikel"),
    path("tambahdataartikel", views.tambahdataartikel, name="tambahdataartikel"),
    path("updateartikel/<str:id>", views.updatedataartikel, name="update_artikel"),
    path("deleteartikel/<str:id>", views.deleteartikel, name="delete_artikel"),

    path("penyusunartikel", views.views_penyusun, name="penyusun_artikel"),
    path("tambahdatapenyusun/<str:id>",views.tambahdatapenyusun,name="tambah_data_penyusun"),
    
    path("konversi", views.konversi, name="konversi"),
    path("updatekonversi/<str:id>",views.konversimaster_update,name="update_data_konversi_master"),
    path("deletekonversi/<str:id>",views.konversimaster_delete,name="delete_data_konversi_master"),

    path("viewspk", views.view_spk, name="view_spk"),
    path("addspk", views.add_spk, name="add_spk"),
    path("updatespk/<str:id>", views.update_spk, name="update_spk"),
    path("deletespk/<str:id>", views.delete_spk, name="delete_spk"),

    path("viewsppb", views.view_sppb, name="view_sppb"),
    path("addsppb", views.add_sppb, name="add_sppb"),
    path("updatesppb/<str:id>", views.update_sppb, name="update_sppb"),
    path("deletesppb/<str:id>", views.delete_sppb, name="delete_sppb"),

    path("viewproduksi", views.view_produksi, name="view_produksi"),
    path("addproduksi", views.add_produksi, name="add_produksi"),
    path("updateproduksi/<str:id>", views.update_produksi, name="update_produksi"),
    path("deleteproduksi/<str:id>", views.delete_produksi, name="delete_produksi"),
]

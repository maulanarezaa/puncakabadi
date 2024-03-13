from django.urls import path
from . import views

urlpatterns = [
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

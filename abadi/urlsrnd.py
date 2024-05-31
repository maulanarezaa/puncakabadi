from django.urls import path
from . import viewsrnd
from .viewsproduksi import views_ksbj

urlpatterns = [
    path("", viewsrnd.dashboard, name="dashboardrnd"),
    path("artikel", viewsrnd.views_artikel, name="views_artikel"),
    path("artikel/tambah", viewsrnd.tambahdataartikel, name="tambahdataartikel"),
    path("artikel/update/<str:id>", viewsrnd.updatedataartikel, name="update_artikel"),
    path("artikel/delete/<str:id>", viewsrnd.deleteartikel, name="delete_artikel"),
    path("penyusun", viewsrnd.views_penyusun, name="penyusun_artikel"),
    path(
        "penyusun/tambah/<str:id>/<str:versi>",
        viewsrnd.tambahdatapenyusun,
        name="tambah_data_penyusun",
    ),
    path("penyusun/versi/tambah/<str:id>", viewsrnd.tambahversi, name="add_versi"),
    path("penyusun/update/<str:id>", viewsrnd.updatepenyusun, name="update_penyusun"),
    path("penyusun/delete/<str:id>", viewsrnd.delete_penyusun, name="delete_penyusun"),
    path("ksbj", viewsrnd.views_ksbj, name="views_ksbj"),
    path("sppb", viewsrnd.views_sppb, name="views_sppb"),
    path("spk", viewsrnd.view_spk, name="views_spk"),
    path("rekapharga", viewsrnd.views_rekapharga, name="rekaphargarnd"),
    path("upload-excel", viewsrnd.uploadexcel, name="upload-excel"),
    path("read_bahanbaku", viewsrnd.read_produk, name="read_bahanbaku_rnd"),
    path("trackingspk/<str:id>", viewsrnd.track_spk, name="trackingspkrnd"),
]

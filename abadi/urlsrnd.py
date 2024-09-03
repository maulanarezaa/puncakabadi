from django.urls import path
from . import viewsrnd

urlpatterns = [
    path("dashboard", viewsrnd.dashboard, name="dashboardrnd"),
    path("artikel", viewsrnd.views_artikel, name="views_artikel"),
    path("artikel/tambah", viewsrnd.tambahdataartikel, name="tambahdataartikel"),
    path("artikel/update/<str:id>", viewsrnd.updatedataartikel, name="update_artikel"),
    path("artikel/delete/<str:id>", viewsrnd.deleteartikel, name="delete_artikel"),
    path("display", viewsrnd.views_display, name="views_display"),
    path("display/tambah", viewsrnd.tambahdatadisplay, name="tambahdatadisplay"),
    path("display/update/<str:id>", viewsrnd.updatedatadisplay, name="update_display"),
    path("display/delete/<str:id>", viewsrnd.deletedisplay, name="delete_display"),
    path("penyusun", viewsrnd.views_penyusun, name="penyusun_artikel"),
    path(
        "penyusun/tambah/<str:id>/<str:versi>",
        viewsrnd.tambahdatapenyusun,
        name="tambah_data_penyusun",
    ),
    path("penyusun/versi/tambah/<str:id>", viewsrnd.tambahversi, name="add_versi"),
    path("penyusun/add/versi/<str:id>", viewsrnd.tambahversibaru, name="add_versibaru"),
    path("penyusun/update/<str:id>", viewsrnd.updatepenyusun, name="update_penyusun"),
    path("penyusun/delete/<str:id>", viewsrnd.delete_penyusun, name="delete_penyusun"),
    path("hargafg", viewsrnd.views_harga, name="views_harga"),
    path("harga/tambah", viewsrnd.tambahdataharga, name="tambahdataharga"),
    path("harga/update/<str:id>", viewsrnd.updatedataharga, name="update_harga"),
    path("harga/delete/<str:id>", viewsrnd.deleteharga, name="delete_harga"),
    path("ksbj", viewsrnd.views_ksbj, name="view_ksbjrnd"),
    path("sppb", viewsrnd.views_sppb, name="views_sppbrnd"),
    path("spk", viewsrnd.view_spk, name="views_spkrnd"),
    path("rekapharga", viewsrnd.views_rekapharga, name="rekaphargarnd"),
    path("upload-excel", viewsrnd.uploadexcel, name="upload-excel"),
    path("read_bahanbaku", viewsrnd.read_produk, name="read_bahanbaku_rnd"),
    path("trackingspk/<str:id>", viewsrnd.track_spk, name="trackingspkrnd"),
    path(
        "updatebahanbaku/<str:id>", viewsrnd.update_produk_rnd, name="update_produk_rnd"
    ),
    path("bulk_addartikel", viewsrnd.bulk_createartikel),
    path("bulk_addpenyusun", viewsrnd.bulk_createpenyusun),
]

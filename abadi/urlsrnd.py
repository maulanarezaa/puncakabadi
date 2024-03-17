from django.urls import path
from . import viewsrnd

urlpatterns = [
    path('dashboard',viewsrnd.dashboard,name='dashboardrnd'),
      path("artikel", viewsrnd.views_artikel, name="views_artikel"),
    path("artikel/tambah", viewsrnd.tambahdataartikel, name="tambahdataartikel"),
    path("artikel/update/<str:id>", viewsrnd.updatedataartikel, name="update_artikel"),
    path("artikel/delete/<str:id>", viewsrnd.deleteartikel, name="delete_artikel"),
    path("penyusun", viewsrnd.views_penyusun, name="penyusun_artikel"),
    path(
        "penyusun/tambah/<str:id>",
        viewsrnd.tambahdatapenyusun,
        name="tambah_data_penyusun",
    ),
    path("penyusun/update/<str:id>", viewsrnd.updatepenyusun, name="update_penyusun"),
    path('sppb',viewsrnd.views_sppb,name='views_sppb'),
    path('ksbj',viewsrnd.views_ksbj,name='views_ksbj')
]
from django.urls import path
from . import viewsppic

urlpatterns = [
    path("", viewsppic.dashboard, name="dashboardppic"),
    path("laporanstokfg", viewsppic.laporanbarangjadi, name="laporanstokfg"),
    path("laporanbarangmasuk", viewsppic.laporanbarangmasuk, name="laporanbarangmasuk"),
    path(
        "laporanbarangmasukexcel",
        viewsppic.excel_laporanbarangmasuk,
        name="laporanbarangmasukexcel",
    ),
    path(
        "laporanbarangkeluar", viewsppic.laporanbarangkeluar, name="laporanbarangkeluar"
    ),
    path(
        "laporanpersediaanbarang",
        viewsppic.laporanpersediaanbarang,
        name="laporanpersediaanbarang",
    ),
    path(
        "confirmationorder", viewsppic.viewconfirmationorder, name="confirmationorder"
    ),
    path("addco", viewsppic.tambahconfirmationorder, name="addco"),
    path("detailco/<str:id>", viewsppic.detailco, name="detaico"),
    path("updateco/<str:id>", viewsppic.updateco, name="updateco"),
    path("deleteco/<str:id>", viewsppic.deleteco, name="deleteco"),
    path("deletedetailco/<str:id>", viewsppic.deletedetailco, name="deletedetailco"),
    path(
        "laporanpersediaanbarang2",
        viewsppic.newlaporanpersediaan,
        name="laporanperseidaanbarang2",
    ),
    # path("delete/<str:id>", viewsppic.updateco, name="updateco"),
]

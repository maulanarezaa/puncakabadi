from django.urls import path
from . import viewsproduksi

urlpatterns = [
    path("dashboard", viewsproduksi.dashboard, name="dashboard"),
    path("load_detailspk/", viewsproduksi.load_detailspk, name="load_detailspk"),
    path("load_artikel/", viewsproduksi.load_artikel, name="load_artikel"),
    path("load_htmx/", viewsproduksi.load_htmx, name="load_htmx"),
    path("load_penyusun", viewsproduksi.load_penyusun, name="load_penyusun"),
    path("viewspk", viewsproduksi.view_spk, name="view_spk"),
    path("addspk", viewsproduksi.add_spk, name="add_spk"),
    path("detailspk/<str:id>", viewsproduksi.detail_spk, name="detail_spk"),
    path("deletespk/<str:id>", viewsproduksi.delete_spk, name="delete_spk"),
    path(
        "detailspk/deletedetailspk/<str:id>",
        viewsproduksi.delete_detailspk,
        name="delete_detailspk",
    ),
    path("trackingspk/<str:id>", viewsproduksi.track_spk, name="tracking_spk"),
    path("viewsppb", viewsproduksi.view_sppb, name="view_sppb"),
    path("addsppb", viewsproduksi.add_sppb, name="add_sppb"),
    path("detailsppb/<str:id>", viewsproduksi.detail_sppb, name="detail_sppb"),
    path("deletesppb/<str:id>", viewsproduksi.delete_sppb, name="delete_sppb"),
    path(
        "detailsppb/deletedetailsppb/<str:id>",
        viewsproduksi.delete_detailsppb,
        name="delete_detailsppb",
    ),
    path("viewproduksi", viewsproduksi.view_produksi, name="view_produksi"),
    path("addproduksi", viewsproduksi.add_produksi, name="add_produksi"),
    path(
        "updateproduksi/<str:id>", viewsproduksi.update_produksi, name="update_produksi"
    ),
    path(
        "deleteproduksi/<str:id>", viewsproduksi.delete_produksi, name="delete_produksi"
    ),
    path("viewmutasi", viewsproduksi.view_mutasi, name="view_mutasi"),
    path("addmutasi", viewsproduksi.add_mutasi, name="add_mutasi"),
    path("updatemutasi/<str:id>", viewsproduksi.update_mutasi, name="update_mutasi"),
    path("deletemutasi/<str:id>", viewsproduksi.delete_mutasi, name="delete_mutasi"),
    path("viewgudang", viewsproduksi.view_gudang, name="view_gudang"),
    path("addgudang", viewsproduksi.add_gudang, name="add_gudang"),
    path("updategudang/<str:id>", viewsproduksi.update_gudang, name="update_gudang"),
    path("deletegudang/<str:id>", viewsproduksi.delete_gudang, name="delete_gudang"),
    path("viewgudangretur", viewsproduksi.view_gudangretur, name="view_gudangretur"),
    path("addgudangretur", viewsproduksi.add_gudangretur, name="add_gudangretur"),
    path(
        "updategudangretur/<str:id>",
        viewsproduksi.update_gudangretur,
        name="update_gudangretur",
    ),
    path(
        "deletegudangretur/<str:id>",
        viewsproduksi.delete_gudangretur,
        name="delete_gudangretur",
    ),
    path("viewksbb", viewsproduksi.view_ksbb3, name="view_ksbb"),
    path(
        "viewksbb/<str:id>/<str:tanggal>", viewsproduksi.detailksbb, name="detail_ksbb"
    ),
    path("viewksbj", viewsproduksi.view_ksbj2, name="view_ksbj"),
    path("viewrekapbarang", viewsproduksi.view_rekapbarang, name="view_rekapbarang"),
    path(
        "viewrekapproduksi", viewsproduksi.view_rekapproduksi, name="view_rekapproduksi"
    ),
    path("viewrekaprusak", viewsproduksi.view_rekaprusak, name="view_rekaprusak"),
    path("viewpemusnahan", viewsproduksi.view_pemusnahan, name="view_pemusnahan"),
    path("addpemusnahan", viewsproduksi.add_pemusnahan, name="add_pemusnahan"),
    path(
        "updatepemusnahan/<str:id>",
        viewsproduksi.update_pemusnahan,
        name="update_pemusnahan",
    ),
    path(
        "deletepemusnahan/<str:id>",
        viewsproduksi.delete_pemusnahan,
        name="delete_pemusnahan",
    ),
    path(
        "viewpemusnahanbarang",
        viewsproduksi.view_pemusnahanbarang,
        name="view_pemusnahanbarang",
    ),
    path(
        "addpemusnahanbarang",
        viewsproduksi.add_pemusnahanbarang,
        name="add_pemusnahanbarang",
    ),
    path(
        "updatepemusnahanbarang/<str:id>",
        viewsproduksi.update_pemusnahanbarang,
        name="update_pemusnahanbarang",
    ),
    path(
        "deletepemusnahanbarang/<str:id>",
        viewsproduksi.delete_pemusnahanbarang,
        name="delete_pemusnahanbarang",
    ),
    path("produksubkon", viewsproduksi.read_produksubkon, name="read_produksubkon"),
    path(
        "addproduksubkon", viewsproduksi.create_produksubkon, name="create_produksubkon"
    ),
    path(
        "updateproduksubkon/<str:id>",
        viewsproduksi.update_produksubkon,
        name="update_produksubkon",
    ),
    path(
        "deleteproduksubkon/<str:id>",
        viewsproduksi.delete_produksubkon,
        name="delete_produksubkon",
    ),
    path("subkonkirim", viewsproduksi.view_subkonkirim, name="view_subkonkirim"),
    path("addsubkonkirim", viewsproduksi.add_subkonkirim, name="add_subkonkirim"),
    path(
        "updatesubkonkirim/<str:id>",
        viewsproduksi.update_subkonkirim,
        name="update_subkonkirim",
    ),
    path(
        "deletesubkonkirim/<str:id>",
        viewsproduksi.delete_subkonkirim,
        name="delete_subkonkirim",
    ),
    path(
        "subkonterima",
        viewsproduksi.transaksi_subkon_terima,
        name="transaksi_subkon_terima",
    ),
    path(
        "addtransaksisubkonterima",
        viewsproduksi.create_transaksi_subkon_terima,
        name="create_transaksi_subkon_terima",
    ),
    path(
        "updatetransaksisubkonterima/<str:id>",
        viewsproduksi.update_transaksi_subkon_terima,
        name="update_transaksi_subkon_terima",
    ),
    path(
        "deletetransaksisubkonterima/<str:id>",
        viewsproduksi.delete_transaksi_subkon_terima,
        name="delete_transaksi_subkon_terima",
    ),
    path("ksbbsubkon", viewsproduksi.view_ksbbsubkon, name="ksbbsubkon"),
    path("ksbjsubkon", viewsproduksi.view_ksbjsubkon, name="ksbjsubkon"),
    path("penyesuaian", viewsproduksi.penyesuaian, name="view_penyesuaian"),
    path("addpenyesuaian", viewsproduksi.addpenyesuaian, name="addpenyesuaian"),
    path(
        "deletepenyesuaian/<str:id>",
        viewsproduksi.delete_penyesuaian,
        name="delete_penyesuaian",
    ),
    path(
        "updatepenyesuaian/<str:id>",
        viewsproduksi.update_penyesuaian,
        name="update_penyesuaian",
    ),
    path(
        "kalkulatorpenyesuaian",
        viewsproduksi.kalkulatorpenyesuaian2,
        name="kalkulatorpenyesuaian",
    ),
    path(
        "kalkulatorpenyesuaian2",
        viewsproduksi.kalkulatorpenyesuaian2,
        name="kalkulatorpenyesuaian2",
    ),
    path("viewsaldobahan", viewsproduksi.view_saldobahan, name="view_saldobahan"),
    path("viewsaldoartikel", viewsproduksi.view_saldoartikel, name="view_saldoartikel"),
    path("viewsaldosubkon", viewsproduksi.view_saldosubkon, name="view_saldosubkon"),
    path("addsaldobahan", viewsproduksi.add_saldobahan, name="add_saldobahan"),
    path("addsaldoartikel", viewsproduksi.add_saldoartikel, name="add_saldoartikel"),
    path("addsaldosubkon", viewsproduksi.add_saldosubkon, name="add_saldosubkon"),
    path(
        "updatesaldobahan/<str:id>",
        viewsproduksi.update_saldobahan,
        name="update_saldobahan",
    ),
    path(
        "updatesaldoartikel/<str:id>",
        viewsproduksi.update_saldoartikel,
        name="update_saldoartikel",
    ),
    path(
        "updatesaldosubkon/<str:id>",
        viewsproduksi.update_saldosubkon,
        name="update_saldosubkon",
    ),
    path(
        "deletesaldobahan/<str:id>",
        viewsproduksi.delete_saldobahan,
        name="delete_saldobahan",
    ),
    path(
        "deletesaldoartikel/<str:id>",
        viewsproduksi.delete_saldoartikel,
        name="delete_saldoartikel",
    ),
    path(
        "deletesaldosubkon/<str:id>",
        viewsproduksi.delete_saldosubkon,
        name="delete_saldosubkon",
    ),
    path("readbahanbaku", viewsproduksi.read_bahanbaku, name="read_produk_produksi"),
    path(
        "updatebahanbaku/<str:id>",
        viewsproduksi.update_produk_produksi,
        name="update_produk_produksi",
    ),
]

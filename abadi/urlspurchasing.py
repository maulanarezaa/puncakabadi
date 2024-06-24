from django.urls import path
from . import viewspurchasing

urlpatterns = [
    # notif purchasing +spk
    path(
        "notif_purchasing",
        viewspurchasing.notif_barang_purchasing,
        name="notif_purchasing",
    ),
    path(
        "update_verif_purchasing/<str:id>",
        viewspurchasing.verifikasi_data,
        name="update_verif_purchasing",
    ),
    path("acc_spk/<str:id>", viewspurchasing.acc_notif_spk, name="acc_spk"),
    # R penyusun
    path("penyusun", viewspurchasing.views_penyusun, name="penyusun"),
    # CR kebutuhan barang
    path("kebutuhan_barang", viewspurchasing.kebutuhan_barang, name="kebutuhan_barang"),
    # path("kebutuhan_barang/",viewspurchasing.kebutuhan_barang,name="kebutuhan_barang"),
    # barang_masuk
    path("barang_masuk", viewspurchasing.barang_masuk, name="barang_masuk"),
    path("export_excel",viewspurchasing.exportbarang_excel, name="export_excel"),
    path(
        "update_barang_masuk/<str:id>",
        viewspurchasing.update_barang_masuk,
        name="update_barang_masuk",
    ),
    # rekap purchasing(gudang+produksi)
    path("rekap_purchasing", viewspurchasing.rekap_purchasing, name="rekap_purchasing"),
    path("rekapgudang2", viewspurchasing.rekap_gudang, name="rekapgudang2"),
    path(
        "viewrekapbarang2", viewspurchasing.view_rekapbarang, name="view_rekapbarang2"
    ),
    # CRUD PRODUK
    path("read_produk", viewspurchasing.read_produk, name="read_produk"),
    path("create_produk", viewspurchasing.create_produk, name="create_produk"),
    path("update_produk/<str:id>", viewspurchasing.update_produk, name="update_produk"),
    path("delete_produk/<str:id>", viewspurchasing.delete_produk, name="delete_produk"),
    # CRUD SPPB
    path("viewsppb2", viewspurchasing.view_sppb, name="view_sppb2"),
    path("addsppb2", viewspurchasing.add_sppb, name="add_sppb2"),
    path("detailsppb2/<str:id>", viewspurchasing.detail_sppb, name="detail_sppb2"),
    path("delete_sppb2/<str:id>", viewspurchasing.delete_sppb, name="delete_sppb2"),
    path(
        "delete_detailsppb2/<str:id>",
        viewspurchasing.delete_detailsppb,
        name="delete_detailsppb2",
    ),
    # R PO
    path("read_po", viewspurchasing.read_po, name="read_po"),
    path("update_po/<str:id>",viewspurchasing.update_po,name="update_po"),
    # R SPK
    path("read_spk", viewspurchasing.read_spk, name="read_spk"),
    path("trackspk/<str:id>", viewspurchasing.track_spk, name="trackspk"),
    # R REKAP HARGA
    path("rekap_harga", viewspurchasing.views_rekapharga, name="rekapharga"),
    path("acc_spk2/<str:id>", viewspurchasing.accspk2, name="acc_spk2"),
    path('upload_excel', viewspurchasing.bulk_createproduk, name='upload_excel'),
    # CRUD Purchasing
    # Saldo awal bb
    path('saldoawalbahanbaku',viewspurchasing.read_saldoawal,name="saldobahanbakupurchasing"),
    path("addsaldobahan", viewspurchasing.add_saldobahan, name="add_saldobahan"),
    path('updatesaldoawalbahanbaku/<str:id>',viewspurchasing.update_saldoawal,name="updatesaldobahanbakupurchasing"),
    path(
        "deletesaldobahan/<str:id>",
        viewspurchasing.delete_saldobahan,
        name="delete_saldobahan",
    ),
    # Saldo awal b.a
    path('saldoawalartikel',viewspurchasing.view_saldoartikel,name="saldoartikelpurchasing"),
    path('updatesaldoawalartikel/<str:id>',viewspurchasing.update_saldoartikel,name='updatesaldoartikelpurchasing'),
    path("addsaldoartikel", viewspurchasing.add_saldoartikel, name="add_saldoartikel"),
    path(
        "deletesaldoartikel/<str:id>",
        viewspurchasing.delete_saldoartikel,
        name="delete_saldoartikel",
    ),
    # Saldo awal b.sub
    path(
        "viewsaldobahansubkon",
        viewspurchasing.view_saldobahansubkon,
        name="view_saldobahansubkon",
    ),
     path(
        "addsaldobahansubkon",
        viewspurchasing.add_saldobahansubkon,
        name="add_saldobahansubkon",
    ),
    path(
        "updatesaldobahansubkon/<str:id>",
        viewspurchasing.update_saldobahansubkon,
        name="update_saldobahansubkon",
    ),
    path(
        "deletesaldobahansubkon/<str:id>",
        viewspurchasing.delete_saldobahansubkon,
        name="delete_saldobahansubkon",
    ),
    # Saldo produk subkon
    path("viewsaldosubkon", viewspurchasing.view_saldosubkon, name="view_saldosubkon"),
    path("addsaldosubkon", viewspurchasing.add_saldosubkon, name="add_saldosubkon"),
    path(
        "updatesaldosubkon/<str:id>",
        viewspurchasing.update_saldosubkon,
        name="update_saldosubkon",
    ),
    path(
        "deletesaldosubkon/<str:id>",
        viewspurchasing.delete_saldosubkon,
        name="delete_saldosubkon",
    ),
]

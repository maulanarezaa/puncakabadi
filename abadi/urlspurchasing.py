from django.urls import path
from . import viewspurchasing

urlpatterns = [
    # notif purchasing +spk
    path(
        "",
        viewspurchasing.notif_barang_purchasing,
        name="notif_purchasing",
    ),
    path(
        "update_verif_purchasing/<str:id>",
        viewspurchasing.verifikasi_data,
        name="update_verif_purchasing",
    ),
    path("acc_spk/<str:id>", viewspurchasing.acc_notif_spk, name="acc_spk"),
    # barang_masuk
    path("barang_masuk", viewspurchasing.barang_masuk, name="barang_masuk"),
    path(
        "update_barang_masuk/<str:id>/<str:input_awal>/<str:input_terakhir>",
        viewspurchasing.update_barang_masuk,
        name="update_barang_masuk",
    ),
    # rekap purchasing(gudang+produksi)
    path("rekap_purchasing", viewspurchasing.rekap_purchasing, name="rekap_purchasing"),
    path(
        "rekap_gudang_purchasing",
        viewspurchasing.rekap_gudang_purchasing,
        name="rekap_gudang_purchasing",
    ),
    path(
        "rekap_produksi_purchasing",
        viewspurchasing.rekap_produksi_purchasing,
        name="rekap_produksi_purchasing",
    ),
    # CRUD PRODUK
    path("read_produk", viewspurchasing.read_produk, name="read_produk"),
    path("create_produk", viewspurchasing.create_produk, name="create_produk"),
    path("update_produk/<str:id>", viewspurchasing.update_produk, name="update_produk"),
    path("delete_produk/<str:id>", viewspurchasing.delete_produk, name="delete_produk"),
    # R PO
    path("read_po", viewspurchasing.read_po, name="read_po"),
    # path("rekap_harga", viewspurchasing.rekap_harga, name="rekap_harga"),
    path("rekap_harga", viewspurchasing.views_rekapharga, name="rekapharga"),
    # TAMBAHAN 28/03/2024
    path("spkpurchasing", viewspurchasing.view_spk, name="spk_purchasing"),
    path("sppbpurchasing", viewspurchasing.view_sppb, name="sppb_purchasing"),
    path(
        "detail_sppb_purchasing/<str:id>",
        viewspurchasing.detail_sppb,
        name="detail_sppb_purchasing",
    ),
]

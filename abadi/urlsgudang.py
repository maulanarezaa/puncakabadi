from django.urls import path
from . import viewsgudang

urlpatterns = [
    path("", viewsgudang.view_gudang, name="viewgudang"),
    path("accgudang/<str:id>", viewsgudang.accgudang, name="accgudang"),
    path("baranggudang", viewsgudang.masuk_gudang, name="baranggudang"),
    path("updategudang/<str:id>", viewsgudang.update_gudang, name="updategudang"),
    path("deletegudang/<str:id>", viewsgudang.delete_gudang, name="deletegudang"),
    path("addgudang", viewsgudang.add_gudang, name="addgudang"),
    path("detailbarang", viewsgudang.detail_barang, name="detailbarang"),
    path("detailbarang/<str:id>/<str:tanggal>/<str:lokasi>", viewsgudang.detailksbb, name="detailksbbgudang"),
    path("rekapgudang", viewsgudang.rekap_gudang, name="rekapgudang"),
    path("barangkeluar", viewsgudang.barang_keluar, name="barangkeluar"),
    path("barangretur", viewsgudang.barang_retur, name="barangretur"),
    path(
        "accgudang2/<str:id>",
        viewsgudang.accgudang2,
        name="accgudang2",
    ),
    path("addtransaksinonproduksi", viewsgudang.addgudang3, name="addgudang3"),
    path(
        "accgudang3/<str:id>",
        viewsgudang.accgudang3,
        name="accgudang3",
    ),
    # path("cobaform", viewsgudang.cobaform, name="coba"),
    path("spkgudang", viewsgudang.spk, name="spkgudang"),
    path("trackingspk/<str:id>", viewsgudang.tracking_spk, name="trackingspkgudang"),
    path("bahanbaku", viewsgudang.read_produk, name="readprodukgudang"),
    path(
        "updatebahanbaku/<str:id>",
        viewsgudang.update_produk_gudang,
        name="update_produk_gudang",
    ),
    path("read_saldoawalbahan", viewsgudang.read_saldoawal, name="read_saldoawalbahan"),
    path("addsaldobahan", viewsgudang.addsaldo, name="addsaldobahan"),
    path(
        "deletesaldobahan/<str:id>", viewsgudang.delete_saldo, name="deletesaldobahan"
    ),
    path(
        "update_saldobahan/<str:id>", viewsgudang.update_saldo, name="updatesaldobahan"
    ),
    path("load_produk", viewsgudang.load_produk, name="load_produk"),
    path(
        "updatetransaksinonproduksi/<str:id>",
        viewsgudang.updatetransaksilainlain,
        name="updatetransaksilainlain",
    ),
    path(
        "deletetransaksilainlain/<str:id>",
        viewsgudang.deletetransaksilainlain,
        name="deletetransaksilainlain",
    ),
    path("bulk_addsjp", viewsgudang.bulk_createsjp),
    path("bulk_addsa", viewsgudang.bulk_createsaldoawal),
    path("bulk_addtg", viewsgudang.bulk_createtransaksigudang),
    path(
        "pemusnahan",
        viewsgudang.view_pemusnahanbarang,
        name="read_pemusnahanbahangudang",
    ),
    path(
        "addpemusnahan",
        viewsgudang.add_pemusnahanbarang,
        name="add_pemusnahangudang",
    ),
    path(
        "updatepemusnahan/<str:id>",
        viewsgudang.update_pemusnahanbarang,
        name="update_pemusnahanbaranggudang",
    ),
    path(
        "deletepemusnahan/<str:id>",
        viewsgudang.delete_pemusnahanbarang,
        name="delete_pemusnahangudang",
    ),
    path('updatecache',viewsgudang.updatecache),
    path('readcachevalue',viewsgudang.readcachevalue),
    path('load_po',viewsgudang.load_detailpo,name='load_detailpo'),
    path('exportbackup',viewsgudang.exportbackup),
    path('bulkaddsjpdsjp',viewsgudang.bulkaddsjpdsjp),
    path('purchaseorder',viewsgudang.view_purchaseorder,name='view_purchaseordergudang'),
    path('trackingpo/<str:id>',viewsgudang.trackingpurchaseorder,name='trackingpogudang'),

]

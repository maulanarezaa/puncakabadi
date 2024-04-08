from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from . import models
import datetime
"""PURCHASING"""

# READ NOTIF BARANG MASUK PURCHASIN +SPK G+ACC
def notif_barang_purchasing(request):
    filter_dataobj = models.DetailSuratJalanPembelian.objects.filter(
        KeteranganACC=False
    )
    filter_spkobj = models.SPK.objects.filter(KeteranganACC=False)
    return render(
        request,
        "Purchasing/notif_purchasing.html",
        {
            "filterobj": filter_dataobj,
            "filter_spkobj": filter_spkobj,
        },
    )


def verifikasi_data(request, id):
    verifobj = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    if request.method == "GET":
        harga_total = verifobj.Jumlah * verifobj.Harga
        return render(
            request,
            "Purchasing/update_verif_data.html",
            {
                "verifobj": verifobj,
                "harga_total": harga_total,
            },
        )
    else:
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        po_barang = request.POST["po_barang"]
        verifobj.KeteranganACC = True
        verifobj.Harga = harga_barang
        verifobj.NoSuratJalan.supplier = supplier
        verifobj.NoSuratJalan.PO = po_barang
        verifobj.save()
        verifobj.NoSuratJalan.save()
        harga_total = verifobj.Jumlah * verifobj.Harga
        return redirect("notif_purchasing")


def acc_notif_spk(request, id):
    print(id)
    # accobj = models.DetailSPK.objects.get(IDDetailSPK=id)
    # if request.method == 'GET':
    #     print(accobj.NoSPK.Tanggal)
    #     return render(request,'Purchasing/cek_detailspk.html',{
    #         "accobj" : accobj
    #     })
    # else :
    #     jumlah_post = request.POST["jumlah_barang"]
    #     print(jumlah_post)
    #     accobj.NoSPK.KeteranganACC = True
    #     accobj.Jumlah = jumlah_post
    #     accobj.save()
    #     accobj.NoSPK.save()
    #     return redirect("notif_purchasing")
    accobj = models.SPK.objects.get(pk=id)
    print("ini acc obj",accobj)
    accobj.KeteranganACC = True
    accobj.save()
    return redirect("notif_purchasing")


def barang_masuk(request):
    if len(request.GET) == 0:
        return render(request, "Purchasing/masuk_purchasing.html")
    else:
        input_awal = request.GET["awal"]
        input_terakhir = request.GET["akhir"]
        list_harga_total = []

        filtersjb = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__Tanggal__range=(input_awal, input_terakhir)
        )
        if len(filtersjb) > 0:

            for x in filtersjb:
                harga_total = x.Jumlah * x.Harga
                list_harga_total.append(harga_total)
            i = 0
            for item in filtersjb:
                item.harga_total = list_harga_total[i]
                i += 1
            return render(
                request,
                "Purchasing/masuk_purchasing.html",
                {
                    "data_hasil_filter": filtersjb,
                    "harga_total": harga_total,
                    "input_awal": input_awal,
                    "input_terakhir": input_terakhir,
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return redirect("barang_masuk")


def update_barang_masuk(request, id, input_awal, input_terakhir):
    updateobj = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    if request.method == "GET":
        harga_total = updateobj.Jumlah * updateobj.Harga
        return render(
            request,
            "Purchasing/update_barang_masuk.html",
            {
                "updateobj": updateobj,
                "harga_total": harga_total,
            },
        )
    else:
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        po_barang = request.POST["po_barang"]
        updateobj.Harga = harga_barang
        updateobj.NoSuratJalan.supplier = supplier
        updateobj.NoSuratJalan.PO = po_barang
        updateobj.save()
        updateobj.NoSuratJalan.save()
        harga_total = updateobj.Jumlah * updateobj.Harga
        return redirect(
            f"/purchasing/barang_masuk?awal={input_awal}&akhir={input_terakhir}"
        )
        # return JsonResponse({'harga_total': harga_total})

def rekap_purchasing(request):
    return render(request, "Purchasing/rekap_purchasing.html")


def rekap_gudang_purchasing(request):
    datasjb = (
        models.DetailSuratJalanPembelian.objects.values(
            "KodeProduk",
            "KodeProduk__NamaProduk",
            "KodeProduk__unit",
            "KodeProduk__keterangan",
        )
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )

    datagudang = (
        models.TransaksiGudang.objects.values("KodeProduk")
        .annotate(kuantitas=Sum("jumlah"))
        .order_by()
    )

    for item in datasjb:
        kode_produk = item["KodeProduk"]
        try:
            corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
            item["kuantitas"] -= corresponding_gudang_item["kuantitas"]
        except models.TransaksiGudang.DoesNotExist:
            pass

    return render(
        request, "Purchasing/rekap_gudang_purchasing.html", {"datasjb": datasjb}
    )


def rekap_produksi_purchasing(request):
    list_hasil_konversi = []
    list_sisa_produksi = []
    list_kode = []

    # Mendapatkan data gudang
    datagudang = (
        models.TransaksiGudang.objects.values(
            "KodeProduk",
            "KodeProduk__NamaProduk",
            "KodeProduk__unit",
            "KodeProduk__keterangan",
        )
        .annotate(kuantitas=Sum("jumlah"))
        .order_by()
    )

    if len(datagudang) <= 0:
        messages.error(request, "Data gudang tidak ditemukan")
        return render(
            request, "Purchasing/rekap_produksi_purchasing.html"
        )  # Redirect ke halaman kesalahan atau penanganan yang sesuai

    # Mendapatkan data produksi
    dataproduksi = (
        models.TransaksiProduksi.objects.filter(Keterangan="mutasi")
        .values("KodeArtikel")
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )

    for item in dataproduksi:
        kode_artikel = item["KodeArtikel"]
        try:
            datakonversi = models.KonversiMaster.objects.filter(
                IDKodePenyusun__Status=True
            ).filter(IDKodePenyusun__KodeArtikel=kode_artikel)

            for konversi in datakonversi:
                hasil_konversi = konversi.Kuantitas * item["kuantitas"]
                list_hasil_konversi.append(hasil_konversi)
                kode_produk_konversi = konversi.IDKodePenyusun.KodeProduk_id
                list_kode.append(kode_produk_konversi)
        except models.KonversiMaster.DoesNotExist:
            messages.error(request, "Data konversi tidak ditemukan")

    for item2 in datagudang:
        kode_produk = item2["KodeProduk"]
        if kode_produk in list_kode:
            index_kode = list_kode.index(kode_produk)
            konversi_produk = list_hasil_konversi[index_kode]
            sisa_produksi = item2["kuantitas"] - konversi_produk
            list_sisa_produksi.append(sisa_produksi)
        else:
            pass

    i = 0
    for item3 in datagudang:
        item3["sisa_produksi"] = list_sisa_produksi[i]
        i += 1

    return render(
        request,
        "Purchasing/rekap_produksi_purchasing.html",
        {"datagudang": datagudang, "sisa_produksi": sisa_produksi},
    )

'''REVISI DELETE ADA YANG ERROR, TRS ERROR HANDLING GABOLE CREATE DENGAN KODE YG SAMA(done)'''
def read_produk(request):
    produkobj = models.Produk.objects.all()
    return render(request, "Purchasing/read_produk.html", {"produkobj": produkobj})


def create_produk(request):
    if request.method == "GET":
        return render(request, "Purchasing/create_produk.html")
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]
        keterangan_produk = request.POST["keterangan_produk"]
        jumlah_minimal = request.POST["jumlah_minimal"]
        produkobj = models.Produk.objects.filter(KodeProduk=kode_produk)
        print(produkobj)
        if len(produkobj) == 1 :
            messages.error(request, "Kode Produk sudah ada")
            return redirect("create_produk")
        else :
            new_produk = models.Produk(
                KodeProduk=kode_produk,
                NamaProduk=nama_produk,
                unit=unit_produk,
                keterangan=keterangan_produk,
                TanggalPembuatan = datetime.datetime.now(),
                Jumlahminimal = jumlah_minimal
            )
            new_produk.save()
            return redirect("read_produk")


def update_produk(request, id):
    produkobj = models.Produk.objects.get(pk=id)
    if request.method == "GET":
        return render(
            request, "Purchasing/update_produk.html", {"produkobj": produkobj}
        )
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]
        keterangan_produk = request.POST["keterangan_produk"]
        jumlah_minimal = request.POST["jumlah_minimal"]
        produkobj.KodeProduk = kode_produk
        produkobj.NamaProduk = nama_produk
        produkobj.unit = unit_produk
        produkobj.keterangan = keterangan_produk
        produkobj.Jumlahminimal = jumlah_minimal 
        produkobj.save()
        return redirect("read_produk")


def delete_produk(request, id):
    print(id)
    produkobj = models.Produk.objects.get(KodeProduk=id)
    produkobj.delete()
    messages.success(request,"Data Berhasil dihapus")
    return redirect("read_produk")


# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
def read_po(request) :
    if len(request.GET) == 0 :
        return render(request, "Purchasing/read_po.html")
    else :
        input_po = request.GET["input_po"]
        po_obj = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__PO=input_po
        )
        if len(po_obj) == 0 :
            messages.error(request, "Data tidak ditemukan")
            return redirect(read_po)
        else :
            return render(
                request,
                "Purchasing/read_po.html",
                {"po_obj": po_obj,
                 "input_po" :input_po})
# def read_po(request):

#     po_objall = models.SuratJalanPembelian.objects.all()
#     # po_objall = models.DetailSuratJalanPembelian.objects.all()
#     if request.method == "GET":
#         return render(request, "Purchasing/read_po.html", {"po_objall": po_objall})
#     else:
#         input_po = request.POST["input_po"]
#         po_obj = models.DetailSuratJalanPembelian.objects.filter(
#             NoSuratJalan__PO=input_po
#         )
#         if len(po_obj) == 0 :
#             return redirect(read_po)
#         else :
#             return render(
#                 request,
#                 "Purchasing/read_po.html",
#                 {"po_objall": po_objall, "po_obj": po_obj},
#             )


# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
def rekap_harga(request):
    """KALAU UNTUK PERHITUNGAN HARGA AVERAGE JANGAN PAKE FILTER TANGGAL, KALAU BUAT DATA DI MASUK BARU PAKE TANGGAL"""
    kodeprodukobj = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request, "Purchasing/rekap_harga.html", {"kodeprodukobj": kodeprodukobj}
        )
    else:
        dict_harga_keluar = {}
        dict_harga_total = {}
        dict_harga_masuk = {}
        dict_harga_average = {}
        list_tanggal = []
        list_supplier = []
        list_kuantitas = []
        list_harga = []
        list_harga_total = []
        kode_produk = request.GET["kode_produk"]
        tanggal_awal = request.GET["awal"]
        tanggal_akhir = request.GET["akhir"]
        # tanggal
        masuk_sjb = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=kode_produk
        ).filter(NoSuratJalan__Tanggal__range=(tanggal_awal, tanggal_akhir))
        masuk_sjb2 = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=kode_produk
        )
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(KodeProduk=kode_produk)

        if len(masuk_sjb2) <= 0:
            messages.error(request, "Data tidak ditemukan")
            return redirect("Purchasing/rekap_harga")
        else:
            for item in masuk_sjb2:
                kodeproduk = item.KodeProduk
                jumlah_masuk = item.Jumlah
                harga_masuk = item.Harga
                harga_total_masuk = jumlah_masuk * harga_masuk

                if kodeproduk in dict_harga_total:
                    dict_harga_total[kodeproduk][0] += harga_total_masuk
                    dict_harga_total[kodeproduk][1] += jumlah_masuk
                else:
                    # dict_harga_total[kodeproduk] = [0]
                    dict_harga_total[kodeproduk] = [harga_total_masuk, jumlah_masuk]

            for key in dict_harga_total.keys():
                average_harga = dict_harga_total[key][0] / dict_harga_total[key][1]
                dict_harga_average[key] = [average_harga, dict_harga_total[key][1]]

            for item in masuk_sjb:
                if item.KodeProduk in dict_harga_masuk:
                    if (
                        dict_harga_masuk[item.KodeProduk]["Tanggal"]
                        == item.NoSuratJalan.Tanggal
                        and dict_harga_masuk[item.KodeProduk]["Supplier"]
                        == item.NoSuratJalan.supplier
                        and dict_harga_masuk[item.KodeProduk]["Harga"] == item.Harga
                    ):
                        dict_harga_masuk[item.KodeProduk]["Kuantitas"] += item.Jumlah
                    else:
                        harga_masuk = item.Harga
                        jumlah_masuk = item.Jumlah
                        harga_total = jumlah_masuk * harga_masuk
                        dict_harga_masuk[item.KodeProduk]["Tanggal"].append(
                            item.NoSuratJalan.Tanggal
                        )
                        dict_harga_masuk[item.KodeProduk]["Supplier"].append(
                            item.NoSuratJalan.supplier
                        )
                        dict_harga_masuk[item.KodeProduk]["Kuantitas"].append(
                            jumlah_masuk
                        )
                        dict_harga_masuk[item.KodeProduk]["Harga"].append(harga_masuk)
                        dict_harga_masuk[item.KodeProduk]["Harga_Total"].append(
                            harga_total
                        )

                else:
                    harga_masuk = item.Harga
                    jumlah_masuk = item.Jumlah
                    harga_total = jumlah_masuk * harga_masuk
                    dict_harga_masuk[item.KodeProduk] = {}
                    dict_harga_masuk[item.KodeProduk]["Tanggal"] = [
                        item.NoSuratJalan.Tanggal
                    ]
                    dict_harga_masuk[item.KodeProduk]["Supplier"] = [
                        item.NoSuratJalan.supplier
                    ]
                    dict_harga_masuk[item.KodeProduk]["Kuantitas"] = [jumlah_masuk]
                    dict_harga_masuk[item.KodeProduk]["Harga"] = [harga_masuk]
                    dict_harga_masuk[item.KodeProduk]["Harga_Total"] = [harga_total]

        if len(saldoawalobj) <= 0:
            jumlah_saldo = 0
            harga_awal_saldo = 0
            for key in dict_harga_total.keys():
                harga_total_awal = jumlah_saldo * harga_awal_saldo
                jumlah_total = jumlah_saldo + dict_harga_total[key][1]

                harga_total_all = round(harga_total_awal + dict_harga_total[key][0])

                average_harga = round(harga_total_all / jumlah_total)
                dict_harga_average[key][0] = average_harga
                dict_harga_average[key][1] = jumlah_total
        else:
            for item2 in saldoawalobj:
                kode_produk2 = item2.KodeProduk
                jumlah_saldo = item2.Jumlah
                harga_awal_saldo = item2.Harga
                jumlah_total = jumlah_saldo + dict_harga_total[key][1]
                harga_total_awal = jumlah_saldo * harga_awal_saldo
                dict_harga_total[key][1]
                harga_total_all = round(harga_total_awal + dict_harga_total[key][0])
                average_harga = round(harga_total_all / jumlah_total)
                dict_harga_average[kode_produk2][0] = average_harga
                dict_harga_average[kode_produk2][1] = jumlah_total
        keluar_sjb = (
            models.TransaksiGudang.objects.filter(KodeProduk=kode_produk)
            .filter(tanggal__range=(tanggal_awal, tanggal_akhir))
            .filter(jumlah__gt=0)
        )

        list_jumlah = []
        for item in keluar_sjb:
            list_jumlah.append(item.jumlah)
        sum_jumlah = sum(list_jumlah)

        for item3 in keluar_sjb:
            kode_produk3 = item3.KodeProduk
            dict_harga_keluar[kode_produk3] = [0, 0, 0, 0]

        for item4 in keluar_sjb:
            kode_produk4 = item4.KodeProduk
            if kode_produk4 in dict_harga_total:
                harga_keluar = round(dict_harga_average[kode_produk4][0] * sum_jumlah)
                dict_harga_keluar[kode_produk4][0] = item4.tanggal
                dict_harga_keluar[kode_produk4][1] = sum_jumlah
                dict_harga_keluar[kode_produk4][2] = dict_harga_average[kode_produk4][0]
                dict_harga_keluar[kode_produk4][3] = harga_keluar
            else:
                continue

        for key in dict_harga_masuk.keys():
            list_tanggal = dict_harga_masuk[key]["Tanggal"]
            list_supplier = dict_harga_masuk[key]["Supplier"]
            list_kuantitas = dict_harga_masuk[key]["Kuantitas"]
            list_harga = dict_harga_masuk[key]["Harga"]
            list_harga_total = dict_harga_masuk[key]["Harga_Total"]

        tanggal = 0
        supplier = 0
        kuantitas = 0
        harga = 0
        harga_total_1 = 0

        i = 0
        for item in masuk_sjb:
            item.tanggal = list_tanggal[i]
            item.supplier = list_supplier[i]
            item.kuantitas = list_kuantitas[i]
            item.harga = list_harga[i]
            item.harga_total_1 = list_harga_total[i]
            i += 1

        return render(
            request,
            "Purchasing/rekap_harga.html",
            {
                "kodeprodukobj": kodeprodukobj,
                "masuk_sjb": masuk_sjb,
                "harga_masuk": dict_harga_masuk,
                "harga_keluar": dict_harga_keluar,
                "harga_total": dict_harga_total,
                "tanggal": tanggal,
                "supplier": supplier,
                "kuantitas": kuantitas,
                "harga": harga,
                "harga_total_1": harga_total_1,
                "awal": tanggal_awal,
                "akhir": tanggal_akhir,
            },
        )


# Coba v2
def views_rekapharga(request):
    kodeprodukobj = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request, "Purchasing/views_ksbb.html", {"kodeprodukobj": kodeprodukobj}
        )
    else:
        kode_produk = request.GET["kode_produk"]

        try:
            produkobj = models.Produk.objects.get(KodeProduk=kode_produk)
        except models.Produk.DoesNotExist:
            messages.error(request, "Kode bahan baku tidak ditemukan")
            return render(
                request, "Purchasing/views_ksbb.html", {"kodeprodukobj": kodeprodukobj}
            )
        masukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=produkobj.KodeProduk
        )


        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk=produkobj.KodeProduk
        )
        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
        print('ini kode bahan baku',keluarobj)
        if not keluarobj.exists():
            messages.error(request,'Tidak ditemukan data Transaksi Barang')
            return redirect('rekapharga')
        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku=produkobj.KodeProduk, IDLokasi=1
            )
            .order_by("-Tanggal")
            .first()
        )
        if saldoawalobj:
            print("ada data")
            saldoawal = saldoawalobj.Jumlah
            hargasatuanawal = saldoawalobj.Harga
            hargatotalawal = saldoawal * hargasatuanawal

        else:
            saldoawal = 0
            hargasatuanawal = 0
            hargatotalawal = saldoawal * hargasatuanawal
        saldoawalobj = {
            "saldoawal": saldoawal,
            "hargasatuanawal": hargasatuanawal,
            "hargatotalawal": hargatotalawal,
        }
        hargaterakhir = 0
        listdata = []
        print(tanggalmasuk)
        print(tanggalkeluar)
        listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
        print(listtanggal)
        for i in listtanggal:
            jumlahmasukperhari = 0
            hargamasuktotalperhari = 0
            hargamasuksatuanperhari = 0
            jumlahkeluarperhari = 0
            hargakeluartotalperhari = 0
            hargakeluarsatuanperhari = 0
            sjpobj = masukobj.filter(NoSuratJalan__Tanggal=i)
            if sjpobj.exists():
                for j in sjpobj:
                    hargamasuktotalperhari += j.Harga * j.Jumlah
                    jumlahmasukperhari += j.Jumlah
                hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
            else:
                hargamasuktotalperhari = 0
                jumlahmasukperhari = 0
                hargamasuksatuanperhari = 0

            transaksigudangobj = keluarobj.filter(tanggal=i)
            print(transaksigudangobj)
            if transaksigudangobj.exists():
                for j in transaksigudangobj:
                    jumlahkeluarperhari += j.jumlah
                    hargakeluartotalperhari += j.jumlah * hargasatuanawal
                hargakeluarsatuanperhari += (
                    hargakeluartotalperhari / jumlahkeluarperhari
                )
            else:
                hargakeluartotalperhari = 0
                hargakeluarsatuanperhari = 0
                jumlahkeluarperhari = 0

            print("Tanggal : ", i)
            print("Sisa Stok Hari Sebelumnya : ", saldoawal)
            print("harga awal Hari Sebelumnya :", hargasatuanawal)
            print("harga total Hari Sebelumnya :", hargatotalawal)
            print("Jumlah Masuk : ", jumlahmasukperhari)
            print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
            print("Harga Total Masuk : ", hargamasuktotalperhari)
            print("Jumlah Keluar : ", jumlahkeluarperhari)
            print("Harga Keluar : ", hargakeluarsatuanperhari)
            print(
                "Harga Total Keluar : ", hargakeluarsatuanperhari * jumlahkeluarperhari
            )
            if saldoawal + jumlahmasukperhari - jumlahkeluarperhari < 0:
                messages.warning(
                    request,
                    "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                        i
                    ),
                )

            dumy = {
                "Tanggal": i,
                "Jumlahstokawal": saldoawal,
                "Hargasatuanawal": round(hargasatuanawal, 2),
                "Hargatotalawal": round(hargatotalawal, 2),
                "Jumlahmasuk": jumlahmasukperhari,
                "Hargamasuksatuan": round(hargamasuksatuanperhari, 2),
                "Hargamasuktotal": round(hargamasuktotalperhari, 2),
                "Jumlahkeluar": jumlahkeluarperhari,
                "Hargakeluarsatuan": round(hargakeluarsatuanperhari, 2),
                "Hargakeluartotal": round(hargakeluartotalperhari, 2),
            }
            """
            Rumus dari Excel KSBB Purchasing
            Sisa = Sisa hari sebelumnya + Jumlah masuk hari ini - jumlah keluar hari ini 
            harga sisa satuan = total sisa / harga total sisa
            Harga keluar = harga satuan hari sebelumnya

            """
            saldoawal += jumlahmasukperhari - jumlahkeluarperhari
            hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
            hargasatuanawal = hargatotalawal / saldoawal

            print("Sisa Stok Hari Ini : ", saldoawal)
            print("harga awal Hari Ini :", hargasatuanawal)
            print("harga total Hari Ini :", hargatotalawal, "\n")
            dumy["Sisahariini"] = saldoawal
            dumy["Hargasatuansisa"] = round(hargasatuanawal, 2)
            dumy["Hargatotalsisa"] = round(hargatotalawal, 2)

            listdata.append(dumy)

        hargaterakhir += hargasatuanawal

        return render(
            request,
            "purchasing/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
            },
        )
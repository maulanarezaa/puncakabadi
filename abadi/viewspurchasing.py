from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import F
from django.db.models import Sum,Value
from . import models
from datetime import datetime
from django.db import IntegrityError
from urllib.parse import quote
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd
from . import logindecorators
from django.contrib.auth.decorators import login_required
from .viewsproduksi import calculate_KSBB
from django.http import HttpResponse
from django.db.models.functions import Coalesce

"""PURCHASING"""


# # READ NOTIF BARANG MASUK PURCHASIN +SPK G+ACC
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def notif_barang_purchasing(request):
    filter_dataobj = models.DetailSuratJalanPembelian.objects.filter(
        KeteranganACC=False
    ).order_by("NoSuratJalan__Tanggal")
    for x in filter_dataobj:
        x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
    filter_spkobj = models.SPK.objects.filter(KeteranganACC=False).order_by("Tanggal")
    for x in filter_spkobj:
        x.Tanggal = x.Tanggal.strftime("%Y-%m-%d")
    print(filter_spkobj)
    list_artikel = []
    list_q_gudang = []
    list_data_art = []
    list_hasil_conv = []
    list_q_akhir = []
    try:
        allartikel = models.Artikel.objects.all()
        for item in allartikel:
            nama_artikel = item.KodeArtikel
            list_artikel.append(nama_artikel)
    except models.Artikel.DoesNotExist:
        messages.error(request, "Data Artikel tidak ditemukan")

    datasjb = (
        models.DetailSuratJalanPembelian.objects.values("KodeProduk")
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )

    if len(datasjb) == 0:
        messages.error(request, "Tidak ada barang masuk ke gudang")

    datagudang = (
        models.TransaksiGudang.objects.values("KodeProduk")
        .annotate(kuantitas=Sum("jumlah"))
        .order_by()
    )

    for item in datasjb:
        kode_produk = item["KodeProduk"]
        try:
            corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
            item["kuantitas"] += corresponding_gudang_item["kuantitas"]
            if item["kuantitas"] + corresponding_gudang_item["kuantitas"] < 0:
                messages.info("Kuantitas gudang menjadi minus")

        except models.TransaksiGudang.DoesNotExist:
            pass
        list_q_gudang.append({kode_produk: item["kuantitas"]})
    dataspk = (
        models.DetailSPK.objects.filter(NoSPK__StatusAktif=True)
        .values(("KodeArtikel__KodeArtikel"))
        .annotate(kuantitas2=Sum("Jumlah"))
        .order_by()
    )

    for item in dataspk:
        art_code = item["KodeArtikel__KodeArtikel"]
        jumlah_art = item["kuantitas2"]
        list_data_art.append({"Kode_Artikel": art_code, "Jumlah_Artikel": jumlah_art})

    for item in list_data_art:
        kodeArt = item["Kode_Artikel"]

        jumlah_art = item["Jumlah_Artikel"]

        getidartikel = models.Artikel.objects.get(KodeArtikel=kodeArt)
        art_code = getidartikel.id

        try:
            konversi_art = (
                models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel=art_code)
                .annotate(
                    kode_art=F("KodePenyusun__KodeArtikel__KodeArtikel"),
                    kode_produk=F("KodePenyusun__KodeProduk"),
                    nilai_konversi=F("Allowance"),
                    nama_bb=F("KodePenyusun__KodeProduk__NamaProduk"),
                    unit_satuan=F("KodePenyusun__KodeProduk__unit"),
                )
                .values(
                    "kode_art", "kode_produk", "Kuantitas", "nama_bb", "unit_satuan"
                )
                .distinct()
            )

            for item2 in konversi_art:
                kode_artikel = art_code
                kode_produk = item2["kode_produk"]
                nilai_conv = item2["Kuantitas"]
                nama_bb = item2["nama_bb"]
                unit_satuan = item2["unit_satuan"]
                hasil_conv = round(jumlah_art * nilai_conv)

                list_hasil_conv.append(
                    {
                        "Kode Artikel": kode_artikel,
                        "Jumlah Artikel": jumlah_art,
                        "Kode Produk": kode_produk,
                        "Nama Produk": nama_bb,
                        "Hasil Konversi": hasil_conv,
                        "Unit Satuan": unit_satuan,
                    }
                )

        except models.KonversiMaster.DoesNotExist:
            pass

    for item in list_hasil_conv:
        kode_produk = item["Kode Produk"]
        hasil_konversi = item["Hasil Konversi"]
        for item2 in list_q_gudang:
            if kode_produk in item2:
                gudang_jumlah = item2[kode_produk]

                hasil_akhir = gudang_jumlah - hasil_konversi
                list_q_akhir.append(
                    {
                        "Kode_Artikel": item["Kode Artikel"],
                        "Jumlah_Artikel": item["Jumlah Artikel"],
                        "Kode_Produk": kode_produk,
                        "Nama_Produk": item["Nama Produk"],
                        "Unit_Satuan": item["Unit Satuan"],
                        "Kebutuhan": hasil_konversi,
                        "Stok_Gudang": gudang_jumlah,
                        "Selisih": hasil_akhir,
                    }
                )

    # list_pengadaan = []
    # for item in list_q_akhir:
    #     kode_produk = item['Kode_Produk']
    #     nama_produk = item['Nama_Produk']
    #     satuan = item['Unit_Satuan']
    #     selisih = item['Selisih']
    #     if kode_produk in pengadaan['Kode_Produk'] :
    #         pengadaan[]
    pengadaan = {}

    for item in list_q_akhir:
        produk = item["Kode_Produk"]
        pengadaan[produk] = [0, 0]

    for item in list_q_akhir:
        produk = item["Kode_Produk"]
        nama_produk = item["Nama_Produk"]
        selisih = item["Selisih"]
        if produk in pengadaan:
            pengadaan[produk][0] = nama_produk
            pengadaan[produk][1] += selisih
        else:
            pengadaan[produk][0] = nama_produk
            pengadaan[produk][1] = selisih

    rekap_pengadaan = {}

    for key, value in pengadaan.items():
        if value[1] < 0:
            new_value = abs(value[1])
            for i, item in enumerate(list_q_akhir):
                if item["Kode_Produk"] == key:
                    index = i
                    rekap_pengadaan[key] = [
                        value[0],
                        new_value,
                        list_q_akhir[index]["Unit_Satuan"],
                    ]

    list_produk = []
    jumlah_min = models.Produk.objects.values("KodeProduk", "Jumlahminimal")
    print(jumlah_min)
    datasjb = (
        models.DetailSuratJalanPembelian.objects.values(
            "KodeProduk",
            "KodeProduk__NamaProduk",
            "KodeProduk__unit",
            "KodeProduk__keteranganGudang",
        )
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )

    datagudang = (
        models.TransaksiGudang.objects.values("KodeProduk")
        .annotate(kuantitas=Sum("jumlah"))
        .order_by()
    )

    # for item2 in jumlah_min :
    #         kode = item2['KodeProduk']
    #         print(kode)
    for item in datasjb:
        kode_produk = item["KodeProduk"]
        nama_produk = item["KodeProduk__NamaProduk"]
        satuan = item["KodeProduk__unit"]
        try:
            corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
            item["kuantitas"] -= corresponding_gudang_item["kuantitas"]
            for item2 in jumlah_min:
                kode = item2["KodeProduk"]
                jumlah_minimal = item2["Jumlahminimal"]
                if kode == kode_produk:
                    if item["kuantitas"] < jumlah_minimal:
                        list_produk.append(
                            {
                                "Kode_Produk": kode_produk,
                                "Nama_Produk": nama_produk,
                                "Satuan": satuan,
                                "Jumlah_minimal": jumlah_minimal,
                                "Jumlah_aktual": item["kuantitas"],
                            }
                        )
                    else:
                        continue
                else:
                    continue

        except models.TransaksiGudang.DoesNotExist:
            pass

    print("Ini list produk: ", list_produk)
    return render(
        request,
        "Purchasing/notif_purchasing.html",
        {
            "filterobj": filter_dataobj,
            "filter_spkobj": filter_spkobj,
            "rekap_pengadaan": rekap_pengadaan,
            "listproduk": list_produk,
        },
    )


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
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
        # print("verif:",verifobj.NoSuratJalan)
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="ACC",
            pesan=f"No Surat Jalan {verifobj.NoSuratJalan} sudah ACC",
        ).save()

        # tes = models.transactionlog.objects.filter(user = "Purchasing")
        # print("Tes ae : ",tes)
        return redirect("notif_purchasing")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def acc_notif_spk(request, id):

    accobj = models.SPK.objects.get(pk=id)
    accobj.KeteranganACC = True
    accobj.save()
    models.transactionlog(
        user="Purchasing",
        waktu=datetime.now(),
        jenis="ACC",
        pesan=f"No SPK {accobj.NoSPK} sudah ACC",
    ).save()
    messages.success(request, "Jangan lupa cek data SPK!")
    return redirect("notif_purchasing")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def barang_masuk(request):
    if len(request.GET) == 0:
        list_harga_total1 = []

        sjball = models.DetailSuratJalanPembelian.objects.all().order_by(
            "NoSuratJalan__Tanggal"
        )
        print(sjball)
        if len(sjball) > 0:

            for x in sjball:
                harga_total = x.Jumlah * x.Harga
                x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
                print(harga_total)
                list_harga_total1.append(harga_total)
            i = 0
            for item in sjball:
                item.harga_total = list_harga_total1[i]
                i += 1

            return render(
                request,
                "Purchasing/masuk_purchasing.html",
                {
                    "sjball": sjball,
                    "harga_total": harga_total,
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return render(
                request,
                "Purchasing/masuk_purchasing.html",
)
    else:
        input_awal = request.GET["awal"]
        input_terakhir = request.GET["akhir"]
        list_harga_total = []

        filtersjb = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__Tanggal__range=(input_awal, input_terakhir)
        ).order_by("NoSuratJalan__Tanggal")
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


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def update_barang_masuk(request, id):
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
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"No Surat Jalan{updateobj.NoSuratJalan} sudah di Update",
        ).save()
        return redirect("barang_masuk")
        # return JsonResponse({'harga_total': harga_total})


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def rekap_purchasing(request):
    return render(request, "Purchasing/rekap_purchasing.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def view_rekapbarang(request):
    tanggal_akhir = request.GET.get("periode")

    sekarang = datetime.now()
    tahun = sekarang.year

    tanggal_mulai = datetime(year=tahun, month=1, day=1)

    dataproduk = models.Produk.objects.all()

    if tanggal_akhir:
        for produk in dataproduk:
            listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, tanggal_akhir)

            if listdata:
                produk.kuantitas = listdata[-1]["Sisa"][0]
            else:
                produk.kuantitas = 0
    else:
        for produk in dataproduk:
            listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, sekarang)

            if listdata:
                produk.kuantitas = listdata[-1]["Sisa"][0]
            else:
                produk.kuantitas = 0
    return render(
        request,
        "Purchasing/rekapproduksi2.html",
        {"data": dataproduk, "tanggal_akhir": tanggal_akhir},
    )


"""REVISI DELETE ADA YANG ERROR, TRS ERROR HANDLING GABOLE CREATE DENGAN KODE YG SAMA(done)"""


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def read_produk(request):
    produkobj = models.Produk.objects.all()
    return render(request, "Purchasing/read_produk.html", {"produkobj": produkobj})


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def create_produk(request):
    if request.method == "GET":
        return render(request, "Purchasing/create_produk.html")
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]
        keterangan_produk = request.POST["keterangan_produk"]
        jumlah_minimal = 0
        produkobj = models.Produk.objects.filter(KodeProduk=kode_produk)
        print(produkobj)
        if len(produkobj) > 0:
            messages.error(request, "Kode Produk sudah ada")
            return redirect("create_produk")
        else:
            new_produk = models.Produk(
                KodeProduk=kode_produk,
                NamaProduk=nama_produk,
                unit=unit_produk,
                keteranganPurchasing=keterangan_produk,
                TanggalPembuatan=datetime.now(),
                Jumlahminimal=jumlah_minimal,
            )
            new_produk.save()
            models.transactionlog(
                user="Purchasing",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Kode Produk {kode_produk} sudah di Create",
            ).save()
            messages.success(request, "Data berhasil disimpan")
            return redirect("read_produk")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
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
        namaproduk = models.Produk.objects.filter(KodeProduk=kode_produk)
        # if len(nama_produk) > 0 :
        #     messages.error(request, "Kode Produk sudah ada")
        #     return redirect("update_produk")
        if produkobj.KodeProduk != kode_produk:
            print("post kode :", kode_produk)
            if len(namaproduk) > 0:
                # if kode_produk ==
                messages.error(request, "Kode Produk sudah ada")
                return redirect("read_produk")
                # return redirect("update_produk",id=id)

            else:
                new_produk = models.Produk(
                    KodeProduk=kode_produk,
                    NamaProduk=nama_produk,
                    unit=unit_produk,
                    keteranganPurchasing=keterangan_produk,
                    TanggalPembuatan=datetime.now(),
                    Jumlahminimal=jumlah_minimal,
                )
                new_produk.save()
                models.transactionlog(
                    user="Purchasing",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Kode Produk {kode_produk} sudah di Create",
                ).save()
        else:
            produkobj.KodeProduk = kode_produk
            produkobj.NamaProduk = nama_produk
            produkobj.unit = unit_produk
            produkobj.keteranganPurchasing = keterangan_produk
            produkobj.Jumlahminimal = jumlah_minimal
            produkobj.save()
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Kode Produk {kode_produk} sudah di Update",
        ).save()
        messages.success(request, "Data berhasil disimpan")
        return redirect("read_produk")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def delete_produk(request, id):
    print(id)
    produkobj = models.Produk.objects.get(KodeProduk=id)
    # print("delete:",produkobj.KodeProduk)
    models.transactionlog(
        user="Purchasing",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Kode Produk {produkobj.KodeProduk} sudah di Delete",
    ).save()
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("read_produk")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def rekap_gudang(request):
    listproduk = []
    listnama = []
    satuan = []
    liststokakhir = []

    dataproduk = models.Produk.objects.all()
    datenow = datetime.now()
    tahun = datenow.year
    mulai = datetime(year=tahun, month=1, day=1)
    date = request.GET.get("date")

    for i in dataproduk:
        listproduk.append(i.KodeProduk)
        listnama.append(i.NamaProduk)
        satuan.append(i.unit)

        if date is not None:
            datagudang = models.TransaksiGudang.objects.filter(
                tanggal__range=(mulai, date), KodeProduk=i
            ).aggregate(kuantitas=Coalesce(Sum("jumlah"), Value(0)))
            datasjp = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__range=(mulai, date), KodeProduk=i
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))
            saldoawal = models.SaldoAwalBahanBaku.objects.filter(
                Tanggal__range=(mulai, date), IDBahanBaku=i, IDLokasi="3"
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))
            pemusnahan = models.PemusnahanBahanBaku.objects.filter(
                Tanggal__range=(mulai, date), KodeBahanBaku=i, lokasi="3"
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))
        else:
            datagudang = models.TransaksiGudang.objects.filter(
                tanggal__range=(mulai, datenow), KodeProduk=i
            ).aggregate(kuantitas=Coalesce(Sum("jumlah"), Value(0)))
            datasjp = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__range=(mulai, datenow), KodeProduk=i
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))
            saldoawal = models.SaldoAwalBahanBaku.objects.filter(
                Tanggal__range=(mulai, datenow), IDBahanBaku=i, IDLokasi="3"
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))
            pemusnahan = models.PemusnahanBahanBaku.objects.filter(
                Tanggal__range=(mulai, datenow), KodeBahanBaku=i, lokasi="3"
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0)))

        stokakhir = (
            datasjp["kuantitas"]
            - datagudang["kuantitas"]
            + saldoawal["kuantitas"]
            - pemusnahan["kuantitas"]
        )
        liststokakhir.append(stokakhir)

        # print(datagudang)
        # print(datasjp)
        # print(saldoawal)
        # print(pemusnahan)
        # print(stokakhir)

    combined_list = zip(listproduk, listnama, satuan, liststokakhir)

    # Membuat dictionary sesuai template yang diinginkan
    produk_dict = {
        kode_produk: {
            "NamaProduk": nama_produk,
            "Satuan": satuan,
            "StokAkhir": stok_akhir,
        }
        for kode_produk, nama_produk, satuan, stok_akhir in combined_list
    }

    return render(
        request,
        "Purchasing/rekapgudang2.html",
        {
            "kodeproduk": listproduk,
            "date": date,
            "dict_semua": produk_dict,
        },
    )
    # # batas
    # datasjb = (
    #     models.DetailSuratJalanPembelian.objects.values(
    #         "KodeProduk",
    #         "KodeProduk__NamaProduk",
    #         "KodeProduk__unit",
    #         "KodeProduk__keteranganGudang",
    #     )
    #     .annotate(kuantitas=Sum("Jumlah"))
    #     .order_by()
    # )
    # print(datasjb)
    # datenow = datetime.now()
    # tahun = datenow.year
    # mulai = datetime(year=tahun, month=1, day=1)
    # date = request.GET.get("date")
    # if date is not None:
    #     datasjb = (
    #         models.DetailSuratJalanPembelian.objects.filter(
    #             NoSuratJalan__Tanggal__range=(mulai, date)
    #         )
    #         .values(
    #             "KodeProduk",
    #             "KodeProduk__NamaProduk",
    #             "KodeProduk__unit",
    #             "KodeProduk__keteranganGudang",
    #         )
    #         .annotate(kuantitas=Sum("Jumlah"))
    #         .order_by()
    #     )

    # if len(datasjb) == 0:
    #     messages.error(request, "Tidak ada barang masuk ke gudang")

    # datagudang = (
    #     models.TransaksiGudang.objects.values("KodeProduk")
    #     .annotate(kuantitas=Sum("jumlah"))
    #     .order_by()
    # )
    # print(datasjb)
    # for item in datasjb:
    #     kode_produk = item["KodeProduk"]
    #     try:
    #         corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
    #         item["kuantitas"] -= corresponding_gudang_item["kuantitas"]

    #         if item["kuantitas"] + corresponding_gudang_item["kuantitas"] < 0:
    #             messages.info("Kuantitas gudang menjadi minus")

    #     except models.TransaksiGudang.DoesNotExist:
    #         pass
    # return render(
    #     request, "Purchasing/rekapgudang2.html", {"datasjb": datasjb, "date": date}
    # )

    # datasjb = models.DetailSuratJalanPembelian.objects.values('KodeProduk','KodeProduk__NamaProduk','KodeProduk__unit','KodeProduk__keterangan').annotate(kuantitas=Sum('Jumlah')).order_by()
    # if len(datasjb) == 0 :
    #     messages.error(request, "Tidak ada barang masuk ke gudang")

    # datagudang = models.TransaksiGudang.objects.values('KodeProduk').annotate(kuantitas=Sum('jumlah')).order_by()

    # for item in datasjb:
    #     kode_produk = item['KodeProduk']
    #     try:
    #         corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
    #         item['kuantitas'] += corresponding_gudang_item['kuantitas']

    #         if item['kuantitas'] + corresponding_gudang_item['kuantitas'] < 0 :
    #             messages.info("Kuantitas gudang menjadi minus")

    #     except models.TransaksiGudang.DoesNotExist:
    #         pass

    # return render(request,'Purchasing/rekapgudang2.html',{
    #     'datasjb' : datasjb,
    # })


# def read_po(request):
#     print(request.GET)
#     if len(request.GET) == 0:
#         po_objall = models.SuratJalanPembelian.objects.all()
#         return render(request, "Purchasing/read_po.html", {'po_objall': po_objall})
#     else:
#         input_po = request.GET["input_po"]
#         if request.method == 'POST' :
#             sort_by = request.POST["sort_by"]
#             if sort_by == "tanggal_terbaru":
#                 po_obj = models.DetailSuratJalanPembelian.objects.filter(
#                     NoSuratJalan__PO=input_po
#                 ).order_by("NoSuratJalan__Tanggal")
#             elif sort_by == "tanggal_terlama":
#                 po_obj = models.DetailSuratJalanPembelian.objects.filter(
#                     NoSuratJalan__PO=input_po
#                 ).order_by("-NoSuratJalan__Tanggal")
#             else:
#                 po_obj_lunas = models.DetailSuratJalanPembelian.objects.filter(
#                     NoSuratJalan__PO=input_po, KeteranganACC=True
#                 ).order_by("-NoSuratJalan__Tanggal")
#                 po_obj_tidak_lunas = models.DetailSuratJalanPembelian.objects.filter(
#                     NoSuratJalan__PO=input_po, KeteranganACC=False
#                 ).order_by("-NoSuratJalan__Tanggal")
#                 if sort_by == "lunas":
#                     po_obj = list(po_obj_lunas) + list(po_obj_tidak_lunas)
#                 elif sort_by == "tidak_lunas":
#                     po_obj = list(po_obj_tidak_lunas) + list(po_obj_lunas)
#         else :
#             po_obj = models.DetailSuratJalanPembelian.objects.filter(
#                 NoSuratJalan__PO=input_po
#             )
#         if len(po_obj) == 0 :
#             messages.error(request, "Data tidak ditemukan")
#             return redirect('read_po')
#         else :
#             return render(
#                 request,
#                 "Purchasing/read_po.html",
#                 {"po_obj": po_obj,
#                  "input_po" :input_po})
# return render(
# request,
# "Purchasing/read_po.html",
# {"po_obj": po_obj,
#     "input_po": input_po}
# )


# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def read_po(request):
    print(request.GET)
    if len(request.GET) == 0:
        po_objall = models.SuratJalanPembelian.objects.all()
        return render(request, "Purchasing/read_po.html", {"po_objall": po_objall})
    else:
        input_po = request.GET["input_po"]
        po_obj = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__PO=input_po
        )
        for item in po_obj:
            item.NoSuratJalan.Tanggal = item.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
        if len(po_obj) == 0:
            messages.error(request, "Data tidak ditemukan")
            return redirect("read_po")
        else:
            return render(
                request,
                "Purchasing/read_po.html",
                {"po_obj": po_obj, "input_po": input_po},
            )


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


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def read_spk(request):
    dataspk = models.SPK.objects.all()
    for spk in dataspk:
        if spk.StatusDisplay == False:
            detailspk = models.DetailSPK.objects.filter(NoSPK=spk.id)
        else:
            detailspk = models.DetailSPKDisplay.objects.filter(NoSPK=spk.id)
        spk.detailspk = detailspk
        spk.Tanggal = spk.Tanggal.strftime("%Y-%m-%d")
    return render(request, "Purchasing/read_spk.html", {"dataspk": dataspk})


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def track_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    if dataspk.StatusDisplay == False:
        datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)
    else:
        datadetail = models.DetailSPKDisplay.objects.filter(NoSPK=dataspk.id)
    if dataspk.StatusDisplay == True:

        # Data SPK terkait yang telah di request ke Gudang
        transaksigudangobj = models.TransaksiGudang.objects.filter(
            DetailSPKDisplay__NoSPK=dataspk.id, jumlah__gte=0
        )

        # Data SPK Terkait yang telah jadi di FG
        transaksiproduksiobj = models.TransaksiProduksi.objects.filter(
            DetailSPK__NoSPK=dataspk.id, Jenis="Mutasi"
        )

        # Data SPK Terkait yang telah dikirim
        sppbobj = models.DetailSPPB.objects.filter(DetailSPKDisplay__NoSPK=dataspk.id)
        rekapjumlahpermintaanperbahanbaku = transaksigudangobj.values(
            "KodeProduk__KodeProduk", "KodeProduk__NamaProduk", "KodeProduk__unit"
        ).annotate(total=Sum("jumlah"))
        rekapjumlahpengirimanperartikel = sppbobj.values(
            "DetailSPKDisplay__KodeDisplay__KodeDisplay"
        ).annotate(total=Sum("Jumlah"))
    else:
        # Data SPK terkait yang telah di request ke Gudang
        transaksigudangobj = models.TransaksiGudang.objects.filter(
            DetailSPK__NoSPK=dataspk.id, jumlah__gte=0
        )

        # Data SPK Terkait yang telah jadi di FG
        transaksiproduksiobj = models.TransaksiProduksi.objects.filter(
            DetailSPK__NoSPK=dataspk.id, Jenis="Mutasi"
        )

        # Data SPK Terkait yang telah dikirim
        sppbobj = models.DetailSPPB.objects.filter(DetailSPK__NoSPK=dataspk.id)
        rekapjumlahpermintaanperbahanbaku = transaksigudangobj.values(
            "KodeProduk__KodeProduk", "KodeProduk__NamaProduk", "KodeProduk__unit"
        ).annotate(total=Sum("jumlah"))
        rekapjumlahpengirimanperartikel = sppbobj.values(
            "DetailSPK__KodeArtikel__KodeArtikel"
        ).annotate(total=Sum("Jumlah"))

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")

    print(transaksigudangobj)

    return render(
        request,
        "purchasing/trackspk.html",
        {
            "data": dataartikel,
            "datadisplay": datadisplay,
            "dataspk": dataspk,
            "datadetail": datadetail,
            "tanggal": tanggal,
            "transaksigudang": transaksigudangobj,
            "transaksiproduksi": transaksiproduksiobj,
            "transaksikeluar": sppbobj,
            "datarekappermintaanbahanbaku": rekapjumlahpermintaanperbahanbaku,
            "datarekappengiriman": rekapjumlahpengirimanperartikel,
        },
    )


# SPPB
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def view_sppb(request):
    datasppb = models.SPPB.objects.all().order_by("-Tanggal")
    for i in datasppb:
        i.detailsppb = models.DetailSPPB.objects.filter(NoSPPB = i)
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")
    return render(request, "Purchasing/view_sppb2.html", {"datasppb": datasppb})


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def add_sppb(request):
    datadetailspk = models.DetailSPK.objects.all()
    if request.method == "GET":
        return render(request, "Purchasing/add_sppb2.html", {"data": datadetailspk})

    if request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]

        datasppb = models.SPPB.objects.filter(NoSPPB=nomor_sppb).exists()
        if datasppb:
            messages.error(request, "Nomor SPPB sudah ada")
            return redirect("add_sppb")
        else:
            messages.success(request, "Data berhasil disimpan")
            data_sppb = models.SPPB(
                NoSPPB=nomor_sppb, Tanggal=tanggal, Keterangan=keterangan
            ).save()

            artikel_list = request.POST.getlist("artikel[]")
            jumlah_list = request.POST.getlist("quantity[]")
            no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

            for artikel, jumlah in zip(artikel_list, jumlah_list):
                # Pisahkan KodeArtikel dari jumlah dengan delimiter '/'
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel)
                jumlah_produk = jumlah

                # Simpan data ke dalam model DetailSPK
                datadetailspk = models.DetailSPPB(
                    NoSPPB=no_sppb, DetailSPK=kode_artikel, Jumlah=jumlah_produk
                )
                datadetailspk.save()

            return redirect("view_sppb2")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def detail_sppb(request, id):
    datadetailspk = models.DetailSPK.objects.all()
    datasppb = models.SPPB.objects.get(id=id)
    datadetailsppb = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id)

    if request.method == "GET":
        tanggal = datetime.strftime(datasppb.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "Purchasing/detail_sppb2.html",
            {
                "data": datadetailspk,
                "datasppb": datasppb,
                "datadetail": datadetailsppb,
                "tanggal": tanggal,
            },
        )

    elif request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggall = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        artikel_list = request.POST.getlist("artikel[]")
        jumlah_list = request.POST.getlist("quantity[]")

        datasppb.NoSPPB = nomor_sppb
        datasppb.Tanggal = tanggall
        datasppb.Keterangan = keterangan
        datasppb.save()

        for detail, artikel_id, jumlah in zip(
            datadetailsppb, artikel_list, jumlah_list
        ):
            kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
            detail.DetailSPK = kode_artikel
            detail.Jumlah = jumlah
            detail.save()

        no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

        for artikel_id, jumlah in zip(
            artikel_list[len(datadetailsppb) :], jumlah_list[len(datadetailsppb) :]
        ):
            kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
            new_detail = models.DetailSPPB.objects.create(
                NoSPPB=no_sppb,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                DetailSPK=kode_artikel,
                Jumlah=jumlah,
            )
            try:
                new_detail.save()
            except IntegrityError:
                # Handle if there's any IntegrityError, such as violating unique constraint
                pass

        return redirect("view_sppb2")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def delete_sppb(request, id):
    print(id)
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("view_sppb2")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def delete_detailsppb(request, id):
    datadetailsppb = models.DetailSPPB.objects.get(IDDetailSPPB=id)
    datasppb = models.SPPB.objects.get(NoSPPB=datadetailsppb.NoSPPB)
    datadetailsppb.delete()
    return redirect("detail_sppb2", id=datasppb.id)


# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
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


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def views_penyusun(request):
    print(request.GET)
    data = request.GET
    if len(request.GET) == 0:
        data = models.Artikel.objects.all()

        return render(request, "Purchasing/penyusun.html", {"dataartikel": data})
    else:
        kodeartikel = request.GET["kodeartikel"]

        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
            data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
            dataversi = data.values_list("versi", flat=True).distinct()
            print(dataversi)
            if dataversi.exists():
                try:
                    if request.GET["versi"] == "":
                        versiterpilih = dataversi.order_by("-versi").first()
                        print("ini versi terbaru", versiterpilih)
                        versiterpilih = versiterpilih.strftime("%Y-%m-%d")
                    else:
                        versiterpilih = request.GET["versi"]
                except:
                    versiterpilih = dataversi.order_by("-versi").first()
                    print("ini versi terbaru", versiterpilih)
                    versiterpilih.strftime("%Y-%m-%d")

                data = data.filter(versi=versiterpilih)
                dataversi = [date.strftime("%Y-%m-%d") for date in dataversi]
                print(dataversi)
                datakonversi = []
                nilaifg = 0
                print(data)
                if data.exists():
                    for item in data:
                        print(item, item.IDKodePenyusun)
                        konversidataobj = models.KonversiMaster.objects.get(
                            KodePenyusun=item.IDKodePenyusun
                        )
                        # print(konversidataobj.Kuantitas)
                        masukobj = models.DetailSuratJalanPembelian.objects.filter(
                            KodeProduk=item.KodeProduk
                        )
                        # print("ini detail sjp", masukobj)
                        tanggalmasuk = masukobj.values_list(
                            "NoSuratJalan__Tanggal", flat=True
                        )
                        keluarobj = models.TransaksiGudang.objects.filter(
                            jumlah__gte=0, KodeProduk=item.KodeProduk
                        )
                        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                        # print(item)
                        saldoawalobj = (
                            models.SaldoAwalBahanBaku.objects.filter(
                                IDBahanBaku=item.KodeProduk.KodeProduk
                            )
                            .order_by("-Tanggal")
                            .first()
                        )
                        if saldoawalobj:
                            # print(saldoawalobj)
                            saldoawal = saldoawalobj.Jumlah
                            hargasatuanawal = saldoawalobj.Harga
                            hargatotalawal = saldoawal * hargasatuanawal
                        else:
                            saldoawal = 0
                            hargasatuanawal = 0
                            hargatotalawal = saldoawal * hargasatuanawal

                        hargaterakhir = 0
                        listdata = []
                        listtanggal = sorted(
                            list(set(tanggalmasuk.union(tanggalkeluar)))
                        )
                        # print("inii", listtanggal)
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
                                hargamasuksatuanperhari += (
                                    hargamasuktotalperhari / jumlahmasukperhari
                                )
                            else:
                                hargamasuktotalperhari = 0
                                jumlahmasukperhari = 0
                                hargamasuksatuanperhari = 0

                            transaksigudangobj = keluarobj.filter(tanggal=i)
                            # print(transaksigudangobj)
                            if transaksigudangobj.exists():
                                for j in transaksigudangobj:
                                    jumlahkeluarperhari += j.jumlah
                                    hargakeluartotalperhari += (
                                        j.jumlah * hargasatuanawal
                                    )
                                hargakeluarsatuanperhari += (
                                    hargakeluartotalperhari / jumlahkeluarperhari
                                )
                            else:
                                hargakeluartotalperhari = 0
                                hargakeluarsatuanperhari = 0
                                jumlahkeluarperhari = 0

                            saldoawal += jumlahmasukperhari - jumlahkeluarperhari
                            hargatotalawal += (
                                hargamasuktotalperhari - hargakeluartotalperhari
                            )
                            try:

                                hargasatuanawal = hargatotalawal / saldoawal
                            except:
                                hargasatuanawal = 0

                            # print("ini hargasatuan awal : ", hargasatuanawal)

                        hargaterakhir += hargasatuanawal
                        kuantitaskonversi = konversidataobj.Kuantitas
                        kuantitasallowance = konversidataobj.Allowance
                        hargaperkotak = hargaterakhir * kuantitasallowance
                        # print("\n", hargaterakhir, "\n")
                        nilaifg += hargaperkotak

                        datakonversi.append(
                            {
                                "HargaSatuan": round(hargaterakhir, 2),
                                "Penyusunobj": item,
                                "Konversi": round(kuantitaskonversi, 5),
                                "Allowance": round(kuantitasallowance, 5),
                                "Hargakotak": round(hargaperkotak, 2),
                            }
                        )


                    return render(
                        request,
                        "Purchasing/penyusun.html",
                        {
                            "data": datakonversi,
                            "kodeartikel": get_id_kodeartikel,
                            "nilaifg": nilaifg,
                            "versiterpilih": versiterpilih,
                            "dataversi": dataversi,
                        },
                    )
            else:
                messages.error(request, "Kode Artikel Belum memiliki penyusun")
                return render(
                    request,
                    "Purchasing/penyusun.html",
                    {"kodeartikel": get_id_kodeartikel},
                )
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return render(
                request,
                "Purchasing/penyusun.html",
                {"dataartikel": models.Artikel.objects.all()},
            )
    # batas
    # print(request.GET)
    # data = request.GET
    # if len(request.GET) == 0:
    #     data = models.Artikel.objects.all()
    #     return render(request, "Purchasing/penyusun.html", {"dataartikel": data})
    # else:
    #     kodeartikel = request.GET["kodeartikel"]
    #     try:
    #         get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
    #         data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
    #         datakonversi = []
    #         nilaifg = 0
    #         if data.exists():
    #             for item in data:
    #                 konversidataobj = models.KonversiMaster.objects.get(
    #                     KodePenyusun=item.IDKodePenyusun
    #                 )
    #                 print(konversidataobj.Kuantitas)
    #                 masukobj = models.DetailSuratJalanPembelian.objects.filter(
    #                     KodeProduk=item.KodeProduk
    #                 )
    #                 print("ini detail sjp", masukobj)
    #                 tanggalmasuk = masukobj.values_list(
    #                     "NoSuratJalan__Tanggal", flat=True
    #                 )
    #                 keluarobj = models.TransaksiGudang.objects.filter(
    #                     jumlah__gte=0, KodeProduk=item.KodeProduk
    #                 )
    #                 tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
    #                 print(item)
    #                 saldoawalobj = (
    #                     models.SaldoAwalBahanBaku.objects.filter(
    #                         IDBahanBaku=item.KodeProduk.KodeProduk
    #                     )
    #                     .order_by("-Tanggal")
    #                     .first()
    #                 )
    #                 if saldoawalobj:
    #                     print(saldoawalobj)
    #                     saldoawal = saldoawalobj.Jumlah
    #                     hargasatuanawal = saldoawalobj.Harga
    #                     hargatotalawal = saldoawal * hargasatuanawal
    #                 else:
    #                     saldoawal = 0
    #                     hargasatuanawal = 0
    #                     hargatotalawal = saldoawal * hargasatuanawal

    #                 hargaterakhir = 0
    #                 listdata = []
    #                 listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
    #                 print("inii", listtanggal)
    #                 for i in listtanggal:
    #                     jumlahmasukperhari = 0
    #                     hargamasuktotalperhari = 0
    #                     hargamasuksatuanperhari = 0
    #                     jumlahkeluarperhari = 0
    #                     hargakeluartotalperhari = 0
    #                     hargakeluarsatuanperhari = 0
    #                     sjpobj = masukobj.filter(NoSuratJalan__Tanggal=i)
    #                     if sjpobj.exists():
    #                         for j in sjpobj:
    #                             hargamasuktotalperhari += j.Harga * j.Jumlah
    #                             jumlahmasukperhari += j.Jumlah
    #                         hargamasuksatuanperhari += (
    #                             hargamasuktotalperhari / jumlahmasukperhari
    #                         )
    #                     else:
    #                         hargamasuktotalperhari = 0
    #                         jumlahmasukperhari = 0
    #                         hargamasuksatuanperhari = 0

    #                     transaksigudangobj = keluarobj.filter(tanggal=i)
    #                     print(transaksigudangobj)
    #                     if transaksigudangobj.exists():
    #                         for j in transaksigudangobj:
    #                             jumlahkeluarperhari += j.jumlah
    #                             hargakeluartotalperhari += j.jumlah * hargasatuanawal
    #                         hargakeluarsatuanperhari += (
    #                             hargakeluartotalperhari / jumlahkeluarperhari
    #                         )
    #                     else:
    #                         hargakeluartotalperhari = 0
    #                         hargakeluarsatuanperhari = 0
    #                         jumlahkeluarperhari = 0

    #                     saldoawal += jumlahmasukperhari - jumlahkeluarperhari
    #                     hargatotalawal += (
    #                         hargamasuktotalperhari - hargakeluartotalperhari
    #                     )
    #                     hargasatuanawal = hargatotalawal / saldoawal

    #                     print("ini hargasatuan awal : ", hargasatuanawal)

    #                 hargaterakhir += hargasatuanawal
    #                 kuantitaskonversi = konversidataobj.Kuantitas
    #                 kuantitasallowance = kuantitaskonversi + kuantitaskonversi * 0.025
    #                 hargaperkotak = hargaterakhir * kuantitasallowance
    #                 print("\n", hargaterakhir, "\n")
    #                 nilaifg += hargaperkotak

    #                 datakonversi.append(
    #                     {
    #                         "HargaSatuan": round(hargaterakhir, 2),
    #                         "Penyusunobj": item,
    #                         "Konversi": round(kuantitaskonversi, 5),
    #                         "Allowance": round(kuantitasallowance, 5),
    #                         "Hargakotak": round(hargaperkotak, 2),
    #                     }
    #                 )

    #             print(data)
    #             print(datakonversi)
    #             return render(
    #                 request,
    #                 "Purchasing/penyusun.html",
    #                 {
    #                     "data": datakonversi,
    #                     "kodeartikel": get_id_kodeartikel,
    #                     "nilaifg": nilaifg,
    #                 },
    #             )
    #         else:
    #             messages.error(request, "Kode Artikel Belum memiliki penyusun")
    #             return render(
    #                 request,
    #                 "Purchasing/penyusun.html",
    #                 {"kodeartikel": get_id_kodeartikel},
    #             )
    #     except models.Artikel.DoesNotExist:
    #         messages.error(request, "Kode Artikel Tidak ditemukan")
    #         return render(request, "Purchasing/penyusun.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def kebutuhan_barang(request):
    list_q_gudang = []
    list_hasil_conv = []
    list_q_akhir = []
    list_kode_art = []
    if len(request.GET) == 0:
        spkall = models.SPK.objects.filter(StatusAktif=True)
        return render(request, "Purchasing/kebutuhan_barang.html", {"spkall": spkall})
    else:
        inputno_spk = request.GET["inputno_spk"]
        try:
            getspk = models.SPK.objects.get(NoSPK=inputno_spk)
        except ObjectDoesNotExist:
            messages.error(request, "Nomor SPK tidak ditemukan atau sudah tidak aktif")
            return redirect("kebutuhan_barang")

        filterspk = models.DetailSPK.objects.filter(NoSPK=getspk.id).filter(
            NoSPK__StatusAktif=True
        )

        if len(filterspk) == 0:
            messages.error(request, "Nomor SPK tidak ditemukan atau sudah tidak aktif")
            return redirect("kebutuhan_barang")
        else:
            dataspk = (
                models.DetailSPK.objects.filter(NoSPK=getspk.id)
                .annotate(kuantitas2=Sum("Jumlah"))
                .order_by()
            )

            for item in dataspk:
                art_code = (
                    item.KodeArtikel
                )  # Ini bukan objek Artikel, tapi kode artikel itu sendiri
                # artikel1 = models.Artikel.objects.get(KodeArtikel=art_code)  # Ambil objek Artikel berdasarkan kode
                artikel = art_code.KodeArtikel
                jumlah_art = item.kuantitas2
                list_kode_art.append(
                    {
                        "Kode_Artikel": artikel,
                        "Jumlah_Artikel": jumlah_art,
                    }  # Gunakan objek Artikel
                )

            if request.method == "POST":
                list_nama_art = request.POST.getlist("artikel[]")
                list_jumlah_art = request.POST.getlist("quantity[]")

                print("list nama", list_nama_art)
                print("list jumlah", list_jumlah_art)
                for item1, item2 in zip(list_nama_art, list_jumlah_art):
                   
                    kode_artikel_ada = False
                    jumlah_artikel = int(item2)
                    for i in list_kode_art:
                        if i["Kode_Artikel"] == item1:
                            i["Jumlah_Artikel"] += jumlah_artikel
                            kode_artikel_ada = True
                            break
                    if not kode_artikel_ada:
                        try:
                            artikelobj = models.Artikel.objects.get(KodeArtikel=item1)
                        except:
                            messages.error(request,f"Data artikel {item1} tidak ditemukan dalam sistem")
                            continue
                        list_kode_art.append(
                            {"Kode_Artikel": item1, "Jumlah_Artikel": jumlah_artikel}
                        )

                print(list_kode_art)

            artall = models.Artikel.objects.all()
            datasjb = (
                models.DetailSuratJalanPembelian.objects.values("KodeProduk")
                .annotate(kuantitas=Sum("Jumlah"))
                .order_by()
            )

            if len(datasjb) == 0:
                messages.error(request, "Tidak ada barang masuk ke gudang")

            datagudang = (
                models.TransaksiGudang.objects.values("KodeProduk")
                .annotate(kuantitas=Sum("jumlah"))
                .order_by()
            )

            for item in datasjb:
                kode_produk = item["KodeProduk"]
                try:
                    corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
                    item["kuantitas"] += corresponding_gudang_item["kuantitas"]
                    if item["kuantitas"] + corresponding_gudang_item["kuantitas"] < 0:
                        messages.info("Kuantitas gudang menjadi minus")

                except models.TransaksiGudang.DoesNotExist:
                    pass

                list_q_gudang.append({kode_produk: item["kuantitas"]})

            for item in list_kode_art:
                kodeArt = item["Kode_Artikel"]

                jumlah_art = item["Jumlah_Artikel"]
                try:

                    getidartikel = models.Artikel.objects.get(KodeArtikel=kodeArt)
                except:
                    messages.error(
                        request, f"Kode artikel {kodeArt} tidak ditemukan dalam sistem"
                    )
                    continue
                art_code = getidartikel

                try:
                    versipenyusunterakhir = models.Penyusun.objects.filter(KodeArtikel =art_code).order_by('-versi').first()
                    print(versipenyusunterakhir)
                    listpenyusun = models.Penyusun.objects.filter(KodeArtikel = art_code, versi = versipenyusunterakhir.versi).values_list('IDKodePenyusun',flat=True)

                    # print(asd)
                    konversi_art = (
                        models.KonversiMaster.objects.filter(
                            KodePenyusun__KodeArtikel=art_code, KodePenyusun__in=listpenyusun
                        )
                        .annotate(
                            kode_art=F("KodePenyusun__KodeArtikel__KodeArtikel"),
                            kode_produk=F("KodePenyusun__KodeProduk"),
                            nilai_konversi=F("Allowance"),
                            nama_bb=F("KodePenyusun__KodeProduk__NamaProduk"),
                        )
                        .values("kode_art", "kode_produk", "Kuantitas", "nama_bb")
                        .distinct()
                    )

                    for item2 in konversi_art:
                        kode_artikel = art_code.KodeArtikel
                        kode_produk = item2["kode_produk"]
                        nilai_conv = item2["Kuantitas"]
                        nama_bb = item2["nama_bb"]

                        hasil_conv = round(jumlah_art * nilai_conv)

                        list_hasil_conv.append(
                            {
                                "Kode Artikel": kode_artikel,
                                "Jumlah Artikel": jumlah_art,
                                "Kode Produk": kode_produk,
                                "Nama Produk": nama_bb,
                                "Hasil Konversi": hasil_conv,
                            }
                        )

                except models.KonversiMaster.DoesNotExist:
                    pass

            for item in list_hasil_conv:
                kode_produk = item["Kode Produk"]

                hasil_konversi = item["Hasil Konversi"]

                for item2 in list_q_gudang:

                    if kode_produk in item2:
                        gudang_jumlah = item2[kode_produk]
                        hasil_akhir = gudang_jumlah - hasil_konversi
                        list_q_akhir.append(
                            {
                                "Kode_Artikel": item["Kode Artikel"],
                                "Jumlah_Artikel": item["Jumlah Artikel"],
                                "Kode_Produk": kode_produk,
                                "Nama_Produk": item["Nama Produk"],
                                "Kebutuhan": hasil_konversi,
                                "Stok_Gudang": gudang_jumlah,
                                "Selisih": hasil_akhir,
                            }
                        )

            pengadaan = {}

            for item in list_q_akhir:
                produk = item["Kode_Produk"]
                pengadaan[produk] = [0, 0]

            for item in list_q_akhir:
                produk = item["Kode_Produk"]
                nama_produk = item["Nama_Produk"]
                selisih = item["Selisih"]
                if produk in pengadaan:
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] += selisih
                else:
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] = selisih

            rekap_pengadaan = {}

            for key, value in pengadaan.items():
                if value[1] < 0:
                    new_value = abs(value[1])
                    rekap_pengadaan[key] = [value[0], new_value]

            return render(
                request,
                "Purchasing/kebutuhan_barang.html",
                {
                    "artall": artall,
                    "filterspk": filterspk,
                    "list_kode_art": list_kode_art,
                    "inputno_spk": inputno_spk,
                    "list_q_akhir": list_q_akhir,
                    "rekap_pengadaan": rekap_pengadaan,
                },
            )


# # Coba v2


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def views_rekapharga(request):
    kodeprodukobj = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request, "Purchasing/views_ksbb.html", {"kodeprodukobj": kodeprodukobj}
        )
    else:
        kode_produk = request.GET["kode_produk"]
        tahun = request.GET["tahun"]
        tahun_period = tahun

        if tahun == "":
            tahun = datetime.now().year

        tahun = datetime.strptime(tahun, format("%Y"))
        awaltahun = datetime(tahun.year, 1, 1)
        akhirtahun = datetime(tahun.year, 12, 31)

        try:
            produkobj = models.Produk.objects.get(KodeProduk=kode_produk)
        except models.Produk.DoesNotExist:
            messages.error(request, "Kode bahan baku tidak ditemukan")
            return render(
                request, "Purchasing/views_ksbb.html", {"kodeprodukobj": kodeprodukobj}
            )
        masukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=produkobj.KodeProduk, NoSuratJalan__Tanggal__gte=awaltahun
        )

        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk=produkobj.KodeProduk, tanggal__gte=awaltahun
        )
        returobj = models.TransaksiGudang.objects.filter(
            jumlah__lt=0, KodeProduk=produkobj.KodeProduk, tanggal__gte=awaltahun
        )
        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
        tanggalretur = returobj.values_list("tanggal", flat=True)
        print("ini kode bahan baku", keluarobj)
        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku=produkobj.KodeProduk,
                IDLokasi__IDLokasi=3,
                Tanggal__range=(awaltahun,akhirtahun)
            )
            .order_by("-Tanggal")
            .first()
        )
        print(saldoawalobj)
        if (
            not keluarobj.exists()
            and not returobj.exists()
            and not masukobj.exists()
            and saldoawalobj is None
        ):
            messages.error(request, "Tidak ditemukan data Transaksi Barang")
            return redirect("rekapharga")
        # print(asdas)
        if saldoawalobj:
            print("ada data")
            saldoawal = saldoawalobj.Jumlah
            hargasatuanawal = saldoawalobj.Harga
            hargatotalawal = saldoawal * hargasatuanawal
            tahun = saldoawalobj.Tanggal.year

        else:
            saldoawal = 0
            hargasatuanawal = 0
            hargatotalawal = saldoawal * hargasatuanawal
            tahun = awaltahun.year

        saldoawalobj = {
            "saldoawal": saldoawal,
            "hargasatuanawal": hargasatuanawal,
            "hargatotalawal": hargatotalawal,
            'tahun' : tahun
        }
        hargaterakhir = 0
        listdata = []
        print(tanggalmasuk)
        print(tanggalkeluar)
        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalretur)))
        )
        print(listtanggal)
        statusmasuk = False
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
                print("data SJP ada")
                print(hargamasuksatuanperhari)
                print(jumlahmasukperhari)
                dumy = {
                    "Tanggal": i.strftime("%Y-%m-%d"),
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
                saldoawal += jumlahmasukperhari - jumlahkeluarperhari
                hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
                hargasatuanawal = hargatotalawal / saldoawal

                print("Sisa Stok Hari Ini : ", saldoawal)
                print("harga awal Hari Ini :", hargasatuanawal)
                print("harga total Hari Ini :", hargatotalawal, "\n")
                dumy["Sisahariini"] = saldoawal
                dumy["Hargasatuansisa"] = round(hargasatuanawal, 2)
                dumy["Hargatotalsisa"] = round(hargatotalawal, 2)
                print(dumy)
                statusmasuk = True
                listdata.append(dumy)
                # print(asdasd)

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
                if statusmasuk:
                    statusmasuk = False
                    continue
                hargakeluartotalperhari = 0
                hargakeluarsatuanperhari = 0
                jumlahkeluarperhari = 0

            transaksireturobj = returobj.filter(tanggal=i)
            if transaksireturobj.exists():
                for j in transaksireturobj:
                    jumlahmasukperhari += j.jumlah * -1
                    hargamasuktotalperhari += j.jumlah * hargasatuanawal * -1
                hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
            else:
                hargamasuktotalperhari = 0
                hargamasuksatuanperhari = 0
                jumlahmasukperhari = 0

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
                "Tanggal": i.strftime("%Y-%m-%d"),
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
            dummysaldoawal = saldoawal
            dummyhargatotalawal = hargatotalawal
            dummyhargasatuanawal = hargasatuanawal

            saldoawal += jumlahmasukperhari - jumlahkeluarperhari
            hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
            print(hargatotalawal, saldoawal)
            try:
                hargasatuanawal = hargatotalawal / saldoawal
            except:
                hargasatuanawal = 0

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
            "Purchasing/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
                "kode_produk": produkobj,
                "tahun": tahun_period,
            },
        )

@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def accspk2(request, id):

    accobj = models.SPK.objects.get(pk=id)
    accobj.KeteranganACC = True
    accobj.save()
    models.transactionlog(
        user="Purchasing",
        waktu=datetime.now(),
        jenis="ACC",
        pesan=f"No SPK {accobj.NoSPK} sudah ACC",
    ).save()
    messages.success(request, "SPK berhasil diacc")
    return redirect("read_spk")

'''

REVISI 6/12/2024
1. Update Harga Saldo Awal 
'''

def read_saldoawal(request):
    dataproduk = models.SaldoAwalBahanBaku.objects.all().order_by("-Tanggal")
    print(dataproduk)
    for i in dataproduk:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/read_saldoawalbahan.html", {"dataproduk": dataproduk}
    )

def update_saldoawal(request,id):
    databarang = models.Produk.objects.all()
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "Purchasing/update_saldobahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj, "databarang": databarang},
        )

    else:

        harga = request.POST["harga"]
        
        hargalama = dataobj.Harga
        dataobj.Harga = harga
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Update Harga Bahan Baku {dataobj.IDBahanBaku.KodeProduk}Jumlah lama {dataobj.Harga}, Jumlah baru {hargalama}",
        ).save()
        dataobj.save()
        messages.success(request, "Data berhasil disimpan")
        return redirect("saldobahanbakupurchasing")



def view_saldoartikel(request):
    dataartikel = models.SaldoAwalArtikel.objects.all().order_by("-Tanggal")
    for i in dataartikel:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/view_saldoartikel.html", {"dataartikel": dataartikel}
    )

def update_saldoartikel(request, id):
    dataartikel = models.Artikel.objects.all()
    dataobj = models.SaldoAwalArtikel.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "Purchasing/update_saldoartikel.html",
            {"data": dataobj, "nama_lokasi": lokasiobj[:2], "dataartikel": dataartikel},
        )

    else:
        artikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalArtikel.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDArtikel__KodeArtikel=artikel,
            IDLokasi=lokasi
        ).exclude(IDSaldoAwalBahanBaku=id).exists()

        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("update_saldoartikel",id=id)
        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=artikel)
            
        except:
            messages.error(request,f'Data artikel {artikel} tidak ditemukan dalam sistem')
            return redirect("update_saldoartikel",id=id)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDArtikel = artikelobj
        dataobj.IDLokasi= lokasiobj

        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Saldo Artikel. Kode Bahan Baku : {artikelobj.KodeArtikel} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldoartikel")
    
def bulk_createproduk(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        df = pd.read_excel(file, engine='openpyxl')
        df = df.fillna('-')
        for index,row in df.iterrows():
            bahanbakubaru = models.Produk(
                KodeProduk = row['Kode Stock'],
                NamaProduk = row['Nama Barang'],
                unit = row['Satuan'],
                TanggalPembuatan = datetime.now(),
                Jumlahminimal = 0,
                keteranganPurchasing = row['Keterangan']
            )
            print(bahanbakubaru.keteranganPurchasing)
            bahanbakubaru.save()
        return HttpResponse("Data successfully uploaded and processed!")
    
    return render(request, 'Purchasing/bulk_createproduk.html')


def bulk_createsjp(request):
    if request.method == "POST" and request.FILES["file"]:
        file = request.FILES["file"]
        excel_file = pd.ExcelFile(file)

        # Mendapatkan daftar nama sheet
        sheet_names = excel_file.sheet_names
        print(sheet_names)
        for item in sheet_names:
            data = models.Artikel(KodeArtikel=item, keterangan="-")
            print(data)
            data.save()
        return HttpResponse("Berhasil Upload")

    return render(request, "Purchasing/bulk_createproduk.html")

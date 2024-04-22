from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import F
from django.db.models import Sum
from . import models
from datetime import datetime
from django.db import IntegrityError
from urllib.parse import quote
from django.core.exceptions import ObjectDoesNotExist
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



def view_rekapbarang(request):
    if len(request.GET) == 0:
        return render(request, "Purchasing/rekapproduksi2.html")
    else:
        if request.GET['periode']:
            tahun = int(request.GET['periode'])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year
        
        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        kode_artikel_produk = (
            models.TransaksiProduksi.objects.filter(
                Jenis="Mutasi", Lokasi=1, Tanggal__range=(tanggal_mulai, tanggal_akhir)
            )
            .values("KodeArtikel")
            .annotate(kuantitas=Sum("Jumlah"))
        )

        # Ambil data penyusun berdasarkan kode artikel yang memiliki transaksi produksi
        penyusun_per_artikel = []
        for kode_artikel in kode_artikel_produk:
            penyusun = models.Penyusun.objects.filter(
                KodeArtikel=kode_artikel["KodeArtikel"]
            )
            konversi = models.KonversiMaster.objects.filter(KodePenyusun__in=penyusun)
            penyusun_per_artikel.append(
                {
                    "KodeArtikel": kode_artikel["KodeArtikel"],
                    "Jumlah": kode_artikel["kuantitas"],
                    "Penyusun": penyusun,
                    "Konversi": konversi,
                }
            )

        # Dictionary untuk menyimpan jumlah total untuk setiap kode produk penyusun
        total_per_produk = {}

        # Output data penyusun per kode artikel
        for item in penyusun_per_artikel:
            for penyusun in item["Penyusun"]:
                konversi = item["Konversi"].filter(KodePenyusun=penyusun)
                total_kuantitas = sum(konv.Kuantitas for konv in konversi) + (sum(konv.Kuantitas for konv in konversi)*2.5/100)
                total = total_kuantitas * item["Jumlah"]
                if penyusun.KodeProduk in total_per_produk:
                    total_per_produk[penyusun.KodeProduk] += total
                else:
                    total_per_produk[penyusun.KodeProduk] = total

        databarang = models.Produk.objects.all()

        datagudang = (
            models.TransaksiGudang.objects.filter(
                Lokasi=1, tanggal__range=(tanggal_mulai, tanggal_akhir)
            )
            .values("KodeProduk")
            .annotate(kuantitas=Sum("jumlah"))
        )

        datagudang = models.TransaksiGudang.objects.filter(Lokasi=1,tanggal__range=(tanggal_mulai,tanggal_akhir)).values('KodeProduk').annotate(kuantitas=Sum('jumlah'))

        # Output hasil perhitungan
        for barang in databarang:
            kode_produk = barang.KodeProduk
            kode = models.Produk.objects.get(KodeProduk=kode_produk)
            try:
                saldoawal = models.SaldoAwalBahanBaku.objects.get(IDBahanBaku=kode, IDLokasi=1,Tanggal__range=(tanggal_mulai,tanggal_akhir))
                saldo = saldoawal.Jumlah
            except models.SaldoAwalBahanBaku.DoesNotExist:
                saldo = 0

            kuantitas = saldo + next((item["kuantitas"] for item in datagudang if item["KodeProduk"] == kode_produk),0,)
            if kode in total_per_produk:
                kuantitas -= total_per_produk[kode]
            barang.kuantitas = round(kuantitas,4)

        return render(request, "Purchasing/rekapproduksi2.html", {"databarang": databarang})


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
                TanggalPembuatan = datetime.now(),
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



def rekap_gudang(request) :
    datasjb = models.DetailSuratJalanPembelian.objects.values('KodeProduk','KodeProduk__NamaProduk','KodeProduk__unit','KodeProduk__keterangan').annotate(kuantitas=Sum('Jumlah')).order_by()
    if len(datasjb) == 0 :
        messages.error(request, "Tidak ada barang masuk ke gudang")

    datagudang = models.TransaksiGudang.objects.values('KodeProduk').annotate(kuantitas=Sum('jumlah')).order_by()

    for item in datasjb:
        kode_produk = item['KodeProduk']
        try:
            corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
            item['kuantitas'] += corresponding_gudang_item['kuantitas']

            if item['kuantitas'] + corresponding_gudang_item['kuantitas'] < 0 :
                messages.info("Kuantitas gudang menjadi minus")

        except models.TransaksiGudang.DoesNotExist:
            pass
    
    return render(request,'Purchasing/rekapgudang2.html',{
        'datasjb' : datasjb,
    })

# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
def read_po(request) :
    print(request.GET)
    if len(request.GET) == 0 :
        po_objall = models.SuratJalanPembelian.objects.all()
        return render(request, "Purchasing/read_po.html",{'po_objall' :po_objall})
    else :
        input_po = request.GET["input_po"]
        po_obj = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__PO=input_po
        )
        if len(po_obj) == 0 :
            messages.error(request, "Data tidak ditemukan")
            return redirect('read_po')
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

def read_spk(request) :
    dataspk = models.DetailSPK.objects.all()
    # if len(dataspk) == 0 :
    #     return render(request,'',{"dataspk":dataspk})
    # else :
    return render(request,'Purchasing/read_spk.html',{"dataspk":dataspk})


# SPPB
def view_sppb(request):
    datasppb = models.SPPB.objects.all()

    return render(request, "Purchasing/view_sppb2.html", {"datasppb": datasppb})


def add_sppb(request):
    datadetailspk = models.DetailSPK.objects.all()
    if request.method == "GET":
        return render(request, "Purchasing/add_sppb2.html",{'data':datadetailspk})

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

            artikel_list = request.POST.getlist('artikel[]')
            jumlah_list = request.POST.getlist('quantity[]')
            no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

            for artikel, jumlah in zip(artikel_list, jumlah_list):
                # Pisahkan KodeArtikel dari jumlah dengan delimiter '/'
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel)
                jumlah_produk = jumlah
                
                # Simpan data ke dalam model DetailSPK
                datadetailspk = models.DetailSPPB(
                    NoSPPB=no_sppb,
                    DetailSPK=kode_artikel,
                    Jumlah=jumlah_produk
                )
                datadetailspk.save()

            return redirect("view_sppb2")


def detail_sppb(request,id):
    datadetailspk = models.DetailSPK.objects.all()
    datasppb = models.SPPB.objects.get(id=id)
    datadetailsppb = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id)

    if request.method == "GET":
        tanggal = datetime.strftime(datasppb.Tanggal, "%Y-%m-%d")

        return render(request,'Purchasing/detail_sppb2.html',{'data':datadetailspk,'datasppb':datasppb,'datadetail':datadetailsppb, 'tanggal':tanggal})
    
    elif request.method == 'POST':
        nomor_sppb = request.POST["nomor_sppb"]
        tanggall = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        artikel_list = request.POST.getlist('artikel[]')
        jumlah_list = request.POST.getlist('quantity[]')

        datasppb.NoSPPB = nomor_sppb
        datasppb.Tanggal = tanggall
        datasppb.Keterangan = keterangan
        datasppb.save()

        for detail, artikel_id, jumlah in zip(datadetailsppb, artikel_list, jumlah_list):
            kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
            detail.DetailSPK = kode_artikel
            detail.Jumlah = jumlah
            detail.save()

        no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

        for artikel_id, jumlah in zip(artikel_list[len(datadetailsppb):], jumlah_list[len(datadetailsppb):]):
            kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
            new_detail = models.DetailSPPB.objects.create(
                NoSPPB=no_sppb,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                DetailSPK=kode_artikel,
                Jumlah=jumlah
            )
            try:
                new_detail.save()
            except IntegrityError:
                # Handle if there's any IntegrityError, such as violating unique constraint
                pass
        
        return redirect('view_sppb2')


def delete_sppb(request, id):
    print(id)
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    messages.success(request,"Data Berhasil dihapus")
    return redirect("view_sppb2")

def delete_detailsppb(request, id):
    datadetailsppb = models.DetailSPPB.objects.get(IDDetailSPPB=id)
    datasppb = models.SPPB.objects.get(NoSPPB=datadetailsppb.NoSPPB)
    datadetailsppb.delete()
    return redirect('detail_sppb2', id=datasppb.id)

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
            datakonversi = []
            nilaifg = 0
            if data.exists():
                for item in data:
                    konversidataobj = models.KonversiMaster.objects.get(
                        KodePenyusun=item.IDKodePenyusun
                    )
                    print(konversidataobj.Kuantitas)
                    masukobj = models.DetailSuratJalanPembelian.objects.filter(
                        KodeProduk=item.KodeProduk
                    )
                    print("ini detail sjp", masukobj)
                    tanggalmasuk = masukobj.values_list(
                        "NoSuratJalan__Tanggal", flat=True
                    )
                    keluarobj = models.TransaksiGudang.objects.filter(
                        jumlah__gte=0, KodeProduk=item.KodeProduk
                    )
                    tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                    print(item)
                    saldoawalobj = (
                        models.SaldoAwalBahanBaku.objects.filter(
                            IDBahanBaku=item.KodeProduk.KodeProduk
                        )
                        .order_by("-Tanggal")
                        .first()
                    )
                    if saldoawalobj:
                        print(saldoawalobj)
                        saldoawal = saldoawalobj.Jumlah
                        hargasatuanawal = saldoawalobj.Harga
                        hargatotalawal = saldoawal * hargasatuanawal
                    else:
                        saldoawal = 0
                        hargasatuanawal = 0
                        hargatotalawal = saldoawal * hargasatuanawal

                    hargaterakhir = 0
                    listdata = []
                    listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
                    print("inii", listtanggal)
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

                        saldoawal += jumlahmasukperhari - jumlahkeluarperhari
                        hargatotalawal += (
                            hargamasuktotalperhari - hargakeluartotalperhari
                        )
                        hargasatuanawal = hargatotalawal / saldoawal

                        print("ini hargasatuan awal : ", hargasatuanawal)

                    hargaterakhir += hargasatuanawal
                    kuantitaskonversi = konversidataobj.Kuantitas
                    kuantitasallowance = kuantitaskonversi + kuantitaskonversi * 0.025
                    hargaperkotak = hargaterakhir * kuantitasallowance
                    print("\n", hargaterakhir, "\n")
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

                print(data)
                print(datakonversi)
                return render(
                    request,
                    "Purchasing/penyusun.html",
                    {
                        "data": datakonversi,
                        "kodeartikel": get_id_kodeartikel,
                        "nilaifg": nilaifg,
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
            return render(request, "Purchasing/penyusun.html")
        

def kebutuhan_barang (request) :
    list_q_gudang = []
    list_hasil_conv = []
    list_q_akhir=[]
    list_kode_art = []
    if len(request.GET)==0 :
        spkall = models.SPK.objects.all()
        return render(request, "Purchasing/kebutuhan_barang.html",
                       {'spkall' :spkall})
    else :
        inputno_spk = request.GET["inputno_spk"]
        try :
            getspk = models.SPK.objects.get(NoSPK = inputno_spk)
        except ObjectDoesNotExist :
            messages.error(request,"Nomor SPK Tidak Ditemukan")
            return redirect("kebutuhan_barang")

        filterspk = models.DetailSPK.objects.filter(NoSPK=getspk.id)
        
        if len(filterspk)==0:
            messages.error(request,"Nomor SPK Tidak Ditemukan")
            return redirect("kebutuhan_barang")
        else  :
            if request.method == 'POST' :
                input_nama_art = request.POST['input_nama_art']
                input_jumlah_art2 = request.POST['input_jumlah_art']
                input_jumlah_art = int(input_jumlah_art2)
                # found = False
                # for item in list_kode_art :
                #     kode_artikel = item["Kode_Artikel"]
                #     if input_nama_art == kode_artikel :
                #         item["Jumlah_Artikel"] = input_jumlah_art
                #         found = True
                #         break
                # if not found :
                list_kode_art.append(
                    {"Kode_Artikel" : input_nama_art,
                    "Jumlah_Artikel" : input_jumlah_art}
                )
                print("INi list kode art1",list_kode_art)
            # if request == 'GET' : 
            artall = models.Artikel.objects.all()        
            datasjb = models.DetailSuratJalanPembelian.objects.values('KodeProduk').annotate(kuantitas=Sum('Jumlah')).order_by()
            print("data sjb :",datasjb)

            if len(datasjb) == 0 :
                messages.error(request, "Tidak ada barang masuk ke gudang")

            datagudang = models.TransaksiGudang.objects.values('KodeProduk').annotate(kuantitas=Sum('jumlah')).order_by()

            for item in datasjb:
                kode_produk = item['KodeProduk']
                try:
                    corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
                    item['kuantitas'] +=corresponding_gudang_item['kuantitas']
                    if item['kuantitas'] + corresponding_gudang_item['kuantitas'] < 0 :
                        messages.info("Kuantitas gudang menjadi minus")
                    
                except models.TransaksiGudang.DoesNotExist:
                    pass

                list_q_gudang.append(
                    {kode_produk:item['kuantitas']}
                    )
            dataspk = models.DetailSPK.objects.filter(NoSPK=getspk.id).annotate(kuantitas2 = Sum('Jumlah')).order_by()
            for item in dataspk :
                art_code = item.KodeArtikel
                jumlah_art = item.kuantitas2
                list_kode_art.append(
                    {"Kode_Artikel" : art_code,
                    "Jumlah_Artikel" :jumlah_art
                    }
                )
            print("LIST KODE ART",list_kode_art)
            for item in list_kode_art :
            
                art_code = item["Kode_Artikel"]
                jumlah_art = item["Jumlah_Artikel"]
                print("jumlah artikel:",jumlah_art)
                print("Kode artikel :",art_code)
                try :
                    konversi_art = models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel = art_code).annotate(kode_art = F('KodePenyusun__KodeArtikel'),kode_produk =F('KodePenyusun__KodeProduk'),nilai_konversi=F('Kuantitas'),nama_bb = F('KodePenyusun__KodeProduk__NamaProduk')).values('kode_art','kode_produk','Kuantitas','nama_bb').distinct()
                    print("ini konversi",konversi_art)
                
                    
                    for item2 in konversi_art :
                        kode_artikel = art_code
                        kode_produk = item2['kode_produk']
                        nilai_conv = item2['Kuantitas']
                        nama_bb = item2['nama_bb']
                        print("Nilai conv", nilai_conv)
                        hasil_conv = round(jumlah_art*nilai_conv)
                        print(hasil_conv)

                        list_hasil_conv.append(
                            {'Kode Artikel' : kode_artikel,
                            'Jumlah Artikel' : jumlah_art,
                            'Kode Produk' : kode_produk,
                            'Nama Produk' : nama_bb,
                            'Hasil Konversi' : hasil_conv
                            }
                        )
                    
                    print("list hasil conv",list_hasil_conv)
                except models.KonversiMaster.DoesNotExist :
                    pass
            
            for item in list_hasil_conv:
                kode_produk = item['Kode Produk']
                hasil_konversi = item['Hasil Konversi']
                for item2 in list_q_gudang :
                    if kode_produk in item2 :
                        gudang_jumlah = item2[kode_produk]

                        hasil_akhir = gudang_jumlah-hasil_konversi
                        list_q_akhir.append(
                            {'Kode_Artikel' : item['Kode Artikel'],
                            'Jumlah_Artikel' : item['Jumlah Artikel'],
                            'Kode_Produk' : kode_produk,
                            'Nama_Produk' : item['Nama Produk'],
                            'Kebutuhan' : hasil_konversi,
                            'Stok_Gudang' : gudang_jumlah,
                            'Selisih' : hasil_akhir
                            }
                        )
                
            
            pengadaan = {}

            for item in list_q_akhir :
                produk = item['Kode_Produk']
                pengadaan[produk] = [0,0]

            for item in list_q_akhir :
                produk = item['Kode_Produk']
                nama_produk = item['Nama_Produk']
                selisih = item['Selisih']
                if produk in pengadaan :
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] += selisih
                else :
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] = selisih
                
                
            rekap_pengadaan = {}

            for key, value in pengadaan.items():
                if value[1] < 0:
                    new_value = abs(value[1])
                    rekap_pengadaan[key] = [value[0], new_value]

        
            
            print("Imi list kode art2",list_kode_art)
            return render(request,"Purchasing/kebutuhan_barang.html",
                        {'artall' :artall,
                        'filterspk':filterspk,
                        'list_kode_art' :list_kode_art,
                        'inputno_spk':inputno_spk,
                        'list_q_akhir' : list_q_akhir,
                        'rekap_pengadaan' : rekap_pengadaan
                        })
        # else :
            #     # BATAS
            #     datasjb = models.DetailSuratJalanPembelian.objects.values('KodeProduk').annotate(kuantitas=Sum('Jumlah')).order_by()
            #     print("data sjb :",datasjb)

            #     if len(datasjb) == 0 :
            #         messages.error(request, "Tidak ada barang masuk ke gudang")

            #     datagudang = models.TransaksiGudang.objects.values('KodeProduk').annotate(kuantitas=Sum('jumlah')).order_by()

            #     for item in datasjb:
            #         kode_produk = item['KodeProduk']
            #         try:
            #             corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
            #             item['kuantitas'] +=corresponding_gudang_item['kuantitas']
            #             if item['kuantitas'] + corresponding_gudang_item['kuantitas'] < 0 :
            #                 messages.info("Kuantitas gudang menjadi minus")
                        
            #         except models.TransaksiGudang.DoesNotExist:
            #             pass

            #         list_q_gudang.append(
            #             {kode_produk:item['kuantitas']}
            #             )

            
            #     input_nama_art = request.POST['input_nama_art']
            #     input_jumlah_art = request.POST['input_jumlah_art']
                
            #     artall = models.Artikel.objects.all()

            #     if len(input_nama_art) or len(input_jumlah_art) != 0 :
            #         list_kode_art.append(
            #             {input_nama_art : input_jumlah_art}
            #         )
            #     dataspk = models.DetailSPK.objects.filter(NoSPK=getspk.id).annotate(kuantitas2 = Sum('Jumlah')).order_by()
            #     for item in dataspk :
            #         art_code = item.KodeArtikel
            #         jumlah_art = item.kuantitas2
            #         list_kode_art.append(
            #             {'Kode_Artikel' : art_code,
            #             "Jumlah_Artikel" :jumlah_art
            #             }
            #         )
            #     print("data spk :",dataspk)
                
            #     for item in list_kode_art :
                
            #         art_code = item['Kode_Artikel']
            #         jumlah_art = item['Jumlah_Artikel']
            #         print("jumlah artikel:",jumlah_art)
            #         print("Kode artikel :",art_code)
            #         try :
            #             konversi_art = models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel = art_code).annotate(kode_art = F('KodePenyusun__KodeArtikel'),kode_produk =F('KodePenyusun__KodeProduk'),nilai_konversi=F('Kuantitas'),nama_bb = F('KodePenyusun__KodeProduk__NamaProduk')).values('kode_art','kode_produk','Kuantitas','nama_bb').distinct()
            #             print("ini konversi",konversi_art)
                    
                        
            #             for item2 in konversi_art :
            #                 kode_artikel = art_code
            #                 kode_produk = item2['kode_produk']
            #                 nilai_conv = item2['Kuantitas']
            #                 nama_bb = item2['nama_bb']
            #                 print("Nilai conv", nilai_conv)
            #                 hasil_conv = round(jumlah_art*nilai_conv)
            #                 print(hasil_conv)

            #                 list_hasil_conv.append(
            #                     {'Kode Artikel' : kode_artikel,
            #                     'Jumlah Artikel' : jumlah_art,
            #                     'Kode Produk' : kode_produk,
            #                     'Nama Produk' : nama_bb,
            #                     'Hasil Konversi' : hasil_conv
            #                     }
            #                 )
                        
            #             print("list hasil conv",list_hasil_conv)
            #         except models.KonversiMaster.DoesNotExist :
            #             pass
                
            #     for item in list_hasil_conv:
            #         kode_produk = item['Kode Produk']
            #         hasil_konversi = item['Hasil Konversi']
            #         for item2 in list_q_gudang :
            #             if kode_produk in item2 :
            #                 gudang_jumlah = item2[kode_produk]

            #                 hasil_akhir = gudang_jumlah-hasil_konversi
            #                 list_q_akhir.append(
            #                     {'Kode_Artikel' : item['Kode Artikel'],
            #                     'Jumlah_Artikel' : item['Jumlah Artikel'],
            #                     'Kode_Produk' : kode_produk,
            #                     'Nama_Produk' : item['Nama Produk'],
            #                     'Kebutuhan' : hasil_konversi,
            #                     'Stok_Gudang' : gudang_jumlah,
            #                     'Selisih' : hasil_akhir
            #                     }
            #                 )
                    
                
            #     pengadaan = {}

            #     for item in list_q_akhir :
            #         produk = item['Kode_Produk']
            #         pengadaan[produk] = [0,0]

            #     for item in list_q_akhir :
            #         produk = item['Kode_Produk']
            #         nama_produk = item['Nama_Produk']
            #         selisih = item['Selisih']
            #         if produk in pengadaan :
            #             pengadaan[produk][0] = nama_produk
            #             pengadaan[produk][1] += selisih
            #         else :
            #             pengadaan[produk][0] = nama_produk
            #             pengadaan[produk][1] = selisih
                    
                    
            #     rekap_pengadaan = {}

            #     for key, value in pengadaan.items():
            #         if value[1] < 0:
            #             new_value = abs(value[1])
            #             rekap_pengadaan[key] = [value[0], new_value]

            
                

            #     return render(request,"Purchasing/kebutuhan_barang.html",
            #                 {'artall' :artall,
            #                 'filterspk':filterspk,
            #                 'list_kode_art' :list_kode_art,
            #                 'inputno_spk':inputno_spk,
            #                 'list_q_akhir' : list_q_akhir,
            #                 'rekap_pengadaan' : rekap_pengadaan
            #                 })

def kebutuhan_barang2(request) :
    list_q_gudang = []
    list_hasil_conv = []
    list_q_akhir=[]
    list_kode_art = []
     
    if len(request.GET)==0 :
        spkall = models.SPK.objects.all()
        artall = models.Artikel.objects.all()
        return render(request, "Purchasing/kebutuhan_barang.html",
                       {'spkall' :spkall,
                        'artall' :artall
                        })
    else :
        inputno_spk = request.GET["inputno_spk"]
        try :
            getspk = models.SPK.objects.get(NoSPK = inputno_spk)
        except ObjectDoesNotExist :
            messages.error(request,"Nomor SPK Tidak Ditemukan")
            return redirect("kebutuhan_barang")

        filterspk = models.DetailSPK.objects.filter(NoSPK=getspk.id)
        
        if len(filterspk)==0:
            messages.error(request,"Nomor SPK Tidak Ditemukan")
            return redirect("kebutuhan_barang")
        else :
            input_nama_art = request.get['input_nama_art']
            input_jumlah_art = request.get['input_jumlah_art']
                        
            if len(input_nama_art) or len(input_jumlah_art) != 0 :
                list_kode_art.append(
                    {input_nama_art : input_jumlah_art}
                )
            dataspk = models.DetailSPK.objects.filter(NoSPK=getspk.id).annotate(kuantitas2 = Sum('Jumlah')).order_by()
            for item in dataspk :
                art_code = item.KodeArtikel
                jumlah_art = item.kuantitas2
                list_kode_art.append(
                    {art_code : jumlah_art}
                )
            
            for item in list_kode_art :
                for key,value in item.items() :
                    art_code = key
                    jumlah_art = value
                    print("jumlah artikel:",jumlah_art)
                print("Kode artikel :",art_code)
                try :
                    konversi_art = models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel = art_code).annotate(kode_art = F('KodePenyusun__KodeArtikel'),kode_produk =F('KodePenyusun__KodeProduk'),nilai_konversi=F('Kuantitas'),nama_bb = F('KodePenyusun__KodeProduk__NamaProduk')).values('kode_art','kode_produk','Kuantitas','nama_bb').distinct()
                    print("ini konversi",konversi_art)
                   
                    
                    for item2 in konversi_art :
                        kode_artikel = art_code
                        kode_produk = item2['kode_produk']
                        nilai_conv = item2['Kuantitas']
                        nama_bb = item2['nama_bb']
                        print("Nilai conv", nilai_conv)
                        hasil_conv = round(jumlah_art*nilai_conv)
                        print(hasil_conv)

                        list_hasil_conv.append(
                            {'Kode Artikel' : kode_artikel,
                             'Jumlah Artikel' : jumlah_art,
                             'Kode Produk' : kode_produk,
                             'Nama Produk' : nama_bb,
                             'Hasil Konversi' : hasil_conv
                            }
                        )
                    
                    print("list hasil conv",list_hasil_conv)
                except models.KonversiMaster.DoesNotExist :
                    pass


            return render(request,"Purchasing/kebutuhan_barang.html",
                    {
                    # 'filterspk':filterspk,
                    # 'inputno_spk':inputno_spk,
                    # 'list_q_akhir' : list_q_akhir,
                    # 'rekap_pengadaan' : rekap_pengadaan
                    })
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
            "Purchasing/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
            },
        )
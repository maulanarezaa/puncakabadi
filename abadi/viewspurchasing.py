from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import F,FloatField
from django.db.models import Sum,Value
from . import models
from datetime import datetime,date
from django.db import IntegrityError
from urllib.parse import quote
from django.core.exceptions import ObjectDoesNotExist
import pandas as pd
from . import logindecorators
from django.contrib.auth.decorators import login_required
from .viewsproduksi import calculate_KSBB
from django.http import HttpResponse
from django.db.models.functions import Coalesce
import openpyxl
from openpyxl.styles import PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import math
"""PURCHASING"""


# # READ NOTIF BARANG MASUK PURCHASIN +SPK G+ACC
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def acc_subkon(request,id) :
    accobj = models.DetailSuratJalanPenerimaanProdukSubkon.objects.get(IDDetailSJPenerimaanSubkon=id)
    print('tes')
    if request.method == "GET" :
        valueppn = request.GET.get("input_ppn",2)
        try:
            valueppn = int(valueppn)
            if valueppn < 0:
                valueppn = 2
                messages.error(request, "Nilai Persentase Minus!")
        except ValueError:
            valueppn = 2
            messages.error(request, "Nilai PPN tidak valid!")
        inputppn = valueppn/100
        harga_total = accobj.Jumlah * accobj.Harga
        harga_potongan = harga_total * inputppn
        harga_total_setelah_potongan = harga_total - harga_potongan
        return render(
            request,"Purchasing/update_detailsubkon.html",
            {
                "accobj":accobj,
                "harga_total":harga_total,
                "harga_potongan":harga_potongan,
                "harga_total_potongan":harga_total_setelah_potongan,
            }
        )
    else :
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        keterangan = request.POST["keterangan"]
        tanggalinvoice = request.POST['tanggal_invoice']
        noinvoice = request.POST['no_invoice']
        # potongan = request.POST["input_ppn"]

        accobj.KeteranganACC = True
        accobj.Harga = harga_barang
        accobj.NoSuratJalan.Supplier = supplier
        accobj.Keterangan= keterangan
        if tanggalinvoice != '':
            accobj.NoSuratJalan.TanggalInvoice = tanggalinvoice
        if noinvoice != '':
            accobj.NoSuratJalan.NoInvoice = noinvoice
        accobj.save()
        accobj.NoSuratJalan.save()
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="ACC",
            pesan=f"No Surat Jalan Penerimaan Barang Subkon {accobj.NoSuratJalan} sudah ACC",
        ).save()
        messages.success(request,'Jangan lupa cek barang subkon')
        return redirect("notif_purchasing")
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def notif_barang_purchasing(request):
    waktusekarang = datetime.now()
    filtersubkonobj = models.DetailSuratJalanPenerimaanProdukSubkon.objects.filter(KeteranganACC = False).order_by("NoSuratJalan__Tanggal")
    for x in filtersubkonobj :
        x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
        if x.NoSuratJalan.TanggalInvoice:
            x.NoSuratJalan.TanggalInvoice = x.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
    print("Data subkon bos!", filtersubkonobj)
    filter_dataobj = models.DetailSuratJalanPembelian.objects.filter(
        KeteranganACC=False
    ).order_by("NoSuratJalan__Tanggal")
    for x in filter_dataobj:
        x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
    filter_spkobj = models.SPK.objects.filter(KeteranganACC=False).order_by("Tanggal")
    for x in filter_spkobj:
        x.Tanggal = x.Tanggal.strftime("%Y-%m-%d")
    print(filter_spkobj)
    '''
    Algoritma mencari kebutuhan barang
    1. Ambil data SPK terlebih dahulu yang belum lunas
    2. Jumlahkan artikel detail SPK
    3. Hitung kebutuhan Artikel berdasarkan bahan baku
    4. Ambil nilai Bahan Baku 
    5. Hitung kurangnya
    '''
    '''REKAP PENGADAAN BAHAN BAKU'''
    dataspk = (
        models.DetailSPK.objects.filter(NoSPK__StatusAktif=True)
        .values(("KodeArtikel__KodeArtikel"))
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )
    print(dataspk)
    querysetartikel = []
    for item in dataspk:
        artikelobj  = models.Artikel.objects.get(KodeArtikel=item['KodeArtikel__KodeArtikel'])
        jumlah = item['kuantitas']
        artikelobj.Jumlah = jumlah
        querysetartikel.append(artikelobj)

        # listtipeartikel.append(item['KodeArtikel__KodeArtikel'])
        # listjumlah.append(item['kuantitas'])
    
    # querysetartikel = models.Artikel.objects.filter(KodeArtikel__in =listtipeartikel)
    # Cari versi terakhir dari tiap artikel
    listkebutuhanproduk = {}
    for item in querysetartikel:
        versiterakhir = models.Penyusun.objects.filter(KodeArtikel = item).values_list('versi',flat=True).distinct().order_by("versi").last()
        # print(versiterakhir)
        penyusunobj = models.Penyusun.objects.filter(KodeArtikel = item, versi = versiterakhir)
        # print(len(penyusunobj))
        konversimaster = models.KonversiMaster.objects.filter(KodePenyusun__in = penyusunobj)
        # print(konversimaster)
        # print(len(konversimaster))
        for datapenyusun in konversimaster:
            bahanbakuobj = models.Produk.objects.get(KodeProduk = datapenyusun.KodePenyusun.KodeProduk)
            print(bahanbakuobj)
            if bahanbakuobj not in listkebutuhanproduk :
                listkebutuhanproduk[bahanbakuobj] = datapenyusun.Allowance * item.Jumlah
            else:
                listkebutuhanproduk[bahanbakuobj] += datapenyusun.Allowance * item.Jumlah


            # if bahanbakuobj.jumlahbahanbaku == None:
                # pass
    # print(listkebutuhanproduk)
    print(querysetartikel)
    rekappengadaanbarang = {}
    for produk,jumlah in listkebutuhanproduk.items():
        # print(jumlah)
        cachevalue = models.CacheValue.objects.filter(KodeProduk = produk,Tanggal__month = waktusekarang.month).first()
        totalsaldosekarang = cachevalue.Jumlah
        kebutuhan = jumlah
        selisih = totalsaldosekarang-kebutuhan
        if selisih<0 : 
            rekappengadaanbarang[produk] = math.ceil(abs(selisih))
        else:
            continue
        # print(cachevalue)
    rekappengadaanbarang = dict(sorted(rekappengadaanbarang.items(), key=lambda item: item[0].KodeProduk))
    print(rekappengadaanbarang)
    '''BARANG DIBAWAH STOK
    ALGORITMA
    1. Ambil semua data bahan baku
    2. Ambil cache value
    3. Bandingkan antar jumlah minimal dan nilai sekarang
    '''

    rekapbahandibawahstok = {}
    allproduk = models.Produk.objects.all()
    for produk in allproduk:
        cachevalue = models.CacheValue.objects.filter(KodeProduk = produk,Tanggal__month = waktusekarang.month).first()
        if cachevalue.Jumlah < produk.Jumlahminimal:
            rekapbahandibawahstok[produk] = cachevalue.Jumlah
        else:
            continue

    print(rekapbahandibawahstok)
    rekapbahandibawahstok = dict(sorted(rekapbahandibawahstok.items(), key=lambda item: item[0].KodeProduk))

    # print(asd)

    # print(asd)

    # list_artikel = []
    # list_q_gudang = []
    # list_data_art = []
    # list_hasil_conv = []
    # list_q_akhir = []
    # try:
    #     allartikel = models.Artikel.objects.all()
    #     for item in allartikel:
    #         nama_artikel = item.KodeArtikel
    #         list_artikel.append(nama_artikel)
    # except models.Artikel.DoesNotExist:
    #     messages.error(request, "Data Artikel tidak ditemukan")

    
    # awaltahun = datetime(year = waktusekarang.year,month=1,day=1)
    # datasjb = (
    #     models.DetailSuratJalanPembelian.objects.values("KodeProduk").filter(NoSuratJalan__Tanggal__range =(awaltahun,waktusekarang))
    #     .annotate(kuantitas=Sum("Jumlah"))
    #     .order_by()
    # )

    # if len(datasjb) == 0:
    #     messages.error(request, "Tidak ada barang masuk ke gudang")

    # datagudang = (
    #     models.TransaksiGudang.objects.values("KodeProduk").filter(tanggal__range =(awaltahun,waktusekarang))
    #     .annotate(kuantitas=Sum("jumlah"))
    #     .order_by()
    # )

    # datasaldoawal = models.SaldoAwalBahanBaku.objects.values("IDBahanBaku").filter(Tanggal__range =(awaltahun,waktusekarang)).filter(IDLokasi__NamaLokasi="Gudang").annotate(kuantitas=Sum("Jumlah")).order_by()

    # datapemusnahan = models.PemusnahanBahanBaku.objects.values("KodeBahanBaku").filter(Tanggal__range = (awaltahun,waktusekarang)).filter(lokasi__NamaLokasi="Gudang").annotate(kuantitas=Sum("Jumlah")).order_by()
    

    # print("data sjb", datasjb)
    # print("data gudang", datagudang)
    # print("data saldoawal", datasaldoawal)
    # print("data pemusnahan", datapemusnahan)
    # for item in datasjb:
    #     kode_produk = item["KodeProduk"]
    #     print('ini kode produk', kode_produk)
    #     try:
    #         corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
    #         print("corresponding gudang :",corresponding_gudang_item)


    #     except models.TransaksiGudang.DoesNotExist:
    #         corresponding_gudang_item = {"KodeProduk" : kode_produk, "kuantitas" : 0}

    #     try :
    #         corresponding_saldo_awal_item = datasaldoawal.get(IDBahanBaku=kode_produk)
    #         print("corresponding saldo_awal :",corresponding_saldo_awal_item)
    #     except models.SaldoAwalBahanBaku.DoesNotExist :
    #         corresponding_saldo_awal_item = {"IDBahanBaku" : kode_produk, "kuantitas" : 0}
        
    #     try :
    #         corresponding_pemusnahan_item = datapemusnahan.get(KodeBahanBaku = kode_produk)
    #         print("corresponding pemusnahan :",corresponding_pemusnahan_item)
    #     except models.PemusnahanBahanBaku.DoesNotExist :
    #         corresponding_pemusnahan_item = {"KodeBahanBaku" : kode_produk, "kuantitas" : 0}
    #     print("kuantitas sjb :", item["kuantitas"])
    #     jumlah_akhir = item["kuantitas"] - corresponding_gudang_item["kuantitas"]+corresponding_saldo_awal_item["kuantitas"]-corresponding_pemusnahan_item["kuantitas"]
    #     # if jumlah_akhir < 0:
    #     #     messages.info(request,"Kuantitas gudang menjadi minus")

    #     list_q_gudang.append({kode_produk: jumlah_akhir})


    # print("LIST KODE ART :", list_artikel)
    # print("LIST Q GUDANG :", list_q_gudang)
    # # print(asd)
   
    # dataspk = (
    #     models.DetailSPK.objects.filter(NoSPK__StatusAktif=True)
    #     .values(("KodeArtikel__KodeArtikel"))
    #     .annotate(kuantitas2=Sum("Jumlah"))
    #     .order_by()
    # )

    # for item in dataspk:
    #     art_code = item["KodeArtikel__KodeArtikel"]
    #     jumlah_art = item["kuantitas2"]
    #     list_data_art.append({"Kode_Artikel": art_code, "Jumlah_Artikel": jumlah_art})

    # for item in list_data_art:
    #     kodeArt = item["Kode_Artikel"]

    #     jumlah_art = item["Jumlah_Artikel"]

    #     getidartikel = models.Artikel.objects.get(KodeArtikel=kodeArt)
    #     art_code = getidartikel.id

    #     try:
    #         konversi_art = (
    #             models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel=art_code)
    #             .annotate(
    #                 kode_art=F("KodePenyusun__KodeArtikel__KodeArtikel"),
    #                 kode_produk=F("KodePenyusun__KodeProduk"),
    #                 nilai_konversi=F("Allowance"),
    #                 nama_bb=F("KodePenyusun__KodeProduk__NamaProduk"),
    #                 unit_satuan=F("KodePenyusun__KodeProduk__unit"),
    #             )
    #             .values(
    #                 "kode_art", "kode_produk", "Kuantitas", "nama_bb", "unit_satuan"
    #             )
    #             .distinct()
    #         )
    #         # print(konversi_art)
    #         # for i in konversi_art:
    #         #     print(i)
    #         # print(asd)

    #         for item2 in konversi_art:
    #             kode_artikel = art_code
    #             kode_produk = item2["kode_produk"]
    #             nilai_conv = item2["Kuantitas"]
    #             nama_bb = item2["nama_bb"]
    #             unit_satuan = item2["unit_satuan"]
    #             hasil_conv = round(jumlah_art * nilai_conv)

    #             list_hasil_conv.append(
    #                 {
    #                     "Kode Artikel": kode_artikel,
    #                     "Jumlah Artikel": jumlah_art,
    #                     "Kode Produk": kode_produk,
    #                     "Nama Produk": nama_bb,
    #                     "Hasil Konversi": hasil_conv,
    #                     "Unit Satuan": unit_satuan,
    #                 }
    #             )

    #     except models.KonversiMaster.DoesNotExist:
    #         pass
    
    # for item in list_hasil_conv:
    #     kode_produk = item["Kode Produk"]
    #     hasil_konversi = item["Hasil Konversi"]
    #     for item2 in list_q_gudang:
    #         if kode_produk in item2:
    #             gudang_jumlah = item2[kode_produk]

    #             hasil_akhir = gudang_jumlah - hasil_konversi
    #             list_q_akhir.append(
    #                 {
    #                     "Kode_Artikel": item["Kode Artikel"],
    #                     "Jumlah_Artikel": item["Jumlah Artikel"],
    #                     "Kode_Produk": kode_produk,
    #                     "Nama_Produk": item["Nama Produk"],
    #                     "Unit_Satuan": item["Unit Satuan"],
    #                     "Kebutuhan": hasil_konversi,
    #                     "Stok_Gudang": gudang_jumlah,
    #                     "Selisih": hasil_akhir,
    #                 }
    #             )

    # # list_pengadaan = []
    # # for item in list_q_akhir:
    # #     kode_produk = item['Kode_Produk']
    # #     nama_produk = item['Nama_Produk']
    # #     satuan = item['Unit_Satuan']
    # #     selisih = item['Selisih']
    # #     if kode_produk in pengadaan['Kode_Produk'] :
    # #         pengadaan[]
    # pengadaan = {}

    # for item in list_q_akhir:
    #     produk = item["Kode_Produk"]
    #     pengadaan[produk] = [0, 0]

    # for item in list_q_akhir:
    #     produk = item["Kode_Produk"]
    #     nama_produk = item["Nama_Produk"]
    #     selisih = item["Selisih"]
    #     if produk in pengadaan:
    #         pengadaan[produk][0] = nama_produk
    #         pengadaan[produk][1] += selisih
    #     else:
    #         pengadaan[produk][0] = nama_produk
    #         pengadaan[produk][1] = selisih

    # rekap_pengadaan = {}

    # for key, value in pengadaan.items():
    #     if value[1] < 0:
    #         new_value = abs(value[1])
    #         for i, item in enumerate(list_q_akhir):
    #             if item["Kode_Produk"] == key:
    #                 key = models.Produk.objects.get(pk = key).KodeProduk
    #                 index = i
    #                 rekap_pengadaan[key] = [
    #                     value[0],
    #                     new_value,
    #                     list_q_akhir[index]["Unit_Satuan"],
    #                 ]

    # list_produk = []
    # jumlah_min = models.Produk.objects.values("KodeProduk", "Jumlahminimal")
    # print(jumlah_min)
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

    # datagudang = (
    #     models.TransaksiGudang.objects.values("KodeProduk")
    #     .annotate(kuantitas=Sum("jumlah"))
    #     .order_by()
    # )

    # # for item2 in jumlah_min :
    # #         kode = item2['KodeProduk']
    # #         print(kode)
    # for item in datasjb:
    #     kode_produk = item["KodeProduk"]
    #     nama_produk = item["KodeProduk__NamaProduk"]
    #     satuan = item["KodeProduk__unit"]
    #     try:
    #         corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
    #         item["kuantitas"] -= corresponding_gudang_item["kuantitas"]
    #         for item2 in jumlah_min:
    #             print(item2)
    #             kode = item2["KodeProduk"]
    #             jumlah_minimal = item2["Jumlahminimal"]
    #             print(jumlah_minimal)
    #             print(item)
    #             # print(ads)
    #             print(kode)
    #             print(kode_produk)
    #             # print(asd)
    #             if kode == models.Produk.objects.get(pk = kode_produk).KodeProduk:
    #                 if item["kuantitas"] < jumlah_minimal:
    #                     list_produk.append(
    #                         {
    #                             "Kode_Produk": kode_produk,
    #                             "Nama_Produk": nama_produk,
    #                             "Satuan": satuan,
    #                             "Jumlah_minimal": jumlah_minimal,
    #                             "Jumlah_aktual": item["kuantitas"],
    #                         }
    #                     )
    #                     print(list_artikel)
    #                     # print(asd)
    #                 else:
    #                     continue
    #             else:
    #                 continue

    #     except models.TransaksiGudang.DoesNotExist:
    #         pass
    
    # print("\nrekap pengadaan :",rekap_pengadaan,"\n")
    # print("Ini list produk: ", list_produk)
    return render(
        request,
        "Purchasing/notif_purchasing.html",
        {
            "filterobj": filter_dataobj,
            "filter_spkobj": filter_spkobj,
            "rekap_pengadaan": rekappengadaanbarang,
            "listproduk": rekapbahandibawahstok,
            "filtersubkonobj" : filtersubkonobj
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
        print(request.POST)
        # print(asd)
        matauang = request.POST['mata_uang']
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        po_barang = request.POST["po_barang"]
        tanggalinvoice = request.POST['tanggalinvoice']
        noinvoice = request.POST['noinvoice']
        if matauang == "dollar":
            verifobj.HargaDollar = request.POST['harga_dollar']
        verifobj.KeteranganACC = True
        verifobj.Harga = harga_barang
        verifobj.NoSuratJalan.supplier = supplier
        verifobj.NoSuratJalan.PO = po_barang
        verifobj.NoSuratJalan.NoInvoice = noinvoice
        verifobj.NoSuratJalan.TanggalInvoice=tanggalinvoice
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def exportbarang_excel(request):
    valueppn = request.GET.get("input_ppn", 11)
    try:
        valueppn = int(valueppn)
        if valueppn < 0:
            valueppn = 11
            messages.error(request, "Nilai Persentase Minus!")
    except ValueError:
        valueppn = 11
        messages.error(request, "Nilai PPN tidak valid!")

    inputppn = valueppn / 100
    print("INPUT PPN NI BANGG", inputppn)

    # Ambil nilai input_awal dan input_terakhir dari query string
    input_awal = request.GET.get("input_awal")
    input_terakhir = request.GET.get("input_terakhir")
    print("Ini input awal ama akhir", input_awal, input_terakhir)
    # print(asd)

    # Validasi format tanggal
    date_awal = parse_date(input_awal) if input_awal else None
    date_terakhir = parse_date(input_terakhir) if input_terakhir else None

    if date_awal is None or date_terakhir is None:
        sjball = models.DetailSuratJalanPembelian.objects.all().order_by("NoSuratJalan__Tanggal")
        print("len = 0, sjb all =", sjball)
    else:
        sjball = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__Tanggal__range=(date_awal, date_terakhir)
        ).order_by("NoSuratJalan__Tanggal")

    print('TES SJB BANG', sjball)

    # Buat Workbook baru
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Barang Masuk'

    # Definisikan header untuk worksheet
    headers = ['Tanggal','Suppliers','Kode Bahan Baku','Nama Bahan Baku', 'Kuantitas', 'Harga', 'Harga Total', f'Harga PPN {valueppn}%', 'Harga Total PPN', "Tanggal Invoice","No Invoice"]
    worksheet.append(headers)

    # Tambahkan data ke worksheet
    for item in sjball:
        harga_total = item.Jumlah * item.Harga
        harga_ppn = harga_total * inputppn
        harga_total_ppn = harga_total + harga_ppn
        row = [
            item.NoSuratJalan.Tanggal.strftime("%Y-%m-%d"),
            item.NoSuratJalan.supplier,
            item.KodeProduk.KodeProduk,
            item.KodeProduk.NamaProduk,
            item.Jumlah,
            item.Harga,
            harga_total,
            harga_ppn,
            harga_total_ppn,
            item.NoSuratJalan.TanggalInvoice,
            item.NoSuratJalan.NoInvoice

        ]
        worksheet.append(row)

    # Menyesuaikan lebar kolom
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width
    for row in worksheet.iter_rows(min_row=2, min_col=5, max_col=11):  # mulai dari baris 2 dan kolom 5 (Kuantitas)
        for cell in row:
            if cell.column in [5, 6, 7, 8, 9]:  # kolom Kuantitas dan Harga
                cell.number_format = '#,##0.00'

    # Menambahkan warna pada header
    header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    for cell in worksheet[1]:
        cell.fill = header_fill

        # Menambahkan border pada semua sel
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    for row in worksheet.iter_rows():
        for cell in row:
            cell.border = thin_border
    # Atur response untuk mengunduh file Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Barang Masuk {input_awal}-{input_terakhir}.xlsx'
    workbook.save(response)

    return response
    
   
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def barang_masuk(request):
    # if request.method ==  'POST' :
    if len(request.POST) == 0 :
        valueppn = 11
    else :
        valueppn = request.POST["input_ppn"]
        if int(valueppn) < 0 :
            valueppn = 11
            messages.error(request,"Nilai Persentase Minus!") 
        else :
            pass

    inputppn = int(valueppn)/100

    print("inputppn",inputppn)
 

    if len(request.GET) == 0:
        list_harga_total1 = []
        list_ppn = []
        list_total_ppn = []
        sjball = models.DetailSuratJalanPembelian.objects.all().order_by(
            "NoSuratJalan__Tanggal"
        )
        print(sjball)
        if len(sjball) > 0:
            # inputppn = request.GET["input_ppn"]
            # if len(inputppn) <= 0 :
            # inputppn = 0.11
            # else :
            #     inputppn = inputppn/100
            # ppn = 0.11
            for x in sjball:
                harga_total = x.Jumlah * x.Harga
                x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
                if x.NoSuratJalan.TanggalInvoice is not None:
                    x.NoSuratJalan.TanggalInvoice = x.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
                print(harga_total)
                list_harga_total1.append(harga_total)
            for item in list_harga_total1:
                harga_ppn = item*inputppn
                harga_total_ppn = item+harga_ppn
                list_ppn.append(harga_ppn)
                list_total_ppn.append(harga_total_ppn)
            i = 0
            for item in sjball:
                item.harga_total = list_harga_total1[i]
                item.harga_ppn = list_ppn[i]
                item.harga_total_ppn = list_total_ppn[i]
                i += 1
            print("list hartot", list_harga_total1)
            
        
            return render(
                request,
                "Purchasing/masuk_purchasing.html",
                {
                    "sjball": sjball,
                    "harga_total": harga_total,
                    "harga_ppn" : harga_ppn,
                    "harga_total_ppn" : harga_total_ppn,
                    "valueppn" : valueppn
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return render(
                request,
                "Purchasing/masuk_purchasing.html",
            )
    else:
        # if request.method == "POST": 
            
        # else :
        input_awal = request.GET["awal"]
        input_terakhir = request.GET["akhir"]
        # valueppn = request.POST["input_ppn"]
        # inputppn = request.POST["input_ppn"]
        list_harga_total = []
        list_ppn_1 = []
        list_total_ppn_1 = []
        
        try :
            filtersjb = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__range=(input_awal, input_terakhir)
            ).order_by("NoSuratJalan__Tanggal")
        except models.DetailSuratJalanPembelian.DoesNotExist :
            messages.error(request, "Data tidak ditemukan")
        if len(filtersjb) > 0:
            # if len(inputppn) <= 0 :
            #     inputppn = 0.11
            # else :
            #     inputppn = inputppn/100
            # ppn = 0.11
            for x in filtersjb:
                harga_total = x.Jumlah * x.Harga
                x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
                list_harga_total.append(harga_total)
                if x.NoSuratJalan.TanggalInvoice is not None:
                    x.NoSuratJalan.TanggalInvoice = x.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
            for item in list_harga_total:
                harga_ppn_1 = item*inputppn
                harga_total_ppn_1 = item+harga_ppn_1
                list_ppn_1.append(harga_ppn_1)
                list_total_ppn_1.append(harga_total_ppn_1)

            i = 0
            for item in filtersjb:
                item.harga_total = list_harga_total[i]
                item.harga_ppn_1 = list_ppn_1[i]
                item.harga_total_ppn_1 = list_total_ppn_1[i]
                i += 1
            return render(
                request,
                "Purchasing/masuk_purchasing.html",
                {
                    "data_hasil_filter": filtersjb,
                    "harga_total": harga_total,
                    "harga_ppn_1" :harga_ppn_1,
                    "harga_total_ppn_1" : harga_total_ppn_1,
                    "input_awal": input_awal,
                    "input_terakhir": input_terakhir,
                    "valueppn" : valueppn
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return redirect("barang_masuk")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def update_barang_masuk(request, id):
    updateobj = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    if updateobj.HargaDollar > 0:
        updateobj.hargakonversi = updateobj.Harga / updateobj.HargaDollar
    else:
        updateobj.hargakonversi = 16000

    if request.method == "GET":
        harga_total = updateobj.Jumlah * updateobj.Harga
        if updateobj.NoSuratJalan.TanggalInvoice :
            updateobj.NoSuratJalan.TanggalInvoice =updateobj.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
        
        return render(
            request,
            "Purchasing/update_barang_masuk.html",
            {
                "updateobj": updateobj,
                "harga_total": harga_total,
            },
        )
    else:
        print(request.POST)
        # print(asd)
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        po_barang = request.POST["po_barang"]
        matauang = request.POST['mata_uang']
        noinvoice = request.POST['noinvoice']
        tanggalinvoice = request.POST['tanggalinvoice']
        if noinvoice != "":
            updateobj.NoSuratJalan.NoInvoice = noinvoice
        else :
            updateobj.NoSuratJalan.NoInvoice = None
        
        if tanggalinvoice != "":
            updateobj.NoSuratJalan.TanggalInvoice = tanggalinvoice
        else:
            updateobj.NoSuratJalan.TanggalInvoice = None
        if matauang == "dollar" :
            updateobj.HargaDollar = request.POST['harga_dollar'] 
        updateobj.Harga = harga_barang
        updateobj.NoSuratJalan.supplier = supplier
        updateobj.NoSuratJalan.PO = po_barang
        updateobj.save()
        updateobj.NoSuratJalan.save()
        print(harga_barang, updateobj.Jumlah)
        harga_total = float(updateobj.Jumlah) * int(harga_barang)
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"No Surat Jalan{updateobj.NoSuratJalan} sudah di Update",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("barang_masuk")
        # return JsonResponse({'harga_total': harga_total})

@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def update_barangsubkon_masuk(request, id):
    updateobj = models.DetailSuratJalanPenerimaanProdukSubkon.objects.get(IDDetailSJPenerimaanSubkon=id)
    updateobj.NoSuratJalan.TanggalInvoice = updateobj.NoSuratJalan.TanggalInvoice.strftime('%Y-%m-%d')
    # if updateobj.HargaDollar > 0:
    #     updateobj.hargakonversi = updateobj.Harga / updateobj.HargaDollar
    # else:
    #     updateobj.hargakonversi = 16000
    
    if request.method == "GET":
        harga_total = updateobj.Jumlah * updateobj.Harga
        return render(
            request,
            "Purchasing/update_barangsubkon_masuk.html",
            {
                "updateobj": updateobj,
                "harga_total": harga_total,
            },
        )
    else:
        print(request.POST)

        harga_barang = request.POST["harga_barang"]
        matauang = request.POST['mata_uang']
        noinvoice = request.POST['noinvoice']
        tanggalinvoice = request.POST['tanggalinvoice']
        if noinvoice != "":
            updateobj.NoSuratJalan.NoInvoice = noinvoice
        else :
            updateobj.NoSuratJalan.NoInvoice = None
        
        if tanggalinvoice != "":
            updateobj.NoSuratJalan.TanggalInvoice = tanggalinvoice
        else:
            updateobj.NoSuratJalan.TanggalInvoice = None

        if matauang == "dollar" :
            updateobj.HargaDollar = request.POST['harga_dollar'] 
        updateobj.Harga = harga_barang
        updateobj.save()
        updateobj.NoSuratJalan.save()
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"No Surat Jalan{updateobj.NoSuratJalan} sudah di Update",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("rekaphargasubkon")
        # return JsonResponse({'harga_total': harga_total})


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def rekap_purchasing(request):
    return render(request, "Purchasing/rekap_purchasing.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def view_rekapbarang(request):
    tanggal_akhir = request.GET.get("periode")

    sekarang = datetime.now()
    tahun = sekarang.year

    tanggal_mulai = datetime(year=tahun, month=1, day=1)

    dataproduk = models.Produk.objects.all()
    try:

        lokasi = request.GET['lokasi']
    except: 
        lokasi = "WIP"

    if tanggal_akhir:
        for produk in dataproduk:
            listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, tanggal_akhir,lokasi)

            if listdata:
                produk.kuantitas = listdata[-1]["Sisa"][0]
            else:
                produk.kuantitas = 0
    else:
        for produk in dataproduk:
            listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, sekarang,lokasi)

            if listdata:
                produk.kuantitas = listdata[-1]["Sisa"][0]
            else:
                produk.kuantitas = 0
    return render(
        request,
        "Purchasing/rekapproduksi2.html",
        {"data": dataproduk, "tanggal_akhir": tanggal_akhir,'lokasi':lokasi},
    )


"""REVISI DELETE ADA YANG ERROR, TRS ERROR HANDLING GABOLE CREATE DENGAN KODE YG SAMA(done)"""


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def read_produk(request):
    produkobj = models.Produk.objects.all().order_by('KodeProduk')
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
    produkobj = models.Produk.objects.get(KodeProduk=id)
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
        namaproduk = models.Produk.objects.filter(KodeProduk=kode_produk).exists()
        print(namaproduk)
        print(request.POST)
        print(id)
        # print(asd)

        if namaproduk and kode_produk != id:
            messages.error(request,f'Kode Produk {kode_produk} sudah ada pada sistem')
            return redirect('update_produk',id = id)
        produkbaru = models.Produk.objects.get(KodeProduk=id)
        produkbaru.KodeProduk = kode_produk
        produkbaru.NamaProduk = nama_produk
        produkbaru.unit = unit_produk
        produkbaru.keteranganPurchasing = keterangan_produk
        produkbaru.Jumlahminimal = jumlah_minimal
        # print(asd)
        produkbaru.save()
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def rekap_gudang(request):
    sekarang = datetime.now().strftime('%Y-%m-%d')
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
            ).aggregate(kuantitas=Coalesce(Sum("Jumlah"), Value(0,output_field=FloatField())))
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
).aggregate(
    kuantitas=Coalesce(Sum("Jumlah"), Value(0,output_field=FloatField()))
)

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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def update_po(request,id) :
    po_obj = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    if request.method == "GET" :
        return render(
            request,
            "Purchasing/update_po.html",
            {
                "po_obj" : po_obj
            }
        )
    else :
        harga_barang = request.POST["harga_barang"]
        supplier = request.POST["supplier"]
        po_barang = request.POST["po_barang"]
        po_obj.NoSuratJalan.PO =po_barang
        po_obj.Harga = harga_barang
        po_obj.NoSuratJalan.supplier = supplier
        po_obj.save()
        po_obj.NoSuratJalan.save()
        models.transactionlog(
            user="Purchasing",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"No Surat Jalan{po_obj.NoSuratJalan} sudah di Update",
        ).save()
        return redirect("read_po")

@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def view_sppb(request):
    datasppb = models.SPPB.objects.all().order_by("-Tanggal")
    for i in datasppb:
        i.detailsppb = models.DetailSPPB.objects.filter(NoSPPB = i)
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")
    return render(request, "Purchasing/view_sppb2.html", {"datasppb": datasppb})




@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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

# Tinggal dibikin gimana biar kodenya yang terkirim pas di reload kode itu lagi yang muncul
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
                sekarang = date.today()
                awaltahun = date(sekarang.year, 1, 1)
                akhirtahun = date(sekarang.year,12,31)
                print(data)
                if data.exists():
                    for item in data:
                        print(item, item.IDKodePenyusun)
                        konversidataobj = models.KonversiMaster.objects.get(
                            KodePenyusun=item.IDKodePenyusun
                        )
                        # print(konversidataobj.Kuantitas)
                        masukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=item.KodeProduk, NoSuratJalan__Tanggal__range=(awaltahun,akhirtahun)
        )

                        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

                        keluarobj = models.TransaksiGudang.objects.filter(
                            jumlah__gte=0, KodeProduk=item.KodeProduk, tanggal__range=(awaltahun,akhirtahun)
                        )
                        returobj = models.TransaksiGudang.objects.filter(
                            jumlah__lt=0, KodeProduk=item.KodeProduk, tanggal__range=(awaltahun,akhirtahun)
                        )
                        pemusnahanobj = models.PemusnahanBahanBaku.objects.filter(
                            lokasi__NamaLokasi = 'Gudang',KodeBahanBaku = item.KodeProduk, Tanggal__range = (awaltahun,akhirtahun)
                        )
                        # print(pemusnahanobj)
                        # print(asd)
                        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                        tanggalretur = returobj.values_list("tanggal", flat=True)
                        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal",flat=True)
                        print("ini kode bahan baku", keluarobj)
                        saldoawalobj = (
                            models.SaldoAwalBahanBaku.objects.filter(
                                IDBahanBaku=item.KodeProduk,
                                IDLokasi__IDLokasi=3,
                                Tanggal__range=(awaltahun,akhirtahun)
                            )
                            .order_by("-Tanggal")
                            .first()
                        )
                        print(saldoawalobj)
                        print('ini item',item)
                        if (
                            not keluarobj.exists()
                            and not returobj.exists()
                            and not masukobj.exists()
                            and saldoawalobj is None
                        ):
                            messages.error(request, f"Tidak ditemukan data Transaksi Barang pada penyusun {item.KodeProduk.KodeProduk} - {item.KodeProduk.NamaProduk}")
                            hargasatuanawal = 0
                            hargaterakhir = 0
                            hargaperkotak = 0
                            # print(asd
                            kuantitaskonversi = konversidataobj.Kuantitas
                            kuantitasallowance = konversidataobj.Allowance
                            print(item)
                            # print(asd)
                            # return redirect("rekapharga")
                        # print(asdas)
                        else :
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
                                list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalretur).union(tanggalpemusnahan)))
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
                                transaksipemusnahan = pemusnahanobj.filter(Tanggal=i)


                                if transaksigudangobj.exists():
                                    for j in transaksigudangobj:
                                        jumlahkeluarperhari += j.jumlah
                                        hargakeluartotalperhari += j.jumlah * hargasatuanawal

                                if transaksipemusnahan.exists():
                                    for j in transaksipemusnahan:
                                        jumlahkeluarperhari += j.Jumlah
                                        hargakeluartotalperhari += j.Jumlah * hargasatuanawal

                                if jumlahkeluarperhari > 0:
                                    hargakeluarsatuanperhari = hargakeluartotalperhari / jumlahkeluarperhari
                                else:
                                    if statusmasuk:
                                        statusmasuk = False
                                        continue
                                    hargakeluartotalperhari = 0
                                    hargakeluarsatuanperhari = 0
                                    jumlahkeluarperhari = 0

                                # transaksigudangobj = keluarobj.filter(tanggal=i)
                                # print(transaksigudangobj)
                                # if transaksigudangobj.exists():
                                #     for j in transaksigudangobj:
                                #         jumlahkeluarperhari += j.jumlah
                                #         hargakeluartotalperhari += j.jumlah * hargasatuanawal
                                #     hargakeluarsatuanperhari += (
                                #         hargakeluartotalperhari / jumlahkeluarperhari
                                #     )
                                # else:
                                #     if statusmasuk:
                                #         statusmasuk = False
                                #         continue
                                #     hargakeluartotalperhari = 0
                                #     hargakeluarsatuanperhari = 0
                                #     jumlahkeluarperhari = 0

                                # transaksipemusnahan = pemusnahanobj.filter(Tanggal=i)
                                # print(transaksipemusnahan)
                                # if transaksipemusnahan.exists():
                                #     for j in transaksipemusnahan:
                                #         jumlahkeluarperhari += j.Jumlah
                                #         hargakeluartotalperhari += j.Jumlah * hargasatuanawal
                                #     hargakeluarsatuanperhari += (
                                #         hargakeluartotalperhari / jumlahkeluarperhari
                                #     )
                                # else:
                                #     if statusmasuk:
                                #         statusmasuk = False
                                #         continue
                                #     hargakeluartotalperhari = 0
                                #     hargakeluarsatuanperhari = 0
                                #     jumlahkeluarperhari = 0

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
                    messages.error(request, "Versi tidak ditemukan")
                    return redirect(
                        f"/rnd/penyusun?kodeartikel={quote(kodeartikel)}&versi="
                    )
            else:
                messages.error(request, "Kode Artikel Belum memiliki penyusun")
                return render(
                    request,
                    "rnd/views_penyusun.html",
                    {"kodeartikel": get_id_kodeartikel},
                )
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return render(
                request,
                "rnd/views_penyusun.html",
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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
            waktusekarang = datetime.now()
            awaltahun = datetime(year = waktusekarang.year,month=1,day=1)
            dataproduk = models.CacheValue.objects.filter(Tanggal__year = waktusekarang.year, Tanggal__month = waktusekarang.month)
            print(dataproduk)
            print(len(dataproduk))
            if dataproduk.exists():
                for item in dataproduk:
                    list_q_gudang.append({item.KodeProduk.id:item.Jumlah})

                # print(asd)
            else:
                datasjb = (
                    models.DetailSuratJalanPembelian.objects.values("KodeProduk").filter(NoSuratJalan__Tanggal__range =(awaltahun,waktusekarang))
                    .annotate(kuantitas=Sum("Jumlah"))
                    .order_by()
                )

                if len(datasjb) == 0:
                    messages.error(request, "Tidak ada barang masuk ke gudang")

                datagudang = (
                    models.TransaksiGudang.objects.values("KodeProduk").filter(tanggal__range =(awaltahun,waktusekarang))
                    .annotate(kuantitas=Sum("jumlah"))
                    .order_by()
                )

                datasaldoawal = models.SaldoAwalBahanBaku.objects.values("IDBahanBaku").filter(Tanggal__range =(awaltahun,waktusekarang)).filter(IDLokasi__NamaLokasi="Gudang").annotate(kuantitas=Sum("Jumlah")).order_by()

                datapemusnahan = models.PemusnahanBahanBaku.objects.values("KodeBahanBaku").filter(Tanggal__range = (awaltahun,waktusekarang)).filter(lokasi__NamaLokasi="Gudang").annotate(kuantitas=Sum("Jumlah")).order_by()
                

                print("data sjb", datasjb)
                print("data gudang", datagudang)
                print("data saldoawal", datasaldoawal)
                print("data pemusnahan", datapemusnahan)
                # print(asd)
                for item in datasjb:
                    kode_produk = item["KodeProduk"]
                    print('ini kode produk', kode_produk)
                    try:
                        corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
                        print("corresponding gudang :",corresponding_gudang_item)


                    except models.TransaksiGudang.DoesNotExist:
                        corresponding_gudang_item = {"KodeProduk" : kode_produk, "kuantitas" : 0}

                    try :
                        corresponding_saldo_awal_item = datasaldoawal.get(IDBahanBaku=kode_produk)
                        print("corresponding saldo_awal :",corresponding_saldo_awal_item)
                    except models.SaldoAwalBahanBaku.DoesNotExist :
                        corresponding_saldo_awal_item = {"IDBahanBaku" : kode_produk, "kuantitas" : 0}
                    
                    try :
                        corresponding_pemusnahan_item = datapemusnahan.get(KodeBahanBaku = kode_produk)
                        print("corresponding pemusnahan :",corresponding_pemusnahan_item)
                    except models.PemusnahanBahanBaku.DoesNotExist :
                        corresponding_pemusnahan_item = {"KodeBahanBaku" : kode_produk, "kuantitas" : 0}
                    print("kuantitas sjb :", item["kuantitas"])
                    jumlah_akhir = item["kuantitas"] - corresponding_gudang_item["kuantitas"]+corresponding_saldo_awal_item["kuantitas"]-corresponding_pemusnahan_item["kuantitas"]
                    # if jumlah_akhir < 0:
                    #     messages.info(request,"Kuantitas gudang menjadi minus")

                    list_q_gudang.append({models.Produk.objects.get(pk = kode_produk): jumlah_akhir})
            

            print("LIST KODE ART :", list_kode_art)
            print("LIST Q GUDANG :", list_q_gudang)
            # print(asd)
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
                    print("versi terakhir",versipenyusunterakhir, art_code)
                    listpenyusun = models.Penyusun.objects.filter(KodeArtikel = art_code, versi = versipenyusunterakhir.versi).values_list('IDKodePenyusun',flat=True)
                    print(listpenyusun)
                    # print(asd)

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
                        print(item2)

                        kode_artikel = art_code.KodeArtikel
                        kode_produk = item2["kode_produk"]
                        nilai_conv = item2["Kuantitas"]
                        nama_bb = item2["nama_bb"]

                        hasil_conv = math.ceil(jumlah_art * nilai_conv)

                        list_hasil_conv.append(
                            {
                                "Kode Artikel": kode_artikel,
                                "Jumlah Artikel": jumlah_art,
                                "Kode Produk": kode_produk,
                                "Nama Produk": nama_bb,
                                "Hasil Konversi": hasil_conv,
                            }
                        )
                    # pritn(asd)

                except Exception as e :
                    messages.error(request,f'Error {e}')
                    continue

            for item in list_hasil_conv:
                print(list_hasil_conv)
                print(item)
                # print(asd)
                kode_produk = item["Kode Produk"]
                hasil_konversi = item["Hasil Konversi"]
                datacachevalue = models.CacheValue.objects.filter(KodeProduk = kode_produk,Tanggal__year = waktusekarang.year, Tanggal__month = waktusekarang.month).first()
                print(datacachevalue)
                print(kode_produk)
                gudang_jumlah = datacachevalue.Jumlah
                hasil_akhir = gudang_jumlah - hasil_konversi
                # print(asd)
                list_q_akhir.append(
                            {
                                "Kode_Artikel": item["Kode Artikel"],
                                "Jumlah_Artikel": item["Jumlah Artikel"],
                                "Kode_Produk": datacachevalue.KodeProduk.KodeProduk,
                                "Nama_Produk": item["Nama Produk"],
                                "Kebutuhan": hasil_konversi,
                                "Stok_Gudang": gudang_jumlah,
                                "Selisih": hasil_akhir,
                            }
                        )
              
                
            pengadaan = {}

            for item in list_q_akhir:
                produk = item["Kode_Produk"]
                pengadaan[produk] = [0, 0,0]
            print(list_q_akhir)
            print(pengadaan)
            # print(asd)
            for item in list_q_akhir:
                produk = item["Kode_Produk"]
                nama_produk = item["Nama_Produk"]
                selisih = item['Kebutuhan']
                stoksekarnag = item['Stok_Gudang']
                if produk in pengadaan:
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] += selisih
                    pengadaan[produk][2] = stoksekarnag
                else:
                    pengadaan[produk][0] = nama_produk
                    pengadaan[produk][1] = selisih
                    pengadaan[produk][2] = stoksekarnag

            rekap_pengadaan = {}

            print(pengadaan)
            for key, value in pengadaan.items():
                value[1] -= value[2]
                if value[1] > 0:
                    new_value = abs(value[1])
                    rekap_pengadaan[key] = [value[0], new_value]
            print(pengadaan)
            # print(asd)
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



@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
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
            KodeProduk__KodeProduk=produkobj.KodeProduk, NoSuratJalan__Tanggal__range=(awaltahun,akhirtahun)
        )

        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk__KodeProduk=produkobj.KodeProduk, tanggal__range=(awaltahun,akhirtahun)
        )
        returobj = models.TransaksiGudang.objects.filter(
            jumlah__lt=0, KodeProduk__KodeProduk=produkobj.KodeProduk, tanggal__range=(awaltahun,akhirtahun)
        )
        pemusnahanobj = models.PemusnahanBahanBaku.objects.filter(
            lokasi__NamaLokasi = 'Gudang',KodeBahanBaku__KodeProduk = produkobj.KodeProduk, Tanggal__range = (awaltahun,akhirtahun)
        )
        # print(pemusnahanobj)
        # print(asd)
        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
        tanggalretur = returobj.values_list("tanggal", flat=True)
        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal",flat=True)
        print("ini kode bahan baku", keluarobj)
        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku__KodeProduk=produkobj.KodeProduk,
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
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalretur).union(tanggalpemusnahan)))
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
                    "Hargasatuanawal": hargasatuanawal, 
                    "Hargatotalawal": hargatotalawal, 
                    "Jumlahmasuk": jumlahmasukperhari,
                    "Hargamasuksatuan": hargamasuksatuanperhari, 
                    "Hargamasuktotal": hargamasuktotalperhari, 
                    "Jumlahkeluar": jumlahkeluarperhari,
                    "Hargakeluarsatuan": hargakeluarsatuanperhari, 
                    "Hargakeluartotal": hargakeluartotalperhari, 
                }
                saldoawal += jumlahmasukperhari - jumlahkeluarperhari
                hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
                hargasatuanawal = hargatotalawal / saldoawal

                print("Sisa Stok Hari Ini : ", saldoawal)
                print("harga awal Hari Ini :", hargasatuanawal)
                print("harga total Hari Ini :", hargatotalawal, "\n")
                dumy["Sisahariini"] = saldoawal
                dumy["Hargasatuansisa"] = hargasatuanawal
                dumy["Hargatotalsisa"] = hargatotalawal
                statusmasuk = True
                listdata.append(dumy)
                # print(asdasd)

            hargamasuktotalperhari = 0
            jumlahmasukperhari = 0
            hargamasuksatuanperhari = 0
            transaksigudangobj = keluarobj.filter(tanggal=i)
            transaksipemusnahan = pemusnahanobj.filter(Tanggal=i)


            if transaksigudangobj.exists():
                for j in transaksigudangobj:
                    jumlahkeluarperhari += j.jumlah
                    hargakeluartotalperhari += j.jumlah * hargasatuanawal

            if transaksipemusnahan.exists():
                for j in transaksipemusnahan:
                    jumlahkeluarperhari += j.Jumlah
                    hargakeluartotalperhari += j.Jumlah * hargasatuanawal

            if jumlahkeluarperhari > 0:
                hargakeluarsatuanperhari = hargakeluartotalperhari / jumlahkeluarperhari
            else:
                if statusmasuk:
                    statusmasuk = False
                    continue
                hargakeluartotalperhari = 0
                hargakeluarsatuanperhari = 0
                jumlahkeluarperhari = 0

            # transaksigudangobj = keluarobj.filter(tanggal=i)
            # print(transaksigudangobj)
            # if transaksigudangobj.exists():
            #     for j in transaksigudangobj:
            #         jumlahkeluarperhari += j.jumlah
            #         hargakeluartotalperhari += j.jumlah * hargasatuanawal
            #     hargakeluarsatuanperhari += (
            #         hargakeluartotalperhari / jumlahkeluarperhari
            #     )
            # else:
            #     if statusmasuk:
            #         statusmasuk = False
            #         continue
            #     hargakeluartotalperhari = 0
            #     hargakeluarsatuanperhari = 0
            #     jumlahkeluarperhari = 0

            # transaksipemusnahan = pemusnahanobj.filter(Tanggal=i)
            # print(transaksipemusnahan)
            # if transaksipemusnahan.exists():
            #     for j in transaksipemusnahan:
            #         jumlahkeluarperhari += j.Jumlah
            #         hargakeluartotalperhari += j.Jumlah * hargasatuanawal
            #     hargakeluarsatuanperhari += (
            #         hargakeluartotalperhari / jumlahkeluarperhari
            #     )
            # else:
            #     if statusmasuk:
            #         statusmasuk = False
            #         continue
            #     hargakeluartotalperhari = 0
            #     hargakeluarsatuanperhari = 0
            #     jumlahkeluarperhari = 0

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
                "Hargasatuanawal": hargasatuanawal, 
                "Hargatotalawal": hargatotalawal, 
                "Jumlahmasuk": jumlahmasukperhari,
                "Hargamasuksatuan": hargamasuksatuanperhari, 
                "Hargamasuktotal": hargamasuktotalperhari, 
                "Jumlahkeluar": jumlahkeluarperhari,
                "Hargakeluarsatuan": hargakeluarsatuanperhari, 
                "Hargakeluartotal": hargakeluartotalperhari, 
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
            dumy["Hargasatuansisa"] = hargasatuanawal
            dumy["Hargatotalsisa"] = hargatotalawal

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
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def exportbarangsubkon_excel(request):
    valueppn = request.GET.get("input_ppn", 2)
    try:
        valueppn = int(valueppn)
        if valueppn < 0:
            valueppn = 2
            messages.error(request, "Nilai Persentase Minus!")
    except ValueError:
        valueppn = 2
        messages.error(request, "Nilai PPN tidak valid!")

    inputppn = valueppn / 100
    print("INPUT PPN NI BANGG", inputppn)

    # Ambil nilai input_awal dan input_terakhir dari query string
    input_awal = request.GET.get("input_awal")
    input_terakhir = request.GET.get("input_terakhir")
    print("Ini input awal ama akhir", input_awal, input_terakhir)

    # Validasi format tanggal
    date_awal = parse_date(input_awal) if input_awal else None
    date_terakhir = parse_date(input_terakhir) if input_terakhir else None

    if date_awal is None or date_terakhir is None:
        sjball = models.DetailSuratJalanPenerimaanProdukSubkon.objects.all().order_by("NoSuratJalan__Tanggal")
        print("len = 0, sjb all =", sjball)
    else:
        sjball = models.DetailSuratJalanPenerimaanProdukSubkon.objects.filter(
            NoSuratJalan__Tanggal__range=(date_awal, date_terakhir)
        ).order_by("NoSuratJalan__Tanggal")

    print('TES SJB BANG', sjball)

    # Buat Workbook baru
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Barang Masuk'

    # Definisikan header untuk worksheet
    headers = ['Tanggal', 'Supplier', 'Kode Bahan Baku Subkon', 'Nama Bahan Baku Subkon', 'Satuan', 'Kuantitas', 'Harga', 'Harga Total', f'Harga Potongan {valueppn}%', 'Harga Total Setelah Potongan', 'Tanggal Invoice', 'No Invoice']
    worksheet.append(headers)

    # Tambahkan data ke worksheet
    for item in sjball:
        harga_total = item.Jumlah * item.Harga
        harga_potongan = harga_total * inputppn
        harga_satuan_setelah_pemotognan = math.ceil(item.Harga - (item.Harga * inputppn))
        harga_total_setelah_potongan = harga_satuan_setelah_pemotognan * item.Jumlah
        row = [
            item.NoSuratJalan.Tanggal.strftime("%Y-%m-%d"),
            str(item.NoSuratJalan.Supplier),
            str(item.KodeProduk),
            str(item.KodeProduk.NamaProduk),
            str(item.KodeProduk.Unit),  # Assuming you have a field for 'Satuan'
            item.Jumlah,
            item.Harga,
            harga_total,
            harga_satuan_setelah_pemotognan,
            harga_total_setelah_potongan,
            item.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d") if item.NoSuratJalan.TanggalInvoice else '',
            str(item.NoSuratJalan.NoInvoice) if item.NoSuratJalan.NoInvoice else ''
        ]
        worksheet.append(row)

    # Menyesuaikan lebar kolom
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column name
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width

    # Menambahkan warna pada header
    header_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    for cell in worksheet[1]:
        cell.fill = header_fill

    # Menambahkan border pada semua sel
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    for row in worksheet.iter_rows():
        for cell in row:
            cell.border = thin_border
    for row in worksheet.iter_rows(min_row=2, min_col=6, max_col=10):  # mulai dari baris 2 dan kolom 5 (Kuantitas)
        for cell in row:
            if cell.column in [6,7, 8, 9, 10]:  # kolom Kuantitas dan Harga
                cell.number_format = '#,##0.00'

    # Atur response untuk mengunduh file Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Bahan Baku Subkon Masuk {input_awal} - {input_terakhir}.xlsx'
    workbook.save(response)

    return response


@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def views_rekaphargasubkon(request):
    # if request.method ==  'POST' :
    if len(request.POST) == 0 :
        valueppn = 2
    else :
        valueppn = request.POST["input_ppn"]
        if int(valueppn) < 0 :
            valueppn = 2
            messages.error(request,"Nilai Persentase Minus!") 
        else :
            pass

    inputppn = int(valueppn)/100

    print("inputppn",inputppn)
 

    if len(request.GET) == 0:
        list_harga_total1 = []
        list_ppn = []
        harga_setelah_ppn = []
        list_total_ppn = []
        sjball = models.DetailSuratJalanPenerimaanProdukSubkon.objects.all().order_by(
            "NoSuratJalan__Tanggal"
        )
        print(sjball)
        # print(asd)
        if len(sjball) > 0:
       
            for x in sjball:
                harga_total = x.Jumlah * x.Harga
                x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
                if x.NoSuratJalan.TanggalInvoice is not None:
                    x.NoSuratJalan.TanggalInvoice = x.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
                print(harga_total)
                list_harga_total1.append(harga_total)
                harga_setelah_pemotongan = math.ceil(x.Harga - (x.Harga * inputppn))
                total_harga_setelah_pemotongan = harga_setelah_pemotongan * x.Jumlah
                harga_setelah_ppn.append(harga_setelah_pemotongan)
                list_total_ppn.append(total_harga_setelah_pemotongan)
            i = 0
            for item in sjball:
                item.harga_total = list_harga_total1[i]
                item.harga_ppn = harga_setelah_ppn[i]
                item.harga_total_ppn = list_total_ppn[i]
                i += 1
            print("list hartot", list_harga_total1)
            
        
            return render(
                request,
                "Purchasing/masuk_subkon.html",
                {
                    "sjball": sjball,
                    "harga_total": harga_total,
                    "valueppn" : valueppn
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return render(
                request,
                "Purchasing/masuk_subkon.html",
            )
    else:
        # if request.method == "POST": 
            
        # else :
        input_awal = request.GET["awal"]
        input_terakhir = request.GET["akhir"]
        # valueppn = request.POST["input_ppn"]
        # inputppn = request.POST["input_ppn"]
        list_harga_total = []
        list_ppn_1 = []
        list_total_ppn = []
        harga_setelah_ppn = []
        try :
            filtersjb = models.DetailSuratJalanPenerimaanProdukSubkon.objects.filter(
                NoSuratJalan__Tanggal__range=(input_awal, input_terakhir)
            ).order_by("NoSuratJalan__Tanggal")
        except models.DetailSuratJalanPenerimaanProdukSubkon.DoesNotExists :
            messages.error(request, "Data tidak ditemukan")
        if len(filtersjb) > 0:

            for x in filtersjb:
                harga_total = x.Jumlah * x.Harga
                x.NoSuratJalan.Tanggal = x.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")
                if x.NoSuratJalan.TanggalInvoice is not None:
                    x.NoSuratJalan.TanggalInvoice = x.NoSuratJalan.TanggalInvoice.strftime("%Y-%m-%d")
                list_harga_total.append(harga_total)
                harga_setelah_pemotongan = math.ceil(x.Harga - (x.Harga * inputppn))
                total_harga_setelah_pemotongan = harga_setelah_pemotongan * x.Jumlah
                harga_setelah_ppn.append(harga_setelah_pemotongan)
                list_total_ppn.append(total_harga_setelah_pemotongan)
            i = 0
            for item in filtersjb:
                item.harga_total = list_harga_total[i]
                item.harga_ppn_1 = harga_setelah_ppn[i]
                item.harga_total_ppn_1 = list_total_ppn[i]
                i += 1
            return render(
                request,
                "Purchasing/masuk_subkon.html",
                {
                    "data_hasil_filter": filtersjb,
                    "harga_total": harga_total,
                    "input_awal": input_awal,
                    "input_terakhir": input_terakhir,
                    "valueppn" : valueppn
                },
            )
        else:
            messages.error(request, "Data tidak ditemukan")
            return redirect("rekaphargasubkon")

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
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def read_saldoawal(request):
    dataproduk = models.SaldoAwalBahanBaku.objects.all().order_by("-Tanggal")
    print(dataproduk)
    for i in dataproduk:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/read_saldoawalbahan.html", {"dataproduk": dataproduk}
    )
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
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


# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])

# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def view_saldoartikel(request):
    dataartikel = models.SaldoAwalArtikel.objects.all().order_by("-Tanggal")
    for i in dataartikel:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/view_saldoartikel.html", {"dataartikel": dataartikel}
    )
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
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
        return redirect("saldoartikelpurchasing")


# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing"])
def update_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    datasubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "purchasing/update_saldosubkon.html",
            {"data": dataobj,"datasubkon": datasubkon },
        )

    else:
        kodeproduk = request.POST["kodebarangHidden"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalSubkon.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDProdukSubkon__NamaProduk=kodeproduk,
        ).exclude(IDSaldoAwalProdukSubkon=id).exists()
          
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("view_saldosubkon")
        
        produkobj = models.ProdukSubkon.objects.get(IDProdukSubkon=kodeproduk)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDProdukSubkon = produkobj
        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Saldo Produk Subkon. Nama Produk : {produkobj.NamaProduk} Kode Artikel : {produkobj.KodeArtikel} Jumlah : {jumlah}",
        ).save()

        return redirect("view_saldosubkon")

# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def delete_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)

    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Saldo Produk Subkon. Nama Produk : {dataobj.IDProdukSubkon.NamaProduk}  Kode Artikel : {dataobj.IDProdukSubkon.KodeArtikel} Jumlah : {dataobj.Jumlah}",
    ).save()
    
    return redirect("view_saldosubkon")

# Saldo Bahan Subkon
# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def view_saldobahansubkon(request):
    datasubkon = models.SaldoAwalBahanBakuSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "purchasing/view_saldobahansubkon.html", {"datasubkon": datasubkon}
    )

# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])

# @login_required
# @logindecorators.allowed_users(allowed_roles=['produksi'])
@login_required
@logindecorators.allowed_users(allowed_roles=["purchasing",'ppic'])
def update_saldobahansubkon(request, id):
    dataobj = models.SaldoAwalBahanBakuSubkon.objects.get(IDSaldoAwalBahanBakuSubkon=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    datasubkon = models.BahanBakuSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "purchasing/update_saldobahansubkon.html",
            {"data": dataobj,"datasubkon": datasubkon },
        )

    else:
        kodeproduk = request.POST["produk"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalBahanBakuSubkon.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDBahanBakuSubkon__KodeProduk=kodeproduk,
        ).exclude(IDSaldoAwalBahanBakuSubkon=id).exists()

        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("update_saldobahansubkon", id=id)
        try:
            produkobj = models.BahanBakuSubkon.objects.get(KodeProduk=kodeproduk)
        except:
            messages.error(request,f"Kode Bahan Baku Subkon {kodeproduk} tidak ditemukan dalam sistem")
            return redirect("update_saldobahansubkon", id = id)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDBahanBakuSubkon = produkobj
        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Saldo Bahan Baku Subkon. Kode Bahan Baku: {produkobj.KodeProduk} Jumlah : {jumlah}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldobahansubkon")

# @login_rexs.allowed_users(allowed_roles=['produksi'])

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


# Saldo Awal Artikel
@login_required
@logindecorators.allowed_users(allowed_roles=['purchasing','ppic'])
def view_saldoartikel(request):
    dataartikel = models.SaldoAwalArtikel.objects.all().order_by("-Tanggal")
    for i in dataartikel:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/views_saldoartikel.html", {"dataartikel": dataartikel}
    )

# Saldo Bahan Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['purchasing','ppic'])
def view_saldobahansubkon(request):
    datasubkon = models.SaldoAwalBahanBakuSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/views_saldobahansubkon.html", {"datasubkon": datasubkon}
    )

# Saldo Awal Produk Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['purchasing','ppic'])
def view_saldosubkon(request):
    datasubkon = models.SaldoAwalSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "Purchasing/views_saldoproduksubkon.html", {"datasubkon": datasubkon}
    )


@login_required
@logindecorators.allowed_users(allowed_roles=['purchasing'])
def update_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    datasubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "Purchasing/update_saldoproduksubkon.html",
            {"data": dataobj,"datasubkon": datasubkon },
        )

    else:
        kodeproduk = request.POST["kodebarangHidden"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalSubkon.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDProdukSubkon__NamaProduk=kodeproduk,
        ).exclude(IDSaldoAwalProdukSubkon=id).exists()
          
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("view_produksubkon")
        
        produkobj = models.ProdukSubkon.objects.get(IDProdukSubkon=kodeproduk)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDProdukSubkon = produkobj
        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Saldo Produk Subkon. Nama Produk : {produkobj.NamaProduk} Kode Artikel : {produkobj.KodeArtikel} Jumlah : {jumlah}",
        ).save()

        return redirect("view_produksubkon")
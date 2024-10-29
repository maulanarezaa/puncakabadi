from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404, JsonResponse, HttpResponse
from django.urls import reverse
from . import models
from django.db.models import Sum
from urllib.parse import quote,urlparse, parse_qs, urlencode
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta, date
from . import logindecorators
from django.contrib.auth.decorators import login_required
from urllib.parse import urlencode, quote
import math
from .viewsproduksi import calculate_ksbj,calculate_KSBB
import re


# Create your views here.
# RND


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def gethargafg(penyusunobj):
    konversiobj = models.KonversiMaster.objects.get(
        KodePenyusun=penyusunobj.IDKodePenyusun
    )
    konversialowance = konversiobj.Kuantitas + (konversiobj.Kuantitas * 0.025)
    detailsjpembelian = models.DetailSuratJalanPembelian.objects.filter(
        KodeProduk=penyusunobj.KodeProduk
    )
    print("ini detailsjpembelian", detailsjpembelian)
    hargatotalkodeproduk = 0
    jumlahtotalkodeproduk = 0
    for m in detailsjpembelian:
        hargatotalkodeproduk += m.Harga * m.Jumlah
        jumlahtotalkodeproduk += m.Jumlah
    print("ini jumlah harga total ", hargatotalkodeproduk)
    rataratahargakodeproduk = hargatotalkodeproduk / jumlahtotalkodeproduk
    print("selesai")
    print(rataratahargakodeproduk)
    nilaifgperkodeproduk = rataratahargakodeproduk * konversialowance
    print("Harga Konversi : ", nilaifgperkodeproduk)
    return nilaifgperkodeproduk


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def dashboard(request):
    '''
    Fitur ini digunakan untuk menampilkan dashboard dari RND
    pada dashboard RND terdapat beberapa section antara lain 
    1. Notifikasi Bahan Baku Baru
    2. Notifikasi SPK Baru
    3. Notifikasi SPPB Baru
    Algoritma
    1. Notifikasi Bahan Baku Baru
        A. Mendapatkan data dari tabel Produk dengan kriteria filter tanggalpembuatan mulai dan akhir antara hari ini dan 30 hari kebelakang
        B. Menampilkan data Bahan Baku
    2. Notifikasi SPK Baru 
        A. Mendapatkan data Tanggal SPK dengan kriteria Tanggal mulai dari hari ini dan 30 hari kebelakang
        B. Mengiterasi tiap data SPK yang didapatkan
        C. Memfilter detailSPK berdasarkan iterasi kode SPK
        D. Menambahkan atribut baru pada objek SPK untuk query set detailSPK
    3. Notifikasi SPPB Baru
        A. Mendapatkan data Tanggal SPPB dengan kriteria Tanggal mulai dari Hari ini dan 30 hari kebelakang
        B. Mengiterasi tiap data SPPB yang didapatkan
        C. Memfilter detailSPPB berdasarkan iterasi kode SPPB
        D. Menambahkan atribut baru detailsppb yang berisi queryset detailSPPB

    '''
    tanggalsekarang = date.today()
    selisihwaktu = timedelta(days=30)
    dataspk = models.SPK.objects.filter(
        Tanggal__range=(tanggalsekarang - selisihwaktu, tanggalsekarang)
    )
    for i in dataspk:
        if i.StatusDisplay == 0:
            detailspk = models.DetailSPK.objects.filter(NoSPK=i.id)
            i.detailspk = detailspk
        else:
            detailspk = models.DetailSPKDisplay.objects.filter(NoSPK=i.id)
            i.detailspk = detailspk

    dataproduk = models.Produk.objects.filter(
        TanggalPembuatan__range=(tanggalsekarang - selisihwaktu, tanggalsekarang)
    )
    print(dataproduk)
    datasppb = models.SPPB.objects.filter(
        Tanggal__range=(tanggalsekarang - selisihwaktu, tanggalsekarang)
    )
    print(datasppb)
    for i in datasppb:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=i.id)
        i.detailsppb = detailsppb
        print(detailsppb)
    return render(
        request,
        "rnd/dashboard.html",
        {"dataspk": dataspk, "dataproduk": dataproduk, "datasppb": datasppb},
    )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_artikel(request):
    '''
    FItur ini digunakan untuk manajemen data Artikel pada sistem
    Algoritma
    1. Mendapatkan semua data Artikel pada tabel Artikel
    2. Mengiterasi semua data Artikel pada tabel
    3. Mencari kode bahan baku penyusun utama tiap artikel 
    4. Apabila ada data penysuun utama maka akan menambahkan kedapat detailartikelobj untuk objek penyusunnya
    5. Apabila ada lebih dari 1 bahan baku utama (multiple version) maka akan diambil yang terakhir
    6. Apabila tidak ada bahan baku penyusun utama maka akan menambhakan keterangan "Belum diset"
    '''
    datakirim = []
    data = models.Artikel.objects.all()
    for item in data:
        detailartikelobj = models.Penyusun.objects.filter(KodeArtikel=item.id).filter(
            Status=1
        )
        if detailartikelobj.exists():
            datakirim.append([item, detailartikelobj.last()])
        else:
            datakirim.append([item, "Belum diset"])
    return render(request, "rnd/views_artikel.html", {"data": datakirim})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdataartikel(request):
    '''
    Fitur ini digunakan untuk menambahkan data artikel pada sistem
    Algoritma
    1. Menampilkan form input artikel berisi Kode Artikel dan Keterangan
    2. User menginput form
    3. Apabila kode artikel telah ada pada sistem maka akan menampilkan pesan error
    4. Apabila tidak ada maka data artikel akan disimpan kedalam sistem beserta keterangannya
    '''
    if request.method == "GET":
        return render(request, "rnd/tambah_artikel.html")
    if request.method == "POST":
        # print(dir(request))
        kodebaru = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        data = models.Artikel.objects.filter(KodeArtikel=kodebaru).exists()
        if data:
            messages.error(request, "Kode Artikel sudah ada")
            return redirect("tambahdataartikel")
        else:
            if keterangan == "":
                keterangan = "-"
            newdataobj = models.Artikel(KodeArtikel=kodebaru, keterangan=keterangan)
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Artikel : {newdataobj.KodeArtikel} Keterangan : {newdataobj.keterangan}",
            ).save()
            newdataobj.save()
            messages.success(request, "Data berhasil disimpan")
            return redirect("views_artikel")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatedataartikel(request, id):
    '''
    Fitur ini digunakan untuk melakukan update data artikel yang sudah ada pada sistem
    Alogirtma
    1. Menampilkan form update artikel berisi Kode Artikel dan Keterangan
    2. User menginput form
    3. Apabila kode artikel telah ada pada sistem kecuali kodeproduk yang diedit maka akan menampilkan pesan error
    4. Apabila tidak ada maka data artikel akan disimpan kedalam sistem beserta keterangannya
    '''
    data = models.Artikel.objects.get(id=id)
    if request.method == "GET":
        return render(request, "rnd/update_artikel.html", {"artikel": data})
    else:
        kodeartikel = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        if keterangan == "":
            keterangan = "-"
        cekkodeartikel = (
            models.Artikel.objects.filter(KodeArtikel=kodeartikel)
            .exclude(id=id)
            .exists()
        )
        if cekkodeartikel:
            messages.error(request, "Kode Artikel telah terdaftar pada database")
            return redirect("update_artikel", id=id)
        else:
            transaksilog = models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Artikel Lama : {data.KodeArtikel} Keterangan Lama : {data.keterangan} Artikel Baru : {kodeartikel} Keterangan Baru : {keterangan}",
            )
            data.KodeArtikel = kodeartikel
            data.keterangan = keterangan
            data.save()
            transaksilog.save()
            messages.success(request, "Data Berhasil diupdate")
        return redirect("views_artikel")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def deleteartikel(request, id):
    '''
    Fitur ini digunakan untuk menghapus data Artikel.
    Algoritma
    1. Mendapatkan data ID dari passing values melalui halaman awal menu Artikel
    2. Menghapus data objek artikel
    '''
    dataobj = models.Artikel.objects.get(id=id)
    models.transactionlog(
        user="RND",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Artikel : {dataobj.KodeArtikel} Keterangan : {dataobj.keterangan}",
    ).save()
    dataobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("views_artikel")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def delete_penyusun(request, id):
    '''
    Fitur ini digunakan untuk menghapus salah satu penyusun dari versi yang ada
    '''
    penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    kodeversiobj = models.Versi.objects.get(Versi = penyusunobj.KodeVersi.Versi,KodeArtikel = penyusunobj.KodeVersi.KodeArtikel)
    kodeartikel = penyusunobj.KodeArtikel.KodeArtikel
    penyusunobj.delete()
    filterversi = models.Penyusun.objects.filter(KodeVersi = kodeversiobj)
    if not filterversi.exists():
        kodeversiobj.delete()
    print(penyusunobj)
    print(id)
    messages.success(request,'Data Berhasil terhapus')
    return redirect(f"/rnd/penyusun?kodeartikel={quote(kodeartikel)}&versi=")

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def delete_versi(request, id):
    '''
    Fitur ini digunakan untuk menghapus keseluruhan versi lengkap dengan penyusunnya
    '''
    print(id)
    kodeversi = models.Versi.objects.get(pk = id)
    print(kodeversi.isdefault)
    if kodeversi.isdefault == True:
        dataversibaru = models.Versi.objects.filter(KodeArtikel = kodeversi.KodeArtikel).exclude(pk=id).order_by('Tanggal').first()
        print(dataversibaru)
        if dataversibaru != None:
            dataversibaru.isdefault = True
            dataversibaru.save()

        print('<asukkk')
    kodeversi.delete()
    messages.success(request,'Data Berhasil terhapus')
    if 'HTTP_REFERER' in request.META:
        back_url = request.META['HTTP_REFERER']
        parsed_url = urlparse(back_url)
        query_params = parse_qs(parsed_url.query)
        
        # Remove the 'versi' parameter from the query parameters
        if 'versi' in query_params:
            query_params.pop('versi')

        # Rebuild the URL without the 'versi' parameter
        updated_query = urlencode(query_params, doseq=True)
        back_url = parsed_url._replace(query=updated_query).geturl()
    else:
        back_url = '/rnd/penyusun'  # Fallback URL if there's no referer

      # URL default jika tidak ada referer
    return redirect(back_url)


# Update Delete Penyusun belum masuk


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def konversi(request):
    data = request.GET
    if len(data) == 0:
        return render(request, "views_konversi.html")
    else:
        kodeartikel = request.GET["kodeartikel"]
        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except models.Artikel.DoesNotExist:
            messages.error(request, "Data Artikel tidak ditemukan")
            return redirect("konversi")
        data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
        if data.exists():
            listdata = []
            for i in data:
                allowance = models.KonversiMaster.objects.get(
                    KodePenyusun=i.IDKodePenyusun
                )
                listdata.append(
                    [i, allowance, allowance.Kuantitas + allowance.Kuantitas * 0.025]
                )
            return render(
                request,
                "views_konversi.html",
                {"data": listdata, "kodeartikel": kodeartikel},
            )
        else:
            return render(request, "rnd/views_konversi.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def konversimaster_update(request, id):
    dataobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        return render(request, "rnd/update_konversimaster.html", {"data": dataobj})
    else:
        konversimasterobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
        print(konversimasterobj)
        konversimasterobj.Kuantitas = float(request.POST["kuantitas"])
        konversimasterobj.save()
        return redirect("konversi")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def konversimaster_delete(request, id):
    dataobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
    dataobj.Kuantitas = 0
    dataobj.save()
    return redirect("konversi")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_sppb(request):
    '''
    FItur ini digunakan untuk menampilkan SPPB yang ada pada sistem
    '''
    data = models.SPPB.objects.all()
    for sppb in data:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=sppb.id)
        sppb.Tanggal = sppb.Tanggal.strftime("%Y-%m-%d")
        sppb.detailsppb = detailsppb
    return render(request, "rnd/views_sppb.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def view_spk(request):
    '''
    FItur ini digunakan untuk menampilkan data SPK pada sistem
    '''
    dataspk = models.SPK.objects.all().order_by("-Tanggal")

    for j in dataspk:
        j.Tanggal = j.Tanggal.strftime("%Y-%m-%d")
        if j.StatusDisplay == False:
            detailspk = models.DetailSPK.objects.filter(NoSPK=j.id)
        else:
            detailspk = models.DetailSPKDisplay.objects.filter(NoSPK=j.id)
        j.detailspk = detailspk

    return render(request, "rnd/view_spk.html", {"dataspk": dataspk})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def hariterakhirdatetime(tahun):
    next_year = datetime(tahun + 1, 1, 1)
    last_day = next_year - timedelta(days=1)
    return last_day


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_ksbb(request):
    '''
    Fitur ini digunakan unutk mendapatkan data KSBB purchasing
    Algoritma :
    1. Input data Kode Bahan Baku dan Periode Tahun
    2. Memasukkan dalam fungsi Calculate KSBB
    3. Menampilkan KSBB
    '''
    kodeproduk = models.Produk.objects.all()
    sekarang = datetime.now().year
    
    if len(request.GET) == 0:
        return render(request, "rnd/view_ksbb.html", {"kodeprodukobj": kodeproduk, "sekarang": sekarang})
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except models.Produk.DoesNotExist:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbbrnd")
        
        if "periode" in request.GET and request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            tahun = sekarang
        
        
        lokasi = request.GET['lokasi']
        print(lokasi)

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, tanggal_akhir,lokasi)

        print(tahun)
        print(listdata)
        print(saldoawal)
        # print(asd)
        if saldoawal != None:
            saldoawal.Tanggal = datetime.strptime(saldoawal.Tanggal,"%Y-%m-%d")

        return render(request, "rnd/view_ksbb.html", {
            'data': listdata,
            'saldo': saldoawal,
            'kodebarang': request.GET["kodebarang"],
            "nama": nama,
            "satuan": satuan,
            'kodeprodukobj': kodeproduk,
            'tahun': tahun,
            'lokasi' : lokasi
        })

@login_required
@logindecorators.allowed_users(allowed_roles=['rnd','ppic'])
def detailksbb(request, id, tanggal,lokasi):
    '''
    Fitur ini digunakan untuk melihat data Detail KSBB perproduk per periode per tanggal
    Algoritma
    1. User menginputkan Kode Stok Bahan Baku dan periode pada fitur KSBB 
    2. User menekan Tanggal untuk melihat detail KSBB 
    3. Menampilkan Barang Masuk dari Gudang
        A. Mengambil data TransaksiGudang dengan kriteria tanggal = Tanggal input (dipilih user dan dikirim melalui passing values html), KodeProduk = kodeproduk input user (melalui html), dan Jumlah > 0 untuk mengindikasikan bahan baku masuk ke area produksi
    4. Menampilkan Barang Retur dari GUdang
        A. Mengambil data TransaksiGudang dengan kriteria tanggal = Tanggal input (dipilih user dan dikirim melalui passing values html), KodeProduk = kodeproduk input user (melalui html), dan Jumlah < 0 untuk mengindikasikan bahan retur dari area produksi
    5. Mutasi Barang Ke FG
        A. Mengambil semua list versi yang berisi data Penyusun dengan kriteria pada versi tersebut terdapat Penyusun dengan Kode Stok yyang diinputkan oleh user
        B. Mengambil data transaksi dengan versi yang terkandung dalam data listversi, dengan kriteria Tanggal = input tanggal user
        C. Mengambil data pemusnahan artikel dengan versi yang terkandung daam data listversi, dengan kriteria Tanggal = input tanggal user
        D. Mengambil data pemusnahan bahan baku dengan kodeproduk = id produk yang diinput user
        E. Mengambil data transaksi mutasi kode stok keluar (untuk mendapatkan mutasi kode stok yang akan dikeluarkan untuk kodestok lain)
        F. Mengambil data transaksi mutasi kode stok masuk ( untuk mendapatkan mutasi kode stok yang dimasukkan unutk kode stok terkait)

        

    '''
    tanggal = datetime.strptime(tanggal, "%Y-%m-%d")
    tanggal = tanggal.strftime("%Y-%m-%d")

    # Transaksi Gudang
    datagudang = models.TransaksiGudang.objects.filter(tanggal=tanggal, KodeProduk__KodeProduk=id,Lokasi__NamaLokasi=(lokasi),jumlah__gte=0)
    dataretur = models.TransaksiGudang.objects.filter(tanggal=tanggal, KodeProduk__KodeProduk=id,Lokasi__NamaLokasi=(lokasi),jumlah__lt=0)
    for item in dataretur:
        item.jumlah = item.jumlah * -1
    listartikel = (
        models.Penyusun.objects.filter(KodeProduk__KodeProduk=id)
        .values_list("KodeArtikel__KodeArtikel", flat=True)
        .distinct()
    )
    listversi = models.Penyusun.objects.filter(KodeProduk__KodeProduk=id).values_list("KodeVersi", flat=True).distinct()
    print(listversi)
    # print(asd)
    # Transaksi Produksi
    dataproduksi = models.TransaksiProduksi.objects.filter(
         VersiArtikel__in=listversi, Jenis="Mutasi", Tanggal=tanggal
    )
    print(dataproduksi)
    # print(asd)

    # Transaksi Pemusnahan
    # datapemusnahan = models.PemusnahanArtikel.objects.filter(
    #     KodeArtikel__KodeArtikel__in=listartikel, Tanggal=tanggal,
    # )
    datapemusnahan = models.PemusnahanArtikel.objects.filter(
        VersiArtikel__in=listversi, Tanggal=tanggal,
    )
    # Transaksi Pemusnahan Bahan Baku
    datapemusnahanbahanbaku  =models.PemusnahanBahanBaku.objects.filter(Tanggal = tanggal,KodeBahanBaku__KodeProduk = id,lokasi__NamaLokasi=lokasi)
    # Transaksi Mutasi Kode Stok
    datamutasikodestokkeluar = models.transaksimutasikodestok.objects.filter(Tanggal=tanggal,KodeProdukAsal__KodeProduk = id,Lokasi__NamaLokasi = lokasi)
    datamutasikodestokmasuk = models.transaksimutasikodestok.objects.filter(Tanggal=tanggal,KodeProdukTujuan__KodeProduk = id,Lokasi__NamaLokasi = lokasi)
    kodeversiincludebahanbaku = models.Penyusun.objects.filter(KodeProduk__KodeProduk = id).values_list('KodeVersi__Versi',flat=True).distinct()
    print(kodeversiincludebahanbaku)
    datapengirimanbarang = models.DetailSPPB.objects.filter(NoSPPB__Tanggal = tanggal)
    # print(datapengirimanbarang[0].VersiArtikel)
    # print(datapengirimanbarang)
    # print(datapemusnahanbahanbakuasd)
    # print(datagudang)
    return render(
        request,
        "rnd/view_detailksbb.html",
        {
            "datagudang": datagudang,
            "dataproduksi": dataproduksi,
            "datapemusnahan": datapemusnahan,
            'datapemusnahanbahanbaku' : datapemusnahanbahanbaku,
            "dataretur" : dataretur,
            'datamutasikodestokkeluar':datamutasikodestokkeluar,
            'datamutasikodestokmasuk': datamutasikodestokmasuk
        },
    )

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_ksbj(request):
    '''
    Fitur ini digunakan untuk melihat KSBJ dari Artikel yang ada pada perusahaan
    Algoritma
    1. Menginputkan Tahun 
    2. Mendapatkan data tanggal awal dan tanggal akhir dari tahun tersebut
    3. Menghitung menggunakan fungsi Calculate KSBJ
    '''
    dataartikel = models.Artikel.objects.all()
    if len(request.GET) == 0:
        return render(request, "rnd/view_ksbj.html", {"dataartikel": dataartikel})
    else:
        kodeartikel = request.GET["kodeartikel"]
        try:
            artikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Data Artikel tidak ditemukan")
            return redirect("view_ksbjrnd")

        if request.GET["tahun"]:
            tahun = int(request.GET["tahun"])
        else:
            sekarang = datetime.now()
            tahun - sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)
        lokasi = request.GET['lokasi']
        
        print(tanggal_mulai)
        print(tanggal_akhir)
        listdata,saldoawalobj = calculate_ksbj(artikel,lokasi,tanggal_mulai.year)

        
        print(listdata)

        return render(
            request,
            "rnd/view_ksbj.html",
            {
                "data": listdata,
                "kodeartikel": kodeartikel,
                "dataartikel": dataartikel,
                "lokasi": lokasi,
                "listdata": listdata,
                "saldoawal": saldoawalobj,
                "tahun": tahun,
            },
        )
        


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def uploadexcel(request):
    if request.method == "POST":
        excel_file = request.FILES["excel_file"]
        if excel_file.name.endswith(".xlsx"):
            df = pd.read_excel(excel_file)
            print(df["KodeProduk"].tolist())
            # Lakukan operasi yang diperlukan dengan dataframe
            # Misalnya, simpan dataframe ke database atau lakukan analisis
            excel_file = BytesIO()
            # df.to_excel('export data.xlsx',index=False)
            with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            excel_file.seek(0)
            response = HttpResponse(
                excel_file.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="data_export.xlsx"'
            return response
        else:
            return HttpResponse("File harus berformat .xlsx")
    return render(request, "rnd/formexcel.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_rekapharga(request):
    kodeprodukobj = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(request, "rnd/views_ksbb.html", {"kodeprodukobj": kodeprodukobj})
    else:
        kode_produk = request.GET["kode_produk"]
        tahun = request.GET["tahun"]
        tahun_period = tahun

        if tahun == "":
            tahun = "2024"

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
            KodeProduk__KodeProduk=produkobj.KodeProduk, NoSuratJalan__Tanggal__gte=awaltahun
        )

        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk__KodeProduk=produkobj.KodeProduk, tanggal__gte=awaltahun
        )
        returobj = models.TransaksiGudang.objects.filter(
            jumlah__lt=0, KodeProduk__KodeProduk=produkobj.KodeProduk, tanggal__gte=awaltahun
        )
        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
        tanggalretur = returobj.values_list("tanggal", flat=True)
        print("ini kode bahan baku", keluarobj)
        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku__KodeProduk=produkobj.KodeProduk,
                IDLokasi__IDLokasi=3,
                Tanggal__range=(awaltahun, akhirtahun),
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
            return redirect("rekaphargarnd")
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
            "tanggal": tahun,
        }
        hargaterakhir = 0
        listdata = []
        # print(tanggalmasuk)
        # print(tanggalkeluar)
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
                # print("data SJP ada")
                # print(hargamasuksatuanperhari)
                # print(jumlahmasukperhari)
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
                try:
                    hargasatuanawal = hargatotalawal / saldoawal
                except ZeroDivisionError:
                    hargasatuanawal = 0 

                # print("Sisa Stok Hari Ini : ", saldoawal)
                # print("harga awal Hari Ini :", hargasatuanawal)
                # print("harga total Hari Ini :", hargatotalawal, "\n")
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

            # print("Tanggal : ", i)
            # print("Sisa Stok Hari Sebelumnya : ", saldoawal)
            # print("harga awal Hari Sebelumnya :", hargasatuanawal)
            # print("harga total Hari Sebelumnya :", hargatotalawal)
            # print("Jumlah Masuk : ", jumlahmasukperhari)
            # print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
            # print("Harga Total Masuk : ", hargamasuktotalperhari)
            # print("Jumlah Keluar : ", jumlahkeluarperhari)
            # print("Harga Keluar : ", hargakeluarsatuanperhari)
            # print(
            #     "Harga Total Keluar : ", hargakeluarsatuanperhari * jumlahkeluarperhari
            # )
            

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
            try:
                hargasatuanawal = hargatotalawal / saldoawal
            except:
                hargasatuanawal = 0

            # print("Sisa Stok Hari Ini : ", saldoawal)
            # print("harga awal Hari Ini :", hargasatuanawal)
            # print("harga total Hari Ini :", hargatotalawal, "\n")
            dumy["Sisahariini"] = saldoawal
            dumy["Hargasatuansisa"] = hargasatuanawal 
            dumy["Hargatotalsisa"] = hargatotalawal

            listdata.append(dumy)

        hargaterakhir += hargasatuanawal

        return render(
            request,
            "rnd/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
                "kode_produk": produkobj,
                "tahun": tahun_period,
            },
        )


"""
REVISI 
5/13/2024
1. Revisi views Penyusun Konversi
2. Add datalist ke KodeProduk pada Add Versi
3. Revisi Perhitungan Bahan Baku
4. Revisi Keterangan Produk
"""


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def read_produk(request):
    '''
    Fitur ini digunakan untuk menampilkan semua data bahan baku yang ada pada sistem
    '''
    produkobj = models.Produk.objects.all()
    print(produkobj[1].keteranganRND)
    return render(request, "rnd/read_produk.html", {"produkobj": produkobj})

def updateversi(request):
    '''
    Fitur ini digunakan untuk melakukan update status default pada sistem
    '''
    if request.method == 'POST':
        print(request.POST)
        versiartikelobj = models.Versi.objects.get(pk = request.POST['versi'])
        versiartikelfiltered = models.Versi.objects.filter(KodeArtikel=versiartikelobj.KodeArtikel)
        for item in versiartikelfiltered :
            item.isdefault = False
            item.save()
        versiartikelobj.isdefault = True
        versiartikelobj.save()
        # print(versiartikelfiltered)
        print(request.META['HTTP_REFERER'])
        return redirect(request.META['HTTP_REFERER'])
    else:
        messages.error(request,'Anda Tidak diizinkan mengakses halaman ini secara langsung')
        return render(
                request,
                "rnd/views_penyusun.html",
                {"dataartikel": models.Artikel.objects.all()},
            )

def rekap_produksi(request):
    if len(request.GET) == 0:
        return render(request, "rnd/rekap_produksi.html")
    else:
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        datarekap = []

        artikelobj = models.Artikel.objects.all()
        # artikelobj = models.Artikel.objects.filter(KodeArtikel = '9010 AC')
        for artikel in artikelobj:

            print(artikel)
            
            dataartikel = []
            getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1)

            if not getbahanbakuutama :
                messages.error(request, ("Bahan Baku",artikel.KodeArtikel,"belum di set"))
                continue

            data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel,Jenis = "Mutasi",Tanggal__range=(tanggal_mulai,tanggal_akhir))
            print(data)
            datamasuk = models.TransaksiGudang.objects.filter(DetailSPK__KodeArtikel = artikel.id,tanggal__range=(tanggal_mulai, tanggal_akhir),KodeProduk = getbahanbakuutama.first().KodeProduk)
            print(datamasuk)
            # print(datapemusnahan)
            # print(asd)
            listtanggalmasuk = datamasuk.values_list('tanggal',flat=True).distinct()

            if not data :
                messages.error(request, ("Tidak ditemukan data Transaki Produksi untuk Artikel",artikel.KodeArtikel))
                continue
            else:
                dataartikel.append(artikel.KodeArtikel)
                
            lokasiobj = models.Lokasi.objects.all()

            for lokasi in lokasiobj[:2]:

                listdata = []

                if lokasi.NamaLokasi == "WIP":
                    datapemusnahan = models.PemusnahanArtikel.objects.filter(Tanggal__range=(tanggal_mulai,tanggal_akhir),KodeArtikel = artikel,lokasi__NamaLokasi = 'WIP')
                    listtanggalpemusnahan = datapemusnahan.values_list('Tanggal',flat=True).distinct()
                    data = data.filter(Lokasi=lokasi.IDLokasi)
                    try:
                        # tessaldo = models.SaldoAwalArtikel.objects.filter(IDArtikel__KodeArtikel=artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                        # print(artikel)
                        # print(tessaldo)
                        saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                        saldo = saldoawalobj.Jumlah
                        listtanggalsaldo = models.SaldoAwalArtikel.objects.filter(IDArtikel__KodeArtikel=artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir)).values_list("Tanggal", flat=True).distinct()
                        saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")

                    except models.SaldoAwalArtikel.DoesNotExist :
                        saldo = 0
                        saldoawal = None
                        saldoawalobj = {'Tanggal' : 'Belum ada Data','saldo' : saldo}
                        listtanggalsaldo = None
                        

                    tanggallist = data.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir)).values_list("Tanggal", flat=True).distinct()
                    saldoawal = saldo                        

                    if listtanggalsaldo:
                        tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk.union(listtanggalsaldo).union(listtanggalpemusnahan))))))
                    else:
                        tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk).union(listtanggalpemusnahan)))))

                    for i in tanggallist:
                        datamodels = {
                            "Tanggal" : None,
                            "Sisa" : None
                        }

                        filtertanggal = data.filter(Tanggal=i)
                        filtertanggaltransaksigudang = datamasuk.filter(tanggal=i)
                        filtertanggalpemusnahan = datapemusnahan.filter(Tanggal = i)

                        jumlahmutasi =  filtertanggal.filter(Jenis ="Mutasi").aggregate(total = Sum('Jumlah'))['total']
                        jumlahmasuk = filtertanggaltransaksigudang.aggregate(total = Sum('jumlah'))['total']
                        jumlahpemusnahan =  filtertanggalpemusnahan.aggregate(total = Sum('Jumlah'))['total']
                       
                        # if jumlahmasuk != None:

                        #     # print(asd)

                        if jumlahmutasi is None:
                            jumlahmutasi = 0
                        if jumlahmasuk is None :
                            jumlahmasuk = 0
                        if jumlahpemusnahan is None:
                            jumlahpemusnahan = 0

                        # Cari data penyusun sesuai tanggal 
                        penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id,Status = 1,KodeVersi__Tanggal__lte = i).order_by('-KodeVersi__Tanggal').first()

                        if not penyusunfiltertanggal:
                            penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id, Status = 1, KodeVersi__Tanggal__gte = i).order_by('KodeVersi__Tanggal').first()

                        # konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)

                        cekpenyesuaian = models.PenyesuaianArtikel.objects.filter(KodeArtikel = artikel, TanggalMulai__lte=i, TanggalMinus__gte=i)
                        allowance = penyusunfiltertanggal.Allowance
                        # print('ini penyesuaian : ', cekpenyesuaian)
                        try:
                            masukpcs = math.ceil(jumlahmasuk/((allowance)))
                        except:
                            masukpcs = 0
                            messages.error(request,"Data allowance belum di setting")
                        if cekpenyesuaian.exists():
                            masukpcs = round(masukpcs*cekpenyesuaian.first().konversi)
                        saldoawal = saldoawal - jumlahmutasi + masukpcs -jumlahpemusnahan
                        print(i)
                        print(saldoawal)
                        
                       
                            # print(asd)
                        datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                        datamodels['Sisa'] = saldoawal

                        listdata.append(datamodels)

                else:
                    datapemusnahan = models.PemusnahanArtikel.objects.filter(Tanggal__range=(tanggal_mulai,tanggal_akhir),KodeArtikel = artikel,lokasi__NamaLokasi = 'FG')
                    listtanggalpemusnahan = datapemusnahan.values_list('Tanggal',flat=True).distinct()
                    data = data.filter(Lokasi=1)
                    try:
                        saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel= artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                        saldo = saldoawalobj.Jumlah
                        saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
                    except models.SaldoAwalArtikel.DoesNotExist :
                        saldo = 0
                        saldoawalobj ={
                            'Tanggal' : 'Belum ada Data',
                            'saldo' : saldo
                        }

                    tanggalmutasi = data.filter(Jenis = 'Mutasi',Tanggal__range=(tanggal_mulai,tanggal_akhir)).values_list('Tanggal',flat=True).distinct()
                    sppb = models.DetailSPPB.objects.filter(DetailSPK__KodeArtikel__KodeArtikel = artikel.KodeArtikel, NoSPPB__Tanggal__range = (tanggal_mulai,tanggal_akhir))
                    tanggalsppb = sppb.values_list('NoSPPB__Tanggal',flat=True).distinct()
                    tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb).union(listtanggalpemusnahan))))
                    saldoawal = saldo

                    for i in tanggallist:
                        datamodels = {
                            "Tanggal" : None,
                            "Sisa" : None
                        }

                        penyerahanwip = models.TransaksiProduksi.objects.filter(Tanggal = i, KodeArtikel__KodeArtikel = artikel.KodeArtikel, Jenis = "Mutasi", Lokasi__NamaLokasi = "WIP" )
                        detailsppbjobj = sppb.filter(NoSPPB__Tanggal = i)
                        filteredpemusnahan = datapemusnahan.filter(Tanggal = i)

                        totalpenyerahanwip = penyerahanwip.aggregate(total=Sum('Jumlah'))['total']
                        totalkeluar = detailsppbjobj.aggregate(total=Sum('Jumlah'))['total']
                        totalpemusnahan = filteredpemusnahan.aggregate(total=Sum('Jumlah'))['total']
                        
                        if not totalpenyerahanwip:
                            totalpenyerahanwip = 0
                        if not totalkeluar :
                            totalkeluar = 0
                        if not totalpemusnahan:
                            totalpemusnahan = 0

                        saldoawal += totalpenyerahanwip - totalkeluar - totalpemusnahan

                        datamodels ['Tanggal'] = i.strftime('%Y-%m-%d')
                        datamodels['Sisa'] = saldoawal
                        listdata.append(datamodels)

                if not listdata:
                    pass
                else:
                    df = pd.DataFrame(listdata)

                    # Convert 'Tanggal' column to datetime
                    df['Tanggal'] = pd.to_datetime(df['Tanggal'])

                    # Resampling to get the last day of each month
                    df_resampled = df.resample('M', on='Tanggal').last().ffill().reset_index()

                    # Creating a new DataFrame with all months from 1 to 12
                    all_months = pd.date_range(start=tanggal_mulai, end=tanggal_akhir, freq='M')
                    df_all_months = pd.DataFrame({'Tanggal': all_months})

                    # Merging the resampled data with all months
                    result_df = pd.merge(df_all_months, df_resampled, on='Tanggal', how='left').ffill()

                    # Getting the data for all months
                    result_data = result_df.to_dict('records')
                
                    dataartikel.append(result_data)
            
            if len(dataartikel) == 1:
                pass
            else:
                item3 = [{'Tanggal': d1['Tanggal'], 'Sisa': d1['Sisa'] + d2['Sisa']} for d1, d2 in zip(dataartikel[1], dataartikel[2])]
                
                dataartikel.append(item3)

                datarekap.append(dataartikel)
        print(datarekap)

        return render(request, "rnd/rekap_produksi.html", {'artikel':artikelobj, 'data':datarekap, 'tahun':tahun })

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_penyusun(request):
    '''
    Fitur ini digunakan untuk melakukan manajemen data konversi pada tiap artikel
    Pada bagian ini user dapat melakukan Melihat Konversi Artikel, Melihat Versi pada Artikel, dan manajemen konversi data artikel
    Algoritma
    1. User mengisi form input kode artikel yang akan dilihat
    2. Secara default, program akan menampilkan data konversi untuk versi default dari kode artikel tersebut
    3. User dapat melakukan manajemen data konversi pada halaman tersebut.
    
    Algoritma mendapatkan Harga Purchasing
    1. Mengambil data penyusun artikel dengan kriteria (KoveVersi__Versi = versiterpilih)
    2. Mengiterasi semua data penyusun pada hasil filter poin 1
    3. memfilter Cache Value dengan kode produk sesuai iterasi dan bulan saat ini
    4. Apabila ada data cachevalue maka akan mengambil data pertama pada queryset tersebut untuk dijadikan data harga bahan baku
    5. Apabila tidak ada maka akan dilakukan proses iterasi menggunakan KSBB.

    Algoritma KSBB
    3. Program mendapatkan input berupa kode produk 
    4. Data tanggal mulai = Awal tahun, Data tanggal akhir = Akhir tahun 
    5. Mengambil data DetailSuratJalanPembelian dengan kriteria KodeProduk = kode produk input user, NoSuratJalan__Tanggal__range = awal tahun, akhir tahun. 
    6. mengambil data Transaksi Gudang keluar dengan kriteria Jumlah >= 0 (mengindikasikan barang keluar), KodeProduk = kode produk input user, Tanggal dalam rentang awal tahun hingga akhir tahun
    7. mengambil data Transaksi Gudang retur dengan kriteria Jumlah < 0 (mengindikasikan barang keluar), KodeProduk = kode produk input user, Tanggal dalam rentang awal tahun hingga akhir tahun
    8. mengambil data pemusnahan bahan baku  dengan lokasi Gudang, kodeproduk = kode produk input user, Tanggal berada dalam rentanga awal tahun, akhirtahun
    9. Mengambil data saldo awal bahan baku dengan kriteria kode produk = kode produk input user, Lokasi = Gudang, Tanggal berada dalam rentang awal tahun dan akhir tahun
    10. Mengiterasi setiap tanggal dari detailsuratjalanpembelian, transaksigudang keluar, transaksigudang retur, dan pemusnahan bahan baku 
    11. Total Stok = Saldoawal bahan baku + Detail surat jalan pembelian + Transaksi Gudang Retur - pemusnahan bahan baku - transaksi gudang keluar
    12. Menghitung harga satuan = harga total / total stok (perhitungan menggunakan weighted average)
    13. Apabila ada pembagian dengan hasil Null / pembagi 0 maka akan diset menjadi 0
    

    '''
    print(request.GET)
    dataartikel = models.Artikel.objects.all()
    if len(request.GET) == 0:
    
        return render(request, "rnd/views_penyusun.html", {"dataartikel": dataartikel})
    else:
        kodeartikel = request.GET["kodeartikel"]

        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
            data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
            versifiltered = models.Versi.objects.filter(KodeArtikel = get_id_kodeartikel)
            dataversi = versifiltered.values_list("Versi", flat=True).distinct()
            print(dataversi)
            if dataversi.exists():
                try:
                    if request.GET["versi"] == "":
                        versiterpilih = versifiltered.filter(isdefault=True).first().Versi
                        print("ini versi terbaru", versiterpilih)
                    else:
                        versiterpilih = request.GET["versi"]
                except:
                    versiterpilih = dataversi.order_by("-Versi").first()
                    print("ini versi terbaru", versiterpilih)
                
                data = data.filter(KodeVersi__Versi=versiterpilih)
                datakonversi = []
                nilaifg = 0
                sekarang = date.today()
                awaltahun = date(sekarang.year, 1, 1)
                akhirtahun = date(sekarang.year,12,31)
                print(data)
                if data.exists():
                    for item in data:
                        hargaterakhir = 0
                        print(item, item.IDKodePenyusun)
                        
                        kuantitaskonversi = item.Kuantitas
                        kuantitasallowance = item.Allowance
                        cachevalue = models.CacheValue.objects.filter(KodeProduk = item.KodeProduk, Tanggal__month =sekarang.month).first()
                        if cachevalue:
                            hargasatuanawal = cachevalue.Harga
                        else:
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
                                kuantitaskonversi = item.Kuantitas
                                kuantitasallowance = item.Allowance
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
                                'Keterangan' : item.keterangan
                            }
                        )
                    HargaFGArtikel= None
                    hargaartikel = models.HargaArtikel.objects.filter(KodeArtikel =get_id_kodeartikel,Tanggal__month = sekarang.month)
                    if hargaartikel.exists():
                        HargaFGArtikel = hargaartikel.first().Harga

                    return render(
                        request,
                        "rnd/views_penyusun.html",
                        {
                            "data": datakonversi,
                            "kodeartikel": get_id_kodeartikel,
                            "nilaifg": nilaifg,
                            "versiterpilih": versiterpilih,
                            "dataversi": dataversi,
                            'dataartikel' : dataartikel,
                            "hargafgartikel" : HargaFGArtikel,
                            'versiterpilihobj': models.Versi.objects.get(Versi = versiterpilih,KodeArtikel=get_id_kodeartikel)
                        },
                    )
                else:
                    print('tes')
                    print(data)
                    print(versiterpilih)
                    messages.error(request, "Versi tidak memiliki penyusun")
                    return render(
                        request,
                        "rnd/views_penyusun.html",
                        {
                            "data": datakonversi,
                            "kodeartikel": get_id_kodeartikel,
                            "nilaifg": nilaifg,
                            "versiterpilih": versiterpilih,
                            "dataversi": dataversi,
                            'dataartikel' : dataartikel,
                            'versiterpilihobj': models.Versi.objects.get(Versi = versiterpilih, KodeArtikel = get_id_kodeartikel)

                            
                        },)
            else:
                print('asd')
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


# @login_required
# @logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
# def tambahversi(request, id):
   
    
#     data = models.Artikel.objects.get(id=id)
#     bahanbaku = models.Produk.objects.all()
#     tanggal = date.today().strftime("%Y-%m-%d")
#     # print(request.META)
#     # print(request.META['HTTP_REFERER'])
#     print(tanggal)
#     if request.method == "GET":
#         if 'HTTP_REFERER' in request.META:
#             back_url = request.META['HTTP_REFERER']
#         else:
#             back_url = '/rnd/penyusun'  # URL default jika tidak ada referer
#         return render(
#             request,
#             "rnd/tambah_versi.html",
#             {"data": data, "versi": tanggal, "dataproduk": bahanbaku,'backurl':back_url},
#         )
#     else:
#         print(request.POST)
#         kodeproduk = request.POST.getlist("kodeproduk")
#         status = request.POST.getlist("Status")
#         lokasi = request.POST.getlist("lokasi")
#         kuantitas = request.POST.getlist("kuantitas")
#         tanggal = request.POST["versi"]
#         allowance = request.POST.getlist("allowance")
#         # print(asdas)
#         if status.count("True") > 1:
#             messages.error(request, "Terdapat Artikel utama lebih dari 1")
#             return redirect("add_versi", id=id)
#         dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas, allowance))
#         print(dataproduk)
#         for i in dataproduk:
#             try:
#                 produkobj = models.Produk.objects.get(KodeProduk=i[0])
#             except:
#                 messages.error(request, f"Data artikel {i[0]} tidak ditemukan")
#                 continue
#             newpenyusun = models.Penyusun(
#                 KodeProduk=produkobj,
#                 KodeArtikel=data,
#                 Status=i[1],
#                 Lokasi=models.Lokasi.objects.get(NamaLokasi=i[2]),
#                 versi=tanggal,
#             )
#             newpenyusun.save()
#             datanewpenyusun = models.Penyusun.objects.all().last()
#             konversimasterobj = models.KonversiMaster(
#                 KodePenyusun=datanewpenyusun, Kuantitas=i[3], Allowance=i[4]
#             )
#             konversimasterobj.save()

#         return redirect(
#             f"/rnd/penyusun?kodeartikel={quote(data.KodeArtikel)}&versi={tanggal}"
#         )

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahversibaru(request, id):
    '''
    Fitur ini digunakan untuk menambahkan data versi pada artikel
    
    Algoritma :
    1. mendapatkan data Artikel dengan parameter id(primarykey) = id (didapatkan dari passing values HTML)
    2. menampilkan form input versi
    3. Program mendapatkan input berupa list kode produk, list status, list lokasi, list kuantitas, list allowance, Tanggal versi, keteranganversi
    4. Program akan cek apakah ada bahan baku penyusun utama lebih dari 1 pada list status
    5. Kalau ada maka akan menampilkan pesan error.
    6. program akan cek kode versi apakah sudah ada untuk artikel tersebut 
    7. Apabila ada maka akan menampilkan pesan eror
    8. Membuat Versi Object dengan KodeArtikel = artikel, Versi = input kode versi, Keterangan = input keterangan versi 
    9. menyimpan data versi
    10. Mengiterasi data list produk
    11. membuat object penyusun dengan kriteria Kode Produk = produk iterasi, Kode artikel = artikel, Status = status iterasi, lokasi = lokasi iterasi, kodeversi = objects terakhir pada tabel versi, kuantitas = kuantitas iterasi, allowance = allowance iterasi
    12. Menyimpan data penyusun

    '''
    print(id)
    data = models.Artikel.objects.get(pk=id)
    bahanbaku = models.Produk.objects.all()
    tanggal = date.today().strftime("%Y-%m-%d")
    # print(request.META)
    # print(request.META['HTTP_REFERER'])
    print(tanggal)
    if request.method == "GET":
        if 'HTTP_REFERER' in request.META:
            back_url = request.META['HTTP_REFERER']
        else:
            back_url = '/rnd/penyusun'  # URL default jika tidak ada referer
        return render(
            request,
            "rnd/tambah_versibaru.html",
            {"data": data, "versi": tanggal, "dataproduk": bahanbaku,'backurl':back_url},
        )
    else:
        print(request.POST)
        # datates = models.Artikel.objects.last()
        # print(datates)
        # print(asd)
        kodeproduk = request.POST.getlist("kodeproduk")
        status = request.POST.getlist("Status")
        lokasi = request.POST.getlist("lokasi")
        kuantitas = request.POST.getlist("kuantitas")
        tanggal = request.POST["tanggal"]
        allowance = request.POST.getlist("allowance")
        kodeversi = request.POST['versi']
        keteranganversi = request.POST['keterangan']
        # print(asdas)
        if status.count("True") > 1:
            messages.error(request, "Terdapat Artikel utama lebih dari 1")
            return redirect("add_versibaru", id=id)
        dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas, allowance))
        print(dataproduk)
        # buat data versi
        cekversi = models.Versi.objects.filter( KodeArtikel = data)
        default = False
        if not cekversi.exists():
            default = True
        cekexistingdata = models.Versi.objects.filter( KodeArtikel = data, Versi = kodeversi)
        if cekexistingdata.exists():
            messages.error(request,f'Kode versi {kodeversi} pada artikel {data.KodeArtikel} sudah terdaftar pada sistem')
            return redirect("add_versibaru", id=id)
        newversiobj = models.Versi(
            KodeArtikel = data,
            Versi = kodeversi,
            Tanggal = tanggal,
            Keterangan = keteranganversi,
            isdefault = default
        )
        newversiobj.save()
        for i in dataproduk:
            try:
                produkobj = models.Produk.objects.get(KodeProduk=i[0])
            except:
                messages.error(request, f"Data artikel {i[0]} tidak ditemukan")
                continue
            newpenyusun = models.Penyusun(
                KodeProduk=produkobj,
                KodeArtikel=data,
                Status=i[1],
                Lokasi=models.Lokasi.objects.get(NamaLokasi=i[2]),
                KodeVersi = models.Versi.objects.last(),
                Kuantitas=i[3], 
                Allowance=i[4]
            )
            newpenyusun.save()
        messages.success(request,'Data berhasil disimpan')

        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(data.KodeArtikel)}&versi={kodeversi}"
        )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdatapenyusun(request, id, versi):
    '''
    Fitur ini digunakan untuk menambahkan penyusun baru dalam versi artikel terkait
    Algoritma 
    1. Mengambil data ID Versi melalui passing value HTML pada menu penyusun 
    2. Mengambil data ID Artikel melalui passing value HTML pada menu penyusun
    3. Mengambil list data kode produk, status, lokasi, kuantitas, dan allowance
    4. Memasangkan kode produk, status, lokasi, kuantitas dan allowance kemudian mengiterasi data tersebut
    5. Menyimpan data dalam tabel Penyusun.
    '''
    dataartikelobj = models.Artikel.objects.get(id=id)
    versiobj = models.Versi.objects.get(pk = versi)
    print(versi, "asdas")
    if request.method == "GET":
        if 'HTTP_REFERER' in request.META:
            back_url = request.META['HTTP_REFERER']
        else:
            back_url = '/rnd/penyusun'
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "rnd/tambah_penyusunversi.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versiobj,
                'backurl':back_url
            },
        )
    else:
        print(request.POST)
        # print(asd)
        listkodeproduk = request.POST.getlist("kodeproduk")
        statusproduk = request.POST.getlist("status")
        listlokasi = request.POST.getlist("lokasi")
        listkuantitas = request.POST.getlist("kuantitas")
        listallowance = request.POST.getlist("allowance")
        versi  = request.POST['idversi']
        print(listkodeproduk)
        print(statusproduk)
        print(listlokasi)
        print(listkuantitas)
        print(listallowance)

        # versiobj =models.Versi.objects.get(pk = versi)

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, KodeVersi__Versi=versi)
            .exists()
        )
        for kodeproduk, status, lokasi, kuantitas, allowance in zip(
            listkodeproduk, statusproduk, listlokasi, listkuantitas, listallowance
        ):

            try:

                newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
            except:
                messages.error(
                    request,
                    f"Kode bahan baku {kodeproduk} tidak ditemukan dalam sistem",
                )
                continue
            print("\n\n", status)
            if datapenyusunobj and status == "True":
                messages.error(
                    request,
                    f"Artikel telah memiliki Bahan baku utama sebelumnya, Kode bahan baku {kodeproduk} gagal disimpan",
                )
                continue
            lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
            penyusunobj = models.Penyusun(
                Status=status,
                KodeArtikel=dataartikelobj,
                KodeProduk=newprodukobj,
                Lokasi=lokasiobj,
                KodeVersi=versiobj,
                Kuantitas=kuantitas,
                lastedited=datetime.now(),
                Allowance=allowance,
            )
            penyusunobj.save()
            messages.success(request, "Data penyusun berhasil ditambahkan")
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Penyusun. Kode Artikel : {dataartikelobj.KodeArtikel}, Kode produk : {newprodukobj.KodeProduk}-{newprodukobj.NamaProduk}, Status Utama : {statusproduk} versi : {versi}, Kuantitas Konversi : {kuantitas}",
            ).save()
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(dataartikelobj.KodeArtikel)}&versi="
        )

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdatapenyusunversi(request, id, versi):
    dataartikelobj = models.Artikel.objects.get(id=id)
    print(versi, "asdas")
    if request.method == "GET":
        if 'HTTP_REFERER' in request.META:
            back_url = request.META['HTTP_REFERER']
        else:
            back_url = '/rnd/penyusun'
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "rnd/tambah_penyusun.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versi,
                'backurl':back_url
            },
        )
    else:

        kodeproduk = request.POST.getlist("kodeproduk")
        statusproduk = request.POST.getlist("status")
        listlokasi = request.POST.getlist("lokasi")
        listkuantitas = request.POST.getlist("kuantitas")
        listallowance = request.POST.getlist("allowance")

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, versi=versi)
            .exists()
        )
        for kodeproduk, status, lokasi, kuantitas, allowance in zip(
            kodeproduk, statusproduk, listlokasi, listkuantitas, listallowance
        ):

            try:

                newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
            except:
                messages.error(
                    request,
                    f"Kode bahan baku {kodeproduk} tidak ditemukan dalam sistem",
                )
                continue
            print("\n\n", status)
            if datapenyusunobj and status == "True":
                messages.error(
                    request,
                    f"Artikel telah memiliki Bahan baku utama sebelumnya, Kode bahan baku {kodeproduk} gagal disimpan",
                )
                continue
            lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
            penyusunobj = models.Penyusun(
                Status=status,
                KodeArtikel=dataartikelobj,
                KodeProduk=newprodukobj,
                Lokasi=lokasiobj,
                versi=versi,
            )
            penyusunobj.save()
            konversimasterobj = models.KonversiMaster(
                KodePenyusun=penyusunobj,
                Kuantitas=kuantitas,
                lastedited=datetime.now(),
                Allowance=allowance,
            ).save()
            messages.success(request, "Data penyusun berhasil ditambahkan")
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Penyusun. Kode Artikel : {dataartikelobj.KodeArtikel}, Kode produk : {newprodukobj.KodeProduk}-{newprodukobj.NamaProduk}, Status Utama : {statusproduk} versi : {versi}, Kuantitas Konversi : {kuantitas}",
            ).save()
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(dataartikelobj.KodeArtikel)}&versi="
        )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatepenyusun(request, id):
    '''
    Fitur ini digunakan untuk melakukan update data bahan penyusun sesuai dengan kode penyusunnya
    Algoritma : 
    1. mendapatkan data penysuun dengan kriteria IDKodePenyusun = id (id didapatkan dari passing values HTML)
    2. menampilkan form update penyusun 
    3. program menerima input kodeproduk, lokasi, status, kuantitas, allowance, dan kodeversi
    4. Mengupdate data penyusun dengan kode produk input, lokasi input, status input, kuantitas input, dan allowance input
    5. menyimpan data penyusun
    6. Apabila kodeversi berubah, mengupdate data versi

    '''
    data = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        if 'HTTP_REFERER' in request.META:
            back_url = request.META['HTTP_REFERER']
        else:
            back_url = '/rnd/penyusun'

        kodebahanbaku = models.Produk.objects.all()
        lokasiobj = models.Lokasi.objects.all()
        return render(
            request,
            "rnd/update_penyusun.html",
            {
                "kodestok": kodebahanbaku,
                "data": data,
                "lokasi": lokasiobj,
                'backurl':back_url
            },
        )
    else:
        print(request.POST)
        # print(asd)
        kodeproduk = request.POST["kodeproduk"]
        lokasi = request.POST["lokasi"]
        status = request.POST["status"]
        kuantitas = request.POST["kuantitas"]
        allowance = request.POST["allowance"]
        kodeversi = request.POST['kodeversi']
        keterangan = request.POST['keterangan']
        keteranganversi = request.POST['keteranganversi']

        datapenyusun = (
            models.Penyusun.objects.filter(KodeArtikel= data.KodeArtikel,KodeVersi=data.KodeVersi, Status=True)
            .exclude(IDKodePenyusun=id)
            .exists()
        )

        if datapenyusun and status == "True":
            messages.error(
                request,
                f"Artikel {data.KodeArtikel.KodeArtikel} pada Versi {data.versi} telah memiliki bahan penyusun utama",
            )
            return redirect("update_penyusun", id=id)

        try:
            produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        except:
            messages.error(
                request, f"Data bahan baku {kodeproduk} tidak ditemukan dalam sistem "
            )
            return redirect("update_penyusun", id=id)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
        data.KodeProduk = produkobj
        data.Lokasi = lokasiobj
        data.Status = status
        data.Kuantitas = kuantitas
        data.Allowance = allowance
        data.keterangan = keterangan
        data.lastedited = datetime.now()
        
        if data.KodeVersi.Versi != kodeversi:
            data.KodeVersi.Versi = kodeversi
            print(data.KodeVersi.Versi,kodeversi)
            data.KodeVersi.save()
        if data.KodeVersi.Keterangan != keteranganversi:
            data.KodeVersi.Keterangan = keteranganversi
            data.KodeVersi.save()

        data.save()
        transaksilog = models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Penyusun Baru. Kode Artikel : {data.KodeArtikel}, Kode produk : {data.KodeProduk}-{data.KodeProduk.NamaProduk}, Status Utama : {data} versi : {data.KodeVersi}, Kuantitas Konversi : {  data.Kuantitas}",
        )
        transaksilog.save()
        messages.success(request, "Data berhasil disimpan")
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(data.KodeArtikel.KodeArtikel)}&versi={data.KodeVersi.Versi}"
        )

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatekonversi(request, id):
    '''
    Fitur ini digunakan untuk melakukan update data bahan penyusun sesuai dengan kode penyusunnya
    Algoritma : 
    1. mendapatkan data penysuun dengan kriteria IDKodePenyusun = id (id didapatkan dari passing values HTML)
    2. menampilkan form update penyusun 
    3. program menerima input kodeproduk, lokasi, status, kuantitas, allowance, dan kodeversi
    4. Mengupdate data penyusun dengan kode produk input, lokasi input, status input, kuantitas input, dan allowance input
    5. menyimpan data penyusun
    6. Apabila kodeversi berubah, mengupdate data versi

    '''
    data = models.Versi.objects.get(pk=id)
    filterdetailkonversi = models.Penyusun.objects.filter(KodeVersi = data)
    data.konversi = filterdetailkonversi
    if request.method == "GET":
        if 'HTTP_REFERER' in request.META:
            back_url = request.META['HTTP_REFERER']
        else:
            back_url = '/rnd/penyusun'
        

        kodebahanbaku = models.Produk.objects.all()
        lokasiobj = models.Lokasi.objects.all()
        return render(
            request,
            "rnd/update_konversi.html",
            {
                "kodestok": kodebahanbaku,
                "data": data,
                "lokasi": lokasiobj,
                'backurl':back_url
                
            },
        )
    else:
        print(request.POST)
        listkodeproduk = request.POST.getlist("kodeproduk")
        listlokasi = request.POST.getlist("lokasi")
        liststatus = request.POST.getlist("status")
        listkuantitas = request.POST.getlist("kuantitas")
        listallowance = request.POST.getlist("allowance")
        listketerangan = request.POST.getlist('keterangan')
        # print(listketerangan)
        kodeartikel = request.POST['kodeartikel']
        kodeversi = request.POST['kodeversi']
        print(kodeversi)
        if data.Versi != kodeversi:
            data.Versi = kodeversi
            data.save()
        # print(asd)
        
        # kodeversi = request.POST['kodeversi']
        dataversi = models.Versi.objects.filter(KodeArtikel__KodeArtikel = kodeartikel,Versi = kodeversi).first()

        # datapenyusun = (
        #     models.Penyusun.objects.filter(KodeArtikel= data.KodeArtikel,KodeVersi=data.KodeVersi, Status=True)
        #     .exclude(IDKodePenyusun=id)
        #     .exists()
        # )
        jumlahstatus = liststatus.count('True')
        print(jumlahstatus)
        # print(asd)
        if jumlahstatus >1:
            messages.error(
                request,
                f"Artikel {dataversi.KodeArtikel.KodeArtikel} pada Versi {data.Versi} telah memiliki bahan penyusun utama",
            )
            return redirect("update_konversi", id=id)
        # for kodeproduk,lokasi, status, kuantitas,allowance, keterangan in zip(listkodeproduk,listlokasi,liststatus,listkuantitas,listallowance,listketerangan):
        for penyusun,update in zip(data.konversi,(zip(listkodeproduk,listlokasi,liststatus,listkuantitas,listallowance,listketerangan))):
            print(penyusun,update)
            # print(asd)
            
            try:
                produkobj = models.Produk.objects.get(KodeProduk=update[0])
            except:
                messages.error(
                    request, f"Data bahan baku {update[0]} tidak ditemukan dalam sistem "
                )
                continue
            # print(asd)
            lokasiobj = models.Lokasi.objects.get(NamaLokasi=update[1])
            penyusun.KodeProduk = produkobj
            penyusun.Lokasi = lokasiobj
            penyusun.Status = update[2]
            penyusun.Kuantitas = update[3]
            penyusun.Allowance = update[4]
            penyusun.keterangan = update[5]
            
            if penyusun.KodeVersi.Versi != kodeversi:
                penyusun.KodeVersi.Versi = kodeversi
                print(penyusun.KodeVersi.Versi,kodeversi)
                # penyusun.KodeVersi.save()

            penyusun.save()
        transaksilog = models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Penyusun Baru. Kode Artikel : {penyusun.KodeArtikel}, Kode produk : {penyusun.KodeProduk}-{penyusun.KodeProduk.NamaProduk}, Status Utama : {penyusun} versi : {penyusun.KodeVersi}, Kuantitas Konversi : {  penyusun.Kuantitas}",
        )
        # transaksilog.save()
        messages.success(request, "Data berhasil disimpan")
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(penyusun.KodeArtikel.KodeArtikel)}&versi={penyusun.KodeVersi.Versi}"
        )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def track_spk(request, id):
    '''
    Fitur ini digunakan untuk melakukan tracking pada SPK
    pada bagian ini ada beberapa section antara lain
    1. Informasi SPK
    2. Rekap Kumulasi permintaan barang
    3. Rekap kumulasi pengiriman produk
    3. Tracking detail permitnaan barang ke SPK
    4. Tracking detail pengiriman produk
    5. Tracking detail mutasi WIP-FG 

    Algoritma
    1. Informasi SPK
        A. Mengambil data detail SPK dan SPK terkait dengan kode SPK id = id, dimana id didapatkan dari passing values pada halaman awal SPK
    2. Rekap Kumulasi permintaan barang
        A. Menghitung agregasi jumlah permintaan barang tiap bahan baku melalui tabel Transaksi Gudang dengan kriteria NoSPK = id dan jumlah > 0
    3. Rekap Kumulasi pengiriman produk
        A. Menghitung agregasi jumlah pengiriman produk melalui tabel DetailSPPB dengan kriteria NoSPK = id 
    3. Tracking detail permitnaan barang ke SPK
        A. Mengambil data transaksi permintaan barang tiap bahan baku melalui tabel Transaksi Gudang dengan kriteria NoSPK = id dan jumlah > 0
    4. Trancking detail pengiriman produk 
        A. Mengambuil data transaksi pengiriman produk melalui tabel detailSPPB dengan kriteraa NoSPK = id
    5. Tracking Mutasi WIP-FG
        A. Mengambil data transaksi mutasi produk melalui tabel Transaksi Produksi dengan kriteria NoSPK = id  dan jenis = Mutasi
    '''
    dataartikel = models.Artikel.objects.all()
    datadisplay =models.Display.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    if dataspk.StatusDisplay == False:
        datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)
    else:
        datadetail = models.DetailSPKDisplay.objects.filter(NoSPK = dataspk.id)
    if dataspk.StatusDisplay ==True:
        
        # Data SPK terkait yang telah di request ke Gudang
        transaksigudangobj = models.TransaksiGudang.objects.filter(
            DetailSPKDisplay__NoSPK=dataspk.id, jumlah__gte=0
        )

        # Data SPK Terkait yang telah jadi di FG
        transaksiproduksiobj = models.TransaksiProduksi.objects.filter(
            DetailSPKDisplay__NoSPK=dataspk.id, Jenis="Mutasi"
        )
        print(transaksiproduksiobj)

        # Data SPK Terkait yang telah dikirim
        sppbobj = models.DetailSPPB.objects.filter(DetailSPKDisplay__NoSPK=dataspk.id)
        rekapjumlahpermintaanperbahanbaku = transaksigudangobj.values('KodeProduk__KodeProduk',"KodeProduk__NamaProduk","KodeProduk__unit").annotate(total = Sum('jumlah'))
        rekapjumlahpengirimanperartikel = sppbobj.values("DetailSPKDisplay__KodeDisplay__KodeDisplay").annotate(total=Sum('Jumlah'))
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
        rekapjumlahpermintaanperbahanbaku = transaksigudangobj.values('KodeProduk__KodeProduk',"KodeProduk__NamaProduk","KodeProduk__unit").annotate(total = Sum('jumlah'))
        rekapjumlahpengirimanperartikel = sppbobj.values("DetailSPK__KodeArtikel__KodeArtikel").annotate(total=Sum('Jumlah'))

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")


    print(transaksigudangobj)
    return render(
        request,
        "rnd/trackingspk.html",
        {
                "data": dataartikel,
                "datadisplay": datadisplay,
                "dataspk": dataspk,
                "datadetail": datadetail,
                "tanggal": tanggal,
                "transaksigudang": transaksigudangobj,
                "transaksiproduksi": transaksiproduksiobj,
                "transaksikeluar": sppbobj,
                'datarekappermintaanbahanbaku': rekapjumlahpermintaanperbahanbaku,
                'datarekappengiriman' : rekapjumlahpengirimanperartikel
            },
    )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def update_produk_rnd(request, id):
    '''
    Fitur ini digunakan unutk mengupdate bahan baku pada RND
    ALgoritma 
    1. Mendapatkan data bahan baku menggunakan parameter KodeProduk = id (id didapatkan dari passing urls html)
    2. Mengiirmkan form input keterangan RND
    3. Menyimpan perubahan
    '''
    produkobj = models.Produk.objects.get(KodeProduk=id)
    if request.method == "GET":
        return render(request, "rnd/update_produk.html", {"produkobj": produkobj})
    else:
        keterangan_produk = request.POST["keterangan_produk"]
        produkobj.keteranganRND = keterangan_produk
        produkobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Bahan Baku. Kode Bahan Baku: {produkobj.KodeProduk} Nama Bahan Baku : {produkobj.NamaProduk}  Keterangan : {produkobj.keteranganProduksi}",
        ).save()
        messages.success(request,'Data berhasil disimpan')

        return redirect("read_bahanbaku_rnd")


def bulk_createartikel(request):
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

    return render(request, "rnd/upload_artikel.html")


def bulk_createpenyusun(request):
    if request.method == "POST" and request.FILES["file"]:
        file = request.FILES["file"]
        excel_file = pd.ExcelFile(file)
        listerror = []

        # Mendapatkan daftar nama sheet
        sheet_names = excel_file.sheet_names
        # print(sheet_names)
        kodepenyusun = 1
        for item in sheet_names:
            lokasi = 'WIP'
            df = pd.read_excel(file, sheet_name=item,header=4)
            print(df)
            print(item)
            # print(df)
                        # print(asd)
            for data, row in df.iterrows():
                # print(row["Kode Stock"])
                print(data)
                # print(row)
                # print(row['Jumlah Sat/ktk'])
                # print(asd)
                if str(row["Jumlah Sat/ktk"]).strip() == 'WIP':
                    lokasi = 'FG'
                    print('Masuk FG')
                    # print(asd)
                elif str(row["Jumlah Sat/ktk"]).strip() == 'FG':
                    break
                if  pd.isna(row['Kode Stock'] and not pd.isna(row['Jumlah Sat/ktk'])):
                    listerror.append([item,(data,row['Kode Stock'],row['Bahan Baku'])])
                else:
                    kuantitas = row["Jumlah Sat/ktk"]
                    try:
                        kodeartikel = models.Artikel.objects.get(KodeArtikel=item)
                    except Exception as e:
                        listerror.append([item,(data,e)])
                        continue
                    try:
                        read_produk = models.Produk.objects.get(
                            KodeProduk=row["Kode Stock"]
                        )
                    except Exception as e:
                        listerror.append([item, (e,data,row["Kode Stock"],row["Jumlah Sat/ktk"])])
                        continue

                    penyusunobj = models.Penyusun(
                        Status=0,
                        KodeArtikel=kodeartikel,
                        KodeProduk=read_produk,
                        Lokasi=models.Lokasi.objects.get(NamaLokasi=lokasi),
                        versi=date(2024, 1, 1),
                    ).save()
                    kkonversimasterobj = models.KonversiMaster(
                        Kuantitas=kuantitas,
                        KodePenyusun=models.Penyusun.objects.last(),
                        lastedited=datetime.now(),
                        Allowance=row['Jumlah Sat/ktk'],
                    ).save()
                
            

        return render(request,'error/errorsjp.html',{'data':listerror})

    return render(request, "rnd/upload_artikel.html")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_display(request):
    '''
    Fitur ini digunakan untuk melakukan manajemen data Display pada sistem
    '''
    data = models.Display.objects.all()
    return render(request, "rnd/views_display.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdatadisplay(request):
    '''
    Fitur ini digunakan untuk menambahkan data display pada sistem
    Algoritma
    1. Menampilkan form input display berisi Kode Display dan Keterangan
    2. User menginput form
    3. Apabila kode display telah ada pada sistem maka akan menampilkan pesan error
    4. Apabila tidak ada maka data display akan disimpan kedalam sistem beserta keterangannya
    '''
    if request.method == "GET":
        return render(request, "rnd/tambah_display.html")
    if request.method == "POST":
        # print(dir(request))
        kodebaru = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        data = models.Display.objects.filter(KodeDisplay=kodebaru).exists()
        if data:
            messages.error(request, "Kode Artikel sudah ada")
            return redirect("tambahdataartikel")
        else:
            if keterangan == "":
                keterangan = "-"
            newdataobj = models.Display(KodeDisplay=kodebaru, keterangan=keterangan)
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Display : {newdataobj.KodeDisplay} Keterangan : {newdataobj.keterangan}",
            ).save()
            newdataobj.save()
            messages.success(request, "Data berhasil disimpan")
            return redirect("views_display")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatedatadisplay(request, id):
    '''
    Fitur ini digunakan untuk melakukan update data display yang sudah ada pada sistem
    *Terminologi : Kode display merupakan kode barang display yang digunakan untuk barang habis pakai.
    *Terminologi : Barang display tidak memiliki konversi pada RND. jadi untuk besar konversi tergantung dari request gudang

    Alogirtma
    1. Menampilkan form update display berisi Kode Display dan Keterangan
    2. User menginput form
    3. Apabila kode display telah ada pada sistem kecuali kodeproduk yang diedit maka akan menampilkan pesan error
    4. Apabila tidak ada maka data display akan disimpan kedalam sistem beserta keterangannya
    '''
    data = models.Display.objects.get(id=id)
    if request.method == "GET":
        return render(request, "rnd/update_display.html", {"artikel": data})
    else:
        kodedisplay = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        if keterangan == "":
            keterangan = "-"
        cekkodeartikel = (
            models.Display.objects.filter(KodeDisplay=kodedisplay)
            .exclude(id=id)
            .exists()
        )
        if cekkodeartikel:
            messages.error(request, "Kode Display telah terdaftar pada database")
            return redirect("update_display", id=id)
        else:
            transaksilog = models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Display Lama : {data.KodeDisplay} Keterangan Lama : {data.keterangan} Artikel Baru : {kodedisplay} Keterangan Baru : {keterangan}",
            )
            data.KodeDisplay = kodedisplay
            data.keterangan = keterangan
            data.save()
            transaksilog.save()
            messages.success(request, "Data Berhasil diupdate")
        return redirect("views_display")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def deletedisplay(request, id):
    '''
    Fitur ini digunakan untuk menghapus data Display.
    Algoritma
    1. Mendapatkan data ID dari passing values melalui halaman awal menu Display
    2. Menghapus data objek display
    '''
    dataobj = models.Display.objects.get(id=id)
    models.transactionlog(
        user="RND",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Artikel : {dataobj.KodeDisplay} Keterangan : {dataobj.keterangan}",
    ).save()
    dataobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("views_display")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_harga(request):
    '''
    Fitur ini digunakan untuk melakukan manajemen data HargaFG
    *HargaFG = Harga akhir dari artikel yang diinputkan secara manual
    Algoritma 
    1. Mengambil data Harga FG dari tabel HargaArtikel
    2. Menyesuaikan format tanggal (YY-MM)
    '''
    datakirim = []
    data = models.HargaArtikel.objects.all()
    for i in data:
        i.Tanggal = i.Tanggal.strftime('%Y-%m')
   
    return render(request, "rnd/views_harga.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdataharga(request):
    '''
    Fitur ini digunakan untuk menambahkan harga FG  tiap bulan dan tahun
    Algoritma 
    1. Menampilkan input form tambah harga FG
    2. User menginputkan Taanggal, Kode Artikel dan HargaFG
    3. Menyimpan data HargaArtikel sesuai input
    '''
    allartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(request, "rnd/tambah_harga.html",{'allartikel':allartikel})
    if request.method == "POST":
        # print(dir(request))
        kodeartikel = request.POST["kodeartikel"]
        tanggal = request.POST["tanggal"]
        tanggalobj = datetime.strptime(str(tanggal),'%Y-%m')
        harga = request.POST['harga']
        data = models.HargaArtikel.objects.filter(KodeArtikel__KodeArtikel=kodeartikel, Tanggal__month = tanggalobj.month ,Tanggal__year = tanggalobj.year).exists()
        if data:
            messages.error(request, "Harga pada artikel sudah ada sebelumnya")
            return redirect("tambahdataharga")
        else:
            try:
                artikelobj = models.Artikel.objects.get(KodeArtikel = kodeartikel)
                newdataobj  = models.HargaArtikel(
                    Tanggal = tanggalobj,
                    KodeArtikel = artikelobj,
                    Harga = harga
                )
                newdataobj.full_clean()
            except Exception as e:
                messages.error(request,f'Error {e}')
                return redirect("tambahdataharga")
            

            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Artikel : {newdataobj.KodeArtikel} Harga : {newdataobj.Harga}",
            ).save()
            newdataobj.save()
            messages.success(request, "Data berhasil disimpan")
            return redirect("views_harga")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatedataharga(request, id):
    '''
    Fitur ini digunakan untuk melakukan update hargaFG yang sudah ada pada sistem
    Algoritma
    1. Mendapatkan data HargaArtikel berdasarkan ID yang dikirimkan melalui passing values url pada halaman awal fitur HargaFG
    2. Menampilkan form update Harga, Tanggal, dan Kode Artikel
    3. Menyimpan data update hargaFG
    '''
    data = models.HargaArtikel.objects.get(pk=id)
    data.Tanggal = data.Tanggal.strftime("%Y-%m")
    allartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(request, "rnd/update_harga.html", {"artikel": data,'allartikel':allartikel})
    else:
        kodeartikel = request.POST["kodeartikel"]
        tanggal = request.POST["tanggal"]
        harga = request.POST['harga']
        tanggalobj = datetime.strptime(tanggal,'%Y-%m')
        cekharga = (
            models.HargaArtikel.objects.filter(KodeArtikel__KodeArtikel=kodeartikel, Tanggal__year = tanggalobj.year, Tanggal__month = tanggalobj.month)
            .exclude(id=id)
            .exists()
        )
        if cekharga:
            messages.error(request, "Kode Artikel telah memiliki Harga pada bulan tersebut")
            return redirect("update_harga", id=id)
        else:
            transaksilog = models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Artikel : {data.KodeArtikel} Harga lama : {data.Harga} Tanggal Lama : {data.Tanggal} Tanggal Baru : {tanggal} Harga Baru : {harga}",
            )
            data.Harga = harga
            data.Tanggal = tanggalobj
            data.save()
            transaksilog.save()
            messages.success(request, "Data Berhasil diupdate")
        return redirect("views_harga")


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def deleteharga(request, id):
    '''
    Fitur ini digunakan untuk menghapus hargaFG pada sistem
    Algoritma 
    1. Mendapatkan data ID HargaArtikel melalui Passing Values url
    2. Menghapus data hargafg
    '''
    dataobj = models.HargaArtikel.objects.get(id=id)
    models.transactionlog(
        user="RND",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Artikel : {dataobj.KodeArtikel} Tanggal : {dataobj.Tanggal}",
    ).save()
    dataobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("views_harga")

def updatepenyusundarikonversimaster(request):
    '''Convert Versi ke Harga'''
    datapenyusun = models.Penyusun.objects.all()
    # for item in datapenyusun:
    #     try:
    #         datakonversimaster = models.KonversiMaster.objects.get(KodePenyusun = item)
    #     except Exception as e:
    #         print(item,e)
    #         continue
    #     item.Kuantitas = datakonversimaster.Kuantitas
    #     item.Allowance = datakonversimaster.Allowance
    #     item.lastedited = datakonversimaster.lastedited
    #     item.save()
    '''Buat data Versi'''
    # dataartikel = models.Artikel.objects.all()
    # for item in dataartikel:
    #     datafilterpenyusun = datapenyusun.filter(KodeArtikel = item).values_list('versi',flat=True).distinct()
    #     print(item,datafilterpenyusun)
    #     for i in datafilterpenyusun:
            
    #         newversi = models.Versi(
    #             KodeArtikel = item,
    #             Versi = i,
    #             Tanggal = i,
    #             Keterangan = 'Default versi 2024'
    #         )
    #         newversi.save()
    '''Update Foreign Key data Versi pada Penysun'''
    # for item in datapenyusun:
    #     item.KodeVersi = models.Versi.objects.filter(KodeArtikel = item.KodeArtikel, Versi = item.versi).first()
    #     item.save()
        # print()
    '''UPDATE DEFAULT VERSI EACH ARTIKEL'''
    # dataartikel = models.Artikel.objects.all()
    # for item in dataartikel:
    #     print(item)
    #     dataversifilter = models.Versi.objects.filter(KodeArtikel = item).order_by('Tanggal')
    #     for i in dataversifilter:
    #         i.isdefault = False
    #         i.save()
    #     dataawal = dataversifilter.first()
    #     dataawal.isdefault= True
    #     dataawal.save()
    # datadetailsppb = models.DetailSPPB.objects.all()
    # for item in datadetailsppb :
    #     print(item.VersiArtikel, item.DetailSPK.KodeArtikel,item.NoSPPB.Tanggal)
    #     # if item.VersiArtikel == None:
    #     kodeversidefault = models.Versi.objects.filter(KodeArtikel = item.DetailSPK.KodeArtikel,isdefault = True).first()
    #     print(kodeversidefault,item,item)
    #     # print(asd)
    #     item.VersiArtikel = kodeversidefault
    #     item.save()
    '''CEK SURAT JALAN PENERIMAAN YANG TIDAK MEMILIKI DETAIL'''
    no_surat_jalan_with_detail = models.DetailSuratJalanPembelian.objects.values_list("NoSuratJalan__NoSuratJalan", flat=True).distinct()
    # Ambil daftar SuratJalanPembelian yang tidak ada di daftar di atas
    surat_jalan_without_detail = models.SuratJalanPembelian.objects.exclude(NoSuratJalan__in=no_surat_jalan_with_detail).distinct()
    # for item in surat_jalan_without_detail:
    #     item.delete()
    # print(surat_jalan_without_detail)
    '''CEK SURAT JALAN PRODUK SUBKON YANG TIDAK MEMILIKI DETAIL'''
    ''''''
    tanggal_mulai = date(2024, 3, 22).strftime('%Y-%m-%d')  # Sesuaikan dengan tahun yang diinginkan
    tanggal_akhir = date(2024, 9, 12).strftime('%Y-%m-%d')  # Sesuaikan dengan tahun yang diinginkan

# Hapus data dengan filter rentang tanggal
    data = models.SuratJalanPembelian.objects.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir))
    print(data)
    data.delete()
        
    
def createhargafg (request):
    if request.method == "POST" and request.FILES["file"]:
        file = request.FILES["file"]
        excel_file = pd.ExcelFile(file)
        print(excel_file)
        # print(asd)

        # Mendapatkan daftar nama sheet
        sheet_names = excel_file.sheet_names
        listerror = []

        for item in sheet_names:
            df = pd.read_excel(file, engine="openpyxl", sheet_name=item)
            print(item)
            print(df)
            # print(asd)


            for index, row in df.iterrows():
                    print("Saldo Akhir")
                    print(row)
                    try:
                        kodeartikel = (row['Kode Artikel'])
                        artikelobj = models.Artikel.objects.get(KodeArtikel = kodeartikel)
                    except Exception as e:
                        listerror.append([row, e])
                        continue
                    # print(asd) 
                    datahargaobj = models.HargaArtikel(
                        Tanggal = row['Tanggal'],
                        KodeArtikel = artikelobj,
                        Harga = row['HargaFG']
                    )
                    datahargaobj.save()

        return render(request,'error/errorsjp.html',{'data':listerror})

    return render(request, "produksi/bulk_createproduk.html")

def clean_string(s):
    # Remove "Art" and any non-alphanumeric characters
    s = re.sub(r'Art', '', s)
    return re.sub(r'[^a-zA-Z0-9]', ' ', s).strip()
from django.shortcuts import render, redirect
from django.contrib import messages
from . import models
from django.db.models import Sum
from datetime import datetime

# Create your views here.
#Dashboard Gudang
def view_accgudang(request):
    datatgudang = models.TransaksiGudang.objects.filter(KeteranganACC=False)

    return render(request, "produksi/acc_gudang.html", {'datatgudang':datatgudang})

def acc_gudang(request, id):
    datatgudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datatgudang.KeteranganACC = True
    datatgudang.save()

    return redirect("view_accgudang")

# SPK
def view_spk(request):
    dataspk = models.SPK.objects.all()

    return render(request, "produksi/view_spk.html", {"dataspk": dataspk})

def add_spk(request):
    if request.method == "GET":
        return render(request, "produksi/add_spk.html")

    if request.method == "POST":
        nomor_spk = request.POST["nomor_spk"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        status = request.POST["status"]

        dataspk = models.SPK.objects.filter(NoSPK=nomor_spk).exists()
        if dataspk:
            messages.error(request, "Nomor SPK sudah ada")
            return redirect("add_spk")
        else:
            messages.success(request, "Data berhasil disimpan")
            data_spk = models.SPK(
                NoSPK=nomor_spk,
                Tanggal=tanggal,
                Keterangan=keterangan,
                KeteranganACC=False,
            ).save()
            return redirect("view_spk")

def update_spk(request, id):
    if request.method == "GET":
        return render(request, "update_spk.html")
    else:
        return redirect("view_spk")

def delete_spk(request, id):
    dataspk = models.SPK.objects.get(id=id)
    dataspk.delete()
    return redirect("view_spk")

# SPPB
def view_sppb(request):
    datasppb = models.SPPB.objects.all()

    return render(request, "produksi/view_sppb.html", {"datasppb": datasppb})

def add_sppb(request):
    if request.method == "GET":
        return render(request, "produksi/add_sppb.html")

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
            return redirect("view_sppb")

def update_sppb(request, id):
    if request.method == "GET":
        return render(request, "produksi/update_sppb.html")
    else:
        return redirect("view_sppb")

def delete_sppb(request, id):
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    return redirect("view_sppb")

# Transaksi Produksi
def view_produksi(request):
    dataproduksi = models.TransaksiProduksi.objects.filter(Jenis="Mutasi")

    return render(request, "produksi/view_produksi.html", {"dataproduksi": dataproduksi})

def add_produksi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_lokasi = models.Lokasi.objects.all()

        return render(
            request,
            "produksi/add_produksi.html",
            {"kode_artikel": data_artikel, "nama_lokasi": data_lokasi},
        )

    if request.method == "POST":
        kode_artikel = request.POST["kode_artikel"]
        lokasi = request.POST["nama_lokasi"]
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        artikelref = models.Artikel.objects.get(KodeArtikel=kode_artikel)
        lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)

        data_produksi = models.TransaksiProduksi(
            KodeArtikel=artikelref,
            Lokasi=lokasiref,
            Tanggal=tanggal,
            Jumlah=jumlah,
            Keterangan=keterangan,
            Jenis="Mutasi",
        ).save()
        messages.success(request, "Data berhasil disimpan")

        return redirect("view_produksi")

def update_produksi(request, id):
    produksiobj = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    data_artikel = models.Artikel.objects.all()
    data_lokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        tanggal = datetime.strftime(produksiobj.Tanggal, '%Y-%m-%d')
        return render(request, "produksi/update_produksi.html",{'produksi':produksiobj,
                                                       'tanggal':tanggal,
                                                       'kode_artikel': data_artikel,
                                                       'nama_lokasi': data_lokasi})
    
    elif request.method == "POST":
        kode_artikel = request.POST["kode_artikel"]
        getartikel = models.Artikel.objects.get(KodeArtikel=kode_artikel)
        lokasi = request.POST["nama_lokasi"]
        getlokasi = models.Lokasi.objects.get(IDLokasi=lokasi)
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        produksiobj.KodeArtikel = getartikel
        produksiobj.Lokasi = getlokasi
        produksiobj.Tanggal = tanggal
        produksiobj.Jumlah = jumlah
        produksiobj.Keterangan = keterangan
        produksiobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_produksi")

def delete_produksi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    messages.success(request,"Data Berhasil dihapus")
    return redirect("view_produksi")

#Transaksi Gudang
def view_gudang(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__gt=0)

    return render(request, "produksi/view_gudang.html", {"datagudang": datagudang})

def view_gudangretur(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__lt=0)

    return render(request, "produksi/view_gudangretur.html", {"datagudang": datagudang})

def add_gudang(request):
    if request.method == "GET":
        data_produk = models.Produk.objects.all()
        data_lokasi = models.Lokasi.objects.all()

        return render(
            request,
            "produksi/add_gudang.html",
            {"kode_produk": data_produk, "nama_lokasi": data_lokasi},
        )

    if request.method == "POST":
        kode_produk = request.POST["kode_produk"]
        lokasi = request.POST["nama_lokasi"]
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        produkref = models.Produk.objects.get(KodeProduk=kode_produk)
        lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)

        data_gudang = models.TransaksiGudang(
            KodeProduk=produkref,
            Lokasi=lokasiref,
            tanggal=tanggal,
            jumlah=jumlah,
            keterangan=keterangan,
            KeteranganACC=False,
        ).save()
        messages.success(request, "Data berhasil disimpan")

        return redirect("view_gudang")

def update_gudang(request, id):
    gudangobj = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    data_produk = models.Produk.objects.all()
    data_lokasi = models.Lokasi.objects.all()

    if request.method == "GET":
        tanggal = datetime.strftime(gudangobj.tanggal, '%Y-%m-%d')
        return render(request, "produksi/update_gudang.html",{'gudang':gudangobj,
                                                       'tanggal':tanggal,
                                                       'kode_produk': data_produk,
                                                       'nama_lokasi': data_lokasi
                                                       })
    
    elif request.method == "POST":
        kode_produk = request.POST["kode_produk"]
        getproduk = models.Produk.objects.get(KodeProduk=kode_produk)
        lokasi = request.POST["nama_lokasi"]
        getlokasi = models.Lokasi.objects.get(IDLokasi=lokasi)
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        gudangobj.KodeProduk = getproduk
        gudangobj.Lokasi = getlokasi
        gudangobj.tanggal = tanggal
        gudangobj.jumlah = jumlah
        gudangobj.keterangan = keterangan

        gudangobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_gudang")

def delete_gudang(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.delete()
    messages.success(request,"Data Berhasil dihapus")

    return redirect("view_gudang")

#Rekapitulasi
def view_ksbb(request):
    if len(request.GET) == 0:
        return render(request,'produksi/view_ksbb.html')
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET['kodebarang'])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect('view_ksbb')
        
        datagudang = models.TransaksiGudang.objects.filter(KodeProduk=produk).order_by('tanggal')

        # Mendapatkan semua penyusun yang terkait dengan produk
        penyusun_produk = models.Penyusun.objects.filter(KodeProduk=produk)

        # Mendapatkan artikel yang terkait dengan penyusun produk
        artikel_penyusun = [penyusun.KodeArtikel for penyusun in penyusun_produk]

        # Memfilter transaksi produksi berdasarkan artikel yang terkait dengan penyusun produk
        dataproduksi = models.TransaksiProduksi.objects.filter(KodeArtikel__in=artikel_penyusun,Jenis="Mutasi").order_by('Tanggal')

        kuantitas_konversi = {}
        for penyusun in penyusun_produk:
            konversi = models.KonversiMaster.objects.filter(KodePenyusun=penyusun)
            if konversi.exists():
                kuantitas_konversi[penyusun.IDKodePenyusun] = konversi[0].Kuantitas
            else:
                kuantitas_konversi[penyusun.IDKodePenyusun] = 0
        
        print(dataproduksi)

        for data in dataproduksi:
            if data.KodeArtikel in artikel_penyusun:
                penyusun = models.Penyusun.objects.get(KodeProduk=produk, KodeArtikel=data.KodeArtikel)
                data.kuantitas = kuantitas_konversi[penyusun.IDKodePenyusun] + (kuantitas_konversi[penyusun.IDKodePenyusun]*2.5/100)
                data.keluar = data.Jumlah * data.kuantitas
        try:
            saldo = models.SaldoAwalBahanBaku.objects.get(IDBahanBaku=request.GET['kodebarang'],IDLokasi=1)
        except:
            messages.error(request, "Masukkan Saldo Awal Bahan Baku")
            return redirect('view_ksbb')
        
        saldoawal = saldo.Jumlah
        sisa = saldo.Jumlah

        for data in dataproduksi:
            masuk_total = 0
            for data_gudang in datagudang:
                if data_gudang.tanggal == data.Tanggal:
                    masuk_total += data_gudang.jumlah
            data.masuk = masuk_total
            
            sisa = sisa + data.masuk - data.keluar
            data.sisa = sisa
        
        return render(request, "produksi/view_ksbb.html", {"kodebarang":request.GET['kodebarang'],
                                                  'nama':nama,
                                                  'satuan':satuan,
                                                  'data':dataproduksi,
                                                  'saldoawal':saldoawal
                                                  })

def views_ksbj(request):
    if len(request.GET) == 0:
        return render(request,'produksi/view_ksbj.html')
    else:   
        print(request.GET)
        lokasi = request.GET['lokasi']
        lokasiobj = models.Lokasi.objects.get(NamaLokasi = lokasi)
        try :
            artikel = models.Artikel.objects.get(KodeArtikel = request.GET['kodeartikel'])
        except:
            messages.error(request,"Kode Artikel Tidak ditemukan")
            return redirect('views_ksbj')
        data = models.TransaksiProduksi.objects.filter(KodeArtikel = artikel.id,Lokasi =lokasiobj.IDLokasi).order_by('Tanggal')
        tanggallist = data.values_list('Tanggal',flat=True).distinct()
        # print(tanggallist[0])
        listdata = []
        try:
            getbahanbakuutama = models.Penyusun.objects.get(KodeArtikel = artikel.id,Status = 1 )
        except models.Penyusun.DoesNotExist:
            messages.error('Bahan Baku utama belum di set')
            return redirect('views_ksbj')
        print(getbahanbakuutama)
        try:
            saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel = artikel.id, IDLokasi = lokasiobj.IDLokasi)
            saldoawaltaun = saldoawalobj.Jumlah
        except models.SaldoAwalArtikel.DoesNotExist as e:
            print(e)
            saldoawaltaun = 0

        sisa = saldoawaltaun
        for i in tanggallist:
            
            jumlahhasil = 0
            jumlahmasuk = 0
            filtertanggal=data.filter(Tanggal = i)
            print('ini tanggal',filtertanggal)
            for j in filtertanggal:
                
                if j.Jenis == "Produksi":
                    jumlahmasuk += j.Jumlah
                else:
                    jumlahhasil += j.Jumlah
                # Cari data konversi bahan baku utama pada artikel terkait
            konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun = getbahanbakuutama.IDKodePenyusun)
            print('Konversi', konversimasterobj.Kuantitas + ( konversimasterobj.Kuantitas*0.025))
            masukpcs = round(jumlahmasuk/((konversimasterobj.Kuantitas + ( konversimasterobj.Kuantitas*0.025)))*0.893643879)
                # Cari data penyesuaian
            sisa = sisa - jumlahhasil +masukpcs
            listdata.append([i,getbahanbakuutama,jumlahmasuk,jumlahhasil,masukpcs,sisa])

        return render(request,'produksi/view_ksbj.html',{'data':data,"kodeartikel":request.GET['kodeartikel'],"lokasi":lokasi,'listdata':listdata,'saldoawal':saldoawaltaun})
        
def view_rekapbarang(request):
    if len(request.GET) == 0:
        return render(request, "produksi/rekap_barang.html")
    else:
        tanggal_mulai = request.GET["tanggalawal"]
        tanggal_akhir = request.GET["tanggalakhir"]
        # Ambil semua kode artikel yang memiliki transaksi produksi

        kode_artikel_produk = models.TransaksiProduksi.objects.filter(Jenis="Mutasi",Lokasi=1,Tanggal__range=(tanggal_mulai,tanggal_akhir)).values('KodeArtikel').annotate(kuantitas=Sum('Jumlah'))

        # Ambil data penyusun berdasarkan kode artikel yang memiliki transaksi produksi
        penyusun_per_artikel = []
        for kode_artikel in kode_artikel_produk:
            penyusun = models.Penyusun.objects.filter(KodeArtikel=kode_artikel['KodeArtikel'])
            konversi = models.KonversiMaster.objects.filter(KodePenyusun__in=penyusun)
            penyusun_per_artikel.append({
                'KodeArtikel': kode_artikel['KodeArtikel'],
                'Jumlah' : kode_artikel['kuantitas'],
                'Penyusun': penyusun,
                'Konversi': konversi
            })

        # Dictionary untuk menyimpan jumlah total untuk setiap kode produk penyusun
        total_per_produk = {}

        # Output data penyusun per kode artikel
        for item in penyusun_per_artikel:
            for penyusun in item['Penyusun']:
                konversi = item['Konversi'].filter(KodePenyusun=penyusun)
                total_kuantitas = sum(konv.Kuantitas for konv in konversi)
                total = total_kuantitas * item['Jumlah']
                if penyusun.KodeProduk in total_per_produk:
                    total_per_produk[penyusun.KodeProduk] += total
                else:
                    total_per_produk[penyusun.KodeProduk] = total

        databarang = models.Produk.objects.all()       

        datagudang = models.TransaksiGudang.objects.filter(Lokasi=1,tanggal__range=(tanggal_mulai,tanggal_akhir)).values('KodeProduk').annotate(kuantitas=Sum('jumlah'))
        
        # Output hasil perhitungan
        for barang in databarang:
            kode_produk = barang.KodeProduk
            kode = models.Produk.objects.get(KodeProduk=kode_produk)
            kuantitas = next((item['kuantitas'] for item in datagudang if item['KodeProduk'] == kode_produk), 0)
            if kode in total_per_produk:
                kuantitas -= total_per_produk[kode]
            barang.kuantitas = kuantitas

        return render(request, "produksi/rekap_barang.html", {'databarang':databarang})
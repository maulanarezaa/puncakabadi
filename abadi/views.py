from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from . import models

# Create your views here.

# RND
def views_artikel(request):
    datakirim = []
    data = models.Artikel.objects.all()
    for item in data:
        print(item)
        detailartikelobj = models.Penyusun.objects.filter(KodeArtikel=item.id).filter(
            Status=1
        )
        print(detailartikelobj)
        if detailartikelobj.exists():
            datakirim.append([item, detailartikelobj[0]])
        else:
            datakirim.append([item, "Belum diset"])
    print(datakirim)
    return render(request, "views_artikel.html", {"data": datakirim})

def tambahdataartikel(request):
    if request.method == "GET":
        return render(request, "tambahdataartikel.html")
    if request.method == "POST":
        # print(dir(request))
        kodebaru = request.POST["kode"]
        keterangan = request.POST["keterangan"]
        data = models.Artikel.objects.filter(KodeArtikel=kodebaru).exists()
        if data:
            messages.error(request, "Kode Artikel sudah ada")
            return redirect("tambahdataartikel")
        else:
            messages.success(request, "Data berhasil disimpan")
            newdataobj = models.Artikel(
                KodeArtikel=kodebaru, keterangan=keterangan
            ).save()
            return redirect("views_artikel")

def updatedataartikel(request, id):
    if request.method == "GET":
        return render(request, "updatedataartikel.html")
    else:
        return redirect("views_artikel")

def deleteartikel(request, id):
    print(id)
    dataobj = models.Artikel.objects.get(id=id)
    dataobj.delete()
    return redirect("views_artikel")

def views_penyusun(request):
    print(request.GET)
    data = request.GET
    if len(request.GET) == 0:
        return render(request, "views_penyusun.html")
    else:
        kodeartikel = request.GET["kodeartikel"]
        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
            data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
            if data.exists():
                print(data)
                return render(
                    request,
                    "views_penyusun.html",
                    {"data": data, "kodeartikel": get_id_kodeartikel},
                )
            else:
                return render(request, "views_penyusun.html")
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return render(request, "views_penyusun.html")

def tambahdatapenyusun(request, id):
    dataartikelobj = models.Artikel.objects.get(id=id)
    if request.method == "GET":
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "tambahdatapenyusun.html",
            {"kodeartikel": dataartikelobj, "dataproduk": dataprodukobj},
        )
    else:
        print(request.POST)
        kodeproduk = request.POST["kodeproduk"]
        statusproduk = request.POST["Status"]
        if statusproduk == "True":
            statusproduk = True
        else:
            statusproduk = False
        lokasi = request.POST["lokasi"]

        newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)

        penyusunobj = models.Penyusun(
            Status=statusproduk,
            KodeArtikel=dataartikelobj,
            KodeProduk=newprodukobj,
            Lokasi=lokasiobj,
        )

        konversimasterobj = models.KonversiMaster(KodePenyusun=penyusunobj, Kuantitas=0)
        penyusunobj.save()
        konversimasterobj.save()

        return redirect("penyusun_artikel")

# Update Delete Penyusun belum masuk
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
                print(i.IDKodePenyusun)
                allowance = models.KonversiMaster.objects.get(
                    KodePenyusun=i.IDKodePenyusun
                )
                listdata.append(
                    [i, allowance, allowance.Kuantitas + allowance.Kuantitas * 0.025]
                )
            print(listdata)
            return render(
                request,
                "views_konversi.html",
                {"data": listdata, "kodeartikel": kodeartikel},
            )
        else:
            return render(request, "views_konversi.html")

def konversimaster_update(request, id):
    dataobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        return render(request, "update_konversimaster.html", {"data": dataobj})
    else:
        konversimasterobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
        print(konversimasterobj)
        konversimasterobj.Kuantitas = float(request.POST["kuantitas"])
        konversimasterobj.save()
        return redirect("konversi")

def konversimaster_delete(request, id):
    dataobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
    dataobj.Kuantitas = 0
    dataobj.save()
    return redirect("konversi")

#SPK
def view_spk(request):
    dataspk = models.SPK.objects.all()

    return render(request, 'view_spk.html', {'dataspk' : dataspk})

def add_spk(request):
    if request.method == "GET":
        return render(request, "add_spk.html")
    
    if request.method == "POST":
        nomor_spk = request.POST["nomor_spk"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        status = request.POST["status"]

        dataspk = models.SPK.objects.filter(NoSPK = nomor_spk).exists()
        if dataspk:
            messages.error(request, "Nomor SPK sudah ada")
            return redirect("add_spk")
        else:
            messages.success(request, "Data berhasil disimpan")
            data_spk = models.SPK(
                NoSPK = nomor_spk,
                Tanggal = tanggal,
                Keterangan = keterangan,
                KeteranganACC = status,
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

#SPPB
def view_sppb(request):
    datasppb = models.SPPB.objects.all()

    return render(request, 'view_sppb.html', {'datasppb' : datasppb})

def add_sppb(request):
    if request.method == "GET":
        return render(request, "add_sppb.html")
    
    if request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]

        datasppb = models.SPPB.objects.filter(NoSPPB = nomor_sppb).exists()
        if datasppb:
            messages.error(request, "Nomor SPPB sudah ada")
            return redirect("add_sppb")
        else:
            messages.success(request, "Data berhasil disimpan")
            data_sppb = models.SPPB(
                NoSPPB = nomor_sppb,
                Tanggal = tanggal,
                Keterangan = keterangan
            ).save()
            return redirect("view_sppb")

def update_sppb(request, id):
    if request.method == "GET":
        return render(request, "update_sppb.html")
    else:
        return redirect("view_sppb")

def delete_sppb(request, id):
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    return redirect("view_sppb")

#Transaksi Produksi
def view_produksi(request):
    dataproduksi = models.TransaksiProduksi.objects.all()

    return render(request, 'view_produksi.html', {'dataproduksi' : dataproduksi})

def add_produksi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_lokasi = models.Lokasi.objects.all()

        return render(request, "add_produksi.html", {"kode_artikel": data_artikel, "nama_lokasi": data_lokasi})
    
    if request.method == "POST":
        kode_artikel = request.POST["kode_artikel"]
        lokasi = request.POST["nama_lokasi"]
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]
        jenis = request.POST["jenis"]

        artikelref = models.Artikel.objects.get(KodeArtikel=kode_artikel)
        lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)

        messages.success(request, "Data berhasil disimpan")
        data_produksi = models.TransaksiProduksi(
            KodeArtikel = artikelref,
            Lokasi = lokasiref,
            Tanggal = tanggal,
            Jumlah = jumlah,
            Keterangan = keterangan,
            Jenis = jenis
        ).save()
        return redirect("view_produksi")

def update_produksi(request, id):
    if request.method == "GET":
        return render(request, "update_produksi.html")
    else:
        return redirect("view_produksi")

def delete_produksi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    return redirect("view_produksi")
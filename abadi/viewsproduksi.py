from django.shortcuts import render, redirect
from django.contrib import messages
from . import models
from django.db.models import Sum
from datetime import datetime, timedelta
from django.db import IntegrityError
import pandas as pd

# Create your views here.
# Dashboard Gudang
def dashboard(request):
    data = models.Artikel.objects.all()
    alldata = []
    for artikel in data:
        kodeartikel = artikel.KodeArtikel

        get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id )

        datakonversi = []
        nilaifg = 0

        if data.exists():
            for item in data:
                konversidataobj = models.KonversiMaster.objects.get(KodePenyusun=item.IDKodePenyusun)

                tanggal_sekarang = datetime.now().date()
                tanggal_awal = (datetime.now() - timedelta(days=7)).date()
                konversidataobj.lastedited

                if konversidataobj.lastedited and (tanggal_awal <= konversidataobj.lastedited.date() <= tanggal_sekarang):
                    pass
                else:
                    continue

                masukobj = models.DetailSuratJalanPembelian.objects.filter(KodeProduk=item.KodeProduk)

                tanggalmasuk = masukobj.values_list(
                    "NoSuratJalan__Tanggal", flat=True
                )
                keluarobj = models.TransaksiGudang.objects.filter(
                    jumlah__gte=0, KodeProduk=item.KodeProduk
                )
                tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                saldoawalobj = (
                    models.SaldoAwalBahanBaku.objects.filter(
                        IDBahanBaku=item.KodeProduk.KodeProduk
                    )
                    .order_by("-Tanggal")
                    .first()
                )
                if saldoawalobj:
                    saldoawal = saldoawalobj.Jumlah
                    hargasatuanawal = saldoawalobj.Harga
                    hargatotalawal = saldoawal * hargasatuanawal
                else:
                    saldoawal = 0
                    hargasatuanawal = 0
                    hargatotalawal = saldoawal * hargasatuanawal

                hargaterakhir = 0
                listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
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

                hargaterakhir += hargasatuanawal
                kuantitaskonversi = konversidataobj.Kuantitas
                kuantitasallowance = kuantitaskonversi + kuantitaskonversi * 0.025
                hargaperkotak = hargaterakhir * kuantitasallowance
                nilaifg += hargaperkotak

                datakonversi.append(
                    {
                        "kodeartikel": get_id_kodeartikel,
                        "Penyusunobj": item,
                        "HargaSatuan": round(hargaterakhir, 2),
                        "Konversi": round(kuantitaskonversi, 5),
                        "Allowance": round(kuantitasallowance, 5),
                        "Hargakotak": round(hargaperkotak, 2),
                    }
                )

        alldata.append(datakonversi)

    return render(request, "produksi/dashboard.html",{"data": alldata})


def load_detailspk(request):
    no_spk = request.GET.get("nomor_spk")
    id_spk = models.SPK.objects.get(NoSPK=no_spk)
    detailspk = models.DetailSPK.objects.filter(NoSPK=id_spk.id)

    return render(request, "produksi/opsi_spk.html", {"detailspk": detailspk})



def load_htmx(request):
    no_spk = request.GET.get("nomor_spk")
    id_spk = models.SPK.objects.get(NoSPK=no_spk)
    detailspk = models.DetailSPK.objects.filter(NoSPK=id_spk.id)

    return render(request, "produksi/opsi_htmx.html", {"detailspk": detailspk})


def load_artikel(request):
    kode_artikel = request.GET.get("kode_artikel")
    artikelobj = models.Artikel.objects.get(KodeArtikel=kode_artikel)
    detailspk = models.DetailSPK.objects.filter(KodeArtikel=artikelobj,)

    return render(request, "produksi/opsi_artikel.html", {"detailspk": detailspk})


def load_penyusun(request):
    kodeartikel = request.GET.get("artikel")
    penyusun = models.Penyusun.objects.filter(KodeArtikel=kodeartikel)

    return render(request, "produksi/opsi_penyusun.html", {"penyusun": penyusun})


# SPK
def view_spk(request):
    dataspk = models.SPK.objects.all().order_by("-Tanggal")

    for j in dataspk:
        total_detail_spk = models.DetailSPK.objects.filter(NoSPK=j).values('KodeArtikel').annotate(total=Sum('Jumlah'))
        is_lunas = True
        for detail_spk in total_detail_spk:
            kode_artikel = detail_spk['KodeArtikel']
            total_requested = detail_spk['total']
            
            total_processed = models.DetailSPPB.objects.filter(DetailSPK__NoSPK=j, DetailSPK__KodeArtikel=kode_artikel).aggregate(total=Sum('Jumlah'))['total'] or 0
            
            if total_processed < total_requested:
                is_lunas = False
                break

        if is_lunas:
            j.Keterangan = "Lunas"
            j.save()
        else:
            j.Keterangan = "Belum-Lunas"
            j.save()            
            

    return render(request, "produksi/view_spk.html", {"dataspk": dataspk})


def add_spk(request):
    dataartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(request, "produksi/add_spk.html", {"data": dataartikel})

    if request.method == "POST":
        nomor_spk = request.POST["nomor_spk"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]

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

            artikel_list = request.POST.getlist("artikel[]")
            jumlah_list = request.POST.getlist("quantity[]")
            no_spk = models.SPK.objects.get(NoSPK=nomor_spk)

            for produk, jumlah in zip(artikel_list, jumlah_list):
                # Pisahkan KodeArtikel dari jumlah dengan delimiter '/'
                kode_artikel = models.Artikel.objects.get(KodeArtikel=produk)
                jumlah_produk = jumlah

                # Simpan data ke dalam model DetailSPK
                datadetailspk = models.DetailSPK(
                    NoSPK=no_spk, KodeArtikel=kode_artikel, Jumlah=jumlah_produk
                )
                datadetailspk.save()

            return redirect("view_spk")


def detail_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "produksi/detail_spk.html",
            {
                "data": dataartikel,
                "dataspk": dataspk,
                "datadetail": datadetail,
                "tanggal": tanggal,
            },
        )

    elif request.method == "POST":
        nomor_spk = request.POST["nomor_spk"]
        tanggall = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        artikel_list = request.POST.getlist("artikel[]")
        jumlah_list = request.POST.getlist("quantity[]")

        dataspk.NoSPK = nomor_spk
        dataspk.Tanggal = tanggall
        dataspk.Keterangan = keterangan
        dataspk.save()

        for detail, artikel_id, jumlah in zip(datadetail, artikel_list, jumlah_list):
            kode_artikel = models.Artikel.objects.get(KodeArtikel=artikel_id)
            detail.KodeArtikel = kode_artikel
            detail.Jumlah = jumlah
            detail.save()

        no_spk = models.SPK.objects.get(NoSPK=nomor_spk)

        for artikel_id, jumlah in zip(
            artikel_list[len(datadetail) :], jumlah_list[len(datadetail) :]
        ):
            kode_artikel = models.Artikel.objects.get(KodeArtikel=artikel_id)
            new_detail = models.DetailSPK.objects.create(
                NoSPK=no_spk,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                KodeArtikel=kode_artikel,
                Jumlah=jumlah,
            )
            try:
                new_detail.save()
            except IntegrityError:
                # Handle if there's any IntegrityError, such as violating unique constraint
                pass

        return redirect("detail_spk", id=id)


def delete_spk(request, id):
    dataspk = models.SPK.objects.get(id=id)
    dataspk.delete()
    return redirect("view_spk")


def delete_detailspk(request, id):
    datadetailspk = models.DetailSPK.objects.get(IDDetailSPK=id)
    dataspk = models.SPK.objects.get(NoSPK=datadetailspk.NoSPK)
    datadetailspk.delete()
    return redirect("detail_spk", id=dataspk.id)


def track_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)

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

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "produksi/trackingspk.html",
            {
                "data": dataartikel,
                "dataspk": dataspk,
                "datadetail": datadetail,
                "tanggal": tanggal,
                "transaksigudang": transaksigudangobj,
                "transaksiproduksi": transaksiproduksiobj,
                "transaksikeluar": sppbobj,
            },
        )
    

# SPPB
def view_sppb(request):
    datasppb = models.SPPB.objects.all().order_by("-Tanggal")
    for i in datasppb:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_sppb.html", {"datasppb": datasppb})


def add_sppb(request):
    dataartikel = models.Artikel.objects.all()

    if request.method == "GET":
        return render(
            request,
            "produksi/add_sppb.html",
            {
                "data": dataartikel,
            },
        )

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

            artikel_list = request.POST.getlist("detail_spk[]")
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

            return redirect("view_sppb")




def delete_sppb(request, id):
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    return redirect("view_sppb")


def delete_detailsppb(request, id):
    datadetailsppb = models.DetailSPPB.objects.get(IDDetailSPPB=id)
    datasppb = models.SPPB.objects.get(NoSPPB=datadetailsppb.NoSPPB)
    datadetailsppb.delete()
    return redirect("detail_sppb", id=datasppb.id)


# Transaksi Produksi
def view_mutasi(request):
    dataproduksi = models.TransaksiProduksi.objects.filter(Jenis="Mutasi").order_by(
        "-Tanggal", "KodeArtikel"
    )
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(request, "produksi/view_mutasi.html", {"dataproduksi": dataproduksi})


def view_produksi(request):
    dataproduksi = models.TransaksiProduksi.objects.filter(Jenis="Produksi").order_by(
        "-Tanggal", "KodeArtikel"
    )
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_produksi.html", {"dataproduksi": dataproduksi}
    )


def add_mutasi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_lokasi = models.Lokasi.objects.all()
        data_spk = models.SPK.objects.all()

        return render(
            request,
            "produksi/add_mutasi.html",
            {
                "kode_artikel": data_artikel,
                "nama_lokasi": data_lokasi,
                "data_spk": data_spk,
            },
        )

    if request.method == "POST":
        listkode_artikel = request.POST.getlist("kode_artikel[]")
        listlokasi = request.POST.getlist("nama_lokasi[]")
        tanggal = request.POST["tanggal"]
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")
        listdetail_spk = request.POST.getlist("detail_spk[]")

        for kode, lokasi, jumlah, keterangan, detail_spk in zip(
            listkode_artikel, listlokasi, listjumlah, listketerangan, listdetail_spk
        ):
            artikelref = models.Artikel.objects.get(KodeArtikel=kode)
            lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)
            try:
                detailspkref = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
            except:
                detailspkref = None

            data_produksi = models.TransaksiProduksi(
                KodeArtikel=artikelref,
                Lokasi=lokasiref,
                Tanggal=tanggal,
                Jumlah=jumlah,
                Keterangan=keterangan,
                Jenis="Mutasi",
                DetailSPK=detailspkref,
            ).save()
            messages.success(request, "Data berhasil disimpan")

        return redirect("view_mutasi")


def add_produksi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_spk = models.SPK.objects.all()

        return render(
            request,
            "produksi/add_produksi.html",
            {"kode_artikel": data_artikel, "data_spk": data_spk},
        )

    if request.method == "POST":
        listkode_artikel = request.POST.getlist("kode_artikel[]")
        tanggal = request.POST["tanggal"]
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")
        listdetail_spk = request.POST.getlist("detail_spk[]")

        for kode, jumlah, keterangan, detail_spk in zip(
            listkode_artikel, listjumlah, listketerangan, listdetail_spk
        ):
            artikelref = models.Artikel.objects.get(KodeArtikel=kode)
            lokasiref = models.Lokasi.objects.get(IDLokasi=1)
            try:
                detailspkref = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
            except:
                detailspkref = None

            data_produksi = models.TransaksiProduksi(
                KodeArtikel=artikelref,
                Lokasi=lokasiref,
                Tanggal=tanggal,
                Jumlah=jumlah,
                Keterangan=keterangan,
                Jenis="Produksi",
                DetailSPK=detailspkref,
            ).save()
            messages.success(request, "Data berhasil disimpan")

        return redirect("view_produksi")


def update_produksi(request, id):
    produksiobj = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    data_artikel = models.Artikel.objects.all()
    data_spk = models.SPK.objects.all()

    try:
        data_detailspk = models.DetailSPK.objects.filter(
            NoSPK=produksiobj.DetailSPK.NoSPK.id
        )
    except:
        data_detailspk = None

    if request.method == "GET":
        tanggal = datetime.strftime(produksiobj.Tanggal, "%Y-%m-%d")
        return render(
            request,
            "produksi/update_produksi.html",
            {
                "produksi": produksiobj,
                "tanggal": tanggal,
                "kode_artikel": data_artikel,
                "data_spk": data_spk,
                "data_detailspk": data_detailspk,
            },
        )

    elif request.method == "POST":
        kode_artikel = request.POST["kode_artikel"]
        getartikel = models.Artikel.objects.get(KodeArtikel=kode_artikel)
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]
        try:
            detail_spk = request.POST["detail_spk"]
            detspkobj = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
        except:
            detspkobj = None

        produksiobj.KodeArtikel = getartikel
        produksiobj.Tanggal = tanggal
        produksiobj.Jumlah = jumlah
        produksiobj.Keterangan = keterangan
        produksiobj.DetailSPK = detspkobj
        produksiobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_produksi")


def update_mutasi(request, id):
    produksiobj = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    data_artikel = models.Artikel.objects.all()
    data_lokasi = models.Lokasi.objects.all()
    data_spk = models.SPK.objects.all()

    try:
        data_detailspk = models.DetailSPK.objects.filter(
            NoSPK=produksiobj.DetailSPK.NoSPK.id
        )
    except:
        data_detailspk = None

    if request.method == "GET":
        tanggal = datetime.strftime(produksiobj.Tanggal, "%Y-%m-%d")
        return render(
            request,
            "produksi/update_mutasi.html",
            {
                "produksi": produksiobj,
                "tanggal": tanggal,
                "kode_artikel": data_artikel,
                "nama_lokasi": data_lokasi,
                "data_spk": data_spk,
                "data_detailspk": data_detailspk,
            },
        )

    elif request.method == "POST":
        kode_artikel = request.POST["kode_artikel"]
        getartikel = models.Artikel.objects.get(KodeArtikel=kode_artikel)
        lokasi = request.POST["nama_lokasi"]
        getlokasi = models.Lokasi.objects.get(IDLokasi=lokasi)
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]
        try:
            detail_spk = request.POST["detail_spk"]
            detspkobj = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
        except:
            detspkobj = None

        produksiobj.KodeArtikel = getartikel
        produksiobj.Lokasi = getlokasi
        produksiobj.Tanggal = tanggal
        produksiobj.Jumlah = jumlah
        produksiobj.Keterangan = keterangan
        produksiobj.DetailSPK = detspkobj
        produksiobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_mutasi")


def delete_produksi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("view_produksi")


def delete_mutasi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("view_mutasi")


# Transaksi Gudang
def view_gudang(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__gt=0).order_by(
        "-tanggal", "KodeProduk"
    )
    for i in datagudang:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")

    return render(request, "produksi/view_gudang.html", {"datagudang": datagudang})


def view_gudangretur(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__lt=0).order_by(
        "-tanggal", "KodeProduk"
    )
    for data in datagudang:
        data.retur = -data.jumlah
    for i in datagudang:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")

    return render(request, "produksi/view_gudangretur.html", {"datagudang": datagudang})


def add_gudang(request):
    if request.method == "GET":
        data_produk = models.Produk.objects.all()
        data_lokasi = models.Lokasi.objects.all()
        data_spk = models.SPK.objects.all()

        listproduk = [produk.NamaProduk for produk in data_produk]

        return render(
            request,
            "produksi/add_gudang.html",
            {
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi,
                "data_spk": data_spk,
                "listproduk": listproduk,
            },
        )

    if request.method == "POST":
        listkode = request.POST.getlist("kode_produk[]")
        listlokasi = request.POST.getlist("nama_lokasi[]")
        tanggal = request.POST["tanggal"]
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")
        listdetail = request.POST.getlist("detail_spk[]")
        print(listkode)
        print(listketerangan)
        print(listdetail)

        for produk, lokasi, jumlah, keterangan, detail in zip(
            listkode, listlokasi, listjumlah, listketerangan, listdetail
        ):
            produkref = models.Produk.objects.get(KodeProduk=produk)
            lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)
            try:
                detailspkref = models.DetailSPK.objects.get(IDDetailSPK=detail)
            except:
                detailspkref = None

            data_gudang = models.TransaksiGudang(
                KodeProduk=produkref,
                Lokasi=lokasiref,
                tanggal=tanggal,
                jumlah=jumlah,
                keterangan=keterangan,
                KeteranganACC=False,
                DetailSPK=detailspkref,
            ).save()
            messages.success(request, "Data berhasil ditambahkan")

        return redirect("view_gudang")


def add_gudangretur(request):
    if request.method == "GET":
        data_produk = models.Produk.objects.all()
        data_lokasi = models.Lokasi.objects.all()
        data_spk = models.SPK.objects.all()

        listproduk = [produk.NamaProduk for produk in data_produk]

        return render(
            request,
            "produksi/add_gudangretur.html",
            {
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi,
                "data_spk": data_spk,
                "listproduk": listproduk,
            },
        )

    if request.method == "POST":
        tanggal = request.POST["tanggal"]
        listproduk = request.POST.getlist("kode_produk[]")
        listlokasi = request.POST.getlist("nama_lokasi[]")
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")

        for produk, lokasi, jumlah, keterangan in zip(
            listproduk, listlokasi, listjumlah, listketerangan
        ):

            produkref = models.Produk.objects.get(KodeProduk=produk)
            lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)

            data_gudang = models.TransaksiGudang(
                KodeProduk=produkref,
                Lokasi=lokasiref,
                tanggal=tanggal,
                jumlah=-int(jumlah),
                keterangan=keterangan,
                KeteranganACC=False,
            ).save()
            messages.success(request, "Data berhasil ditambahkan")

        return redirect("view_gudangretur")


def update_gudang(request, id):
    gudangobj = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    data_produk = models.Produk.objects.all()
    data_lokasi = models.Lokasi.objects.all()
    data_spk = models.SPK.objects.all()
    try:
        data_detailspk = models.DetailSPK.objects.filter(
            NoSPK=gudangobj.DetailSPK.NoSPK.id
        )
    except:
        data_detailspk = None

    if request.method == "GET":
        tanggal = datetime.strftime(gudangobj.tanggal, "%Y-%m-%d")
        return render(
            request,
            "produksi/update_gudang.html",
            {
                "gudang": gudangobj,
                "tanggal": tanggal,
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi,
                "data_spk": data_spk,
                "data_detailspk": data_detailspk,
            },
        )

    elif request.method == "POST":
        kode_produk = request.POST["kode_produk"]
        getproduk = models.Produk.objects.get(KodeProduk=kode_produk)
        lokasi = request.POST["nama_lokasi"]
        getlokasi = models.Lokasi.objects.get(IDLokasi=lokasi)
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        try:
            detail_spk = request.POST["detail_spk"]
            detspkobj = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
        except:
            detspkobj = None

        gudangobj.KodeProduk = getproduk
        gudangobj.Lokasi = getlokasi
        gudangobj.tanggal = tanggal
        gudangobj.jumlah = jumlah
        gudangobj.keterangan = keterangan
        gudangobj.DetailSPK = detspkobj

        gudangobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_gudang")


def update_gudangretur(request, id):
    gudangobj = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    data_produk = models.Produk.objects.all()
    data_lokasi = models.Lokasi.objects.all()

    if request.method == "GET":
        tanggal = datetime.strftime(gudangobj.tanggal, "%Y-%m-%d")
        jumlah = -gudangobj.jumlah
        return render(
            request,
            "produksi/update_gudangretur.html",
            {
                "gudang": gudangobj,
                "tanggal": tanggal,
                "jumlah": jumlah,
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi,
            },
        )

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
        gudangobj.jumlah = -int(jumlah)
        gudangobj.keterangan = keterangan

        gudangobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_gudangretur")


def delete_gudang(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.delete()
    messages.success(request, "Data Berhasil dihapus")

    return redirect("view_gudang")


def delete_gudangretur(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.delete()
    messages.success(request, "Data Berhasil dihapus")

    return redirect("view_gudangretur")


# Rekapitulasi
def view_ksbb2(request):
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbb.html")
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb")

        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        # Mendapatkan semua penyusun yang terkait dengan produk
        penyusun_produk = models.Penyusun.objects.filter(KodeProduk=produk)

        # Mendapatkan artikel yang terkait dengan penyusun produk
        artikel_penyusun = [penyusun.KodeArtikel for penyusun in penyusun_produk]

        # Memfilter transaksi produksi berdasarkan artikel yang terkait dengan penyusun produk
        dataproduksi = (
            models.TransaksiProduksi.objects.filter(
                KodeArtikel__in=artikel_penyusun,
                Jenis="Mutasi",
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            .values("KodeArtikel", "Tanggal")
            .annotate(Jumlah=Sum("Jumlah"))
        )

        kuantitas_konversi = {}
        for penyusun in penyusun_produk:
            konversi = models.KonversiMaster.objects.filter(KodePenyusun=penyusun)
            if konversi.exists():
                kuantitas_konversi[penyusun.IDKodePenyusun] = konversi[0].Kuantitas
            else:
                kuantitas_konversi[penyusun.IDKodePenyusun] = 0

        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)

        listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))

        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0

        sisa = saldo

        data = []
        for i in listtanggal:
            try:
                datamasuk = datagudang.filter(tanggal=i)
                masuk = 0
                for k in datamasuk:
                    masuk += k.jumlah
            except:
                masuk = 0

            detail = []
            try:
                is_first_iteration = True
                datakeluar = dataproduksi.filter(Tanggal=i)
                for keluar in datakeluar:
                    kode_artikel = models.Artikel.objects.filter(
                        id=keluar["KodeArtikel"]
                    )
                    for kode in kode_artikel:
                        if kode in artikel_penyusun:
                            konversi = 0
                            penyusun = models.Penyusun.objects.filter(
                                KodeProduk=produk, KodeArtikel=kode
                            )
                            for j in penyusun:
                                konversi += kuantitas_konversi[j.IDKodePenyusun] + (
                                    kuantitas_konversi[j.IDKodePenyusun] * 2.5 / 100
                                )

                    jumlah = keluar["Jumlah"]
                    fkonversi = round(konversi, 6)
                    keluar = jumlah * konversi
                    fkeluar = round(keluar, 6)
                    if is_first_iteration:
                        sisa = sisa + masuk - fkeluar
                        is_first_iteration = False
                    else:
                        sisa = sisa - fkeluar

                    fsisa = round(sisa, 4)

                    dummy = {
                        "nama": kode_artikel,
                        "jumlah": jumlah,
                        "konversi": fkonversi,
                        "keluar": fkeluar,
                        "sisa": fsisa,
                    }
                    detail.append(dummy)
            except:
                pass

            if not detail:
                sisa = sisa + masuk
                fsisa = round(sisa, 4)
                deta = {
                    "nama": 0,
                    "jumlah": 0,
                    "konversi": 0,
                    "keluar": 0,
                    "sisa": fsisa,
                }
                detail.append(deta)

            dumy = {
                "tanggal": i,
                "detail": detail,
                "masuk": masuk,
            }
            data.append(dumy)

        return render(
            request,
            "produksi/view_ksbb.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": data,
                "saldo": saldo,
                "tahun": tahun,
            },
        )


def views_ksbj(request):
    if len(request.GET) == 0:
        dataartikel = models.Artikel.objects.all()
        return render(request, "produksi/view_ksbj.html", {"dataartikel": dataartikel})
    else:
        print(request.GET)
        lokasi = request.GET["lokasi"]
        tahun = request.GET["tahun"]
        kodeartikel = request.GET["kodeartikel"]
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
        saldoawalobj = models.SaldoAwalArtikel.objects.filter(
            IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi
        )

        # Cek apabila Kode Artikel user tidak ada
        try:
            artikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return redirect("views_ksbj")
        # Cek apabila penyusun utama belum di setting
        try:
            getbahanbakuutama = models.Penyusun.objects.get(
                KodeArtikel=artikel.id, Status=1
            )
        except models.Penyusun.DoesNotExist:
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("views_ksbj")

        data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id)
        # if lokasi == "WIP":
        # # print(tanggallist)
        listdata = []

        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoakhirgte = (
                    saldoawalobj.filter(Tanggal__year__gt=tahun)
                    .order_by("Tanggal")
                    .first()
                )
                saldoawallte = (
                    saldoawalobj.filter(Tanggal__year__lte=tahun)
                    .order_by("-Tanggal")
                    .first()
                )
                print("Ini saldo gte : ", saldoakhirgte)
                print("Ini Saldo LTE : ", saldoawallte)
                print("Tahun saat ini : ", tahun)
                print("Saldo Awal Tahun : ", saldoawallte)
                print("Saldo Akhir Tahun : ", saldoakhirgte)
            except:
                saldoawallte = None
                saldoakhirgte = None
            print(saldoawalobj)

            if saldoawallte and saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = saldoakhirgte.Tanggal
            elif saldoawallte and not saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = datetime.max
            elif not saldoawallte and saldoakhirgte:
                print("data awal tidak ditemukan")
                tanggalawal = datetime.min
                tanggalakhir = saldoakhirgte.Tanggal
            else:
                print("Tidak ditemukan data awal dan akhir")
                tanggalawal = datetime.min
                tanggalakhir = datetime.max

            tanggallist = (
                data.filter(Tanggal__range=(tanggalawal, tanggalakhir))
                .values_list("Tanggal", flat=True)
                .order_by("Tanggal")
                .distinct()
            )

            saldoawalobj = saldoawallte

            if saldoawalobj:
                saldoawal = saldoawalobj.Jumlah
            else:
                saldoawal = 0
            # print('ini WIP')
            saldoawaltaun = saldoawal
            for i in tanggallist:

                jumlahhasil = 0
                jumlahmasuk = 0
                # print(data)
                print(i)
                filtertanggal = data.filter(Tanggal=i)
                print(filtertanggal)
                if filtertanggal:
                    jumlahmasuk = filtertanggal.filter(Jenis="Produksi").aggregate(
                        total=Sum("Jumlah")
                    )["total"]
                    print(jumlahmasuk)
                    if jumlahmasuk is None:
                        jumlahmasuk = 0
                    jumlahhasil = filtertanggal.filter(Jenis="Mutasi").aggregate(
                        total=Sum("Jumlah")
                    )["total"]
                    if jumlahhasil is None:
                        jumlahhasil = 0
                    print(jumlahhasil)

                    # Cari data konversi bahan baku utama pada artikel terkait

                konversimasterobj = models.KonversiMaster.objects.get(
                    KodePenyusun=getbahanbakuutama.IDKodePenyusun
                )
                # print('Konversi', konversimasterobj.Kuantitas + ( konversimasterobj.Kuantitas*0.025))
                masukpcs = round(
                    jumlahmasuk
                    / (
                        (
                            konversimasterobj.Kuantitas
                            + (konversimasterobj.Kuantitas * 0.025)
                        )
                    )
                    * 0.893643879
                )
                # Cari data penyesuaian
                saldoawal = saldoawal - jumlahhasil + masukpcs
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )
                # listdata.append([i,getbahanbakuutama,jumlahmasuk,jumlahhasil,masukpcs,sisa])
                listdata.append(
                    {
                        "Tanggal": i,
                        "Bahanbakuutama": getbahanbakuutama,
                        "Jumlahmasuk": jumlahmasuk,
                        "Jumlahhasil": jumlahhasil,
                        "Masukpcs": masukpcs,
                        "Sisa": saldoawal,
                    }
                )

            stockopname = 0
            if saldoakhirgte:
                stockopname = saldoakhirgte.Jumlah - saldoawal
            print(saldoakhirgte)

            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": lokasi,
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                    "stockopname": stockopname,
                    "saldoakhir": saldoakhirgte,
                },
            )

            #     print(getbahanbakuutama)

        else:
            data = data.filter(Lokasi=1)
            saldoawalperiode = (
                saldoawalobj.values_list("Tanggal__year", flat=True)
                .distinct()
                .order_by("-Tanggal")
            )
            print(saldoawalperiode)
            try:
                saldoakhirgte = (
                    saldoawalobj.filter(Tanggal__year__gt=tahun)
                    .order_by("Tanggal")
                    .first()
                )
                saldoawallte = (
                    saldoawalobj.filter(Tanggal__year__lte=tahun)
                    .order_by("-Tanggal")
                    .first()
                )
                print("Ini saldo gte : ", saldoakhirgte)
                print("Ini Saldo LTE : ", saldoawallte)
                print("Tahun saat ini : ", tahun)
                print("Saldo Awal Tahun : ", saldoawallte)
                print("Saldo Akhir Tahun : ", saldoakhirgte)
            except ValueError:
                saldoawallte = None
                saldoakhirgte = None

            # IF Saldo awal LTE kosong --> Data saldoawal belum di set --> Harusnya di set semua pertahun
            if saldoawallte and saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = saldoakhirgte.Tanggal
            elif saldoawallte and not saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = datetime.max
            elif not saldoawallte and saldoakhirgte:
                print("data awal tidak ditemukan")
                tanggalawal = datetime.min
                tanggalakhir = saldoakhirgte.Tanggal
            else:
                print("Tidak ditemukan data awal dan akhir")
                tanggalawal = datetime.min
                tanggalakhir = datetime.max
            # IF Saldo Akhir GT kosong --> Data filter data tahun saat ini
            tanggallist = (
                data.filter(Tanggal__range=(tanggalawal, tanggalakhir))
                .values_list("Tanggal", flat=True)
                .distinct()
            )

            saldoawalobj = saldoawallte

            if saldoawalobj:
                saldoawal = saldoawalobj.Jumlah
            else:
                saldoawal = 0
            sppb = models.DetailSPPB.objects.filter(
                DetailSPK__KodeArtikel__KodeArtikel=kodeartikel,
                NoSPPB__Tanggal__range=(tanggalawal, tanggalakhir),
            )
            tanggalsppb = sppb.values_list("NoSPPB__Tanggal", flat=True).distinct()
            # print(tanggalsppb)
            tanggallist = sorted(list(set(tanggallist.union(tanggalsppb))))
            # print(tanggallist)

            # print('ini FG')
            saldoawaltaun = saldoawal
            for i in tanggallist:
                jumlahhasil = 0
                jumlahmasuk = 0
                totalmasuk = 0
                totalkeluar = 0
                nosppb = []
                nospk = []
                jumlah = []
                listsppbobj = []

                penyerahanwip = models.TransaksiProduksi.objects.filter(
                    Tanggal=i,
                    KodeArtikel__KodeArtikel=kodeartikel,
                    Jenis="Mutasi",
                    Lokasi__NamaLokasi="WIP",
                )
                detailsppbobj = sppb.filter(NoSPPB__Tanggal=i)
                # print(detailsppbobj)
                if penyerahanwip:
                    # print('data penyerahan ada ',i)
                    totalmasuk = penyerahanwip.aggregate(total=Sum("Jumlah"))["total"]

                    # print(totalmasuk)
                if detailsppbobj:
                    # print('data Pengiriman Ada',i)
                    totalkeluar = detailsppbobj.aggregate(total=Sum("Jumlah"))["total"]
                    # print(totalkeluar)
                    for j in detailsppbobj:
                        nosppb.append(j.NoSPPB)
                        nospk.append(j.DetailSPK.NoSPK)
                        jumlah.append(j.Jumlah)
                saldoawal += totalmasuk - totalkeluar
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )
                # print('Tanggal : ',i)
                # print('Jumlah Penyerahan dari WIP : ',totalmasuk)
                # print('SPPB : ', nosppb)
                # print('SPK : ',nospk)
                # print('Jumlah Kirim : ',jumlah)
                # print('Sisa : ')
                # print('\n')

                listdata.append(
                    {
                        "Tanggal": i,
                        "JumlahPenyerahan": totalmasuk,
                        "SPPB": nosppb,
                        "SPK": nospk,
                        "Jumlahkirim": jumlah,
                        "Sisa": saldoawal,
                    }
                )

            print("ini saldo awal", saldoawalobj)
            # print('saldoakhir ', saldoakhirgte.Jumlah)
            stockopname = 0
            if saldoakhirgte:
                stockopname = saldoakhirgte.Jumlah - saldoawal
                print(stockopname)

            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": "FG",
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                    "saldoakhir": saldoakhirgte,
                    "stockopname": stockopname,
                },
            )


def view_rekapbarang(request):
    if len(request.GET) == 0:
        return render(request, "produksi/rekap_barang.html")
    else:
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        dataproduk = models.Produk.objects.all()
        for produk in dataproduk:
            print(produk)
            # Menceri data transaksi gudang dengan kode 
            datagudang = models.TransaksiGudang.objects.filter(KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir))
            
            # Kode Artikel yang di susun oleh bahan baku 
            penyusun_produk = (models.Penyusun.objects.filter(KodeProduk=produk).values_list("KodeArtikel", flat=True).distinct())

            # Mencari data pemusnahan artikel yang disupport
            pemusnahanobj = models.PemusnahanArtikel.objects.filter(KodeArtikel__id__in=penyusun_produk,Tanggal__range=(tanggal_mulai, tanggal_akhir))
            dataproduksi = models.TransaksiProduksi.objects.filter(KodeArtikel__id__in=penyusun_produk,Jenis="Mutasi",Tanggal__range=(tanggal_mulai, tanggal_akhir))
            
            listartikelmaster = []
            ''' PENYESUAIAN SECTION '''
            for artikel in penyusun_produk:
                artikelmaster = models.Artikel.objects.get(id = artikel)

                konversi = models.KonversiMaster.objects.filter(KodePenyusun__KodeArtikel=artikel, KodePenyusun__KodeProduk=produk).order_by('KodePenyusun__versi')

                tanggalversi = konversi.values_list('KodePenyusun__versi',flat=True).distinct()
                listkonversi = []

                if konversi.exists():
                    for tanggal in tanggalversi:
                        datakonversi = konversi.filter(KodePenyusun__versi = tanggal)
                        kuantitas = datakonversi.aggregate(total = Sum('Kuantitas'))
                        listkonversi.append(kuantitas['total'])

                artikelmaster.listkonversi = listkonversi
                artikelmaster.tanggalversi = tanggalversi

                # Data Penyesuaian 
                penyesuaianobj  = models.Penyesuaian.objects.filter(KodePenyusun__KodeArtikel = artikel, TanggalMulai__range = (tanggal_mulai,tanggal_akhir))

                penyesuaiandataperartikel = [i.konversi for i in penyesuaianobj]
                tanggalpenyesuaianperartikel = [i.TanggalMulai for i in penyesuaianobj]
                tanggalpenyesuaianakhirperartikel = [i.TanggalAkhir for i in penyesuaianobj]

                artikelmaster.listpenyesuaian = penyesuaiandataperartikel
                artikelmaster.tanggalpenyesuaian =tanggalpenyesuaianperartikel
                artikelmaster.tanggalpenyesuaianakhir = tanggalpenyesuaianakhirperartikel
                listartikelmaster.append(artikelmaster)

            ''' TANGGAL SECTION '''
            tanggalmasuk = datagudang.values_list("tanggal", flat=True)
            tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
            tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

            listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan))))

            ''' SALDO AWAL SECTION '''
            try:
                saldoawal = models.SaldoAwalBahanBaku.objects.get(
                    IDBahanBaku=produk,
                    IDLokasi=1,
                    Tanggal__range=(tanggal_mulai, tanggal_akhir),
                )
                saldo = saldoawal.Jumlah
                saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

            except models.SaldoAwalBahanBaku.DoesNotExist:
                saldo = 0
                saldoawal = None

            sisa = saldo

            ''' PENGOLAHAN DATA '''
            listdata =[]
            for i in listtanggal:
                # Data Models
                datamodelsartikel = []
                datamodelsperkotak = []
                datamodelskonversi = []
                datamodelskeluar = []
                datamodelssisa = []
                data = {
                    'Tanggal': None,
                    'Artikel': datamodelsartikel,
                    'Perkotak' : datamodelsperkotak,
                    "Konversi" : datamodelskonversi,
                    'Masuk' : None,
                    'Keluar' : datamodelskeluar,
                    'Sisa' : datamodelssisa
                    
                }
                data['Tanggal'] = i.strftime("%Y-%m-%d")
                # Data Masuk
                masuk = 0
                datamasuk = datagudang.filter(tanggal=i)
                for k in datamasuk:
                    masuk += k.jumlah
                sisa  += masuk
                
                # Data Keluar
                data['Masuk'] = masuk
                datakeluar = dataproduksi.filter(Tanggal = i)
                artikelkeluar = datakeluar.values_list('KodeArtikel',flat=True).distinct()
                datapemusnahan = pemusnahanobj.filter(Tanggal = i)
                artikelpemusnahan = datapemusnahan.values_list('KodeArtikel',flat=True).distinct()

                for j in artikelkeluar:
                    artikelkeluarobj = models.Artikel.objects.get(id = j)
                    total = datakeluar.filter(KodeArtikel__id = j).aggregate(total = Sum('Jumlah'))
                    indexartikel = listartikelmaster.index(artikelkeluarobj)
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                    filtered_data.sort(reverse=True)

                    if not filtered_data:
                        filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi]

                    tanggalversiterdekat = max(filtered_data)
                    indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                    konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat]

                    if listartikelmaster[indexartikel].tanggalpenyesuaian :
                        filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]

                        if not filtered_data:
                            konversiterdekat = konversiterdekat
                        else:
                            filtered_data.sort(reverse=True)
                            tanggalversiterdekat = max(filtered_data)
                            indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                            konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]

                    datamodelskonversi.append(konversiterdekat)
                    datamodelskeluar.append(konversiterdekat*total['total'])
                    datamodelsartikel.append(artikelkeluarobj)
                    datamodelsperkotak.append(total['total'])
                    sisa -= konversiterdekat*total['total']
                    sisa = round(sisa, 5)
                    datamodelssisa.append(sisa)

                for j in artikelpemusnahan:
                    artikelkeluarobj = models.Artikel.objects.get(id = j)
                    total = datapemusnahan.filter(KodeArtikel__id = j).aggregate(total=Sum('Jumlah'))
                    indexartikel = listartikelmaster.index(artikelkeluarobj)
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                    filtered_data.sort(reverse=True)
                    tanggalversiterdekat = max(filtered_data)
                    indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                    konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat]

                    if listartikelmaster[indexartikel].tanggalpenyesuaian :
                        filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]

                        if not filtered_data:
                            konversiterdekat = konversiterdekat
                        else:
                            filtered_data.sort(reverse=True)
                            tanggalversiterdekat = max(filtered_data)
                            indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                            konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]

                    datamodelskonversi.append(konversiterdekat)
                    datamodelskeluar.append(konversiterdekat*total['total'])
                    datamodelsartikel.append(artikelkeluarobj)
                    datamodelsperkotak.append(total['total'])
                    sisa -= konversiterdekat*total['total']
                    sisa = round(sisa, 5)
                    datamodelssisa.append(sisa)

                if not datamodelssisa :
                    sisa = round(sisa, 5)
                    datamodelssisa.append(sisa)

                listdata.append(data['Sisa'])
            
            produk.kuantitas = sisa

        return render(request, "produksi/rekap_barang.html", {'data':dataproduk})


def view_rekaprusak(request):
    if len(request.GET) == 0:
        return render(request, "produksi/rekap_rusak.html")
    else:
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        lokasi = request.GET["lokasi"]
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        databarang = models.PemusnahanBahanBaku.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, tanggal_akhir)).values('KodeBahanBaku','KodeBahanBaku__NamaProduk','KodeBahanBaku__unit','KodeBahanBaku__keterangan').annotate(kuantitas=Sum('Jumlah'))
        dataartikel = models.PemusnahanArtikel.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, tanggal_akhir)).values('KodeArtikel__KodeArtikel','KodeArtikel__keterangan').annotate(kuantitas=Sum('Jumlah'))

        return render(request, "produksi/rekap_rusak.html", {"databarang": databarang, "dataartikel": dataartikel, "lokasi":lokasi})


def view_rekapproduksi(request):
    if len(request.GET) == 0:
        return render(request, "produksi/rekap_produksi.html")
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
        for artikel in artikelobj:
            
            dataartikel = []
            getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1)

            if not getbahanbakuutama :
                messages.error(request, ("Bahan Baku",artikel.KodeArtikel,"belum di set"))
                continue

            data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id)
            if not data :
                messages.error(request, ("Tidak ditemukan data Transaki Produksi untuk Artikel",artikel.KodeArtikel))
                continue
            else:
                dataartikel.append(artikel.KodeArtikel)
                print(artikel.KodeArtikel)
                
            lokasiobj = models.Lokasi.objects.all()
            for lokasi in lokasiobj:

                listdata = []

                if lokasi.IDLokasi == 1:
                    data = data.filter(Lokasi=lokasi)
                    try:
                        saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                        saldo = saldoawalobj.Jumlah
                        saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
                        # print('ini saldo awallll',saldoawalobj)
                    except models.SaldoAwalArtikel.DoesNotExist :
                        saldo = 0
                        saldoawal = None
                        saldoawalobj ={'Tanggal' : 'Belum ada Data','saldo' : saldo}

                    tanggallist = (data.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir)).values_list("Tanggal", flat=True).order_by("Tanggal").distinct())
                    saldoawal = saldo

                    if not tanggallist:
                        listdata.append({'Tanggal': tanggal_mulai.strftime("%Y-%m-%d"), 'Sisa': 0})

                    
                    for i in tanggallist:
                        datamodels = {
                            'Tanggal': None,
                            "Sisa" : None
                        }

                        filtertanggal = data.filter(Tanggal=i)
                        # print(filtertanggal[0].Jumlah)

                        jumlahmutasi =  filtertanggal.filter(Jenis ="Mutasi").aggregate(total = Sum('Jumlah'))['total']
                        jumlahmasuk = filtertanggal.filter(Jenis = 'Produksi').aggregate(total = Sum('Jumlah'))['total']

                        if jumlahmutasi is None:
                            jumlahmutasi = 0
                        if jumlahmasuk is None :
                            jumlahmasuk = 0

                        # print(f'{i} tanggal,filtertangga {filtertanggal}, {jumlahmutasi} jumlah')
                        # print(i)

                        # Cari data penyusun sesuai tanggal 
                        penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id,Status = 1,versi__lte = i).order_by('-versi').first()

                        if not penyusunfiltertanggal:
                            penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id, Status = 1, versi__gte = i).order_by('versi').first()

                        konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)
                        # print(konversimasterobj.Kuantitas)

                        masukpcs = round(jumlahmasuk/((konversimasterobj.Kuantitas + (konversimasterobj.Kuantitas * 0.025))))
                        saldoawal = saldoawal - jumlahmutasi + masukpcs
                        # print(saldoawal)

                        datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                        datamodels['Sisa'] = saldoawal

                        listdata.append(datamodels)

                else:
                    data = data.filter(Lokasi=1)
                    try:
                        saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=artikel.KodeArtikel, IDLokasi=lokasi.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                        saldo = saldoawalobj.Jumlah
                        saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
                    except models.SaldoAwalArtikel.DoesNotExist :
                        saldo = 0
                        saldoawalobj ={
                            'Tanggal' : 'Belum ada Data',
                            'saldo' : saldo
                        }
                    # print('ini saldoawalobj',saldoawalobj)

                    tanggalmutasi = data.filter(Jenis = 'Produksi',Tanggal__range=(tanggal_mulai,tanggal_akhir)).values_list('Tanggal',flat=True).distinct()
                    sppb = models.DetailSPPB.objects.filter(DetailSPK__KodeArtikel__KodeArtikel = artikel.KodeArtikel, NoSPPB__Tanggal__range = (tanggal_mulai,tanggal_akhir))
                    tanggalsppb = sppb.values_list('NoSPPB__Tanggal',flat=True).distinct()
                    tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb))))
                    if not tanggallist:
                        listdata.append({'Tanggal': tanggal_mulai.strftime("%Y-%m-%d"), 'Sisa': 0})

                    saldoawal = saldo

                    for i in tanggallist:
                        datamodels = {
                            "Tanggal" : None,
                            "Sisa" : None
                        }

                        penyerahanwip = models.TransaksiProduksi.objects.filter(Tanggal = i, KodeArtikel__KodeArtikel =artikel.KodeArtikel, Jenis = "Mutasi", Lokasi__NamaLokasi = "WIP" )
                        detailsppbjobj = sppb.filter(NoSPPB__Tanggal = i)

                        totalpenyerahanwip = penyerahanwip.aggregate(total=Sum('Jumlah'))['total']
                        totalkeluar = detailsppbjobj.aggregate(total=Sum('Jumlah'))['total']
                        
                        if not totalpenyerahanwip:
                            totalpenyerahanwip = 0
                        if not totalkeluar :
                            totalkeluar = 0

                        saldoawal += totalpenyerahanwip - totalkeluar
                        # print(totalpenyerahanwip)

                        datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                        datamodels['Sisa'] = saldoawal

                        listdata.append(datamodels)


                if listdata:
                    df = pd.DataFrame(listdata)

                    # Convert 'Tanggal' column to datetime
                    df['Tanggal'] = pd.to_datetime(df['Tanggal'])

                    # Resampling to get the last day of each month
                    df_resampled = df.resample('M', on='Tanggal').last().fillna({'Sisa': 0}).reset_index()

                    # Creating a new DataFrame with all months from 1 to 12
                    all_months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
                    df_all_months = pd.DataFrame({'Tanggal': all_months})

                    # Merging the resampled data with all months
                    result_df = pd.merge(df_all_months, df_resampled, on='Tanggal', how='left').fillna({'Sisa': 0})

                    # Getting the data for all months
                    result_data = result_df.to_dict('records')
                
                dataartikel.append(result_data)
            
            item3 = [{'Tanggal': d1['Tanggal'], 'Sisa': d1['Sisa'] + d2['Sisa']} for d1, d2 in zip(dataartikel[1], dataartikel[2])]
            dataartikel.append(item3)

            datarekap.append(dataartikel)

        return render(request, "produksi/rekap_produksi.html", {'artikel':artikelobj, 'data':datarekap })


def view_ksbb(request):
    kodeproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbb.html", {"kodeprodukobj": kodeproduk})
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb")

        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year
        # print(produk)

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        # Mendapatkan semua penyusun yang terkait dengan produk
        penyusun_produk = (
            models.Penyusun.objects.filter(KodeProduk=produk)
            .values_list("KodeArtikel", flat=True)
            .distinct()
        )
        print("ini penyusun produk", penyusun_produk)

        # print(penyusun_produk)

        pemusnahanobj = models.PemusnahanArtikel.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        print(pemusnahanobj, "Pemusnahan Artikel")

        """
        Revisi
        1. KSBB hanya mengambil jumlah konversi sesuai dengan jumlah penggunaan kode bahan baku tersebut per artikel bukan kumulatif semua penyusun artikel 

        """

        # Mendapatkan artikel yang terkait dengan penyusun produk
        # artikel_penyusun = [penyusun.KodeArtikel for penyusun in penyusun_produk]

        # Memfilter transaksi produksi berdasarkan artikel yang terkait dengan penyusun produk
        dataproduksi = models.TransaksiProduksi.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Jenis="Mutasi",
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        # print(dataproduksi)
        # Memfilter transaksi pemusnahan artikel yang terkait
        # datapemusnahan = models.PemusnahanArtikel.objects.filter(KodeArtikel = )
        kuantitas_konversi = {}
        for penyusun in penyusun_produk:
            konversi = models.KonversiMaster.objects.filter(
                KodePenyusun__KodeArtikel=penyusun, KodePenyusun__KodeProduk=produk
            )
            if konversi.exists():
                kuantitas = konversi.aggregate(total=Sum("Kuantitas"))
                # print('ini kuantitas',kuantitas)
                # Simpan ke dictionary kuantitas konversi dengan keynya adalah ID Kode Artikel
                kuantitas_konversi[penyusun] = kuantitas["total"]

            else:
                kuantitas_konversi[penyusun] = 0
        print(kuantitas_konversi)
        # Belum dikalikan dengan penyesuaian

        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan)))
        )

        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        data = []
        for i in listtanggal:
            datamasuk = datagudang.filter(tanggal=i)
            masuk = 0
            for k in datamasuk:
                masuk += k.jumlah

            datakeluar = dataproduksi.filter(Tanggal=i)
            datapemusnahan = pemusnahanobj.filter(Tanggal=i)

            listartikelobjkeluar = []
            for j in datakeluar:
                artikelobj = models.Artikel.objects.get(id=j.KodeArtikel.id)
                jumlah = j.Jumlah
                artikelobj.Jumlahkeluar = jumlah
                artikelobj.Konversi = kuantitas_konversi[artikelobj.id]
                listartikelobjkeluar.append(artikelobj)

            listartikelobjpemusnahan = []

            for j in datapemusnahan:
                artikelobj = models.Artikel.objects.get(id=j.KodeArtikel.id)
                print("ini artikel pemusnahan", artikelobj, j.Tanggal)
                artikelobj.Jumlahpemusnahan = j.Jumlah
                listartikelobjpemusnahan.append(artikelobj)

            print(
                f"ini list masuk {masuk} ini list artikel keluar {listartikelobjkeluar} ini list artikel pemusnahan {listartikelobjpemusnahan}"
            )
            datakirim = []
            totalkonversisemuaartikel = 0
            dataartikel = set(listartikelobjpemusnahan + listartikelobjkeluar)
            for item in dataartikel:
                artikelobj = models.Artikel.objects.get(id=item.id)
                artikelobj.totalkeluar = 0
                konversi = kuantitas_konversi[artikelobj.id]
                konversi = round(konversi + konversi * 2.5 / 100, 5)
                print(konversi)

                print("ini artikel obj", artikelobj)
                for objkeluar in listartikelobjkeluar:
                    if objkeluar.id == artikelobj.id:
                        artikelobj.totalkeluar += objkeluar.Jumlahkeluar
                    else:
                        continue
                for objpemusnahan in listartikelobjpemusnahan:
                    if objpemusnahan.id == artikelobj.id:
                        artikelobj.totalkeluar += objpemusnahan.Jumlahpemusnahan
                artikelobj.konversikeluar = round(konversi * artikelobj.totalkeluar, 4)
                datakirim.append(artikelobj)
                artikelobj.konversi = konversi
                artikelobj.sisa = sisa - artikelobj.konversikeluar
                totalkonversisemuaartikel += artikelobj.konversikeluar
                print(artikelobj.totalkeluar)
                print(artikelobj.konversikeluar)

            sisa = sisa + masuk - totalkonversisemuaartikel
            data.append(
                {
                    "Tanggal": i.strftime("%Y-%m-%d"),
                    "Artikel": datakirim,
                    "Masuk": masuk,
                    "Sisa": round(sisa, 3),
                }
            )

        return render(
            request,
            "produksi/view_ksbb.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": data,
                "saldo": saldoawal,
                "tahun": tahun,
            },
        )
    

# Pemusnahan Artikel
def view_pemusnahan(request):
    dataproduksi = models.PemusnahanArtikel.objects.all().order_by("-Tanggal")
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_pemusnahan.html", {"dataproduksi": dataproduksi}
    )


def add_pemusnahan(request):
    dataartikel = models.Artikel.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_pemusnahan.html",
            {"nama_lokasi": datalokasi, "dataartikel": dataartikel},
        )
    else:
        print(request.POST)
        # Get object
        kodeartikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        artikelobj = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.PemusnahanArtikel(
            Tanggal=tanggal, Jumlah=jumlah, KodeArtikel=artikelobj, lokasi=lokasiobj
        )
        pemusnahanobj.save()
        return redirect("view_pemusnahan")


def update_pemusnahan(request, id):
    dataobj = models.PemusnahanArtikel.objects.get(IDPemusnahanArtikel=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "produksi/update_pemusnahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj},
        )

    else:
        print(request.POST)
        kodeartikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        artikelobj = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.KodeArtikel = artikelobj
        dataobj.lokasi = lokasiobj

        dataobj.save()
        return redirect("view_pemusnahan")


def delete_pemusnahan(request, id):
    dataobj = models.PemusnahanArtikel.objects.get(IDPemusnahanArtikel=id)

    dataobj.delete()
    return redirect(view_pemusnahan)


# Pemusnahan Barang
def view_pemusnahanbarang(request):
    dataproduksi = models.PemusnahanBahanBaku.objects.all().order_by("-Tanggal")
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_pemusnahanbarang.html", {"dataproduksi": dataproduksi}
    )


def add_pemusnahanbarang(request):
    databarang = models.Produk.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_pemusnahanbarang.html",
            {"nama_lokasi": datalokasi, "databarang": databarang},
        )
    else:
        print(request.POST)
        # Get object
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.PemusnahanBahanBaku(
            Tanggal=tanggal, Jumlah=jumlah, KodeBahanBaku=produkobj, lokasi=lokasiobj
        )
        pemusnahanobj.save()
        return redirect("view_pemusnahanbarang")


def update_pemusnahanbarang(request, id):
    dataobj = models.PemusnahanBahanBaku.objects.get(IDPemusnahanBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "produksi/update_pemusnahanbarang.html",
            {"data": dataobj, "nama_lokasi": lokasiobj},
        )

    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.KodeBahanBaku = produkobj
        dataobj.lokasi = lokasiobj

        dataobj.save()
        return redirect("view_pemusnahanbarang")


def delete_pemusnahanbarang(request, id):
    dataobj = models.PemusnahanBahanBaku.objects.get(IDPemusnahanBahanBaku=id)

    dataobj.delete()
    return redirect(view_pemusnahan)


# Produk SUBKON
def read_produksubkon(request):
    produkobj = models.ProdukSubkon.objects.all()
    return render(request, "produksi/read_produksubkon.html", {"produkobj": produkobj})


def create_produksubkon(request):
    kodeartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(
            request, "produksi/create_produksubkon.html", {"kodeartikel": kodeartikel}
        )
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]
        keterangan_produk = request.POST["keterangan_produk"]
        print(request.POST)
        # produkobj = models.Produk.objects.filter(KodeProduk=kode_produk)
        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=kode_produk)
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Peruntukan tidak ditemukan")
            return redirect("update_produksubkon")
        listkodeproduk = (
            models.ProdukSubkon.objects.filter(KodeArtikel=artikelobj.id)
            .values_list("NamaProduk", flat=True)
            .distinct()
        )
        print(listkodeproduk)

        if nama_produk in listkodeproduk:
            messages.error(
                request, "Nama Produk untuk Artikel terkait sudah ada pada Database"
            )
            return redirect("create_produksubkon")
        else:
            new_produk = models.ProdukSubkon(
                NamaProduk=nama_produk,
                Unit=unit_produk,
                KodeArtikel=artikelobj,
                keterangan=keterangan_produk,
            )
            new_produk.save()
            return redirect("read_produksubkon")


def update_produksubkon(request, id):
    produkobj = models.ProdukSubkon.objects.get(pk=id)
    dataartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_produksubkon.html",
            {"produkobj": produkobj, "dataartikel": dataartikel},
        )
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]
        keterangan_produk = request.POST["keterangan_produk"]
        produkobj.KodeProduk = kode_produk
        produkobj.NamaProduk = nama_produk
        produkobj.Unit = unit_produk
        produkobj.keterangan = keterangan_produk
        produkobj.save()
        return redirect("read_produksubkon")


def delete_produksubkon(request, id):
    print(id)
    produkobj = models.ProdukSubkon.objects.get(IDProdukSubkon=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("read_produksubkon")


# Transaksi Subkon Kirim
def view_subkonkirim(request):
    datasubkon = models.DetailSubkonKirim.objects.all().order_by("IDSubkonKirim__Tanggal")
    for i in datasubkon:
        i.IDSubkonKirim.Tanggal = i.IDSubkonKirim.Tanggal.strftime("%d-%m-%Y")

    return render(request, "produksi/view_subkonkirim.html", {"datasubkon": datasubkon})


def add_subkonkirim(request):
    if request.method == "GET":
        subkonkirim = models.DetailSubkonKirim.objects.all()
        detailsk = models.SubkonKirim.objects.all()
        getproduk = models.Produk.objects.all()

        return render(
            request,
            "produksi/add_subkonkirim.html",
            {"subkonkirim": subkonkirim, "detailsk": detailsk, "getproduk": getproduk},
        )
    if request.method == "POST":
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]
        supplier = request.POST["supplier"]
        nomorpo = request.POST["nomorpo"]

        if nomorpo == "":
            nomorpo = "-"
        if supplier == "":
            supplier = "-"
        subkonkirimobj = models.SubkonKirim(IDSubkonKirim=nosuratjalan, Tanggal=tanggal, supplier=supplier, PO=nomorpo)
        subkonkirimobj.save()

        subkonkirimobj = models.SubkonKirim.objects.get(IDSubkonKirim=nosuratjalan)
        for kodeproduk, jumlah in zip(request.POST.getlist("kodeproduk"), request.POST.getlist("jumlah")):
            # print(kodeproduk)
            newprodukobj = models.DetailSubkonKirim(
                KodeProduk=models.Produk.objects.get(KodeProduk=kodeproduk),
                Jumlah=jumlah,
                KeteranganACC=0,
                Harga=0,
                IDSubkonKirim=subkonkirimobj,
            )
            newprodukobj.save()

        return redirect("view_subkonkirim")


def update_subkonkirim(request, id):
    datasjp = models.DetailSubkonKirim.objects.get(IDDetailSubkonKirim=id)

    datasjp_getobj = models.SubkonKirim.objects.get(
        IDSubkonKirim = datasjp.IDSubkonKirim.IDSubkonKirim
    )
    detailsjp_filtered = models.DetailSubkonKirim.objects.filter(
        IDSubkonKirim = datasjp_getobj.IDSubkonKirim
    )
    if request.method == "GET":

        return render(
            request,
            "produksi/update_subkonkirim.html",
            {
                "datasjp": datasjp_getobj,
                "detailsjp": detailsjp_filtered,
                "tanggal": datetime.strftime(datasjp_getobj.Tanggal, "%Y-%m-%d"),
            },
        )

    else:
        tanggal = request.POST["tanggal"]
        kode_produk = request.POST.get("kodeproduk")
        kode_produkobj = models.Produk.objects.get(KodeProduk=kode_produk)
        jumlah = request.POST["jumlah"]

        datasjp.KodeProduk = kode_produkobj
        datasjp.Jumlah = jumlah
        datasjp.KeteranganACC = datasjp.KeteranganACC
        datasjp.Harga = datasjp.Harga
        datasjp.IDSubkonKirim = datasjp.IDSubkonKirim
        datasjp.IDSubkonKirim.Tanggal = tanggal
        datasjp.save()
        datasjp.IDSubkonKirim.save()

        return redirect("view_subkonkirim")


def delete_subkonkirim(request, id):
    dataskk = models.DetailSubkonKirim.objects.get(IDDetailSubkonKirim=id)
    dataskk.delete()
    return redirect("view_subkonkirim")


# Transaksi subkon masuk = nilai + pada kolom jumlah berarti masuk dari subkon ke pabrik, Transaksi nilai - pada kolom jumlah berarti keluar ke WIP
def transaksi_subkon_terima(request):
    produkobj = models.TransaksiSubkon.objects.all().order_by("-Tanggal")
    for i in produkobj:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")
    return render(
        request, "produksi/read_transaksisubkon_terima.html", {"produkobj": produkobj}
    )


def create_transaksi_subkon_terima(request):
    produksubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/create_transaksisubkon_terima.html",
            {"produksubkon": produksubkon},
        )
    else:
        tanggal = request.POST["tanggal"]
        nama_produk = request.POST["nama_produk"]
        jumlah = request.POST["jumlah"]

        try:
            produksubkonobj = models.ProdukSubkon.objects.get(
                IDProdukSubkon=nama_produk
            )

        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Produk Subkon tidak ditemukan")
            return redirect("update_transaksi_subkon_terima")
        
        new_produk = models.TransaksiSubkon(
            Tanggal=tanggal,
            Jumlah=jumlah,
            IDProdukSubkon=produksubkonobj,
        )
        new_produk.save()
        return redirect("transaksi_subkon_terima")


def update_transaksi_subkon_terima(request, id):
    produkobj = models.TransaksiSubkon.objects.get(pk=id)
    produkobj.Tanggal = produkobj.Tanggal.strftime("%Y-%m-%d")
    produksubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_transaksisubkon_terima.html",
            {"produkobj": produkobj, "produksubkon": produksubkon},
        )
    else:
        jumlah = request.POST["jumlah"]
        nama_produk = request.POST["nama_produk"]
        idproduk = models.ProdukSubkon.objects.get(NamaProduk=nama_produk)
        tanggal = request.POST["tanggal"]
        try:
            produksubkonobj = models.ProdukSubkon.objects.get(
                IDProdukSubkon=idproduk.IDProdukSubkon
            )
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Produk Subkon tidak ditemukan")
            return redirect("update_transaksi_subkon_terima")
        produkobj.IDProdukSubkon = produksubkonobj
        produkobj.Jumlah = jumlah
        produkobj.Tanggal = tanggal

        produkobj.save()
        return redirect("transaksi_subkon_terima")


def delete_transaksi_subkon_terima(request, id):
    produkobj = models.TransaksiSubkon.objects.get(IDTransaksiSubkon=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("transaksi_subkon_terima")


# Penyesuaian
def penyesuaian(request):
    datapenyesuaian = models.Penyesuaian.objects.all()
    return render(
        request, "produksi/view_penyesuaian.html", {"datapenyesuaian": datapenyesuaian}
    )


def addpenyesuaian(request):
    dataartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(
            request, "produksi/add_penyesuaian.html", {"Artikel": dataartikel}
        )
    else:
        print(request.POST)
        # Add Penyesuaian
        tanggalmulai = request.POST["tanggalmulai"]
        tanggalakhir = request.POST["tanggalakhir"]
        if tanggalakhir == "":
            tanggalakhir = datetime.max
        kodepenyusun = request.POST["penyusun"]
        kuantitas = request.POST["kuantitas"]
        penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=kodepenyusun)
        print(penyusunobj)
        penyesuaianobj = models.Penyesuaian(
            TanggalMulai=tanggalmulai,
            TanggalAkhir=tanggalakhir,
            KodePenyusun=penyusunobj,
            konversi = kuantitas

        )
        penyesuaianobj.save()

        return redirect("view_penyesuaian")


def update_penyesuaian(request, id):
    datapenyesuaianobj = models.DetailKonversiProduksi.objects.get(
        IDDetailKonversiProduksi=id
    )
    datapenyesuaianobj.KodePenyesuaian.TanggalMulai = (
        datapenyesuaianobj.KodePenyesuaian.TanggalMulai.strftime("%Y-%m-%d")
    )
    dataartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_penyesuaian.html",
            {"dataobj": datapenyesuaianobj, "Artikel": dataartikel},
        )
    else:
        print(request.POST)
        detailkonversiobj = models.DetailKonversiProduksi.objects.get(
            IDDetailKonversiProduksi=request.POST["id"]
        )
        print(detailkonversiobj)
        penyesuaianobj = models.Penyesuaian.objects.get(
            IDPenyesuaian=detailkonversiobj.IDDetailKonversiProduksi
        )
        print(penyesuaianobj)
        penyesuaianobj.TanggalMulai = request.POST["tanggalmulai"]
        tanggalakhir = request.POST["tanggalakhir"]
        if tanggalakhir == "":
            tanggalakhir = datetime.max
        penyesuaianobj.TanggalAkhir = tanggalakhir
        detailkonversiobj.kuantitas = request.POST["kuantitas"]
        detailkonversiobj.save()
        penyesuaianobj.save()
        return redirect("view_penyesuaian")


def delete_penyesuaian(request, id):
    datapenyesuaian = models.Penyesuaian.objects.get(IDPenyesuaian=id)
    datapenyesuaian.delete()
    return redirect("view_penyesuaian")


def kalkulatorpenyesuaian(request):
    kodeproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request,
            "produksi/kalkulator_penyesuaian.html",
            {"kodeprodukobj": kodeproduk},
        )
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb")

        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year
        # print(produk)

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        # Mendapatkan semua penyusun yang terkait dengan produk
        penyusun_produk = (
            models.Penyusun.objects.filter(KodeProduk=produk)
            .values_list("KodeArtikel", flat=True)
            .distinct()
        )

        # print(penyusun_produk)

        pemusnahanobj = models.PemusnahanArtikel.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        # print(pemusnahanobj, 'Pemusnahan Artikel')

        """
        Revisi
        1. KSBB hanya mengambil jumlah konversi sesuai dengan jumlah penggunaan kode bahan baku tersebut per artikel bukan kumulatif semua penyusun artikel 

        """

        # Mendapatkan artikel yang terkait dengan penyusun produk
        # artikel_penyusun = [penyusun.KodeArtikel for penyusun in penyusun_produk]

        # Memfilter transaksi produksi berdasarkan artikel yang terkait dengan penyusun produk
        dataproduksi = models.TransaksiProduksi.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Jenis="Mutasi",
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        # print(dataproduksi)
        # Memfilter transaksi pemusnahan artikel yang terkait
        # datapemusnahan = models.PemusnahanArtikel.objects.filter(KodeArtikel = )
        kuantitas_konversi = {}
        for penyusun in penyusun_produk:
            konversi = models.KonversiMaster.objects.filter(
                KodePenyusun__KodeArtikel=penyusun, KodePenyusun__KodeProduk=produk
            )
            if konversi.exists():
                kuantitas = konversi.aggregate(total=Sum("Kuantitas"))
                # print('ini kuantitas',kuantitas)
                # Simpan ke dictionary kuantitas konversi dengan keynya adalah ID Kode Artikel
                kuantitas_konversi[penyusun] = kuantitas["total"]

            else:
                kuantitas_konversi[penyusun] = 0
        # print(kuantitas_konversi)
        # Belum dikalikan dengan penyesuaian

        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan)))
        )

        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        data = []
        for i in listtanggal:
            datamasuk = datagudang.filter(tanggal=i)
            masuk = 0
            for k in datamasuk:
                masuk += k.jumlah

            sisa += masuk
            print(i)
            print("sisa : ", masuk)
            datakeluar = dataproduksi.filter(Tanggal=i)
            datapemusnahan = pemusnahanobj.filter(Tanggal=i)

            listartikelobjkeluar = []
            for j in datakeluar:
                artikelobj = models.Artikel.objects.get(id=j.KodeArtikel.id)
                jumlah = j.Jumlah
                artikelobj.Jumlahkeluar = jumlah
                artikelobj.Konversi = kuantitas_konversi[artikelobj.id]
                listartikelobjkeluar.append(artikelobj)

            listartikelobjpemusnahan = []

            for j in datapemusnahan:
                artikelobj = models.Artikel.objects.get(id=j.KodeArtikel.id)
                # print('ini artikel pemusnahan',artikelobj,j.Tanggal)
                artikelobj.Jumlahpemusnahan = j.Jumlah
                listartikelobjpemusnahan.append(artikelobj)

            # print(f'ini list masuk {masuk} ini list artikel keluar {listartikelobjkeluar} ini list artikel pemusnahan {listartikelobjpemusnahan}')
            datakirim = []
            totalkonversisemuaartikel = 0
            dataartikel = set(listartikelobjpemusnahan + listartikelobjkeluar)

            for item in dataartikel:
                artikelobj = models.Artikel.objects.get(id=item.id)
                artikelobj.totalkeluar = 0
                konversi = kuantitas_konversi[artikelobj.id]
                konversi = round(konversi + konversi * 2.5 / 100, 5)
                # print(konversi)

                # print('ini artikel obj', artikelobj)
                for objkeluar in listartikelobjkeluar:
                    if objkeluar.id == artikelobj.id:
                        artikelobj.totalkeluar += objkeluar.Jumlahkeluar
                    else:
                        continue
                for objpemusnahan in listartikelobjpemusnahan:
                    if objpemusnahan.id == artikelobj.id:
                        artikelobj.totalkeluar += objpemusnahan.Jumlahpemusnahan
                artikelobj.konversikeluar = round(konversi * artikelobj.totalkeluar, 4)
                datakirim.append(artikelobj)
                artikelobj.konversi = konversi
                artikelobj.sisa = round(sisa - artikelobj.konversikeluar, 4)
                print("ini Sisa : ", sisa)
                print("konversi keluar : ", artikelobj.konversikeluar)
                print("artikel obj sisa : ", artikelobj.sisa)
                totalkonversisemuaartikel += artikelobj.konversikeluar
                sisa = artikelobj.sisa
                # print(artikelobj.totalkeluar)
                # print(artikelobj.konversikeluar)

            # sisa = sisa + masuk - totalkonversisemuaartikel
            if sisa < 0:
                messages.warning(request, f"Terdapat nilai minus pada tanggal {i}")
            data.append(
                {
                    "Tanggal": i.strftime("%Y-%m-%d"),
                    "Artikel": datakirim,
                    "Masuk": masuk,
                    "Sisa": round(sisa, 3),
                }
            )

        # Perhitungan penyesuaian\
        try:
            dataaktual = int(request.GET["jumlah"])
        except Exception:
            dataaktual = 0
        datasisaminus = 0
        datajumlah = 0
        dataajumlahartikel = {}
        datakonversiartikel = {}
        print(data)
        firstindex = True
        for item in data:
            print('ini item',item)
            for i in item["Artikel"]:
                dataajumlahartikel.setdefault(i.KodeArtikel, 0)
                dataajumlahartikel[i.KodeArtikel] += i.totalkeluar
                datakonversiartikel.setdefault(i.KodeArtikel, 0)
                datakonversiartikel[i.KodeArtikel] = i.konversi
                datajumlah += i.konversikeluar
                print(dataajumlahartikel)
            if item["Sisa"] < 0 and firstindex:
                datasisaminus = item["Sisa"]
                firstindex = False

        # print(dataajumlahartikel)
        # print(datakonversiartikel)
        # print(datasisaminus)
        # print(datajumlah)
        # print(dataaktual)
        # Perhitungan konversi

        sum_product = sum(
            dataajumlahartikel[key] * datakonversiartikel[key]
            for key in dataajumlahartikel
        )
        print("Sum Product 2 Dictionary : ", sum_product)
        # Contoh perhitungan untuk 1 kode artikel 9010/ACC
        # jumlahxkonversi = dataajumlahartikel['9010/ACC'] * datakonversiartikel['9010/ACC']
        # print('Perkalian jumlah dan konversi : ',jumlahxkonversi)
        # keluarpenyesuaian = datajumlah-(dataaktual-datasisaminus)
        # print('Keluar Penyesuaian : ',keluarpenyesuaian)
        # jumlahpenyesuaian = dataajumlahartikel['9010/ACC']/keluarpenyesuaian
        # nilaikonversibaru = jumlahxkonversi /(sum_product * jumlahpenyesuaian)
        # print('Nilai konversi Baru : ', nilaikonversibaru)
        datakonversiakhir = {}
        for key in dataajumlahartikel:
            jumlahxkonversi = dataajumlahartikel[key] * datakonversiartikel[key]
            print("Perkalian jumlah dan konversi untuk", key, ":", jumlahxkonversi)

            keluarpenyesuaian = datajumlah - (dataaktual - datasisaminus)
            print(datajumlah)
            print(dataaktual)
            print(datasisaminus)
            print("Keluar Penyesuaian untuk", key, ":", keluarpenyesuaian)

            jumlahpenyesuaian = dataajumlahartikel[key] / keluarpenyesuaian
            nilaikonversibaru = jumlahxkonversi / (sum_product * jumlahpenyesuaian)
            print("Nilai konversi Baru untuk", key, ":", nilaikonversibaru)
            datakonversiakhir[key] = nilaikonversibaru

        return render(
            request,
            "produksi/kalkulator_penyesuaian.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": data,
                "saldo": saldoawal,
                "tahun": tahun,
                "jumlahartikel": dataajumlahartikel,
                "konversiawal": datakonversiartikel,
                "jumlahaktual": dataaktual,
                "datasisaminus": datasisaminus,
                "datajumlah": datajumlah,
                "datakonversiakhir": datakonversiakhir,
            },
        )


def detailksbb(request, id, tanggal):
    tanggal = datetime.strptime(tanggal, "%Y-%m-%d")
    tanggal = tanggal.strftime("%Y-%m-%d")

    # Transaksi Gudang
    datagudang = models.TransaksiGudang.objects.filter(tanggal=tanggal, KodeProduk=id)
    listartikel = (
        models.Penyusun.objects.filter(KodeProduk__KodeProduk=id)
        .values_list("KodeArtikel__KodeArtikel", flat=True)
        .distinct()
    )

    # Transaksi Produksi
    dataproduksi = models.TransaksiProduksi.objects.filter(
        KodeArtikel__KodeArtikel__in=listartikel, Jenis="Mutasi", Tanggal=tanggal
    )
    print(dataproduksi)

    # Transaksi Pemusnahan
    datapemusnahan = models.PemusnahanArtikel.objects.filter(
        KodeArtikel__KodeArtikel__in=listartikel, Tanggal=tanggal
    )
    print(datapemusnahan)
    return render(
        request,
        "produksi/view_detailksbb.html",
        {
            "datagudang": datagudang,
            "dataproduksi": dataproduksi,
            "datapemusnahan": datapemusnahan,
        },
    )


def view_ksbb3(request):
    kodeproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbb.html", {"kodeprodukobj": kodeproduk})
    else:
        """
        1. Cari 
        """
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb")
        
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)
        # Menceri data transaksi gudang dengan kode 
        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )
        # Kode Artikel yang di susun oleh bahan baku 
        penyusun_produk = (
            models.Penyusun.objects.filter(KodeProduk=produk)
            .values_list("KodeArtikel", flat=True)
            .distinct()
        )

        # Mencari data pemusnahan artikel yang disupport
        pemusnahanobj = models.PemusnahanArtikel.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        dataproduksi = models.TransaksiProduksi.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Jenis="Mutasi",
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        listartikelmaster = []
        ''' PENYESUAIAN SECTION '''
        for artikel in penyusun_produk:
            artikelmaster = models.Artikel.objects.get(id = artikel)

            konversi = models.KonversiMaster.objects.filter(
                KodePenyusun__KodeArtikel=artikel, KodePenyusun__KodeProduk=produk
            ).order_by('KodePenyusun__versi')

            tanggalversi = konversi.values_list('KodePenyusun__versi',flat=True).distinct()
            listkonversi = []
            if konversi.exists():
                for tanggal in tanggalversi:
                    datakonversi = konversi.filter(KodePenyusun__versi = tanggal)
                    kuantitas = datakonversi.aggregate(total = Sum('Kuantitas'))
                    listkonversi.append(kuantitas['total'])

            artikelmaster.listkonversi = listkonversi
            artikelmaster.tanggalversi = tanggalversi

            # Data Penyesuaian 
            penyesuaianobj  = models.Penyesuaian.objects.filter(KodePenyusun__KodeArtikel = artikel, TanggalMulai__range = (tanggal_mulai,tanggal_akhir))

            penyesuaiandataperartikel = [i.konversi for i in penyesuaianobj]
            tanggalpenyesuaianperartikel = [i.TanggalMulai for i in penyesuaianobj]
            tanggalpenyesuaianakhirperartikel = [i.TanggalAkhir for i in penyesuaianobj]

            artikelmaster.listpenyesuaian = penyesuaiandataperartikel
            artikelmaster.tanggalpenyesuaian =tanggalpenyesuaianperartikel
            artikelmaster.tanggalpenyesuaianakhir = tanggalpenyesuaianakhirperartikel
            listartikelmaster.append(artikelmaster)

        ''' TANGGAL SECTION '''
        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan)))
        )

        ''' SALDO AWAL SECTION '''
        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        ''' PENGOLAHAN DATA '''
        listdata =[]
        for i in listtanggal:
            # Data Models
            datamodelsartikel = []
            datamodelsperkotak = []
            datamodelskonversi = []
            datamodelskeluar = []
            datamodelssisa = []
            data = {
                'Tanggal': None,
                'Artikel': datamodelsartikel,
                'Perkotak' : datamodelsperkotak,
                "Konversi" : datamodelskonversi,
                'Masuk' : None,
                'Keluar' : datamodelskeluar,
                'Sisa' : datamodelssisa
                
            }
            data['Tanggal'] = i.strftime("%Y-%m-%d")
            # Data Masuk
            masuk = 0
            datamasuk = datagudang.filter(tanggal=i)
            for k in datamasuk:
                masuk += k.jumlah
            sisa  += masuk
            
            # Data Keluar
            data['Masuk'] = masuk
            datakeluar = dataproduksi.filter(Tanggal = i)
            artikelkeluar = datakeluar.values_list('KodeArtikel',flat=True).distinct()
            datapemusnahan = pemusnahanobj.filter(Tanggal = i)
            artikelpemusnahan = datapemusnahan.values_list('KodeArtikel',flat=True).distinct()

            for j in artikelkeluar:
                artikelkeluarobj = models.Artikel.objects.get(id = j)
                total = datakeluar.filter(KodeArtikel__id = j).aggregate(total = Sum('Jumlah'))
                indexartikel = listartikelmaster.index(artikelkeluarobj)
                filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                filtered_data.sort(reverse=True)

                if not filtered_data:
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi]

                tanggalversiterdekat = max(filtered_data)
                indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat]

                if listartikelmaster[indexartikel].tanggalpenyesuaian :
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]

                    if not filtered_data:
                        konversiterdekat = konversiterdekat
                    else:
                        filtered_data.sort(reverse=True)
                        tanggalversiterdekat = max(filtered_data)
                        indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                        konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]

                datamodelskonversi.append(konversiterdekat)
                datamodelskeluar.append(konversiterdekat*total['total'])
                datamodelsartikel.append(artikelkeluarobj)
                datamodelsperkotak.append(total['total'])
                sisa -= konversiterdekat*total['total']
                sisa = round(sisa, 5)
                datamodelssisa.append(sisa)

            for j in artikelpemusnahan:
                artikelkeluarobj = models.Artikel.objects.get(id = j)
                total = datapemusnahan.filter(KodeArtikel__id = j).aggregate(total=Sum('Jumlah'))
                indexartikel = listartikelmaster.index(artikelkeluarobj)
                filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                filtered_data.sort(reverse=True)
                tanggalversiterdekat = max(filtered_data)
                indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat]

                if listartikelmaster[indexartikel].tanggalpenyesuaian :
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]

                    if not filtered_data:
                        konversiterdekat = konversiterdekat
                    else:
                        filtered_data.sort(reverse=True)
                        tanggalversiterdekat = max(filtered_data)
                        indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                        konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]

                datamodelskonversi.append(konversiterdekat)
                datamodelskeluar.append(konversiterdekat*total['total'])
                datamodelsartikel.append(artikelkeluarobj)
                datamodelsperkotak.append(total['total'])
                sisa -= konversiterdekat*total['total']
                sisa = round(sisa, 5)
                datamodelssisa.append(sisa)

            if not datamodelssisa :
                sisa = round(sisa, 5)
                datamodelssisa.append(sisa)

            data['Sisa'] = datamodelssisa
            listdata.append(data)

        return render(request, "produksi/view_ksbb.html",{'data':listdata,'saldo':saldoawal,'kodebarang':request.GET["kodebarang"],"nama": nama,"satuan": satuan,})


def view_ksbj2(request):
    dataartikel = models.Artikel.objects.all()
    if len(request.GET) == 0:
        return render(request,'produksi/view_ksbj.html', {"dataartikel": dataartikel})
    else :
        kodeartikel =  request.GET['kodeartikel']
        try:
            artikel = models.Artikel.objects.get(KodeArtikel = kodeartikel)
        except:
            messages.error(request,'Data Artikel tidak ditemukan')
            return redirect('view_ksbj')
        
        if request.GET['tahun']:
            tahun = int(request.GET['tahun'])
        else:
            sekarang = datetime.now()
            tahun - sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        lokasi = request.GET['lokasi']
        lokasiobj = models.Lokasi.objects.get(NamaLokasi = lokasi)

        getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1)

        if not getbahanbakuutama :
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("view_ksbj")
        
        data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id)
        listdata = []

        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
                print('ini saldo awallll',saldoawalobj)
            except models.SaldoAwalArtikel.DoesNotExist :
                saldo = 0
                saldoawal = None
                saldoawalobj ={'Tanggal' : 'Belum ada Data','saldo' : saldo}

            tanggallist = (data.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir)).values_list("Tanggal", flat=True).order_by("Tanggal").distinct())
            saldoawal = saldo
            
            for i in tanggallist:
                datamodels = {
                    'Tanggal': None,
                    "SPK" : None,
                    "Kodeproduk" : None,
                    "Masuklembar":None,
                    "Masukkonversi" : None,
                    'Hasil' : None,
                    "Sisa" : None
                }

                filtertanggal = data.filter(Tanggal=i)
                print(filtertanggal[0].Jumlah)

                jumlahmutasi =  filtertanggal.filter(Jenis ="Mutasi").aggregate(total = Sum('Jumlah'))['total']
                jumlahmasuk = filtertanggal.filter(Jenis = 'Produksi').aggregate(total = Sum('Jumlah'))['total']

                if jumlahmutasi is None:
                    jumlahmutasi = 0
                if jumlahmasuk is None :
                    jumlahmasuk = 0

                print(f'{i} tanggal,filtertangga {filtertanggal}, {jumlahmutasi} jumlah')
                print(i)

                # Cari data penyusun sesuai tanggal 
                penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id,Status = 1,versi__lte = i).order_by('-versi').first()

                if not penyusunfiltertanggal:
                    penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id, Status = 1, versi__gte = i).order_by('versi').first()

                konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)
                print(konversimasterobj.Kuantitas)

                masukpcs = round(jumlahmasuk/((konversimasterobj.Kuantitas + (konversimasterobj.Kuantitas * 0.025))))
                saldoawal = saldoawal - jumlahmutasi + masukpcs
                print(saldoawal)

                datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                datamodels['Masuklembar'] = jumlahmasuk
                datamodels['Masukkonversi'] = masukpcs
                datamodels['Sisa'] = saldoawal
                datamodels['Hasil'] = jumlahmutasi
                datamodels['SPK'] = filtertanggal.filter(Jenis = 'Mutasi')
                datamodels["Kodeproduk"] = penyusunfiltertanggal

                # Cari data penyesuaian
                print(datamodels)
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(i),)
                listdata.append(datamodels)

            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": lokasi,
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                },
            )
        else:
            data = data.filter(Lokasi=1)
            try:
                saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
            except models.SaldoAwalArtikel.DoesNotExist :
                saldo = 0
                saldoawalobj ={
                    'Tanggal' : 'Belum ada Data',
                    'saldo' : saldo
                }
            print('ini saldoawalobj',saldoawalobj)

            tanggalmutasi = data.filter(Jenis = 'Produksi',Tanggal__range=(tanggal_mulai,tanggal_akhir)).values_list('Tanggal',flat=True).distinct()
            sppb = models.DetailSPPB.objects.filter(DetailSPK__KodeArtikel__KodeArtikel = kodeartikel, NoSPPB__Tanggal__range = (tanggal_mulai,tanggal_akhir))
            tanggalsppb = sppb.values_list('NoSPPB__Tanggal',flat=True).distinct()
            tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb))))
            print(tanggallist)
            saldoawal = saldo

            for i in tanggallist:
                datamodels = {
                    "Tanggal" : None,
                    "Penyerahanwip": None,
                    "DetailSPPB" : None,
                    "Sisa" : None
                }

                penyerahanwip = models.TransaksiProduksi.objects.filter(Tanggal = i, KodeArtikel__KodeArtikel = kodeartikel, Jenis = "Mutasi", Lokasi__NamaLokasi = "WIP" )
                detailsppbjobj = sppb.filter(NoSPPB__Tanggal = i)

                totalpenyerahanwip = penyerahanwip.aggregate(total=Sum('Jumlah'))['total']
                totalkeluar = detailsppbjobj.aggregate(total=Sum('Jumlah'))['total']
                
                if not totalpenyerahanwip:
                    totalpenyerahanwip = 0
                if not totalkeluar :
                    totalkeluar = 0

                saldoawal += totalpenyerahanwip - totalkeluar
                print(totalpenyerahanwip)

                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )

                datamodels ['Tanggal'] = i
                datamodels ['Penyerahanwip'] = totalpenyerahanwip
                datamodels['DetailSPPB'] = detailsppbjobj
                datamodels['Sisa'] = saldoawal
                print(datamodels)
                listdata.append(datamodels)
            
            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": "FG",
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                },
            )


def kalkulatorpenyesuaian2(request):
    kodeproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request,
            "produksi/kalkulator_penyesuaian.html",
            {"kodeprodukobj": kodeproduk},
        )
    else:
        """
        1. Cari 
        """
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb")
        
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)
        # Menceri data transaksi gudang dengan kode 
        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )
        # Kode Artikel yang di susun oleh bahan baku 
        penyusun_produk = (
            models.Penyusun.objects.filter(KodeProduk=produk)
            .values_list("KodeArtikel", flat=True)
            .distinct()
        )
        # Mencari data pemusnahan artikel yang disupport
        pemusnahanobj = models.PemusnahanArtikel.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )
        dataproduksi = models.TransaksiProduksi.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Jenis="Mutasi",
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )

        listartikelmaster = []
        ''' PENYESUAIAN SECTION '''
        for artikel in penyusun_produk:
            artikelmaster = models.Artikel.objects.get(id = artikel)
            print(artikelmaster)
            konversi = models.KonversiMaster.objects.filter(
                KodePenyusun__KodeArtikel=artikel, KodePenyusun__KodeProduk=produk
            ).order_by('KodePenyusun__versi')
            # print(konversi)
            
            tanggalversi = konversi.values_list('KodePenyusun__versi',flat=True).distinct()
            listkonversi = []
            # print(tanggalversi)
            if konversi.exists():
                for tanggal in tanggalversi:
                    datakonversi = konversi.filter(KodePenyusun__versi = tanggal)
                    kuantitas = datakonversi.aggregate(total = Sum('Kuantitas'))
                    listkonversi.append(kuantitas['total'])
            artikelmaster.listkonversi = listkonversi
            artikelmaster.tanggalversi = tanggalversi
            penyesuaianobj  = models.Penyesuaian.objects.filter(KodePenyusun__KodeArtikel = artikel, TanggalMulai__range = (tanggal_mulai,tanggal_akhir))

            penyesuaiandataperartikel = [i.konversi for i in penyesuaianobj]
            tanggalpenyesuaianperartikel = [i.TanggalMulai for i in penyesuaianobj]
            tanggalpenyesuaianakhirperartikel = [i.TanggalAkhir for i in penyesuaianobj]

            artikelmaster.listpenyesuaian = penyesuaiandataperartikel
            artikelmaster.tanggalpenyesuaian =tanggalpenyesuaianperartikel
            artikelmaster.tanggalpenyesuaianakhir = tanggalpenyesuaianakhirperartikel
            listartikelmaster.append(artikelmaster)
            # print(artikelmaster.listpenyesuaian)
            # print(artikelmaster.tanggalpenyesuaian)
            # print(artikelmaster.tanggalpenyesuaianakhir)
            # print(aasdasd)
        
        # print(listartikelmaster)
        for art in listartikelmaster:
            print("ini artikel",art)
            print(art.tanggalpenyesuaian)
            print(art.tanggalversi)
            print(art.listkonversi)
            print(art.produksubkon_set)
        
        
        

        ''' TANGGAL SECTION '''
        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
        tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan)))
        )

        ''' SALDO AWAL SECTION '''
        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        ''' PENGOLAHAN DATA '''
        listdata =[]
        for i in listtanggal:
            # Data Models
            datamodelsartikel = []
            datamodelsperkotak = []
            datamodelskonversi = []
            datamodelskeluar = []
            datamodelssisa = []
            data = {
                'Tanggal': None,
                'Artikel': datamodelsartikel,
                'Perkotak' : datamodelsperkotak,
                "Konversi" : datamodelskonversi,
                'Masuk' : None,
                'Keluar' : datamodelskeluar,
                'Sisa' : datamodelssisa
                
            }
            # Data Masuk
            masuk = 0
            datamasuk = datagudang.filter(tanggal=i)
            for k in datamasuk:
                masuk += k.jumlah
            sisa  += masuk
            sisa = round(sisa,3)
            '''Versi 2'''
            '''
            data models
            {
            Artikel:{
            listtanggal : []
            listkuantitas : []

            }
            }


            '''


            data['Tanggal'] = i.strftime("%Y-%m-%d")
            # Data Keluar
            data['Masuk'] = masuk
            datakeluar = dataproduksi.filter(Tanggal = i)
            artikelkeluar = datakeluar.values_list('KodeArtikel',flat=True).distinct()
            datapemusnahan = pemusnahanobj.filter(Tanggal = i)
            artikelpemusnahan = datapemusnahan.values_list('KodeArtikel',flat=True).distinct()
            for j in artikelkeluar:
                artikelkeluarobj = models.Artikel.objects.get(id = j)
                total = datakeluar.filter(KodeArtikel__id = j).aggregate(total = Sum('Jumlah'))
                indexartikel = listartikelmaster.index(artikelkeluarobj)
                filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                filtered_data.sort(reverse=True)
                # print(artikelkeluarobj)
                if not filtered_data:
                    # print(f'Artikel {artikelkeluarobj} Tidak memiliki versi sebelum tanggal {i} list tanggal versi {listartikelmaster[indexartikel].tanggalversi}')
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi ]
                    # print(filtered_data)
                    filtered_data.sort()
                    # print(f'sorted filtered', filtered_data)
                # print(asdasd)
                tanggalversiterdekat = filtered_data[0]
                indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat]
                konversiterdekat += konversiterdekat *0.025
                print('ini konversi terdekat : ',konversiterdekat)
                # print(asdas)

                if listartikelmaster[indexartikel].tanggalpenyesuaian :
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]
                    if not filtered_data:
                        konversiterdekat = konversiterdekat
                    else:
                        filtered_data.sort(reverse=True)
                        tanggalversiterdekat = max(filtered_data)
                        indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                        konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]

                konversiterdekat = round(konversiterdekat,5)
                datamodelskonversi.append(konversiterdekat)
                datamodelskeluar.append(round((konversiterdekat*total['total']),2))
                datamodelsartikel.append(artikelkeluarobj)
                datamodelsperkotak.append(total['total'])
                sisa -= konversiterdekat*total['total']
            
                datamodelssisa.append(round((sisa),3))
            for j in artikelpemusnahan:
                artikelkeluarobj = models.Artikel.objects.get(id = j)
                total = datapemusnahan.filter(KodeArtikel__id = j).aggregate(total=Sum('Jumlah'))
                # print(total)
                indexartikel = listartikelmaster.index(artikelkeluarobj)
                filtered_data = [d for d in listartikelmaster[indexartikel].tanggalversi if d <= i]
                filtered_data.sort(reverse=True)
                tanggalversiterdekat = max(filtered_data)
                indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalversi).index(tanggalversiterdekat)
                konversiterdekat = listartikelmaster[indexartikel].listkonversi[indextanggalterdekat] 
                if listartikelmaster[indexartikel].tanggalpenyesuaian :
                    filtered_data = [d for d in listartikelmaster[indexartikel].tanggalpenyesuaian if d <= i]
                    if not filtered_data:
                        konversiterdekat = konversiterdekat
                    else:
                        filtered_data.sort(reverse=True)
                        tanggalversiterdekat = max(filtered_data)
                        indextanggalterdekat = list(listartikelmaster[indexartikel].tanggalpenyesuaian).index(tanggalversiterdekat)
                        konversiterdekat = listartikelmaster[indexartikel].listpenyesuaian[indextanggalterdekat]
                datamodelskonversi.append(konversiterdekat)
                datamodelskeluar.append(konversiterdekat*total['total'])
                datamodelsartikel.append(artikelkeluarobj)
                datamodelsperkotak.append(total['total'])
                sisa -= konversiterdekat*total['total']
                datamodelssisa.append(sisa)
            print(konversiterdekat)
            # print(asdasd)

            if not datamodelssisa :
                datamodelssisa.append(sisa)
            data['Sisa'] = datamodelssisa
            print(f'ini list data \n\n{data}\n\n')
            # print(asdasd)
            listdata.append(data)

        # Perhitungan penyesuaian\
        try:
            dataaktual = int(request.GET["jumlah"])
        except Exception:
            dataaktual = 0
        datasisaminus = 0
        datajumlah = 0
        dataajumlahartikel = {}
        datakonversiartikel = {}
        # print(data)
        firstindex = True
        listartikel = list(set(dataproduksi.values_list('KodeArtikel',flat=True).distinct()).union(datapemusnahan.values_list('KodeArtikel',flat=True).distinct()))
        # print('ini list artikel ',listdata)
        # Mendapatkan data minus pertama
        sisa_minus_pertama = None
        tanggalminus = None
        lanjut = True
        datakuantitasperhitungan = {
            'saldodata': 0,
            'saldofisik':0,
            'datakeluar': 0,
        }
        for item in listdata:
            sisa = item['Sisa']
            for j in sisa:
                if j <0 :
                    sisa_minus_pertama = sisa.index(j)
                    tanggalminus = item['Tanggal']
                    datasisaminus = j
                    lanjut = False
                    break
            if not lanjut:
                break
        
        
        # print(sisa_minus_pertama)
        # print(tanggalminus)
        listdataperhitungan = {}
        if not tanggalminus:
            return render(
            request,
            "produksi/newkalkulator_penyesuaian.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": listdata,
                'dataperhitungan' : listdataperhitungan,
                "saldo": saldoawal,
                "tahun": tahun,
                "jumlahartikel": dataajumlahartikel,
                "konversiawal": datakonversiartikel,
                "datakuantitas" : datakuantitasperhitungan
            },
        )
        '''
        1. Kumpulkan data perartikel (v)
        2. Cek index dan sisa minus  (v)
        3. Datajumlah artikel tetap 
        4. datakonversiartikel tetap (v)
        '''
        print(listartikelmaster)
        # print(asds)
        for item in listartikel:
            kuantitas = 0
            artikelmaster = models.Artikel.objects.get(id = item)
            # print(tanggalminus)
            dataartikelfiltertanggalminus = dataproduksi.filter(KodeArtikel = artikelmaster,Tanggal__lte = tanggalminus)
            dataartikeljumlah = dataartikelfiltertanggalminus.aggregate(total=Sum('Jumlah'))['total']
            datakonversiversiterdekat = models.Penyusun.objects.filter(KodeArtikel =artikelmaster,versi__lte=tanggalminus,KodeProduk= produk).order_by('-versi').first()
            # print('data konversi awal', datakonversiversiterdekat)
            try:
                print(f'\nArtikel {item} datakonversiterdekat {datakonversiversiterdekat.IDKodePenyusun}\n')
            except :
                pass
            if not datakonversiversiterdekat:
                datakonversiversiterdekat = models.Penyusun.objects.filter(KodeArtikel =artikelmaster,versi__gte=tanggalminus).order_by('versi').first()
            kuantitas = models.KonversiMaster.objects.get(KodePenyusun = datakonversiversiterdekat.IDKodePenyusun).Kuantitas
            kuantitas += kuantitas *0.025
            # print(f'Kuantitas Awal {kuantitas}')
            # print(asdas)
            # cari data penyesuaian apabila ada
            datapenyesuaian = models.Penyesuaian.objects.filter(KodePenyusun__KodeArtikel = artikelmaster, TanggalMulai__lte = tanggalminus).order_by('-TanggalMulai').first()
            # print(datapenyesuaian)
            if datapenyesuaian:
                datakonversiversiterdekat = datapenyesuaian
                kuantitas = datakonversiversiterdekat.konversi
            if dataartikeljumlah is None:
                dataartikeljumlah = 0
            # print(datakonversiversiterdekat)
            # print(asdas)
                
            # print(f'Kuantitas akhir {kuantitas}')
            # print('data konversi Akhir', datakonversiversiterdekat)

            '''
            Data penyesuaian dan konversi master sudah didapatkan 
            Kurang ambil kuantitasnya
            '''
            kuantitas = round(kuantitas,4)
            datakuantitasperhitungan['datakeluar'] += (dataartikeljumlah * kuantitas)
            listdataperhitungan [item] = {'artikelobj' : artikelmaster, 'jumlah' : dataartikeljumlah,'konversi':kuantitas}
            # print(f' ini list perhitungan \n {listdataperhitungan}')
            # print(asdasda)
        
        # print('data kuantitas Perhitingan',datakuantitasperhitungan)

        sum_product = sum(listdataperhitungan[key]['jumlah'] * listdataperhitungan[key]['konversi'] for key in listdataperhitungan)
        # print(sum_product)
        # print("Sum Product 2 Dictionary : ", sum_product)
        print(listdataperhitungan)
        # print(asdsaasd)
        # print('aaaa')
        datakuantitasperhitungan['saldodata'] = datasisaminus
        datakuantitasperhitungan['saldofisik'] = dataaktual
        for key in listdataperhitungan:
            # print(key)
            jumlahxkonversi = listdataperhitungan[key]['jumlah'] * listdataperhitungan[key]['konversi']

            keluarpenyesuaian = datakuantitasperhitungan['datakeluar'] - (datakuantitasperhitungan['saldofisik'] - datakuantitasperhitungan['saldodata'])
            # print(f'Data Jumlah : {datajumlah}\nData Aktual : {dataaktual}\nData Sisa : {datasisaminus}')
            # print("Perkalian jumlah dan konversi untuk", key, ":", jumlahxkonversi)
            # print("Keluar Penyesuaian untuk", key, ":", keluarpenyesuaian)
            try:
                # print(f"jumlah : {listdataperhitungan[key]['jumlah']}")
                jumlahpenyesuaian = listdataperhitungan[key]['jumlah'] / keluarpenyesuaian
                nilaikonversibaru = round(jumlahxkonversi / (sum_product * jumlahpenyesuaian),5)
                # print('ini konversi baru',nilaikonversibaru)
            except ZeroDivisionError:
                nilaikonversibaru = listdataperhitungan[key]['konversi']
            # print("Nilai konversi Baru untuk", key, ":", nilaikonversibaru)
            listdataperhitungan[key]['konversibaru'] = nilaikonversibaru
        
        datakuantitasperhitungan
        print(f' ini list perhitungan \n {listdataperhitungan}')
        # print('bbb')
        # print(data)
        # print(listdata)
        return render(
            request,
            "produksi/newkalkulator_penyesuaian.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": listdata,
                'dataperhitungan' : listdataperhitungan,
                "saldo": saldoawal,
                "tahun": tahun,
                "jumlahartikel": dataajumlahartikel,
                "konversiawal": datakonversiartikel,
                "datakuantitas" : datakuantitasperhitungan
            },
        )


# Saldo Awal Bahan Baku
def view_saldobahan(request):
    dataproduk = models.SaldoAwalBahanBaku.objects.all().order_by("-Tanggal")
    for i in dataproduk:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_saldobahan.html", {"dataproduk": dataproduk}
    )


def add_saldobahan(request):
    databarang = models.Produk.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldobahan.html",
            {"nama_lokasi": datalokasi, "databarang": databarang},
        )
    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        harga = request.POST["harga"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalBahanBaku.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDBahanBaku__KodeProduk=kodeproduk,
            IDLokasi=lokasi
        ).exists()
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("view_saldobahan")
        
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.SaldoAwalBahanBaku(
            Tanggal=tanggal, Jumlah=jumlah, IDBahanBaku=produkobj, IDLokasi=lokasiobj, Harga=harga)
        pemusnahanobj.save()
        return redirect("view_saldobahan")


def update_saldobahan(request, id):
    databarang = models.Produk.objects.all()
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_saldobahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj,"databarang": databarang},
        )

    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        harga = request.POST["harga"]
        tanggal = request.POST["tanggal"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDBahanBaku = produkobj
        dataobj.IDLokasi = lokasiobj
        dataobj.Harga = harga
        dataobj.save()
        return redirect("view_saldobahan")


def delete_saldobahan(request, id):
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)

    dataobj.delete()
    return redirect(view_saldobahan)


# Saldo Awal Artikel
def view_saldoartikel(request):
    dataartikel = models.SaldoAwalArtikel.objects.all().order_by("-Tanggal")
    for i in dataartikel:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_saldoartikel.html", {"dataartikel": dataartikel}
    )


def add_saldoartikel(request):
    dataartikel = models.Artikel.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldoartikel.html",
            {"nama_lokasi": datalokasi, "dataartikel": dataartikel},
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
        ).exists()
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("view_saldoartikel")
        
        artikelobj = models.Artikel.objects.get(KodeArtikel=artikel)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.SaldoAwalArtikel(
            Tanggal=tanggal, Jumlah=jumlah, IDArtikel=artikelobj, IDLokasi=lokasiobj
        )
        pemusnahanobj.save()
        return redirect("view_saldoartikel")


def update_saldoartikel(request, id):
    dataartikel = models.Artikel.objects.all()
    dataobj = models.SaldoAwalArtikel.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "produksi/update_saldoartikel.html",
            {"data": dataobj, "nama_lokasi": lokasiobj, "dataartikel": dataartikel},
        )

    else:
        artikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        artikelobj = models.Artikel.objects.get(KodeArtikel=artikel)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDArtikel = artikelobj
        dataobj.IDLokasi= lokasiobj

        dataobj.save()
        return redirect("view_saldoartikel")


def delete_saldoartikel(request, id):
    dataobj = models.SaldoAwalArtikel.objects.get(IDSaldoAwalBahanBaku=id)

    dataobj.delete()
    return redirect(view_saldoartikel)


# Saldo Awal Subkon
def view_saldosubkon(request):
    datasubkon = models.SaldoAwalSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "produksi/view_saldosubkon.html", {"datasubkon": datasubkon}
    )


def add_saldosubkon(request):
    datasubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldosubkon.html",
            { "datasubkon": datasubkon},
        )
    else:
        kodeproduk = request.POST["produk"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalSubkon.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDProdukSubkon__NamaProduk=kodeproduk,
        ).exists()
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("view_saldosubkon")
        
        produkobj = models.ProdukSubkon.objects.get(NamaProduk=kodeproduk)
        pemusnahanobj = models.SaldoAwalSubkon(
            Tanggal=tanggal, Jumlah=jumlah, IDProdukSubkon=produkobj)
        pemusnahanobj.save()
        return redirect("view_saldosubkon")


def update_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    datasubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_saldosubkon.html",
            {"data": dataobj,"datasubkon": datasubkon },
        )

    else:
        kodeproduk = request.POST["produk"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        produkobj = models.ProdukSubkon.objects.get(NamaProduk=kodeproduk)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDProdukSubkon = produkobj
        dataobj.save()
        return redirect("view_saldosubkon")


def delete_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)

    dataobj.delete()
    return redirect(view_saldosubkon)


# Kartu Stok Subkon
def view_ksbbsubkon(request):
    kodeproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbbsubkon.html", {"kodeprodukobj": kodeproduk})
    else:
        """
        1. Cari 
        """
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("ksbbsubkon")
        
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        # Menceri data transaksi gudang dengan kode 
        datagudang = models.TransaksiGudang.objects.filter(
            KodeProduk=produk, tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        datakirim = models.DetailSubkonKirim.objects.filter(
            KodeProduk=produk, IDSubkonKirim__Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )

        ''' TANGGAL SECTION '''
        tanggalmasuk = datagudang.values_list("tanggal", flat=True)
        tanggalkeluar = datakirim.values_list("IDSubkonKirim__Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar)))
        )

        ''' SALDO AWAL SECTION '''
        try:
            saldoawal = models.SaldoAwalBahanBaku.objects.get(
                IDBahanBaku=request.GET["kodebarang"],
                IDLokasi=1,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBaku.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        ''' PENGOLAHAN DATA '''
        listdata =[]
        for i in listtanggal:
            data = {
                'Tanggal': None,
                'Masuk' : None,
                'Keluar' : None,
                'Sisa' : None
            }

            data['Tanggal'] = i.strftime("%Y-%m-%d")
            # Data Masuk
            masuk = 0
            datamasuk = datagudang.filter(tanggal=i)
            for m in datamasuk:
                masuk += m.jumlah
            sisa  += masuk
            data['Masuk'] = masuk
            
            # Data Keluar
            keluar = 0
            datakeluar = datakirim.filter(IDSubkonKirim__Tanggal = i)
            for k in datakeluar:
                keluar += k.Jumlah
            sisa -= keluar
            data['Keluar'] = keluar

            data['Sisa'] = sisa
            listdata.append(data)

        return render(request, "produksi/view_ksbbsubkon.html",{'data':listdata,'saldo':saldoawal,'kodebarang':request.GET["kodebarang"],"nama": nama,"satuan": satuan,})
    

def view_ksbjsubkon(request):
    kodeproduk = models.ProdukSubkon.objects.all()
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbjsubkon.html", {"kodeprodukobj": kodeproduk})
    else:
        """
        1. Cari 
        """
        try:
            produk = models.ProdukSubkon.objects.get(NamaProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.Unit
        except:
            messages.error(request, "Data Produk Subkon tidak ditemukan")
            return redirect("ksbjsubkon")
        
        idartikel = produk.KodeArtikel
        artikel = models.Artikel.objects.get(KodeArtikel=idartikel)
        
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)
        
        # Menceri data transaksi gudang dengan kode 
        dataterima = models.TransaksiSubkon.objects.filter(
            IDProdukSubkon=produk.IDProdukSubkon, Tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        # Kode Artikel yang di susun oleh bahan baku 
        penyusun_produk = (
            models.ProdukSubkon.objects.filter(NamaProduk=request.GET["kodebarang"])
            .values_list("KodeArtikel", flat=True)
            .distinct()
        )

        dataproduksi = models.TransaksiProduksi.objects.filter(
            KodeArtikel__id__in=penyusun_produk,
            Jenis="Mutasi",
            Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )

        # ''' TANGGAL SECTION '''
        tanggalmasuk = dataterima.values_list("Tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
        # tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)

        listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))

        ''' SALDO AWAL SECTION '''
        try:
            saldoawal = models.SaldoAwalSubkon.objects.get(
                IDProdukSubkon=produk.IDProdukSubkon,
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalSubkon.DoesNotExist:
            saldo = 0
            saldoawal = None

        sisa = saldo

        # ''' PENGOLAHAN DATA '''
        listdata = [ ]
        for i in listtanggal:
            # Data Models
            data = {
                'Tanggal': None,
                'Masuk' : None,
                'Keluar' : None,
                'Sisa' : None
                
            }
            data['Tanggal'] = i.strftime("%Y-%m-%d")
            # Data Masuk
            masuk = 0
            datamasuk = dataterima.filter(Tanggal=i)
            for m in datamasuk:
                masuk += m.Jumlah
            sisa  += masuk
            data['Masuk'] = masuk
            
            # Data Keluar
            datakeluar = dataproduksi.filter(Tanggal = i)
            keluar = 0
            for k in datakeluar:
                keluar += k.Jumlah
            sisa -= keluar
            data['Keluar'] = keluar

            data['Sisa'] = sisa

            listdata.append(data)

        return render(request, "produksi/view_ksbjsubkon.html",{"data":listdata,'saldo':saldoawal,"nama": nama,"satuan": satuan,"artikel":artikel})


def read_bahanbaku(request):
    produkobj = models.Produk.objects.all()
    return render(request, "produksi/read_produk.html", {"produkobj": produkobj})


def update_produk_produksi(request, id):
    produkobj = models.Produk.objects.get(pk=id)
    if request.method == "GET":
        return render(request, "produksi/update_produk.html", {"produkobj": produkobj})
    else:
        print(request.POST)
        keterangan_produk = request.POST["keterangan_produk"]
        jumlah_minimal = request.POST["jumlah_minimal"]
        produkobj.keterangan = keterangan_produk
        produkobj.Jumlahminimal = jumlah_minimal
        produkobj.save()
        return redirect("read_produk_produksi")

'''
REVISI 5/11/2024
1. Tambah Transaksi Display pada SPPB
'''

def add_sppb(request):
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    purchaseorder = models.confirmationorder.objects.filter(StatusAktif = True)

    if request.method == "GET":
        return render(
            request,
            "produksi/add_sppb.html",
            {
                "data": dataartikel,
                'display': datadisplay,
                "purchaseorder":purchaseorder
            },
        )

    if request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        
        print(request.POST)
        displaylist = request.POST.getlist("detail_spkdisplay[]")
        jumlahdisplay = request.POST.getlist('quantitydisplay[]')
        confirmationorderdisplay = request.POST.getlist("purchaseorderdisplay")

        datasppb = models.SPPB.objects.filter(NoSPPB=nomor_sppb).exists()
        if datasppb:
            messages.error(request, "Nomor SPPB sudah ada")
            return redirect("add_sppb")
        else:
            messages.success(request, "Data berhasil disimpan")
            data_sppb = models.SPPB(
                NoSPPB=nomor_sppb, Tanggal=tanggal, Keterangan=keterangan
            ).save()

            artikel_list = request.POST.getlist("detail_spk[]")
            jumlah_list = request.POST.getlist("quantity[]")
            confirmationorderartikel = request.POST.getlist("purchaseorderartikel")
            no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

            for artikel, jumlah, confirmationorder in zip(artikel_list, jumlah_list,confirmationorderartikel):
                if artikel == '' or jumlah == '':
                    print('tidak ada data artikel')
                    continue
                # Pisahkan KodeArtikel dari jumlah dengan delimiter '/'
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel)
                jumlah_produk = jumlah

                # Simpan data ke dalam model DetailSPK
                datadetailspk = models.DetailSPPB(
                    NoSPPB=no_sppb, DetailSPK=kode_artikel, Jumlah=jumlah_produk
                )
                if not confirmationorder == "":

                    datadetailspk.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)
                datadetailspk.save()

            for display,jumlah,confirmationorder in zip(displaylist,jumlahdisplay,confirmationorderdisplay):
                print('ini : ',display, jumlah)
                if display == "" or jumlah == "":
                    print('tidak ada Display')
                    continue
                detailspkdisplayobj = models.DetailSPKDisplay.objects.get(IDDetailSPK = display)
                datadetailspkdisplay = models.DetailSPPB(
                NoSPPB=no_sppb, DetailSPKDisplay=detailspkdisplayobj, Jumlah=jumlah
                )
                if not confirmationorder == "":
                    datadetailspkdisplay.IDCO = models.confirmationorder.objects.get(pk = confirmationorder)
                datadetailspkdisplay.save()

                # Buat Transaksi Mutasi 
                transaksiproduksiobj = models.TransaksiProduksi(
                    Tanggal = tanggal, Jumlah = jumlah, Jenis = "Mutasi", Keterangan = "Mutasi Display", Lokasi = models.Lokasi.objects.get(pk = 1), DetailSPPBDisplay = datadetailspkdisplay
                
                )
                
                transaksiproduksiobj.save()
                print(transaksiproduksiobj)

            return redirect("view_sppb")

def load_display(request):
    print(request.GET)
    kode_display = request.GET.get("kode_artikel")
    displayobj = models.Display.objects.get(KodeDisplay=kode_display)
    detailspk = models.DetailSPKDisplay.objects.filter(KodeDisplay=displayobj.id,NoSPK__StatusDisplay = 1, NoSPK__StatusAktif=1)
    print(detailspk)

    return render(request, "produksi/opsi_spkdisplay.html", {"detailspk": detailspk})

def detail_sppb(request, id):
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    datadetailspk = models.DetailSPK.objects.all()
    datadetailspkdisplay = models.DetailSPKDisplay.objects.all()
    datasppb = models.SPPB.objects.get(id=id)
    datadetailsppbArtikel = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id,DetailSPKDisplay = None)
    datadetailsppbdisplay = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id,DetailSPK = None)
    purchaseorderdata = models.confirmationorder.objects.filter(StatusAktif =True)
    print(datadetailsppbdisplay)
    if request.method == "GET":
        tanggal = datetime.strftime(datasppb.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "produksi/detail_sppb.html",
            {
                "dataartikel": dataartikel,
                "datadisplay": datadisplay,
                "data": datadetailspk,
                "dataspkdisplay": datadetailspkdisplay,
                "datasppb": datasppb,
                "datadetail": datadetailsppbArtikel,
                "datadetaildisplay": datadetailsppbdisplay,
                "tanggal": tanggal,
                'purchaseorder':purchaseorderdata
            },
        )

    elif request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggall = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        artikel_list = request.POST.getlist("detail_spkawal[]")
        jumlah_list = request.POST.getlist("quantity[]")
        display_list = request.POST.getlist("detail_spkdisplayawal[]")
        jumlahdisplay_list = request.POST.getlist('quantitydisplay[]')

        artikel_baru = request.POST.getlist('detail_spk[]')
        jumlah_baru = request.POST.getlist('quantitybaru[]')
        purchaseorder_artikelbaru = request.POST.getlist('purchaseorderartikelbaru')

        display_baru = request.POST.getlist('detail_spkdisplay[]')
        jumlahdisplay_baru = request.POST.getlist('quantitydisplaybaru[]')
        purchaseorder_displaybaru = request.POST.getlist('purchaseorderdisplay')

        print(request.POST)
        # print(datadetailsppbArtikel)
        # print(asdasd)
        datasppb.NoSPPB = nomor_sppb
        datasppb.Tanggal = tanggall
        datasppb.Keterangan = keterangan
        datasppb.save()
        if datadetailsppbArtikel:
            print('Masuk Artikel')
            for detail, artikel_id, jumlah in zip(
                datadetailsppbArtikel, artikel_list, jumlah_list
            ):
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
                detail.DetailSPK = kode_artikel
                detail.Jumlah = jumlah
                detail.save()
        if datadetailsppbdisplay:
            print('Masuk Display')
            for detail, artikel_id, jumlah in zip(
                datadetailsppbdisplay, display_list, jumlahdisplay_list
            ):
                kode_display = models.DetailSPKDisplay.objects.get(IDDetailSPK=artikel_id)
                detail.DetailSPKDisplay = kode_display
                detail.Jumlah = jumlah
                detail.save()


        no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

        if artikel_baru:
            print("Artikel Baru")
            print(artikel_baru,jumlah_baru)
            for artikel_id, jumlah,confirmationorder in zip(
                artikel_baru,jumlah_baru,purchaseorder_artikelbaru
            ):
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
                new_detail = models.DetailSPPB(
                    NoSPPB=no_sppb,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                    DetailSPK=kode_artikel,
                    Jumlah=jumlah,
                )
                if not confirmationorder == "":
                    new_detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)
                new_detail.save()

        if display_baru:
            print('Display Baru')
            print(display_baru,jumlahdisplay_baru)
            for display_id, jumlah, confirmationorder in zip(display_baru,jumlahdisplay_baru,purchaseorder_displaybaru):
                kode_display = models.DetailSPKDisplay.objects.get(IDDetailSPK = display_id)
                new_detail = models.DetailSPPB(
                    NoSPPB=no_sppb,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                    DetailSPKDisplay=kode_display,
                    Jumlah=jumlah)
                if not confirmationorder == "":
                    new_detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)
                new_detail.save()
        
        return redirect("detail_sppb", id=id)

# KSBB
# KSBJ
# Kalkulator Penyesuaian Belum bisa 2 kali Penyesuaian

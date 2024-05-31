from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404, JsonResponse, HttpResponse
from django.urls import reverse
from . import models
from django.db.models import Sum
from urllib.parse import quote
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta, date
from . import logindecorators
from django.contrib.auth.decorators import login_required


# Create your views here.
# RND
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
@logindecorators.allowed_users(allowed_roles=['rnd'])
def dashboard(request):
    tanggalsekarang = date.today()
    selisihwaktu = timedelta(days=7)
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
    return render(
        request,
        "rnd/dashboard.html",
        {"dataspk": dataspk, "dataproduk": dataproduk, "datasppb": datasppb},
    )


def views_artikel(request):
    datakirim = []
    data = models.Artikel.objects.all()
    for item in data:
        detailartikelobj = models.Penyusun.objects.filter(KodeArtikel=item.id).filter(
            Status=1
        )
        if detailartikelobj.exists():
            datakirim.append([item, detailartikelobj[0]])
        else:
            datakirim.append([item, "Belum diset"])
    return render(request, "rnd/views_artikel.html", {"data": datakirim})


def tambahdataartikel(request):
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


def updatedataartikel(request, id):
    data = models.Artikel.objects.get(id=id)
    if request.method == "GET":
        return render(request, "rnd/update_artikel.html", {"artikel": data})
    else:
        kodeartikel = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        if keterangan == "":
            keterangan = "-"
        cekkodeartikel = models.Artikel.objects.filter(KodeArtikel=kodeartikel).exists()
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


def deleteartikel(request, id):
    dataobj = models.Artikel.objects.get(id=id)
    models.transactionlog(
        user="RND",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Artikel : {dataobj.kodebaru} Keterangan : {dataobj.keterangan}",
    ).save()
    dataobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("views_artikel")


def views_penyusun(request):
    print(request.GET)
    data = request.GET
    if len(request.GET) == 0:
        data = models.Artikel.objects.all()

        return render(request, "rnd/views_penyusun.html", {"dataartikel": data})
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
                            hargasatuanawal = hargatotalawal / saldoawal

                            # print("ini hargasatuan awal : ", hargasatuanawal)

                        hargaterakhir += hargasatuanawal
                        kuantitaskonversi = konversidataobj.Kuantitas
                        kuantitasallowance = (
                            kuantitaskonversi + kuantitaskonversi * 0.025
                        )
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

                    # print(data)
                    print(versiterpilih)
                    # print(dasdatakonversi)

                    return render(
                        request,
                        "rnd/views_penyusun.html",
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


def updatepenyusun(request, id):
    data = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        datakonversi = models.KonversiMaster.objects.get(
            KodePenyusun=data.IDKodePenyusun
        )
        datakonversi.allowance = datakonversi.Kuantitas + (
            datakonversi.Kuantitas * 0.025
        )
        kodebahanbaku = models.Produk.objects.all()
        lokasiobj = models.Lokasi.objects.all()
        return render(
            request,
            "rnd/update_penyusun.html",
            {
                "kodestok": kodebahanbaku,
                "data": data,
                "lokasi": lokasiobj,
                "konversi": datakonversi,
            },
        )
    else:
        print(request.POST)
        kodeproduk = request.POST["kodeproduk"]
        lokasi = request.POST["lokasi"]
        status = request.POST["status"]
        kuantitas = request.POST["kuantitas"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        konversiobj = models.KonversiMaster.objects.get(KodePenyusun=id)
        data.KodeProduk = produkobj
        data.Lokasi = lokasiobj
        data.Status = status
        data.save()
        konversiobj.Kuantitas = kuantitas
        konversiobj.save()
        transaksilog = models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Penyusun Baru. Kode Artikel : {data.KodeArtikel}, Kode produk : {data.KodeProduk}-{data.NamaProduk}, Status Utama : {data} versi : {data.versi}, Kuantitas Konversi : {  konversiobj.Kuantitas}",
        )
        transaksilog.save()
        return redirect("penyusun_artikel")


def tambahdatapenyusun(request, id, versi):
    dataartikelobj = models.Artikel.objects.get(id=id)
    print(versi)
    if request.method == "GET":
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "rnd/tambah_penyusun.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versi,
            },
        )
    else:
        kodeproduk = request.POST["kodeproduk"]
        statusproduk = request.POST["Status"]
        if statusproduk == "True":
            statusproduk = True
        else:
            statusproduk = False
        lokasi = request.POST["lokasi"]

        newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, versi=versi)
            .exists()
        )
        if datapenyusunobj and statusproduk:
            messages.error(
                request, "Artikel telah memiliki Bahan baku utama sebelumnya"
            )
            return redirect("tambah_data_penyusun", id=id, versi=versi)
        penyusunobj = models.Penyusun(
            Status=statusproduk,
            KodeArtikel=dataartikelobj,
            KodeProduk=newprodukobj,
            Lokasi=lokasiobj,
            versi=versi,
        )
        penyusunobj.save()
        kuantitas = request.POST["kuantitas"]
        konversimasterobj = models.KonversiMaster(
            KodePenyusun=penyusunobj, Kuantitas=kuantitas, lastedited=datetime.now()
        ).save()
        messages.success(request, "Data penyusun berhasil ditambahkan")
        models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Penyusun. Kode Artikel : {dataartikelobj.KodeArtikel}, Kode produk : {newprodukobj.KodeProduk}-{newprodukobj.NamaProduk}, Status Utama : {statusproduk} versi : {versi}, Kuantitas Konversi : {kuantitas}",
        ).save()
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(dataartikelobj.KodeArtikel)}"
        )


def delete_penyusun(request, id):
    penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    penyusunobj.delete()
    print(penyusunobj)
    print(id)
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


def konversimaster_delete(request, id):
    dataobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
    dataobj.Kuantitas = 0
    dataobj.save()
    return redirect("konversi")


def views_sppb(request):
    data = models.SPPB.objects.all()
    for sppb in data:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=sppb.id)
        sppb.detailsppb = detailsppb
    return render(request, "rnd/views_sppb.html", {"data": data})


def view_spk(request):
    dataspk = models.SPK.objects.all().order_by("-Tanggal")

    for j in dataspk:
        j.Tanggal = j.Tanggal.strftime("%Y-%m-%d")
        total_detail_spk = (
            models.DetailSPK.objects.filter(NoSPK=j)
            .values("KodeArtikel")
            .annotate(total=Sum("Jumlah"))
        )
        for detail_spk in total_detail_spk:
            kode_artikel = detail_spk["KodeArtikel"]
            total_requested = detail_spk["total"]

            total_processed = (
                models.DetailSPPB.objects.filter(
                    DetailSPK__NoSPK=j, DetailSPK__KodeArtikel=kode_artikel
                ).aggregate(total=Sum("Jumlah"))["total"]
                or 0
            )

            if total_processed < total_requested:
                is_lunas = False
                break

    return render(request, "rnd/view_spk.html", {"dataspk": dataspk})


def hariterakhirdatetime(tahun):
    next_year = datetime(tahun + 1, 1, 1)
    last_day = next_year - timedelta(days=1)
    return last_day


def views_ksbj(request):
    dataartikel = models.Artikel.objects.all()
    if len(request.GET) == 0:
        return render(request, "rnd/view_ksbj.html", {"dataartikel": dataartikel})
    else:
        kodeartikel = request.GET["kodeartikel"]
        try:
            artikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Data Artikel tidak ditemukan")
            return redirect("view_ksbj")

        if request.GET["tahun"]:
            tahun = int(request.GET["tahun"])
        else:
            sekarang = datetime.now()
            tahun - sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        lokasi = request.GET["lokasi"]
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)

        getbahanbakuutama = models.Penyusun.objects.filter(
            KodeArtikel=artikel.id, Status=1
        )

        if not getbahanbakuutama:
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("view_ksbj")

        data = models.TransaksiProduksi.objects.filter(
            KodeArtikel=artikel.id, Jenis="Mutasi"
        )
        datamasuk = models.TransaksiGudang.objects.filter(
            DetailSPK__KodeArtikel=artikel.id
        )
        print(datamasuk)
        # print(datamaasdasd)
        listtanggalmasuk = datamasuk.values_list("tanggal", flat=True).distinct()
        listdata = []
        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoawalobj = models.SaldoAwalArtikel.objects.get(
                    IDArtikel__KodeArtikel=kodeartikel,
                    IDLokasi=lokasiobj.IDLokasi,
                    Tanggal__range=(tanggal_mulai, tanggal_akhir),
                )
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
                print("ini saldo awallll", saldoawalobj)
            except models.SaldoAwalArtikel.DoesNotExist:
                saldo = 0
                saldoawal = None
                saldoawalobj = {"Tanggal": "Belum ada Data", "saldo": saldo}

            tanggallist = (
                data.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir))
                .values_list("Tanggal", flat=True)
                .distinct()
            )
            saldoawal = saldo
            tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk)))))
            print(tanggallist)
            # print(asdasd)
            for i in tanggallist:
                datamodels = {
                    "Tanggal": None,
                    "SPK": None,
                    "Kodeproduk": None,
                    "Masuklembar": None,
                    "Masukkonversi": None,
                    "Hasil": None,
                    "Sisa": None,
                }

                filtertanggal = data.filter(Tanggal=i)
                filtertanggaltransaksigudang = datamasuk.filter(tanggal=i)
                print(filtertanggaltransaksigudang)
                # print(asdasd)

                jumlahmutasi = filtertanggal.filter(Jenis="Mutasi").aggregate(
                    total=Sum("Jumlah")
                )["total"]
                jumlahmasuk = filtertanggaltransaksigudang.aggregate(
                    total=Sum("jumlah")
                )["total"]

                if jumlahmutasi is None:
                    jumlahmutasi = 0
                if jumlahmasuk is None:
                    jumlahmasuk = 0

                print(
                    f"{i} tanggal,filtertangga {filtertanggal}, {jumlahmutasi} jumlah"
                )
                print(i)

                # Cari data penyusun sesuai tanggal
                penyusunfiltertanggal = (
                    models.Penyusun.objects.filter(
                        KodeArtikel=artikel.id, Status=1, versi__lte=i
                    )
                    .order_by("-versi")
                    .first()
                )

                if not penyusunfiltertanggal:
                    penyusunfiltertanggal = (
                        models.Penyusun.objects.filter(
                            KodeArtikel=artikel.id, Status=1, versi__gte=i
                        )
                        .order_by("versi")
                        .first()
                    )

                konversimasterobj = models.KonversiMaster.objects.get(
                    KodePenyusun=penyusunfiltertanggal.IDKodePenyusun
                )
                print(konversimasterobj.Kuantitas)

                masukpcs = round(
                    jumlahmasuk
                    / (
                        (
                            konversimasterobj.Kuantitas
                            + (konversimasterobj.Kuantitas * 0.025)
                        )
                    )
                )
                saldoawal = saldoawal - jumlahmutasi + masukpcs
                print(saldoawal)

                datamodels["Tanggal"] = i.strftime("%Y-%m-%d")
                datamodels["Masuklembar"] = jumlahmasuk
                datamodels["Masukkonversi"] = masukpcs
                datamodels["Sisa"] = saldoawal
                datamodels["Hasil"] = jumlahmutasi
                datamodels["SPK"] = filtertanggal.filter(Jenis="Mutasi")
                datamodels["Kodeproduk"] = penyusunfiltertanggal

                # Cari data penyesuaian
                print(datamodels)
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )
                listdata.append(datamodels)
                print(listdata)

            return render(
                request,
                "rnd/view_ksbj.html",
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
                saldoawalobj = models.SaldoAwalArtikel.objects.get(
                    IDArtikel__KodeArtikel=kodeartikel,
                    IDLokasi=lokasiobj.IDLokasi,
                    Tanggal__range=(tanggal_mulai, tanggal_akhir),
                )
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")
            except models.SaldoAwalArtikel.DoesNotExist:
                saldo = 0
                saldoawalobj = {"Tanggal": "Belum ada Data", "saldo": saldo}
            print("ini saldoawalobj", saldoawalobj)

            tanggalmutasi = (
                data.filter(
                    Jenis="Produksi", Tanggal__range=(tanggal_mulai, tanggal_akhir)
                )
                .values_list("Tanggal", flat=True)
                .distinct()
            )
            sppb = models.DetailSPPB.objects.filter(
                DetailSPK__KodeArtikel__KodeArtikel=kodeartikel,
                NoSPPB__Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            tanggalsppb = sppb.values_list("NoSPPB__Tanggal", flat=True).distinct()
            tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb))))
            print(tanggallist)
            saldoawal = saldo

            for i in tanggallist:
                datamodels = {
                    "Tanggal": None,
                    "Penyerahanwip": None,
                    "DetailSPPB": None,
                    "Sisa": None,
                }
                print(kodeartikel)
                penyerahanwip = models.TransaksiProduksi.objects.filter(
                    Tanggal=i,
                    KodeArtikel__KodeArtikel=kodeartikel,
                    Jenis="Mutasi",
                )
                print(penyerahanwip)
                print(i)
                # print(asdasd)
                detailsppbjobj = sppb.filter(NoSPPB__Tanggal=i)

                totalpenyerahanwip = data.filter(Tanggal=i, Jenis="Mutasi").aggregate(
                    total=Sum("Jumlah")
                )["total"]
                totalkeluar = detailsppbjobj.aggregate(total=Sum("Jumlah"))["total"]

                if not totalpenyerahanwip:
                    totalpenyerahanwip = 0
                if not totalkeluar:
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

                datamodels["Tanggal"] = i
                datamodels["Penyerahanwip"] = totalpenyerahanwip
                datamodels["DetailSPPB"] = detailsppbjobj
                datamodels["Sisa"] = saldoawal
                listdata.append(datamodels)
            print(listdata)

            return render(
                request,
                "rnd/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": "FG",
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                },
            )


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
            tahun = "2024"

        tahun = datetime.strptime(tahun, format("%Y"))
        awaltahun = datetime(tahun.year, 1, 1)

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
                Tanggal__gte=awaltahun,
            )
            .order_by("-Tanggal")
            .first()
        )
        print(saldoawalobj)
        if (
            not keluarobj.exists()
            and not returobj.exists()
            and not masukobj.exists()
            and saldoawalobj is not None
        ):
            messages.error(request, "Tidak ditemukan data Transaksi Barang")
            return redirect("rekapharga")
        # print(asdas)
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
            "rnd/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
            },
        )


def tambahversi(request, id):
    data = models.Artikel.objects.get(id=id)
    tanggal = date.today().strftime("%Y-%m-%d")
    print(tanggal)
    if request.method == "GET":
        return render(
            request, "rnd/tambah_versi.html", {"data": data, "versi": tanggal}
        )
    else:
        print(request.POST)
        kodeproduk = request.POST.getlist("kodeproduk")
        status = request.POST.getlist("Status")
        lokasi = request.POST.getlist("lokasi")
        kuantitas = request.POST.getlist("kuantitas")
        if status.count("True") > 1:
            messages.error(request, "Terdapat Artikel utama lebih dari 1")
            return redirect("add_versi", id=id)
        dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas))
        print(dataproduk)
        for i in dataproduk:
            newpenyusun = models.Penyusun(
                KodeProduk=models.Produk.objects.get(KodeProduk=i[0]),
                KodeArtikel=data,
                Status=i[1],
                Lokasi=models.Lokasi.objects.get(NamaLokasi=i[2]),
                versi=tanggal,
            ).save()
            datanewpenyusun = models.Penyusun.objects.all().last()
            konversimasterobj = models.KonversiMaster(
                KodePenyusun=datanewpenyusun, Kuantitas=i[3]
            ).save()
            print(newpenyusun)
            print(konversimasterobj)
        return redirect("penyusun_artikel")


"""
REVISI 
5/13/2024
1. Revisi views Penyusun Konversi
2. Add datalist ke KodeProduk pada Add Versi
3. Revisi Perhitungan Bahan Baku
4. Revisi Keterangan Produk
"""


def read_produk(request):
    produkobj = models.Produk.objects.all()
    print(produkobj[1].keteranganRND)
    return render(request, "rnd/read_produk.html", {"produkobj": produkobj})


def views_penyusun(request):
    print(request.GET)
    data = request.GET
    if len(request.GET) == 0:
        data = models.Artikel.objects.all()

        return render(request, "rnd/views_penyusun.html", {"dataartikel": data})
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
                awaltahun = datetime(2024, 1, 1)
                print(data)
                if data.exists():
                    for item in data:
                        print(item, item.IDKodePenyusun)
                        konversidataobj = models.KonversiMaster.objects.get(
                            KodePenyusun=item.IDKodePenyusun
                        )
                        # print(konversidataobj.Kuantitas)
                        masukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=item.KodeProduk, NoSuratJalan__Tanggal__gte=awaltahun
        )
                        # print("ini detail sjp", masukobj)
                        tanggalmasuk = masukobj.values_list(
                            "NoSuratJalan__Tanggal", flat=True
                        )
                        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk=item.KodeProduk, tanggal__gte=awaltahun
        )

                        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                        # print(item)
                        returobj = models.TransaksiGudang.objects.filter(
            jumlah__lt=0, KodeProduk=item.KodeProduk, tanggal__gte=awaltahun
        )        
                        tanggalretur = returobj.values_list("tanggal", flat=True)

                        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku=item.KodeProduk,
                IDLokasi__IDLokasi=3,
                Tanggal__gte=awaltahun,
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
                            list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalretur)))
                        )
                        # print("inii", listtanggal)
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
                            hargasatuanawal = hargatotalawal / saldoawal

                            print("Sisa Stok Hari Ini : ", saldoawal)
                            print("harga awal Hari Ini :", hargasatuanawal)
                            print("harga total Hari Ini :", hargatotalawal, "\n")
                            dumy["Sisahariini"] = saldoawal
                            dumy["Hargasatuansisa"] = round(hargasatuanawal, 2)
                            dumy["Hargatotalsisa"] = round(hargatotalawal, 2)

                            listdata.append(dumy)

                        hargaterakhir += hargasatuanawal
                        kuantitaskonversi = konversidataobj.Kuantitas
                        kuantitasallowance = (
                            kuantitaskonversi + kuantitaskonversi * 0.025
                        )
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

                    # print(data)
                    print(versiterpilih)
                    # print(dasdatakonversi)

                    return render(
                        request,
                        "rnd/views_penyusun.html",
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


def tambahversi(request, id):
    data = models.Artikel.objects.get(id=id)
    bahanbaku = models.Produk.objects.all()
    tanggal = date.today().strftime("%Y-%m-%d")
    print(tanggal)
    if request.method == "GET":
        return render(
            request,
            "rnd/tambah_versi.html",
            {"data": data, "versi": tanggal, "dataproduk": bahanbaku},
        )
    else:
        print(request.POST)
        kodeproduk = request.POST.getlist("kodeproduk")
        status = request.POST.getlist("Status")
        lokasi = request.POST.getlist("lokasi")
        kuantitas = request.POST.getlist("kuantitas")
        tanggal = request.POST["versi"]
        print(request.POST)
        # print(asdas)
        if status.count("True") > 1:
            messages.error(request, "Terdapat Artikel utama lebih dari 1")
            return redirect("add_versi", id=id)
        dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas))
        print(dataproduk)
        for i in dataproduk:
            newpenyusun = models.Penyusun(
                KodeProduk=models.Produk.objects.get(KodeProduk=i[0]),
                KodeArtikel=data,
                Status=i[1],
                Lokasi=models.Lokasi.objects.get(NamaLokasi=i[2]),
                versi=tanggal,
            ).save()
            datanewpenyusun = models.Penyusun.objects.all().last()
            konversimasterobj = models.KonversiMaster(
                KodePenyusun=datanewpenyusun, Kuantitas=i[3]
            ).save()
            print(newpenyusun)
            print(konversimasterobj)
        return redirect("penyusun_artikel")


def tambahdatapenyusun(request, id, versi):
    dataartikelobj = models.Artikel.objects.get(id=id)
    print(versi, "asdas")
    if request.method == "GET":
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "rnd/tambah_penyusun.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versi,
            },
        )
    else:
        print(request.POST)
        kodeproduk = request.POST.getlist("kodeproduk")
        statusproduk = request.POST.getlist("status")
        listlokasi = request.POST.getlist("lokasi")
        listkuantitas = request.POST.getlist("kuantitas")

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, versi=versi)
            .exists()
        )
        if datapenyusunobj and "True" in statusproduk:
            messages.error(
                request, "Artikel telah memiliki Bahan baku utama sebelumnya"
            )
            return redirect("tambah_data_penyusun", id=id, versi=versi)
        for kodeproduk, status, lokasi, kuantitas in zip(
            kodeproduk, statusproduk, listlokasi, listkuantitas
        ):
            print(kodeproduk, status, lokasi, kuantitas)

            newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
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
                KodePenyusun=penyusunobj, Kuantitas=kuantitas, lastedited=datetime.now()
            ).save()
            messages.success(request, "Data penyusun berhasil ditambahkan")
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Penyusun. Kode Artikel : {dataartikelobj.KodeArtikel}, Kode produk : {newprodukobj.KodeProduk}-{newprodukobj.NamaProduk}, Status Utama : {statusproduk} versi : {versi}, Kuantitas Konversi : {kuantitas}",
            ).save()
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(dataartikelobj.KodeArtikel)}"
        )


def updatepenyusun(request, id):
    data = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        datakonversi = models.KonversiMaster.objects.get(
            KodePenyusun=data.IDKodePenyusun
        )
        datakonversi.allowance = datakonversi.Kuantitas + (
            datakonversi.Kuantitas * 0.025
        )
        kodebahanbaku = models.Produk.objects.all()
        lokasiobj = models.Lokasi.objects.all()
        data.versi = data.versi.strftime("%Y-%m-%d")
        return render(
            request,
            "rnd/update_penyusun.html",
            {
                "kodestok": kodebahanbaku,
                "data": data,
                "lokasi": lokasiobj,
                "konversi": datakonversi,
            },
        )
    else:
        print(request.POST)
        kodeproduk = request.POST["kodeproduk"]
        lokasi = request.POST["lokasi"]
        status = request.POST["status"]
        kuantitas = request.POST["kuantitas"]
        versi = request.POST["versi"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        konversiobj = models.KonversiMaster.objects.get(KodePenyusun=id)
        data.KodeProduk = produkobj
        data.Lokasi = lokasiobj
        data.Status = status
        data.versi = versi
        data.save()
        konversiobj.Kuantitas = kuantitas
        konversiobj.save()
        transaksilog = models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Penyusun Baru. Kode Artikel : {data.KodeArtikel}, Kode produk : {data.KodeProduk}-{data.KodeProduk.NamaProduk}, Status Utama : {data} versi : {data.versi}, Kuantitas Konversi : {  konversiobj.Kuantitas}",
        )
        transaksilog.save()
        return redirect("penyusun_artikel")

def track_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    datadisplay =models.Display.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    if dataspk.StatusDisplay == False:
        datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)
    else:
        datadetail = models.DetailSPKDisplay.objects.filter(NoSPK = dataspk.id)

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

    rekapjumlahpermintaanperbahanbaku = transaksigudangobj.values('KodeProduk__KodeProduk',"KodeProduk__NamaProduk","KodeProduk__unit").annotate(total = Sum('jumlah'))
    rekapjumlahpengirimanperartikel = sppbobj.values("DetailSPK__KodeArtikel__KodeArtikel").annotate(total=Sum('Jumlah'))

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
 

from django.shortcuts import render, redirect
from django.contrib import messages
from . import models
from django.db.models import Sum
from datetime import datetime, timedelta
import pandas as pd

from . import logindecorators
from django.contrib.auth.decorators import login_required

# Dashboard Produksi
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
                tanggalupdate = konversidataobj.lastedited.strftime("%Y-%m-%d")
                kuantitasallowance = konversidataobj.Allowance
                hargaperkotak = hargaterakhir * kuantitasallowance
                nilaifg += hargaperkotak

                datakonversi.append(
                    {
                        "kodeartikel": get_id_kodeartikel,
                        "Penyusunobj": item,
                        "Tanggal" : tanggalupdate,
                        "HargaSatuan": round(hargaterakhir, 2),
                        "Konversi": round(kuantitaskonversi, 5),
                        "Allowance": round(kuantitasallowance, 5),
                        "Hargakotak": round(hargaperkotak, 2),
                    }
                )

        alldata.append(datakonversi)

    return render(request, "produksi/dashboard.html",{"data": alldata})


#Load dropdown
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])    
def load_detailspk(request):
    no_spk = request.GET.get("nomor_spk")
    id_spk = models.SPK.objects.get(NoSPK=no_spk)
    if id_spk.StatusDisplay == False :
        detailspk = models.DetailSPK.objects.filter(NoSPK=id_spk.id,)
    else :
        detailspk = models.DetailSPKDisplay.objects.filter(NoSPK = id_spk.id,)

    return render(request, "produksi/opsi_spk.html", {"detailspk": detailspk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_htmx(request):
    no_spk = request.GET.get("nomor_spk")
    id_spk = models.SPK.objects.get(NoSPK=no_spk)
    detailspk = models.DetailSPK.objects.filter(NoSPK=id_spk.id)

    return render(request, "produksi/opsi_htmx.html", {"detailspk": detailspk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_artikel(request):
    kode_artikel = request.GET.get("kode_artikel")
    artikelobj = models.Artikel.objects.get(KodeArtikel=kode_artikel)
    detailspk = models.DetailSPK.objects.filter(KodeArtikel=artikelobj, NoSPK__StatusAktif=1)

    return render(request, "produksi/opsi_artikel.html", {"detailspk": detailspk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_penyusun(request):
    kodeartikel = request.GET.get("artikel")
    penyusun = models.Penyusun.objects.filter(KodeArtikel=kodeartikel)

    return render(request, "produksi/opsi_penyusun.html", {"penyusun": penyusun})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_display(request):
    print(request.GET)
    kode_display = request.GET.get("kode_artikel")
    displayobj = models.Display.objects.get(KodeDisplay=kode_display)
    detailspk = models.DetailSPKDisplay.objects.filter(KodeDisplay=displayobj.id,NoSPK__StatusDisplay = 1, NoSPK__StatusAktif=1)
    print(detailspk)

    return render(request, "produksi/opsi_spkdisplay.html", {"detailspk": detailspk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_versi(request):
    kodeartikel = request.GET.get("artikel")
    print(request.GET)
    penyusun = models.Penyusun.objects.filter(KodeArtikel__id = kodeartikel).values_list('versi',flat=True).distinct()
    print(penyusun)

    return render(request, "produksi/opsi_versi.html", {"penyusun": penyusun,'kodeartikel':kodeartikel})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def load_penyusun2(request):
    print(request.GET)
    kodeartikel = request.GET.get("artikel")
    versi = request.GET.get("versi")
    tanggalversi = datetime.strptime(versi, '%b. %d, %Y')
    versi = tanggalversi.strftime('%Y-%m-%d')

    penyusun = models.Penyusun.objects.filter(KodeArtikel=kodeartikel,versi = versi)
    print(penyusun)

    return render(request, "produksi/opsi_penyusun.html", {"penyusun": penyusun})


# SPK
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_spk(request):
    dataspk = models.SPK.objects.all().order_by("-Tanggal")

    for j in dataspk:
        j.Tanggal = j.Tanggal.strftime('%Y-%m-%d')
        total_detail_spk = models.DetailSPK.objects.filter(NoSPK=j).values('KodeArtikel').annotate(total=Sum('Jumlah'))
        for detail_spk in total_detail_spk:
            kode_artikel = detail_spk['KodeArtikel']
            total_requested = detail_spk['total']
            
            total_processed = models.DetailSPPB.objects.filter(DetailSPK__NoSPK=j, DetailSPK__KodeArtikel=kode_artikel).aggregate(total=Sum('Jumlah'))['total'] or 0
            
            if total_processed < total_requested:
                is_lunas = False
                break
            

    return render(request, "produksi/view_spk.html", {"dataspk": dataspk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_spk(request):
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    if request.method == "GET":
        return render(request, "produksi/add_spk.html", {"data": dataartikel,'datadisplay':datadisplay})

    if request.method == "POST":
        nomor_spk = request.POST["nomor_spk"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        try:
            jenisspk = request.POST['jenisspk']
        except:
            messages.error(request, "Masukkan Jenis SPK")
            return redirect("add_spk")

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
                StatusAktif = 1
            )
            if jenisspk == 'spkartikel' : 
                StatusDisplay = 0
            else : 
                StatusDisplay = 1
            
            data_spk.StatusDisplay = StatusDisplay
            data_spk.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Surat Perintah Kerja. No SPK : {nomor_spk} Keterangan : {keterangan} Status Display : {StatusDisplay}",
            ).save()
            
            artikel_list = request.POST.getlist("artikel[]")
            jumlah_list = request.POST.getlist("quantity[]")
            no_spk = models.SPK.objects.get(NoSPK=nomor_spk)

            for produk, jumlah in zip(artikel_list, jumlah_list):
                # Pisahkan KodeArtikel dari jumlah dengan delimiter '/'
                if jenisspk == "spkartikel":
                    kode_artikel = models.Artikel.objects.get(KodeArtikel=produk)

                    # Simpan data ke dalam model DetailSPK
                    datadetailspk = models.DetailSPK(
                        NoSPK=no_spk, KodeArtikel=kode_artikel, Jumlah=jumlah
                    )
                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Detail Surat Perintah Kerja. No SPK : {no_spk.NoSPK} Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah}",
                    ).save()
                elif jenisspk == "spkdisplay":
                    kode_display = models.Display.objects.get(KodeDisplay = produk)

                    # Simpan data dalam model detailSPK
                    datadetailspk = models.DetailSPKDisplay(
                        NoSPK = no_spk, KodeDisplay = kode_display, Jumlah = jumlah
                    )
                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Detail Surat Perintah Kerja. No SPK : {no_spk.NoSPK} Kode Display : {kode_display.KodeDisplay} Jumlah : {jumlah}",
                    ).save()
                datadetailspk.save()

            return redirect("view_spk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def detail_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    datadisplay =models.Display.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    if dataspk.StatusDisplay == False:
        datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)
    else:
        datadetail = models.DetailSPKDisplay.objects.filter(NoSPK = dataspk.id)

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "produksi/detail_spk.html",
            {
                "data": dataartikel,
                "datadisplay" : datadisplay,
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
        statusaktif = request.POST['StatusAktif']

        spkbaru = models.SPK.objects.filter(NoSPK=nomor_spk)
        existspk = spkbaru.exists()
        print(dataspk)
        print(spkbaru)
        if existspk and dataspk != spkbaru.first():
            messages.error(request, "Nomor SPK sudah ada")
            return redirect("detail_spk", id=id)
        else:
            dataspk.NoSPK = nomor_spk
            dataspk.Tanggal = tanggall
            dataspk.Keterangan = keterangan
            dataspk.StatusAktif = statusaktif
            dataspk.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Surat Perintah Kerja. No SPK : {nomor_spk} Keterangan : {keterangan} Status Aktif : {statusaktif}",
            ).save()
        
        if dataspk.StatusDisplay == False:
            for detail, artikel_id, jumlah in zip(datadetail, artikel_list, jumlah_list):
                kode_artikel = models.Artikel.objects.get(KodeArtikel=artikel_id)
                detail.KodeArtikel = kode_artikel
                detail.Jumlah = jumlah
                detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Detail Surat Perintah Kerja. No SPK : {dataspk.NoSPK} Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah}",
                ).save()
            
            no_spk = models.SPK.objects.get(NoSPK=nomor_spk)

            for artikel_id, jumlah in zip(artikel_list[len(datadetail) :], jumlah_list[len(datadetail) :]):
                kode_artikel = models.Artikel.objects.get(KodeArtikel=artikel_id)
                new_detail = models.DetailSPK.objects.create(
                    NoSPK=no_spk,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                    KodeArtikel=kode_artikel,
                    Jumlah=jumlah,
                )

                new_detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail Surat Perintah Kerja. Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah}",
                ).save()

        else:
            for detail, artikel_id, jumlah in zip(datadetail, artikel_list, jumlah_list):
                kode_artikel = models.Display.objects.get(KodeDisplay=artikel_id)
                detail.KodeDisplay = kode_artikel
                detail.Jumlah = jumlah
                detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Detail Surat Perintah Kerja. No SPK : {dataspk.NoSPK} Kode Artikel : {kode_artikel.KodeDisplay} Jumlah : {jumlah}",
                ).save()

            no_spk = models.SPK.objects.get(NoSPK=nomor_spk)
            
            for artikel_id, jumlah in zip(artikel_list[len(datadetail) :], jumlah_list[len(datadetail) :]):
                kode_artikel = models.Display.objects.get(KodeDisplay=artikel_id)
                new_detail = models.DetailSPKDisplay.objects.create(
                    NoSPK=no_spk,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                    KodeDisplay=kode_artikel,
                    Jumlah=jumlah,
                )

                new_detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail Surat Perintah Kerja. Kode Display : {kode_artikel.KodeDisplay} Jumlah : {jumlah}",
                ).save()

        messages.success(request,'Data berhasil di update')
        return redirect("detail_spk", id=id)

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_spk(request, id):
    dataspk = models.SPK.objects.get(id=id)
    dataspk.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Surat Perintah Kerja. Nomor SPK : {dataspk.NoSPK} ",
    ).save()

    return redirect("view_spk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_detailspk(request, id):
    datadetailspk = models.DetailSPK.objects.get(IDDetailSPK=id)
    dataspk = models.SPK.objects.get(NoSPK=datadetailspk.NoSPK)
    datadetailspk.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Detail Surat Perintah Kerja. Nomor SPK : {dataspk.NoSPK} Artikel : {datadetailspk.KodeArtikel.KodeArtikel}",
    ).save()

    return redirect("detail_spk", id=dataspk.id)

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_detailspkdisplay(request, id):
    datadetailspk = models.DetailSPKDisplay.objects.get(IDDetailSPK=id)
    dataspk = models.SPK.objects.get(NoSPK=datadetailspk.NoSPK)
    datadetailspk.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Detail Surat Perintah Kerja. Nomor SPK : {dataspk.NoSPK} Kode Artikel : {datadetailspk.KodeDisplay.KodeDisplay}",
    ).save()

    return redirect("detail_spk", id=dataspk.id)

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def track_spk(request, id):
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
            DetailSPPBDisplay__DetailSPKDisplay__NoSPK=dataspk.id, Jenis="Mutasi"
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
            "produksi/trackingspk.html",
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


# SPPB   
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_sppb(request):
    datasppb = models.SPPB.objects.all().order_by("-Tanggal")
    for i in datasppb:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_sppb.html", {"datasppb": datasppb})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_sppb(request):
    databahan = models.Produk.objects.all()
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    purchaseorder = models.confirmationorder.objects.filter(StatusAktif = True)

    if request.method == "GET":
        return render(
            request,
            "produksi/add_sppb.html",
            {
                "bahan": databahan,
                "artikel": dataartikel,
                "display": datadisplay,
                "purchaseorder":purchaseorder
            },
        )

    if request.method == "POST":
        nomor_sppb = request.POST["nomor_sppb"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        
        displaylist = request.POST.getlist("detail_spkdisplay[]")
        jumlahdisplay = request.POST.getlist('quantitydisplay[]')
        confirmationorderdisplay = request.POST.getlist("purchaseorderdisplay")

        datasppb = models.SPPB.objects.filter(NoSPPB=nomor_sppb).exists()
        if datasppb:
            messages.error(request, "Nomor SPPB sudah ada")
            return redirect("add_sppb")
        else:
            artikel_list = request.POST.getlist("detail_spk[]")
            jumlah_list = request.POST.getlist("quantity[]")
            confirmationorderartikel = request.POST.getlist("purchaseorderartikel")

            bahan_list = request.POST.getlist("kode_bahan[]")
            jumlahbahan = request.POST.getlist("quantitybahan[]")
            confirmationorderbahan = request.POST.getlist("purchaseorderbahan")

            # Periksa apakah setidaknya satu item dari artikel atau display list memiliki data
            valid_bahan_list = any(bahan_list) and any(jumlahbahan)
            valid_artikel_list = any(artikel_list) and any(jumlah_list)
            valid_display_list = any(displaylist) and any(jumlahdisplay)

            if valid_artikel_list or valid_display_list or valid_bahan_list:

                data_sppb = models.SPPB(
                    NoSPPB=nomor_sppb, Tanggal=tanggal, Keterangan=keterangan
                ).save()
                messages.success(request, "Data berhasil disimpan")

                no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Keterangan : {no_sppb.Keterangan}",
                ).save()

                for bahan, jumlah, confirmationorder in zip(bahan_list, jumlahbahan, confirmationorderbahan):
                    if bahan == '' or jumlah == '':
                        continue

                    kode_bahan = models.Produk.objects.get(KodeProduk=bahan)
                    jumlah_bahan = jumlah

                    # Simpan data ke dalam model DetailSPK
                    datadetailspk = models.DetailSPPB(
                        NoSPPB=no_sppb, DetailBahan=kode_bahan, Jumlah=jumlah_bahan
                    )

                    if not confirmationorder == "":
                        datadetailspk.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                    datadetailspk.save()

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Bahan Baku : {kode_bahan.NamaProduk} Jumlah : {jumlah} CO : { datadetailspk.IDCO if datadetailspk.IDCO is not None  else None}",
                    ).save()

                for artikel, jumlah, confirmationorder in zip(artikel_list, jumlah_list,confirmationorderartikel):
                    if artikel == '' or jumlah == '':
                        continue

                    kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel)
                    jumlah_produk = jumlah

                    # Simpan data ke dalam model DetailSPK
                    datadetailspk = models.DetailSPPB(
                        NoSPPB=no_sppb, DetailSPK=kode_artikel, Jumlah=jumlah_produk
                    )

                    if not confirmationorder == "":
                        datadetailspk.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                    datadetailspk.save()

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah} CO : { datadetailspk.IDCO if datadetailspk.IDCO is not None  else None}",
                    ).save()

                for display,jumlah,confirmationorder in zip(displaylist,jumlahdisplay,confirmationorderdisplay):

                    if display == "" or jumlah == "":
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

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Display : {detailspkdisplayobj.KodeDisplay} Jumlah : {jumlah} CO : { datadetailspkdisplay.IDCO if datadetailspkdisplay.IDCO is not None  else None}",
                    ).save()

                return redirect("view_sppb")
            
            else:
                messages.error(request, "Masukkan Bahan, Artikel atau Display")
                return redirect("add_sppb")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def detail_sppb(request, id):
    databahan = models.Produk.objects.all()
    dataartikel = models.Artikel.objects.all()
    datadisplay = models.Display.objects.all()
    datadetailspk = models.DetailSPK.objects.all()
    datadetailspkdisplay = models.DetailSPKDisplay.objects.all()
    datasppb = models.SPPB.objects.get(id=id)
    datadetailsppbbahan = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id,DetailSPK = None,DetailSPKDisplay = None)
    datadetailsppbArtikel = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id,DetailSPKDisplay = None,DetailBahan = None)
    datadetailsppbdisplay = models.DetailSPPB.objects.filter(NoSPPB=datasppb.id,DetailSPK = None,DetailBahan = None)
    purchaseorderdata = models.confirmationorder.objects.filter(StatusAktif =True)

    if request.method == "GET":
        tanggal = datetime.strftime(datasppb.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "produksi/detail_sppb.html",
            {
                "bahan": databahan,
                "dataartikel": dataartikel,
                "datadisplay": datadisplay,
                "data": datadetailspk,
                "dataspkdisplay": datadetailspkdisplay,
                "datasppb": datasppb,
                "datadetailbahan" : datadetailsppbbahan,
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

        bahan_list = request.POST.getlist("kode_bahanawal[]")
        jumlahbahan = request.POST.getlist("quantitybahan[]")
        confirmationorderbahan = request.POST.getlist("purchaseorderbahan")

        artikel_list = request.POST.getlist("detail_spkawal[]")
        jumlah_list = request.POST.getlist("quantity[]")
        confirmationorderartikel = request.POST.getlist("purchaseorderartikel")

        display_list = request.POST.getlist("detail_spkdisplayawal[]")
        jumlahdisplay_list = request.POST.getlist('quantitydisplay[]')
        confirmationorderdisplay = request.POST.getlist("purchaseorderdisplay")

        artikel_baru = request.POST.getlist('detail_spk[]')
        jumlah_baru = request.POST.getlist('quantitybaru[]')
        purchaseorder_artikelbaru = request.POST.getlist('purchaseorderartikelbaru')

        display_baru = request.POST.getlist('detail_spkdisplay[]')
        jumlahdisplay_baru = request.POST.getlist('quantitydisplaybaru[]')
        purchaseorder_displaybaru = request.POST.getlist('purchaseorderdisplaybaru')

        bahan_baru = request.POST.getlist("kode_bahan[]")
        jumlahbahan_baru = request.POST.getlist("quantitybahanbaru[]")
        purchaseorder_bahanbaru = request.POST.getlist("purchaseorderbahanbaru")

        datasppbbaru = models.SPPB.objects.filter(NoSPPB=nomor_sppb)
        existsppb = datasppbbaru.exists()
        if existsppb and datasppb != datasppbbaru.first():
            messages.error(request, "Nomor SPPB sudah ada")
            return redirect("detail_sppb", id=id)
        else:
            datasppb.NoSPPB = nomor_sppb
            datasppb.Tanggal = tanggall
            datasppb.Keterangan = keterangan
            datasppb.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} Keterangan : {datasppb.Keterangan}",
            ).save()

        if datadetailsppbbahan:
            for detail, bahan, jumlah, confirmationorder in zip(datadetailsppbbahan,bahan_list, jumlahbahan, confirmationorderbahan):

                kode_bahan = models.Produk.objects.get(KodeProduk=bahan)

                detail.DetailBahan = kode_bahan
                detail.Jumlah = jumlah

                if not confirmationorder == "":
                    detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)
                    
                detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} Kode Bahan Baku: {kode_bahan.NamaProduk} Jumlah : {jumlah}",
                ).save()


        if datadetailsppbArtikel:
            for detail, artikel_id, jumlah, confirmationorder in zip(
                datadetailsppbArtikel, artikel_list, jumlah_list, confirmationorderartikel
            ):
                kode_artikel = models.DetailSPK.objects.get(IDDetailSPK=artikel_id)
                detail.DetailSPK = kode_artikel
                detail.Jumlah = jumlah

                if not confirmationorder == "":
                    detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah}",
                ).save()
                
        if datadetailsppbdisplay:
            for detail, artikel_id, jumlah, confirmationorder in zip(
                datadetailsppbdisplay, display_list, jumlahdisplay_list, confirmationorderdisplay
            ):
                kode_display = models.DetailSPKDisplay.objects.get(IDDetailSPK=artikel_id)
                detail.DetailSPKDisplay = kode_display
                detail.Jumlah = jumlah

                if not confirmationorder == "":
                    detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                detail.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} Kode Artikel : {kode_display.KodeDisplay} Jumlah : {jumlah}",
                ).save()

        no_sppb = models.SPPB.objects.get(NoSPPB=nomor_sppb)

        if bahan_baru:
            for bahan, jumlah, confirmationorder in zip(bahan_baru, jumlahbahan_baru, purchaseorder_bahanbaru):
                if bahan == '' or jumlah == '':
                    continue

                kode_bahan = models.Produk.objects.get(KodeProduk=bahan)
                jumlah_bahan = jumlah

                # Simpan data ke dalam model DetailSPK
                datadetailspk = models.DetailSPPB(
                    NoSPPB=no_sppb, DetailBahan=kode_bahan, Jumlah=jumlah_bahan
                )

                print(confirmationorder)

                if not confirmationorder == "":
                    datadetailspk.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                datadetailspk.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Bahan Baku : {kode_bahan.NamaProduk} Jumlah : {jumlah} CO : { datadetailspk.IDCO if datadetailspk.IDCO is not None  else None}",
                ).save()

        if artikel_baru:
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

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Artikel : {kode_artikel.KodeArtikel} Jumlah : {jumlah}",
                ).save()

        if display_baru:
            for display_id, jumlah, confirmationorder in zip(display_baru,jumlahdisplay_baru,purchaseorder_displaybaru):
                kode_display = models.DetailSPKDisplay.objects.get(IDDetailSPK = display_id)
                new_detail = models.DetailSPPB(
                    NoSPPB=no_sppb,  # Assuming NoSPK is the ForeignKey field to SPK in DetailSPK model
                    DetailSPKDisplay=kode_display,
                    Jumlah=jumlah
                    )
                
                if not confirmationorder == "":
                    new_detail.IDCO = models.confirmationorder.objects.get(pk=confirmationorder)

                new_detail.save()
                transaksiproduksiobj = models.TransaksiProduksi(
                        Tanggal = tanggall, Jumlah = jumlah, Jenis = "Mutasi", Keterangan = "Mutasi Display", Lokasi = models.Lokasi.objects.get(pk = 1), DetailSPPBDisplay = new_detail
                    
                    )
                transaksiproduksiobj.save()
                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {no_sppb.NoSPPB} Kode Display : {kode_display.KodeDisplay} Jumlah : {jumlah}",
                ).save()

        messages.success(request,"Data berhasil disimpan")
        return redirect("detail_sppb", id=id)
    
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_sppb(request, id):
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} ",
    ).save()

    return redirect("view_sppb")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_detailsppb(request, id):
    datadetailsppb = models.DetailSPPB.objects.get(IDDetailSPPB=id)
    datasppb = models.SPPB.objects.get(NoSPPB=datadetailsppb.NoSPPB)
    datadetailsppb.delete()

    if datadetailsppb.DetailSPK :
        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB} Artikel : {datadetailsppb.DetailSPK.KodeArtikel.KodeArtikel} ",
        ).save()
    elif datadetailsppb.DetailSPKDisplay:
        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB}  Display : {datadetailsppb.DetailSPKDisplay.KodeDisplay.KodeDisplay} ",
        ).save()
    else:
        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Detail Surat Perintah Pengiriman Barang. Nomor SPPB : {datasppb.NoSPPB}  Display : {datadetailsppb.DetailBahan.KodeProduk} ",
        ).save()

    return redirect("detail_sppb", id=datasppb.id)


#Transaksi Produksi
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_mutasi(request):
    dataproduksi = models.TransaksiProduksi.objects.filter(Jenis="Mutasi").order_by(
        "-Tanggal", "KodeArtikel"
    )
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_mutasi.html", {"dataproduksi": dataproduksi})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_produksi(request):
    dataproduksi = models.TransaksiProduksi.objects.filter(Jenis="Produksi").order_by(
        "-Tanggal", "KodeArtikel"
    )
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_produksi.html", {"dataproduksi": dataproduksi}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_mutasi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_lokasi = models.Lokasi.objects.all()
        data_spk = models.SPK.objects.filter(StatusAktif=True)


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
        tanggal = request.POST["tanggal"]
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")
        listdetail_spk = request.POST.getlist("detail_spk[]")

        for kode, jumlah, keterangan, detail_spk in zip(
            listkode_artikel, listjumlah, listketerangan, listdetail_spk
        ):
            try:
                artikelref = models.Artikel.objects.get(KodeArtikel=kode)
            except:
                messages.error(request, "Kode Artikel tidak ditemukan")
                return redirect("add_mutasi")
            
            try:
                detailspkref = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
            except:
                detailspkref = None

            data_produksi = models.TransaksiProduksi(
                KodeArtikel=artikelref,
                Lokasi=models.Lokasi.objects.get(IDLokasi=1),
                Tanggal=tanggal,
                Jumlah=jumlah,
                Keterangan=keterangan,
                Jenis="Mutasi",
                DetailSPK=detailspkref,
            ).save()
            messages.success(request, "Data berhasil disimpan")

            if detailspkref:
                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Transaksi Mutasi. Kode Artikel : {artikelref.KodeArtikel} Jumlah : {jumlah} No SPK : {detailspkref.NoSPK} Keterangan : {keterangan}",
                ).save()
            else:
                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Transaksi Mutasi. Kode Artikel : {artikelref.KodeArtikel} Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()

        return redirect("view_mutasi")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_mutasi(request, id):
    produksiobj = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    data_artikel = models.Artikel.objects.all()
    data_spk = models.SPK.objects.filter(StatusAktif=True)

    if produksiobj.DetailSPPBDisplay is  None:
        try:
            data_detailspk = models.DetailSPK.objects.filter(
            NoSPK=produksiobj.DetailSPK.NoSPK.id
        )
        except:
            data_detailspk = None
    else:
        data_detailspk = models.DetailSPKDisplay.objects.filter(NoSPK =produksiobj.DetailSPPBDisplay.DetailSPKDisplay.NoSPK)

    if request.method == "GET":
        tanggal = datetime.strftime(produksiobj.Tanggal, "%Y-%m-%d")
        return render(
            request,
            "produksi/update_mutasi.html",
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

        if detspkobj:
            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Transaksi Mutasi. Kode Artikel : {getartikel.KodeArtikel} Jumlah : {jumlah} No SPK : {detspkobj.NoSPK} Keterangan : {keterangan}",
            ).save()
        else:
            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Transaksi Mutasi. Kode Artikel : {getartikel.KodeArtikel} Jumlah : {jumlah}  Keterangan : {keterangan}",
            ).save()

        return redirect("view_mutasi")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_produksi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    messages.success(request, "Data Berhasil dihapus")

    return redirect("view_produksi")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_mutasi(request, id):
    dataproduksi = models.TransaksiProduksi.objects.get(idTransaksiProduksi=id)
    dataproduksi.delete()
    messages.success(request, "Data Berhasil dihapus")

    if dataproduksi.DetailSPK:
        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Transaksi Mutasi. Kode Artikel : {dataproduksi.KodeArtikel} Jumlah : {dataproduksi.Jumlah} No SPK : {dataproduksi.DetailSPK.NoSPK} Keterangan : {dataproduksi.Keterangan}",
        ).save()
    else:
        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Transaksi Mutasi. Kode Artikel : {dataproduksi.KodeArtikel} Jumlah : {dataproduksi.Jumlah} Keterangan : {dataproduksi.Keterangan}",
        ).save()

    return redirect("view_mutasi")


# Transaksi Gudang
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_gudang(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__gt=0).order_by(
        "-tanggal", "KodeProduk"
    )
    for i in datagudang:
        i.tanggal = i.tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_gudang.html", {"datagudang": datagudang})

@login_required  
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_gudangretur(request):
    datagudang = models.TransaksiGudang.objects.filter(jumlah__lt=0).order_by(
        "-tanggal", "KodeProduk"
    )
    for data in datagudang:
        data.retur = -data.jumlah
    for i in datagudang:
        i.tanggal = i.tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_gudangretur.html", {"datagudang": datagudang})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_gudang(request):
    if request.method == "GET":
        data_produk = models.Produk.objects.all()
        data_lokasi = models.Lokasi.objects.all()
        data_spk = models.SPK.objects.filter(StatusAktif=True)

        listproduk = [produk.NamaProduk for produk in data_produk]

        return render(
            request,
            "produksi/add_gudang.html",
            {
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi[:2],
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

        i = 1
        for produk, lokasi, jumlah, keterangan, detail in zip(
            listkode, listlokasi, listjumlah, listketerangan, listdetail
        ):
            nomorspk = request.POST[f"nomor_spk-{i}"]

            if nomorspk != '':
                spkobj = models.SPK.objects.get(NoSPK = nomorspk)
            produkref = models.Produk.objects.get(KodeProduk=produk)
            lokasiref = models.Lokasi.objects.get(IDLokasi=lokasi)

            data_gudang = models.TransaksiGudang(
                KodeProduk=produkref,
                Lokasi=lokasiref,
                tanggal=tanggal,
                jumlah=jumlah,
                keterangan=keterangan,
                KeteranganACC=False,
            )
            
            if detail != "":
                if spkobj.StatusDisplay == True:
                    try:
                        detailspkref = models.DetailSPKDisplay.objects.get(IDDetailSPK=detail)
                    except:
                        detailspkref = None
                    data_gudang.DetailSPKDisplay = detailspkref

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Transaksi Barang Masuk. Kode Produk : {produkref.KodeProduk} Jumlah : {jumlah} No SPK Display: {detailspkref.NoSPK} Kode Display : {detailspkref.KodeDisplay} Keterangan : {keterangan}",
                    ).save()
                    
                else:
                    try:
                        detailspkref = models.DetailSPK.objects.get(IDDetailSPK=detail)
                    except:
                        detailspkref = None

                    data_gudang.DetailSPK = detailspkref

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Create",
                        pesan=f"Transaksi Barang Masuk. Kode Produk : {produkref.KodeProduk} Jumlah : {jumlah} No SPK : {detailspkref.NoSPK} Kode Artikel : {detailspkref.KodeArtikel} Keterangan : {keterangan}",
                    ).save()
            else:
                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Transaksi Barang Masuk. Kode Produk : {produkref.KodeProduk} Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()

            i+=1
            data_gudang.save()
            messages.success(request, "Data berhasil ditambahkan")
                
        
        return redirect("view_gudang")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
                "nama_lokasi": data_lokasi[:2],
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

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Transaksi Barang Retur. Kode Produk : {produkref.KodeProduk} Jumlah : {jumlah} Keterangan : {keterangan}",
            ).save()

        return redirect("view_gudangretur")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_gudang(request, id):
    gudangobj = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    data_produk = models.Produk.objects.all()
    data_lokasi = models.Lokasi.objects.all()
    data_spk = models.SPK.objects.filter(StatusAktif=True)

    try:
        data_detailspk = models.DetailSPK.objects.filter(
            NoSPK=gudangobj.DetailSPK.NoSPK.id
        )
    except:
        data_detailspk = None

    try:
        data_detailspkdisplay = models.DetailSPKDisplay.objects.filter(
            NoSPK=gudangobj.DetailSPKDisplay.NoSPK.id
        )
    except:
        data_detailspkdisplay = None

    if request.method == "GET":
        tanggal = datetime.strftime(gudangobj.tanggal, "%Y-%m-%d")
        return render(
            request,
            "produksi/update_gudang.html",
            {
                "gudang": gudangobj,
                "tanggal": tanggal,
                "kode_produk": data_produk,
                "nama_lokasi": data_lokasi[:2],
                "data_spk": data_spk,
                "data_detailspk": data_detailspk,
                "data_detailspkdisplay": data_detailspkdisplay,
            },
        )

    elif request.method == "POST":
        kode_produk = request.POST["kode_produk"]
        lokasi = request.POST["nama_lokasi"]
        tanggal = request.POST["tanggal"]
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        getproduk = models.Produk.objects.get(KodeProduk=kode_produk)
        getlokasi = models.Lokasi.objects.get(IDLokasi=lokasi)

        gudangobj.KodeProduk = getproduk
        gudangobj.Lokasi = getlokasi
        gudangobj.tanggal = tanggal
        gudangobj.jumlah = jumlah
        gudangobj.keterangan = keterangan
        detail_spk = request.POST["detail_spk[]"]
        nomorspk = request.POST["nomor_spk"]

        try:
            detail_spk = request.POST["detail_spk[]"]
            nomorspk = request.POST["nomor_spk"]
            if detail_spk == "tot":
                gudangobj.DetailSPK = None
                gudangobj.DetailSPKDisplay = None

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Update",
                    pesan=f"Transaksi Barang Masuk. Kode Produk : {getproduk.KodeProduk} Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()

            try:
                spkobj = models.SPK.objects.get(NoSPK=nomorspk)
            except models.SPK.DoesNotExist:
                spkobj = None
                print("SPK object not found for NoSPK:", nomorspk)

            if spkobj.StatusDisplay==True:

                try:
                    detspkobj = models.DetailSPKDisplay.objects.get(IDDetailSPK=detail_spk)
                    print(detspkobj)
                    gudangobj.DetailSPKDisplay = detspkobj
                    gudangobj.DetailSPK = None

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Update",
                        pesan=f"Transaksi Barang Masuk. Kode Produk : {getproduk.KodeProduk} Jumlah : {jumlah} No SPK Display: {detspkobj.NoSPK} Kode Display : {detspkobj.KodeDisplay} Keterangan : {keterangan}",
                    ).save()
                except models.DetailSPKDisplay.DoesNotExist:
                    gudangobj.DetailSPKDisplay = None
                    print("DetailSPKDisplay object not found for IDDetailSPKDisplay:", detail_spk)
            else:
                try:
                    detspkobj = models.DetailSPK.objects.get(IDDetailSPK=detail_spk)
                    print(detspkobj)
                    gudangobj.DetailSPK = detspkobj
                    gudangobj.DetailSPKDisplay = None

                    models.transactionlog(
                        user="Produksi",
                        waktu=datetime.now(),
                        jenis="Update",
                        pesan=f"Transaksi Barang Masuk. Kode Produk : {getproduk.KodeProduk} Jumlah : {jumlah} No SPK : {detspkobj.NoSPK} Kode Artikel : {detspkobj.KodeArtikel} Keterangan : {keterangan}",
                    ).save()

                except models.DetailSPK.DoesNotExist:
                    gudangobj.DetailSPK = None
                    print("DetailSPK object not found for IDDetailSPK:", detail_spk)

        except:
            detspkobj = None

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Transaksi Barang Masuk. Kode Produk : {getproduk.KodeProduk} Jumlah : {jumlah} Keterangan : {keterangan}",
            ).save()

        gudangobj.save()
        messages.success(request, "Data berhasil diupdate")

        return redirect("view_gudang")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_gudangretur(request, id):
    gudangobj = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    data_produk = models.Produk.objects.all()
    data_lokasi = models.Lokasi.objects.filter(NamaLokasi__in=("WIP","FG"))

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
        try:
            getproduk = models.Produk.objects.get(KodeProduk=kode_produk)
        except:
            messages.error(request,f"Data bahan baku {kode_produk} tidak ditemukan")
            return redirect("update_gudangretur",id=id)
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

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Transaksi Barang Retur. Kode Produk : {getproduk.KodeProduk} Jumlah : {jumlah} Keterangan : {keterangan}",
        ).save()

        return redirect("view_gudangretur")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_gudang(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Transaksi Barang Masuk. Kode Produk : {datagudang.KodeProduk} Jumlah : {datagudang.jumlah} Keterangan : {datagudang.keterangan}",
    ).save()

    return redirect("view_gudang")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_gudangretur(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Transaksi Barang Retur. Kode Produk : {datagudang.KodeProduk} Jumlah : {-int(datagudang.jumlah)} Keterangan : {datagudang.keterangan}",
    ).save()

    return redirect("view_gudangretur")


# Rekapitulasi
def calculate_KSBB(produk,tanggal_mulai,tanggal_akhir):
    '''
    Perhitungan KSBB : 
    1. Jumlah Transaksi Gudang dalam rentang 1 tahun per produk 
    2. Jumlah Pemusnahan Bahan baku di produksi per bahan baku
    3. Jumlah konversi Bahan yang Bermutasi ke FG dalam bentuk kotak
    4. Jumlah Konversi Pemusnahan Kotak di area Produksi
    '''
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
    # Mencari data pemusnahan bahan baku 
    pemusnahanbahanbakuobj = models.PemusnahanBahanBaku.objects.filter(KodeBahanBaku = produk,Tanggal__range=(tanggal_mulai,tanggal_akhir))

    # print(dasdas)
    dataproduksi = models.TransaksiProduksi.objects.filter(
        KodeArtikel__id__in=penyusun_produk,
        Jenis="Mutasi",
        Tanggal__range=(tanggal_mulai, tanggal_akhir),
    )

    # Mencari data Bahan Display. Transaksi Produksi-->SPPBDisplay-->SPK-->FIlter TransaksiGudang by SPK
    datadisplay = datagudang.filter(DetailSPKDisplay__NoSPK__StatusDisplay =1).values_list('DetailSPKDisplay__NoSPK',flat=True).distinct()
    datadisplay2 = models.TransaksiProduksi.objects.filter(Jenis ="Mutasi",Tanggal__range = (tanggal_mulai,tanggal_akhir)).exclude(DetailSPPBDisplay = None)
    datadisplaykeluar = datadisplay2.filter(DetailSPPBDisplay__DetailSPKDisplay__NoSPK__in = datadisplay)
    
    datadisplaykeluar=datadisplaykeluar.aggregate(total =Sum('Jumlah'))

    # print(asdas)
    listartikelmaster = []

    '''Masukan Logika : 
    Jumlah Barang yang di request pakai kode SPK diasumsikan langsung keluar walaupun belum ada Transaksi Keluar pada SPPB
    Pertimbangakan tidak menggunakan SPPB karena bisa mempengaruhi besar nilai penyesuaian apabila menunggu hasil SPPB karena penyesuaian melihat STOK KSBB REAL. Stok Display berkurang secara dinamis apabila menggunakan SPPB 
    contoh : Total request ke gudang 10 MDF pada SPK untuk produksi 10 Display. Ketika ada pengiriman 5 Unit maka pada KSBB total untuk display 10 Masuk, keluar 5 Maka masih sisa 5 Lembar. Apabila dikemudian hari ada penyesuaian maka yang dihitung adalah menggunakan penyesuaian dengan sisa 5 lembar MDF masih dalam produksi Hal ini akan mempengaruhi besar kecilnya penyesuaian dikemudian hari.
    '''

    ''' PENYESUAIAN SECTION '''
    '''
    Data Models
    Artikel :{
    tanggal1 : 0.033,
    tanggal2 : 0.0xx 
    }
    Output datamodelskonversimaster:
    {1: {datetime.date(2024, 1, 1): 0.01357, datetime.date(2024, 2, 1): 0.5}}
    '''
    datamodelskonversimaster = {}
    for artikel in penyusun_produk:
        artikelmaster = models.Artikel.objects.get(id = artikel)

        konversi = models.KonversiMaster.objects.filter(
            KodePenyusun__KodeArtikel=artikel, KodePenyusun__KodeProduk=produk
        ).order_by('KodePenyusun__versi')

        
        tanggalversi = konversi.values_list('KodePenyusun__versi',flat=True).distinct()
        listkonversi = []
        if konversi.exists():
            dummy = {}
            for tanggal in tanggalversi:
                print(tanggal,tanggalversi,konversi)
                datakonversi = konversi.filter(KodePenyusun__versi = tanggal)
                print(datakonversi)
                kuantitas = datakonversi.aggregate(total = Sum('Allowance'))
                print(kuantitas)
                listkonversi.append(kuantitas['total'])
                dummy[tanggal] = kuantitas['total']
            datamodelskonversimaster[artikel] = {'konversi':dummy,'penyesuaian':{}}

        artikelmaster.listkonversi = listkonversi
        artikelmaster.tanggalversi = tanggalversi

        # Data Penyesuaian 
        penyesuaianobj  = models.Penyesuaian.objects.filter(KodePenyusun__KodeArtikel = artikel, TanggalMulai__range = (tanggal_mulai,tanggal_akhir))
        # print(penyesuaianobj)
        if penyesuaianobj.exists:
            dummy ={}
            for penyesuaian in penyesuaianobj:
                dummy[penyesuaian.TanggalMulai] = penyesuaian.konversi
            datamodelskonversimaster[artikel]['penyesuaian'] = dummy
        penyesuaiandataperartikel = [i.konversi for i in penyesuaianobj]
        tanggalpenyesuaianperartikel = [i.TanggalMulai for i in penyesuaianobj]

        artikelmaster.listpenyesuaian = penyesuaiandataperartikel
        artikelmaster.tanggalpenyesuaian =tanggalpenyesuaianperartikel
        listartikelmaster.append(artikelmaster)

        # print(asdas)
        
    ''' TANGGAL SECTION '''
    tanggalmasuk = datagudang.values_list("tanggal", flat=True)
    tanggalkeluar = dataproduksi.values_list("Tanggal", flat=True)
    tanggalpemusnahan = pemusnahanobj.values_list("Tanggal", flat=True)
    tanggalpemusnahanbahanbaku = pemusnahanbahanbakuobj.values_list('Tanggal',flat=True)
    # Belum Mempertimbangkan SPK Display

    '''BELUM MEMPERTIMBANGKAN KELUAR DISPLAY'''

    listtanggal = sorted(
        list(set(tanggalmasuk.union(tanggalkeluar).union(tanggalpemusnahan).union(tanggalpemusnahanbahanbaku)))
    )

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
        masukdisplay = 0
        datamasuk = datagudang.filter(tanggal=i)

        for k in datamasuk:
            masuk += k.jumlah
            print(k.DetailSPKDisplay != None)
            if k.DetailSPKDisplay != None and k.DetailSPKDisplay.NoSPK.StatusDisplay == True:
                masukdisplay +=k.jumlah
                print(masukdisplay)

        sisa  += masuk
        
        # Data Keluar
        data['Masuk'] = masuk
        datakeluar = dataproduksi.filter(Tanggal = i)
        datapemusnahan = pemusnahanobj.filter(Tanggal = i)
        datapemusnahanbahanbaku = pemusnahanbahanbakuobj.filter(Tanggal = i)

        artikelkeluar = datakeluar.values_list('KodeArtikel',flat=True).distinct()
        artikelpemusnahan = datapemusnahan.values_list('KodeArtikel',flat=True).distinct()
        # '''Belum Mempertimbangkan keluar Display''' DONE
        if masukdisplay != 0:
            datamodelskeluar.append(masukdisplay)
            sisa -=masukdisplay
                # if display.DetailSPPBDisplay != None:

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

            konversiterdekat= round(konversiterdekat,5)
            datamodelskonversi.append(konversiterdekat)
            datamodelskeluar.append(konversiterdekat*total['total'])
            datamodelsartikel.append(artikelkeluarobj)
            datamodelsperkotak.append(total['total'])
            sisa -= konversiterdekat*total['total']
            sisa = round(sisa, 2)
            datamodelssisa.append(sisa)

        for j in artikelpemusnahan:
            artikelkeluarobj = models.Artikel.objects.get(id = j)
            total = datapemusnahan.filter(KodeArtikel__id = j).aggregate(total=Sum('Jumlah'))
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

            konversiterdekat= round(konversiterdekat,5)
            datamodelskonversi.append(konversiterdekat)
            datamodelskeluar.append(konversiterdekat*total['total'])
            datamodelsartikel.append(artikelkeluarobj)
            datamodelsperkotak.append(total['total'])
            sisa -= konversiterdekat*total['total']
            sisa = round(sisa, 2)
            datamodelssisa.append(sisa)

        # Pemusnahan Bahan Baku
        if datapemusnahanbahanbaku.exists():
            # Mengagregat Jumlah Bahan Baku rusak
            totalbahanbakurusak = datapemusnahanbahanbaku.aggregate(total=Sum('Jumlah'))

            sisa -= totalbahanbakurusak['total']
            datamodelssisa.append(sisa)
            datamodelskeluar.append(totalbahanbakurusak['total'])
            # print(asdasd)

        if not datamodelssisa :
            sisa = round(sisa, 2)
            datamodelssisa.append(sisa)

        data['Sisa'] = datamodelssisa
        listdata.append(data)

    return listdata,saldoawal

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_ksbb3(request):
    kodeproduk = models.Produk.objects.all()
    sekarang = datetime.now().year
    
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbb.html", {"kodeprodukobj": kodeproduk, "sekarang": sekarang})
    else:
        try:
            produk = models.Produk.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except models.Produk.DoesNotExist:
            messages.error(request, "Data Produk tidak ditemukan")
            return redirect("view_ksbb3")
        
        if "periode" in request.GET and request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            tahun = sekarang

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        listdata, saldoawal = calculate_KSBB(produk, tanggal_mulai, tanggal_akhir)

        print(tahun)

        return render(request, "produksi/view_ksbb.html", {
            'data': listdata,
            'saldo': saldoawal,
            'kodebarang': request.GET["kodebarang"],
            "nama": nama,
            "satuan": satuan,
            'kodeprodukobj': kodeproduk,
            'tahun': tahun
        })


@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
    # Transaksi Pemusnahan Bahan Baku
    datapemusnahanbahanbaku  =models.PemusnahanBahanBaku.objects.filter(Tanggal = tanggal,KodeBahanBaku = id)
    print(datapemusnahanbahanbaku)
    return render(
        request,
        "produksi/view_detailksbb.html",
        {
            "datagudang": datagudang,
            "dataproduksi": dataproduksi,
            "datapemusnahan": datapemusnahan,
            'datapemusnahanbahanbaku' : datapemusnahanbahanbaku
        },
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

        print(tanggal_mulai)
        print(tanggal_akhir)

        lokasi = request.GET['lokasi']
        lokasiobj = models.Lokasi.objects.get(NamaLokasi = lokasi)

        getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1)

        if not getbahanbakuutama :
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("view_ksbj")
        
        data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id,Jenis = "Mutasi")
        datamasuk = models.TransaksiGudang.objects.filter(DetailSPK__KodeArtikel = artikel.id,tanggal__range=(tanggal_mulai, tanggal_akhir))
        listtanggalmasuk = datamasuk.values_list('tanggal',flat=True).distinct()

        listdata = []
        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%Y-%m-%d")

            except models.SaldoAwalArtikel.DoesNotExist :
                saldo = 0
                saldoawal = None
                saldoawalobj ={'Tanggal' : 'Belum ada Data','saldo' : saldo}

            tanggallist = (data.filter(Tanggal__range=(tanggal_mulai, tanggal_akhir)).values_list("Tanggal", flat=True).distinct())
            saldoawal = saldo
            tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk)))))

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
                filtertanggaltransaksigudang = datamasuk.filter(tanggal=i)

                jumlahmutasi =  filtertanggal.filter(Jenis ="Mutasi").aggregate(total = Sum('Jumlah'))['total']
                jumlahmasuk = filtertanggaltransaksigudang.aggregate(total = Sum('jumlah'))['total']

                if jumlahmutasi is None:
                    jumlahmutasi = 0
                if jumlahmasuk is None :
                    jumlahmasuk = 0

                # Cari data penyusun sesuai tanggal 
                penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id,Status = 1,versi__lte = i).order_by('-versi').first()

                if not penyusunfiltertanggal:
                    penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id, Status = 1, versi__gte = i).order_by('versi').first()

                konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)
                try:
                    masukpcs = round(jumlahmasuk/((konversimasterobj.Allowance)))
                except:
                    masukpcs = round(0)
                    messages.error(request,'Data allowance belum di set')
                saldoawal = saldoawal - jumlahmutasi + masukpcs

                datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                datamodels['Masuklembar'] = jumlahmasuk
                datamodels['Masukkonversi'] = masukpcs
                datamodels['Sisa'] = saldoawal
                datamodels['Hasil'] = jumlahmutasi
                datamodels['SPK'] = filtertanggal.filter(Jenis = 'Mutasi')
                datamodels["Kodeproduk"] = penyusunfiltertanggal

                # Cari data penyesuaian

                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(i),)
                listdata.append(datamodels)

            print(listdata)

            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "dataartikel": dataartikel,
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


            tanggalmutasi = data.filter(Jenis = 'Mutasi',Tanggal__range=(tanggal_mulai,tanggal_akhir)).values_list('Tanggal',flat=True).distinct()
            sppb = models.DetailSPPB.objects.filter(DetailSPK__KodeArtikel__KodeArtikel = kodeartikel, NoSPPB__Tanggal__range = (tanggal_mulai,tanggal_akhir))
            tanggalsppb = sppb.values_list('NoSPPB__Tanggal',flat=True).distinct()
            tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb))))

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


                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )

                datamodels ['Tanggal'] = i.strftime('%Y-%m-%d')
                datamodels ['Penyerahanwip'] = totalpenyerahanwip
                datamodels['DetailSPPB'] = detailsppbjobj
                datamodels['Sisa'] = saldoawal

                listdata.append(datamodels)

            print(listdata)
            
            return render(
                request,
                "produksi/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "dataartikel": dataartikel,
                    "lokasi": "FG",
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                },
            )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

    return render(request, "produksi/rekap_barang.html", {'data':dataproduk , 'tanggal_akhir':tanggal_akhir})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_rekaprusak(request):

    tanggal_akhir = request.GET.get("periode")
    
    sekarang = datetime.now()
    tahun = sekarang.year

    tanggal_mulai = datetime(year=tahun, month=1, day=1)

    lokasi = request.GET.get("lokasi")
    if lokasi:
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
    else:
        lokasiobj = models.Lokasi.objects.get(IDLokasi=1)
        
    tanggal_mulai = datetime(year=tahun, month=1, day=1)

    if tanggal_akhir:

        databarang = models.PemusnahanBahanBaku.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, tanggal_akhir)).values('KodeBahanBaku','KodeBahanBaku__NamaProduk','KodeBahanBaku__unit','KodeBahanBaku__keteranganProduksi').annotate(kuantitas=Sum('Jumlah'))
        dataartikel = models.PemusnahanArtikel.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, tanggal_akhir)).values('KodeArtikel__KodeArtikel','KodeArtikel__keterangan').annotate(kuantitas=Sum('Jumlah'))

    else:
        databarang = models.PemusnahanBahanBaku.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, sekarang)).values('KodeBahanBaku','KodeBahanBaku__NamaProduk','KodeBahanBaku__unit','KodeBahanBaku__keteranganProduksi').annotate(kuantitas=Sum('Jumlah'))
        dataartikel = models.PemusnahanArtikel.objects.filter(lokasi=lokasiobj,Tanggal__range=(tanggal_mulai, sekarang)).values('KodeArtikel__KodeArtikel','KodeArtikel__keterangan').annotate(kuantitas=Sum('Jumlah'))

    return render(request, "produksi/rekap_rusak.html", {"databarang": databarang, "dataartikel": dataartikel, "lokasi":lokasi,'tanggal_akhir':tanggal_akhir})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

            print(artikel)
            
            dataartikel = []
            getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1)

            if not getbahanbakuutama :
                messages.error(request, ("Bahan Baku",artikel.KodeArtikel,"belum di set"))
                continue

            data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id,Jenis = "Mutasi")
            datamasuk = models.TransaksiGudang.objects.filter(DetailSPK__KodeArtikel = artikel.id,tanggal__range=(tanggal_mulai, tanggal_akhir))
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
                    data = data.filter(Lokasi=lokasi.IDLokasi)
                    try:
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
                        tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk.union(listtanggalsaldo))))))
                    else:
                        tanggallist = sorted(list(set((tanggallist.union(listtanggalmasuk)))))

                    for i in tanggallist:
                        datamodels = {
                            "Tanggal" : None,
                            "Sisa" : None
                        }

                        filtertanggal = data.filter(Tanggal=i)
                        filtertanggaltransaksigudang = datamasuk.filter(tanggal=i)

                        jumlahmutasi =  filtertanggal.filter(Jenis ="Mutasi").aggregate(total = Sum('Jumlah'))['total']
                        jumlahmasuk = filtertanggaltransaksigudang.aggregate(total = Sum('jumlah'))['total']

                        if jumlahmutasi is None:
                            jumlahmutasi = 0
                        if jumlahmasuk is None :
                            jumlahmasuk = 0

                        # Cari data penyusun sesuai tanggal 
                        penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id,Status = 1,versi__lte = i).order_by('-versi').first()

                        if not penyusunfiltertanggal:
                            penyusunfiltertanggal = models.Penyusun.objects.filter(KodeArtikel = artikel.id, Status = 1, versi__gte = i).order_by('versi').first()

                        konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)
                        try:
                            masukpcs = round(jumlahmasuk/((konversimasterobj.Allowance)))
                        except:
                            masukpcs = 0
                            messages.error(request,"Data allowance belum di setting")
                        saldoawal = saldoawal - jumlahmutasi + masukpcs

                        datamodels['Tanggal'] = i.strftime("%Y-%m-%d")
                        datamodels['Sisa'] = saldoawal

                        listdata.append(datamodels)

                else:
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
                    tanggallist = sorted(list(set(tanggalmutasi.union(tanggalsppb))))
                    saldoawal = saldo

                    for i in tanggallist:
                        datamodels = {
                            "Tanggal" : None,
                            "Sisa" : None
                        }

                        penyerahanwip = models.TransaksiProduksi.objects.filter(Tanggal = i, KodeArtikel__KodeArtikel = artikel.KodeArtikel, Jenis = "Mutasi", Lokasi__NamaLokasi = "WIP" )
                        detailsppbjobj = sppb.filter(NoSPPB__Tanggal = i)

                        totalpenyerahanwip = penyerahanwip.aggregate(total=Sum('Jumlah'))['total']
                        totalkeluar = detailsppbjobj.aggregate(total=Sum('Jumlah'))['total']
                        
                        if not totalpenyerahanwip:
                            totalpenyerahanwip = 0
                        if not totalkeluar :
                            totalkeluar = 0

                        saldoawal += totalpenyerahanwip - totalkeluar

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
                    df_resampled = df.resample('M', on='Tanggal').last().fillna({'Sisa': 0}).reset_index()

                    # Creating a new DataFrame with all months from 1 to 12
                    all_months = pd.date_range(start=tanggal_mulai, end=tanggal_akhir, freq='M')
                    df_all_months = pd.DataFrame({'Tanggal': all_months})

                    # Merging the resampled data with all months
                    result_df = pd.merge(df_all_months, df_resampled, on='Tanggal', how='left').fillna({'Sisa': 0})

                    # Getting the data for all months
                    result_data = result_df.to_dict('records')
                
                    dataartikel.append(result_data)
            
            if len(dataartikel) == 1:
                pass
            else:
                item3 = [{'Tanggal': d1['Tanggal'], 'Sisa': d1['Sisa'] + d2['Sisa']} for d1, d2 in zip(dataartikel[1], dataartikel[2])]
                
                dataartikel.append(item3)

                datarekap.append(dataartikel)

        return render(request, "produksi/rekap_produksi.html", {'artikel':artikelobj, 'data':datarekap, 'tahun':tahun })


# Pemusnahan Artikel
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_pemusnahan(request):
    dataproduksi = models.PemusnahanArtikel.objects.all().order_by("-Tanggal")
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_pemusnahan.html", {"dataproduksi": dataproduksi}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_pemusnahan(request):
    dataartikel = models.Artikel.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_pemusnahan.html",
            {"nama_lokasi": datalokasi[:2], "dataartikel": dataartikel},
        )
    else:

        kodeartikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Kode Artikel tidak ditemukan")
            return redirect("add_pemusnahan")

        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.PemusnahanArtikel(
            Tanggal=tanggal, Jumlah=jumlah, KodeArtikel=artikelobj, lokasi=lokasiobj
        )
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Pemusnahan Artikel. Kode Artikel : {artikelobj.KodeArtikel} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()
        
        return redirect("view_pemusnahan")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_pemusnahan(request, id):
    dataartikel = models.Artikel.objects.all()
    dataobj = models.PemusnahanArtikel.objects.get(IDPemusnahanArtikel=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_pemusnahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj[:2], "dataartikel": dataartikel},
        )

    else:
        kodeartikel = request.POST["artikel"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Kode Artikel tidak ditemukan")
            return redirect("update_pemusnahan" ,id=id)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.KodeArtikel = artikelobj
        dataobj.lokasi = lokasiobj

        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Pemusnahan Artikel. Kode Artikel : {artikelobj.KodeArtikel} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()

        return redirect("view_pemusnahan")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_pemusnahan(request, id):
    dataobj = models.PemusnahanArtikel.objects.get(IDPemusnahanArtikel=id)
    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Pemusnahan Artikel. Kode Artikel : {dataobj.KodeArtikel.KodeArtikel} Jumlah : {dataobj.Jumlah} Lokasi : {dataobj.lokasi.NamaLokasi}",
    ).save()

    return redirect(view_pemusnahan)


# Pemusnahan Barang
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_pemusnahanbarang(request):
    dataproduksi = models.PemusnahanBahanBaku.objects.filter(lokasi__NamaLokasi__in=("WIP","FG")).order_by("-Tanggal")
    for i in dataproduksi:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_pemusnahanbarang.html", {"dataproduksi": dataproduksi}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_pemusnahanbarang(request):
    databarang = models.Produk.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_pemusnahanbarang.html",
            {"nama_lokasi": datalokasi[:2], "databarang": databarang},
        )
    else:
        print(request.POST)
        # Get object
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = float(request.POST["jumlah"])
        tanggal = request.POST["tanggal"]
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        try:
            produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        except:
            messages.error(request, "Kode Bahan Baku tidak ditemukan")
            return redirect("add_pemusnahanbarang")
        
        pemusnahanobj = models.PemusnahanBahanBaku(
            Tanggal=tanggal, Jumlah=jumlah, KodeBahanBaku=produkobj, lokasi=lokasiobj
        )
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Pemusnahan Bahan Baku. Kode Bahan Baku : {produkobj.KodeProduk} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()
        messages.success(request, "Data berhasil disimpan")
        return redirect("view_pemusnahanbarang")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_pemusnahanbarang(request, id):
    databarang = models.Produk.objects.all()
    dataobj = models.PemusnahanBahanBaku.objects.get(IDPemusnahanBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "produksi/update_pemusnahanbarang.html",
            {"data": dataobj, "nama_lokasi": lokasiobj[:2], 'dataproduk':databarang},
        )

    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        tanggal = request.POST["tanggal"]
        try:
            produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        except:
            messages.error(request, "Kode Bahan Baku tidak ditemukan")
            return redirect("update_pemusnahanbarang",id=id)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.KodeBahanBaku = produkobj
        dataobj.lokasi = lokasiobj

        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Pemusnahan Bahan Baku. Kode Bahan Baku : {produkobj.KodeProduk} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()
        messages.success(request,'Data berhasil diupdate')
        return redirect("view_pemusnahanbarang")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_pemusnahanbarang(request, id):
    dataobj = models.PemusnahanBahanBaku.objects.get(IDPemusnahanBahanBaku=id)

    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Pemusnahan Bahan Baku. Kode Bahan Baku : {dataobj.KodeBahanBaku.KodeProduk} Jumlah : {dataobj.Jumlah} Lokasi : {dataobj.lokasi.NamaLokasi}",
    ).save()

    return redirect(view_pemusnahanbarang)


# Penyesuaian
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def penyesuaian(request):
    datapenyesuaian = models.Penyesuaian.objects.all()
    return render(
        request, "produksi/view_penyesuaian.html", {"datapenyesuaian": datapenyesuaian}
    )
    
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
        tanggalminus = request.POST['tanggalminus']
        
        listkodepenyusun = request.POST.getlist("penyusun")
        listkuantitas = request.POST.getlist("kuantitas")

        for penyusun,kuantitas in zip(listkodepenyusun,listkuantitas):

            penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=penyusun)
            print(penyusunobj)
            penyesuaianobj = models.Penyesuaian(
                TanggalMulai=tanggalmulai,
                TanggalMinus = tanggalminus,

                KodePenyusun=penyusunobj,
                konversi = kuantitas

            )
            penyesuaianobj.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Penyesuaian. Kode Penyusun : {penyusunobj.KodeProduk} Tanggal Mulai : {tanggalmulai} Tanggal Minus : {tanggalminus} Konversi : {kuantitas} ",
            ).save()

        return redirect("view_penyesuaian")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_penyesuaian(request, id):
    
    dataartikel = models.Artikel.objects.all()

    datapenyesuaianobj = models.Penyesuaian.objects.get(pk = id)
    datapenyesuaianobj.TanggalMulai = datapenyesuaianobj.TanggalMulai.strftime('%Y-%m-%d')
    datapenyesuaianobj.TanggalMinus = datapenyesuaianobj.TanggalMinus.strftime('%Y-%m-%d')

    if request.method == "GET":
        return render(
            request,
            "produksi/update_penyesuaian.html",
            {"dataobj": datapenyesuaianobj, "Artikel": dataartikel},
        )
    else:
        
        tanggalmulai = request.POST["tanggalmulai"]
        tanggalminus = request.POST['tanggalminus']
        penyusun = request.POST["penyusun"]
        idpenyesuaian = request.POST['idpenyesuaian']
        kuantitas = request.POST['kuantitas']

        penyesuaianobj = models.Penyesuaian.objects.get(
            IDPenyesuaian=idpenyesuaian
        )
        penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=penyusun)
        penyesuaianobj.TanggalMinus = tanggalminus
        penyesuaianobj.TanggalMulai = tanggalmulai
        penyesuaianobj.KodePenyusun = penyusunobj
        penyesuaianobj.konversi = kuantitas
        penyesuaianobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Penyesuaian. Kode Penyusun : {datapenyesuaianobj.KodePenyusun.KodeProduk} Tanggal Mulai : {datapenyesuaianobj.TanggalMulai} Tanggal Minus : {datapenyesuaianobj.TanggalMinus} Konversi : {kuantitas} ",
        ).save()
        messages.success(request,"Data berhasil disimpan")
        return redirect("view_penyesuaian")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_penyesuaian(request, id):
    datapenyesuaianobj = models.Penyesuaian.objects.get(IDPenyesuaian=id)
    datapenyesuaianobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Penyesuaian. Kode Penyusun : {datapenyesuaianobj.KodePenyusun.KodeProduk} Tanggal Mulai : {datapenyesuaianobj.TanggalMulai} Tanggal Minus : {datapenyesuaianobj.TanggalMinus} Konversi : {datapenyesuaianobj.konversi} ",
    ).save()

    return redirect("view_penyesuaian")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

        listdata,saldoawal = calculate_KSBB(produk,tanggal_mulai,tanggal_akhir)
        # Perhitungan penyesuaian\
        # print(listdata)
        # print('\n',sum(listdata[-1]['Sisa']))
        # print(asdas)
        

        datasisaminus = 0
        datajumlah = 0
        dataajumlahartikel = {}
        datakonversiartikel = {}
        # print(data)

        firstindex = True

        listartikel = models.Penyusun.objects.filter(KodeProduk = produk).values_list("KodeArtikel__KodeArtikel",flat=True).distinct()
        # Mendapatkan data minus pertama
        sisa_minus_pertama = None
        tanggalminus = None
        lanjut = True
        datakuantitasperhitungan = {
            'saldodata': 0,
            'saldofisik':None,
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
      
        dataproduksi = models.TransaksiProduksi.objects.filter(Tanggal__range=(tanggal_mulai,tanggalminus),Jenis = 'Mutasi',KodeArtikel__KodeArtikel__in=listartikel)

        totaljumlahkotakperartikel = dataproduksi.values('KodeArtikel__KodeArtikel').annotate(total=Sum('Jumlah'))

        
        '''Coba V2'''
        sumproduct = 0
        jumlahkeluar = 0
        jumlahxkonversidictionary = {}
        datapenyesuaian = models.Penyesuaian.objects.filter(KodePenyusun__KodeProduk = produk).values_list('TanggalMinus',flat=True).distinct()
        print(datapenyesuaian)

        for item in listdata:
            tanggal = item['Tanggal']

            datetimetanggal = datetime.strptime(tanggal,"%Y-%m-%d")
            datetimetanggalminus = datetime.strptime(tanggalminus,"%Y-%m-%d")
            if datapenyesuaian:
                datetimepenyesuaian = str(datapenyesuaian[0])
                datetimepenyesuaian = datetime.strptime(datetimepenyesuaian,"%Y-%m-%d")
                

                
                if datetimetanggal > datetimetanggalminus:
                    break
                if datetimetanggal <= datetimepenyesuaian:
                    print(datetimetanggal, datetimepenyesuaian)
                    continue
                else :
                    if item['Artikel']:
                        for artikel,jumlah,konversi in zip(item['Artikel'],item['Perkotak'],item['Konversi']):
                            sumproduct += jumlah * konversi
                            if artikel in jumlahxkonversidictionary:
                                jumlahxkonversidictionary[artikel]['jumlahxkonversi'] += jumlah * konversi
                                jumlahxkonversidictionary[artikel]['jumlah'] += jumlah 
                            else:
                                jumlahxkonversidictionary[artikel] = {'jumlahxkonversi': jumlah*konversi,'jumlah':jumlah}
                    jumlahkeluar += sum(item['Keluar'])
            else:

                if datetimetanggal > datetimetanggalminus:
                    break
                if item['Artikel']:
                    for artikel,jumlah,konversi in zip(item['Artikel'],item['Perkotak'],item['Konversi']):
                        sumproduct += jumlah * konversi
                        if artikel in jumlahxkonversidictionary:
                            jumlahxkonversidictionary[artikel]['jumlahxkonversi'] += jumlah * konversi
                            jumlahxkonversidictionary[artikel]['jumlah'] += jumlah 
                        else:
                            jumlahxkonversidictionary[artikel] = {'jumlahxkonversi': jumlah*konversi,'jumlah':jumlah}
                jumlahkeluar += sum(item['Keluar'])
        

            
        
        saldodata = datasisaminus
        datakuantitasperhitungan["datakeluar"] = jumlahkeluar
        datakuantitasperhitungan["saldodata"] = saldodata
        datakuantitasperhitungan['Tanggalminus'] = tanggalminus
        print(datasisaminus)
        # print(adasd)
        try:
            dataaktual = int(request.GET["jumlah"])
        except Exception:
            return render(
            request,
            "produksi/newkalkulator_penyesuaian.html",
            {
                "kodebarang": request.GET["kodebarang"],
                "nama": nama,
                "satuan": satuan,
                "data": listdata,
                "saldo": saldoawal,
                "tahun": tahun,
                "datakuantitas" : datakuantitasperhitungan

            },
        )
        datakuantitasperhitungan["saldofisik"] = dataaktual
        saldoaktual = dataaktual
        keluarpenyesuaian = jumlahkeluar -  (saldoaktual - saldodata)
        datakonversiakhir = {}
        for key,value in jumlahxkonversidictionary.items():
            try:
                jumlahpenyesuaian =  keluarpenyesuaian/value['jumlah']
                productpersumproduct = value['jumlahxkonversi'] / sumproduct
                konversiakhir = jumlahpenyesuaian*productpersumproduct
                print(f'Artikel : {key} Jumlah Penyesuaian : {jumlahpenyesuaian} Sumproductperproduct : {productpersumproduct}')
            except ZeroDivisionError:
                jumlahxkonversidictionary[key].delete()
            datakonversiakhir[key] = {'jumlah': value['jumlah'],'konversiakhir':round(konversiakhir,6)}
        
        print(f'Keluar Penyesuaian : {keluarpenyesuaian} Jumlah Keluar : {jumlahkeluar} Saldo Aktual : {saldoaktual} Saldo Data : {saldodata}')
        


        # print(sumproduct)
        # print(saldodata)
        # print(jumlahkeluar)
        # print(dataproduksi)
        # print('\n',listdata)
        # print('\njumlahxkonversi : ',jumlahxkonversidictionary)
        # print('\ntotaljumlahkotakperartikel :',totaljumlahkotakperartikel)
        # print(asdas)

        
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
                "dataaktual" : dataaktual,
                "jumlahartikel": dataajumlahartikel,
                "konversiawal": datakonversiartikel,
                "datakuantitas" : datakuantitasperhitungan,
                "konversiakhirfix" : datakonversiakhir
            },
        )


# Saldo Awal Bahan Baku
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_saldobahan(request):
    dataproduk = models.SaldoAwalBahanBaku.objects.filter(IDLokasi__NamaLokasi__in=("WIP","FG")).order_by("-Tanggal")
    for i in dataproduk:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_saldobahan.html", {"dataproduk": dataproduk}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_saldobahan(request):
    databarang = models.Produk.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldobahan.html",
            {"nama_lokasi": datalokasi[:2], "databarang": databarang},
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
            messages.warning(request,f'Sudah ada Entry pada {kodeproduk} di {lokasi} pada tahun{tanggal_formatted.year}')
            return redirect("add_saldobahan")
        try :
            produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        except :
            messages.error(request,f'Bahan Baku {kodeproduk} tidak ditemukan dalam sistem')
            return redirect("add_saldobahan")
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        pemusnahanobj = models.SaldoAwalBahanBaku(
            Tanggal=tanggal, Jumlah=jumlah, IDBahanBaku=produkobj, IDLokasi=lokasiobj, Harga=harga)
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Saldo Bahan Baku. Kode Bahan Baku : {produkobj.KodeProduk} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi} Harga : {harga}",
        ).save()

        messages.success(request,"Data berhasil disimpan")
        return redirect("view_saldobahan")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_saldobahan(request, id):
    databarang = models.Produk.objects.all()
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_saldobahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj[:2],"databarang": databarang},
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
        ).exclude(IDSaldoAwalBahanBaku=id).exists()

        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("update_saldobahan",id=id)
        try :
            produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        except :
            messages.error(request,f'Bahan Baku {kodeproduk} tidak ditemukan dalam sistem')
            return redirect("update_saldobahan", id=id)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDBahanBaku = produkobj
        dataobj.IDLokasi = lokasiobj
        dataobj.Harga = harga
        dataobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Saldo Bahan Baku. Kode Bahan Baku : {produkobj.KodeProduk} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi} Harga : {harga}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldobahan")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_saldobahan(request, id):
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)

    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Saldo Bahan Baku. Kode Bahan Baku : {dataobj.IDBahanBaku.KodeProduk} Jumlah : {dataobj.Jumlah} Lokasi : {dataobj.IDLokasi.NamaLokasi} Harga : {dataobj.Harga}",
    ).save()
    
    return redirect(view_saldobahan)


# Saldo Awal Artikel
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_saldoartikel(request):
    dataartikel = models.SaldoAwalArtikel.objects.all().order_by("-Tanggal")
    for i in dataartikel:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_saldoartikel.html", {"dataartikel": dataartikel}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_saldoartikel(request):
    dataartikel = models.Artikel.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldoartikel.html",
            {"nama_lokasi": datalokasi[:2], "dataartikel": dataartikel},
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
            return redirect("add_saldoartikel")
        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=artikel)
        except :
            messages.error(request,f"Tidak ditemukan data artikel {artikel}")
            return redirect('add_saldoartikel')
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        pemusnahanobj = models.SaldoAwalArtikel(
            Tanggal=tanggal, Jumlah=jumlah, IDArtikel=artikelobj, IDLokasi=lokasiobj
        )
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Saldo Artikel. Kode Bahan Baku : {artikelobj.KodeArtikel} Jumlah : {jumlah} Lokasi : {lokasiobj.NamaLokasi}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldoartikel")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_saldoartikel(request, id):
    dataartikel = models.Artikel.objects.all()
    dataobj = models.SaldoAwalArtikel.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":

        return render(
            request,
            "produksi/update_saldoartikel.html",
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

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_saldoartikel(request, id):
    dataobj = models.SaldoAwalArtikel.objects.get(IDSaldoAwalBahanBaku=id)

    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Saldo Artikel. Kode Bahan Baku : {dataobj.IDArtikel.KodeArtikel} Jumlah : {dataobj.Jumlah} Lokasi : {dataobj.IDLokasi.NamaLokasi}",
    ).save()
    
    return redirect(view_saldoartikel)


# Saldo Awal Produk Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_saldosubkon(request):
    datasubkon = models.SaldoAwalSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_saldosubkon.html", {"datasubkon": datasubkon}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_saldosubkon(request):
    datasubkon = models.ProdukSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldosubkon.html",
            { "datasubkon": datasubkon},
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
        ).exists()

        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("add_saldosubkon")
        try:
            produkobj = models.ProdukSubkon.objects.get(IDProdukSubkon=kodeproduk)
        except:
            messages.error(request,"Tidak ditemukan data Produk pada sistem")
            return redirect('add_saldosubkon')

        pemusnahanobj = models.SaldoAwalSubkon(
            Tanggal=tanggal, Jumlah=jumlah, IDProdukSubkon=produkobj)
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Saldo Produk Subkon. Nama Produk : {produkobj.NamaProduk} Kode Artikel : {produkobj.KodeArtikel} Jumlah : {jumlah}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldosubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_saldosubkon(request, id):
    dataobj = models.SaldoAwalSubkon.objects.get(IDSaldoAwalProdukSubkon=id)

    dataobj.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Saldo Produk Subkon. Nama Produk : {dataobj.IDProdukSubkon.NamaProduk}  Kode Artikel : {dataobj.IDProdukSubkon.KodeArtikel} Jumlah : {dataobj.Jumlah}",
    ).save()
    
    return redirect(view_saldosubkon)


# Saldo Bahan Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_saldobahansubkon(request):
    datasubkon = models.SaldoAwalBahanBakuSubkon.objects.all().order_by("-Tanggal")
    for i in datasubkon:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")

    return render(
        request, "produksi/view_saldobahansubkon.html", {"datasubkon": datasubkon}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_saldobahansubkon(request):
    datasubkon = models.BahanBakuSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/add_saldobahansubkon.html",
            { "datasubkon": datasubkon},
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
        ).exists()

        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("add_saldobahansubkon")
        try:
            produkobj = models.BahanBakuSubkon.objects.get(KodeProduk=kodeproduk)
        except:
            messages.error(request,f"Kode Bahan Baku Subkon {kodeproduk} tidak ditemukan dalam sistem")
            return redirect("add_saldobahansubkon")
        pemusnahanobj = models.SaldoAwalBahanBakuSubkon(
            Tanggal=tanggal, Jumlah=jumlah, IDBahanBakuSubkon=produkobj)
        pemusnahanobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Saldo Bahan Baku Subkon. Kode Bahan Baku: {produkobj.KodeProduk} Jumlah : {jumlah}",
        ).save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("view_saldobahansubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_saldobahansubkon(request, id):
    dataobj = models.SaldoAwalBahanBakuSubkon.objects.get(IDSaldoAwalBahanBakuSubkon=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    datasubkon = models.BahanBakuSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_saldobahansubkon.html",
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

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_saldobahansubkon(request, id):
    dataobj = models.SaldoAwalBahanBakuSubkon.objects.get(IDSaldoAwalBahanBakuSubkon=id)

    dataobj.delete()

    models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Saldo Bahan Baku Subkon. Kode Bahan Baku: {dataobj.IDBahanBakuSubkon.KodeProduk} Jumlah : {dataobj.Jumlah}",
        ).save()
    
    return redirect(view_saldobahansubkon)


# Keterangan Bahan Baku
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def read_bahanbaku(request):
    produkobj = models.Produk.objects.all()
    return render(request, "produksi/read_produk.html", {"produkobj": produkobj})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_produk_produksi(request, id):
    produkobj = models.Produk.objects.get(pk=id)
    if request.method == "GET":
        return render(request, "produksi/update_produk.html", {"produkobj": produkobj})
    else:
        keterangan_produk = request.POST["keterangan_produk"]
        produkobj.keteranganProduksi = keterangan_produk
        produkobj.save()

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Bahan Baku. Kode Bahan Baku: {produkobj.KodeProduk} Nama Bahan Baku : {produkobj.NamaProduk}  Keterangan : {produkobj.keteranganProduksi}",
        ).save()

        return redirect("read_produk_produksi")


'''SUBKON SECTION'''
# Bahan Baku SUBKON
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def read_bahansubkon(request):
    produkobj = models.BahanBakuSubkon.objects.all()
    return render(request, "produksi/read_bahansubkon.html", {"produkobj": produkobj})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def create_bahansubkon(request):
    if request.method == "GET":
        return render(
            request, "produksi/create_bahansubkon.html")
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]

        databahan = models.BahanBakuSubkon.objects.filter(KodeProduk=kode_produk).exists()
        
        if databahan:
            messages.error(request, "Kode Produk sudah ada")
            return redirect("create_bahansubkon")
        else:
            new_produk = models.BahanBakuSubkon(
                KodeProduk = kode_produk,
                NamaProduk = nama_produk,
                unit = unit_produk,
            )
            new_produk.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Bahan Baku Subkon. Kode Bahan Baku: {kode_produk} Nama Bahan Baku : {nama_produk}  Unit : {unit_produk}",
            ).save()
            messages.success(request,"Data berhasil disimpan")
            return redirect("read_bahansubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_bahansubkon(request, id):
    produkobj = models.BahanBakuSubkon.objects.get(pk=id)

    if request.method == "GET":
        return render(
            request,
            "produksi/update_bahansubkon.html",
            {"produkobj": produkobj},
        )
    else:
        kode_produk = request.POST["kode_produk"]
        nama_produk = request.POST["nama_produk"]
        unit_produk = request.POST["unit_produk"]

        databahan = models.BahanBakuSubkon.objects.filter(KodeProduk=kode_produk).exclude(id=id).exists()
        
        if databahan:
            messages.error(request, "Kode Bahan Baku Subkon sudah ada")
            return redirect("update_bahansubkon",id=id)
        else:
            produkobj.KodeProduk = kode_produk
            produkobj.NamaProduk = nama_produk
            produkobj.unit = unit_produk

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Bahan Baku Subkon. Kode Bahan Baku: {kode_produk} Nama Bahan Baku : {nama_produk}  Unit : {unit_produk}",
            ).save()

        produkobj.save()
        messages.success(request,"Data berhasil diupdate")
        return redirect("read_bahansubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_bahansubkon(request, id):
    produkobj = models.BahanBakuSubkon.objects.get(id=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Bahan Baku Subkon. Kode Bahan Baku: {produkobj.KodeProduk} Nama Bahan Baku : {produkobj.NamaProduk}  Unit : {produkobj.unit}",
    ).save()
    
    return redirect("read_bahansubkon")


# Produk SUBKON
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def read_produksubkon(request):
    produkobj = models.ProdukSubkon.objects.all()
    return render(request, "produksi/read_produksubkon.html", {"produkobj": produkobj})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=kode_produk)
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Peruntukan tidak ditemukan")
            return redirect("create_produksubkon")
        
        listkodeproduk = (
            models.ProdukSubkon.objects.filter(KodeArtikel=artikelobj.id)
            .values_list("NamaProduk", flat=True)
            .distinct()
        )

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

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Produk Subkon. Nama Produk: {nama_produk} Artikel Peruntukan : {artikelobj.KodeArtikel}  Unit : {unit_produk} Keterangan : {keterangan_produk}",
            ).save()
            messages.success(request,'Data berhasil disimpan')
            return redirect("read_produksubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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

        try:
            artikelobj = models.Artikel.objects.get(KodeArtikel=kode_produk)
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Peruntukan tidak ditemukan")
            return redirect("update_produksubkon")
        
        listkodeproduk = (
            models.ProdukSubkon.objects.filter(KodeArtikel=artikelobj.id)
            .values_list("NamaProduk", flat=True).exclude(IDProdukSubkon=id)
            .distinct()
        )

        if nama_produk in listkodeproduk:
            messages.error(
                request, "Nama Produk untuk Artikel terkait sudah ada pada Database"
            )
            return redirect("update_produksubkon",id= id)
        else:
            produkobj.KodeArtikel= artikelobj
            produkobj.NamaProduk = nama_produk
            produkobj.Unit = unit_produk
            produkobj.keterangan = keterangan_produk
            produkobj.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Produk Subkon. Nama Produk: {nama_produk} Artikel Peruntukan : {artikelobj.KodeArtikel}  Unit : {unit_produk} Keterangan : {keterangan_produk}",
            ).save()

        return redirect("read_produksubkon")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_produksubkon(request, id):
    produkobj = models.ProdukSubkon.objects.get(IDProdukSubkon=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Produk Subkon. Nama Produk: {produkobj.NamaProduk} Artikel Peruntukan : {produkobj.KodeArtikel.KodeArtikel}  Unit : {produkobj.Unit} Keterangan : {produkobj.keterangan}",
    ).save()

    return redirect("read_produksubkon")


# Surat Jalan Kirim Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_subkonbahankeluar(request):
    datasubkon = models.DetailSuratJalanPengirimanBahanBakuSubkon.objects.all().order_by("NoSuratJalan__Tanggal")
    for i in datasubkon:
        i.NoSuratJalan.Tanggal = i.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_subkonbahankeluar.html", {"datasubkon": datasubkon})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_subkonbahankeluar(request):
    if request.method == "GET":
        subkonkirim = models.DetailSuratJalanPengirimanBahanBakuSubkon.objects.all()
        detailsk = models.SuratJalanPengirimanBahanBakuSubkon.objects.all()
        getproduk = models.BahanBakuSubkon.objects.all()

        return render(
            request,
            "produksi/add_subkonbahankeluar.html",
            {"subkonkirim": subkonkirim, "detailsk": detailsk, "getproduk": getproduk},
        )
    if request.method == "POST":
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]

        datasj = models.SuratJalanPengirimanBahanBakuSubkon.objects.filter(NoSuratJalan=nosuratjalan).exists()
        if datasj:
            messages.error(request, "No Surat Jalan sudah ada")
            return redirect("add_subkonbahankeluar")
        else:
            subkonkirimobj = models.SuratJalanPengirimanBahanBakuSubkon(NoSuratJalan=nosuratjalan, Tanggal=tanggal)
            subkonkirimobj.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"SJ Kirim Bahan Subkon. No Surat Jalan: {nosuratjalan}" ,
            ).save()

            subkonkirimobj = models.SuratJalanPengirimanBahanBakuSubkon.objects.get(NoSuratJalan=nosuratjalan)

            listkode = request.POST.getlist("kodeproduk")
            listjumlah = request.POST.getlist("jumlah")
            listket = request.POST.getlist("keterangan")

            for kodeproduk, jumlah, keterangan in zip(listkode, listjumlah, listket):
                try:
                    bahanobj = models.BahanBakuSubkon.objects.get(KodeProduk=kodeproduk)
                except models.BahanBakuSubkon.DoesNotExist :
                    messages.error(request,f"Data Bahan Baku {kodeproduk} tidak ditemukan dalam sistem")    
                    continue
                newprodukobj = models.DetailSuratJalanPengirimanBahanBakuSubkon(
                    KodeBahanBaku = bahanobj,
                    Jumlah=jumlah,
                    Keterangan=keterangan,
                    NoSuratJalan=subkonkirimobj,
                )
                newprodukobj.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail SJ Kirim Bahan Subkon. Kode Bahan Baku: {bahanobj.KodeProduk} Nama Bahan Baku : {bahanobj.NamaProduk}  Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()
            messages.success(request,"Data berhasil disimpan")
            return redirect("view_subkonbahankeluar")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_subkonbahankeluar(request, id):
    datasjp = models.DetailSuratJalanPengirimanBahanBakuSubkon.objects.get(IDDetailSJPengirimanSubkon=id)

    datasjp_getobj = models.SuratJalanPengirimanBahanBakuSubkon.objects.get(
        NoSuratJalan = datasjp.NoSuratJalan.NoSuratJalan
    )
    getproduk = models.BahanBakuSubkon.objects.all()

    if request.method == "GET":
        return render(
            request,
            "produksi/update_subkonbahankeluar.html",
            {
                "datasjp": datasjp_getobj,
                "detailsjp" :datasjp,
                "tanggal": datetime.strftime(datasjp_getobj.Tanggal, "%Y-%m-%d"),
                "getproduk": getproduk
            },
        )
    else:
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]
        kode_produk = request.POST["kodeproduk"]
        kode_produkobj = models.BahanBakuSubkon.objects.get(KodeProduk=kode_produk)
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        datasj = models.SuratJalanPengirimanBahanBakuSubkon.objects.filter(NoSuratJalan=nosuratjalan).exclude(NoSuratJalan=datasjp.NoSuratJalan.NoSuratJalan).exists()
        print(datasj)
        if datasj:
            messages.error(request, "No Surat Jalan sudah ada")
            return redirect("update_subkonbahankeluar",id)
        else:

            datasjp.NoSuratJalan.NoSuratJalan = nosuratjalan
            datasjp.NoSuratJalan.Tanggal = tanggal


            datasjp.NoSuratJalan.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"SJ Kirim Bahan Subkon. No Surat Jalan: {nosuratjalan}" ,
            ).save()

            datasjp.KodeBahanBaku = kode_produkobj
            datasjp.Jumlah = jumlah
            datasjp.Keterangan = keterangan
            
            datasjp.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Detail SJ Kirim Bahan Subkon. Kode Bahan Baku: {kode_produkobj.KodeProduk} Nama Bahan Baku : {kode_produkobj.NamaProduk}  Jumlah : {jumlah} Keterangan : {keterangan}",
            ).save()

            listkode = request.POST.getlist('kodeproduk[]')
            listjumlah = request.POST.getlist('jumlah[]')
            listket = request.POST.getlist('keterangan[]')

            for kodeproduk, jumlah, keterangan in zip(listkode, listjumlah, listket):
                bahanobj = models.BahanBakuSubkon.objects.get(KodeProduk=kodeproduk)
                newprodukobj = models.DetailSuratJalanPengirimanBahanBakuSubkon(
                    KodeBahanBaku = bahanobj,
                    Jumlah=jumlah,
                    Keterangan=keterangan,
                    NoSuratJalan=datasjp_getobj,
                )
                newprodukobj.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail SJ Kirim Bahan Subkon. Kode Bahan Baku: {bahanobj.KodeProduk} Nama Bahan Baku : {bahanobj.NamaProduk}  Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()
            messages.success(request,"Data berhasil disimpan")
            return redirect("view_subkonbahankeluar")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_subkonbahankeluar(request, id):
    dataskk = models.DetailSuratJalanPengirimanBahanBakuSubkon.objects.get(IDDetailSJPengirimanSubkon=id)
    dataskk.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Detail SJ Kirim Bahan Subkon. Kode Bahan Baku: {dataskk.KodeBahanBaku.KodeProduk} Nama Bahan Baku : {dataskk.KodeBahanBaku.NamaProduk}  Jumlah : {dataskk.Jumlah} Keterangan : {dataskk.Keterangan}",
    ).save()
    
    return redirect("view_subkonbahankeluar")


# Surat Jalan Terima Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_subkonprodukmasuk(request):
    datasubkon = models.DetailSuratJalanPenerimaanProdukSubkon.objects.all().order_by("NoSuratJalan__Tanggal")
    for i in datasubkon:
        i.NoSuratJalan.Tanggal = i.NoSuratJalan.Tanggal.strftime("%Y-%m-%d")

    return render(request, "produksi/view_subkonprodukmasuk.html", {"datasubkon": datasubkon})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def add_subkonprodukmasuk(request):
    if request.method == "GET":
        subkonkirim = models.DetailSuratJalanPenerimaanProdukSubkon.objects.all()
        detailsk = models.SuratJalanPenerimaanProdukSubkon.objects.all()
        getproduk = models.ProdukSubkon.objects.all()

        return render(
            request,
            "produksi/add_subkonprodukmasuk.html",
            {"subkonkirim": subkonkirim, "detailsk": detailsk, "getproduk": getproduk},
        )
    
    if request.method == "POST":
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]

        datasj = models.SuratJalanPenerimaanProdukSubkon.objects.filter(NoSuratJalan=nosuratjalan).exists()
        if datasj:
            messages.error(request, "No Surat Jalan sudah ada")
            return redirect("add_subkonprodukmasuk")
        else:
            listkode = request.POST.getlist("kodebarangHidden")
            listjumlah = request.POST.getlist("jumlah")
            listket = request.POST.getlist("keterangan")
            error = 0
            for item in listkode:
                try:
                    produksubkonobj = models.ProdukSubkon.objects.get(
                        IDProdukSubkon=item
                    )
                except :
                    error +=1
            if error == len(listkode):
                messages.error(request,"Kode Produk Subkon tidak terdapat dalam sistem")
                return redirect('add_subkonprodukmasuk')
            subkonkirimobj = models.SuratJalanPenerimaanProdukSubkon(NoSuratJalan=nosuratjalan, Tanggal=tanggal)
            subkonkirimobj.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"SJ Terima Produk Subkon. No Surat Jalan: {nosuratjalan}" ,
            ).save()

            subkonkirimobj = models.SuratJalanPenerimaanProdukSubkon.objects.get(NoSuratJalan=nosuratjalan)



            for kodeproduk, jumlah, keterangan in zip(listkode, listjumlah, listket):

                try:
                    produksubkonobj = models.ProdukSubkon.objects.get(
                        IDProdukSubkon=kodeproduk
                    )
                except :
                    messages.error(request, f"Kode Produk Subkon {kodeproduk}tidak ditemukan")
                    continue
                
                newprodukobj = models.DetailSuratJalanPenerimaanProdukSubkon(
                    KodeProduk = produksubkonobj,
                    Jumlah=jumlah,
                    Keterangan=keterangan,
                    NoSuratJalan=subkonkirimobj,
                )
                newprodukobj.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail SJ Terima Produk Subkon. Nama Produk : {produksubkonobj.NamaProduk} Artikel Untuk : {produksubkonobj.KodeArtikel}  Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()

            return redirect("view_subkonprodukmasuk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_subkonprodukmasuk(request, id):
    datasjp = models.DetailSuratJalanPenerimaanProdukSubkon.objects.get(IDDetailSJPengirimanSubkon=id)

    datasjp_getobj = models.SuratJalanPenerimaanProdukSubkon.objects.get(
        NoSuratJalan = datasjp.NoSuratJalan.NoSuratJalan
    )
    getproduk = models.ProdukSubkon.objects.all()

    if request.method == "GET":
        return render(
            request,
            "produksi/update_subkonprodukmasuk.html",
            {
                "datasjp": datasjp_getobj,
                "detailsjp" :datasjp,
                "tanggal": datetime.strftime(datasjp_getobj.Tanggal, "%Y-%m-%d"),
                "getproduk": getproduk
            },
        )
    else:
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]
        kode_produk = request.POST["kodebarangHiddens"]
        try:
            produksubkonobj = models.ProdukSubkon.objects.get(IDProdukSubkon=kode_produk)

        except models.ProdukSubkon.DoesNotExist:
            messages.error(request, "Kode Produk Subkon tidak ditemukan")
            return redirect("transaksi_subkon_terima")
    
        jumlah = request.POST["jumlah"]
        keterangan = request.POST["keterangan"]

        datasj = models.SuratJalanPenerimaanProdukSubkon.objects.filter(NoSuratJalan=nosuratjalan).exclude(NoSuratJalan=datasjp.NoSuratJalan.NoSuratJalan).exists()
        if datasj:
            messages.error(request, "No Surat Jalan sudah ada")
            return redirect("update_subkonprodukmasuk",id)
        else:
            datasjp.NoSuratJalan.NoSuratJalan = nosuratjalan
            datasjp.NoSuratJalan.Tanggal = tanggal

            datasjp.NoSuratJalan.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"SJ Terima Produk Subkon. No Surat Jalan: {nosuratjalan}" ,
            ).save()

            datasjp.KodeProduk = produksubkonobj
            datasjp.Jumlah = jumlah
            datasjp.Keterangan = keterangan
            
            datasjp.save()

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Detail SJ Terima Produk Subkon. Nama Produk : {produksubkonobj.NamaProduk} Artikel Untuk : {produksubkonobj.KodeArtikel}  Jumlah : {jumlah} Keterangan : {keterangan}",
            ).save()

            listkode = request.POST.getlist("kodebarangHidden")
            listjumlah = request.POST.getlist("jumlah[]")
            listket = request.POST.getlist("keterangan[]")

            for kodeproduk, jumlah, keterangan in zip(listkode, listjumlah, listket):

                try:
                    produksubkon = models.ProdukSubkon.objects.get(
                        IDProdukSubkon=kodeproduk
                    )

                except models.ProdukSubkon.DoesNotExist:
                    messages.error(request, "Kode Produk Subkon tidak ditemukan")
                    return redirect("transaksi_subkon_terima")
                
                newprodukobj = models.DetailSuratJalanPenerimaanProdukSubkon(
                    KodeProduk = produksubkon,
                    Jumlah=jumlah,
                    Keterangan=keterangan,
                    NoSuratJalan=datasjp_getobj,
                )
                newprodukobj.save()

                models.transactionlog(
                    user="Produksi",
                    waktu=datetime.now(),
                    jenis="Create",
                    pesan=f"Detail SJ Terima Produk Subkon. Nama Produk : {produksubkon.NamaProduk} Artikel Untuk : {produksubkon.KodeArtikel}  Jumlah : {jumlah} Keterangan : {keterangan}",
                ).save()


            return redirect("view_subkonprodukmasuk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_subkonprodukmasuk(request, id):
    dataskk = models.DetailSuratJalanPenerimaanProdukSubkon.objects.get(IDDetailSJPengirimanSubkon=id)
    dataskk.delete()

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Detail SJ Terima Produk Subkon. Nama Produk : {dataskk.KodeProduk.NamaProduk} Artikel Untuk : {dataskk.KodeProduk.KodeArtikel}  Jumlah : {dataskk.Jumlah} Keterangan : {dataskk.Keterangan}",
    ).save()
    
    return redirect("view_subkonprodukmasuk")


# Transaksi subkon bahan baku masuk
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def transaksi_subkonbahan_masuk(request):
    produkobj = models.TransaksiBahanBakuSubkon.objects.all().order_by("-Tanggal")
    for i in produkobj:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")
    return render(
        request, "produksi/read_transaksisubkonbahan_masuk.html", {"produkobj": produkobj}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def create_transaksi_subkonbahan_masuk(request):
    produksubkon = models.BahanBakuSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/create_transaksisubkonbahan_masuk.html",
            {"produksubkon": produksubkon},
        )
    else:
        tanggal = request.POST["tanggal"]
        list_nama_kode = request.POST.getlist("nama_produk[]")
        listjumlah = request.POST.getlist("jumlah[]")
        listketerangan = request.POST.getlist("keterangan[]")

        for nama_kode, jumlah, keterangan in zip(list_nama_kode,listjumlah, listketerangan):
            try:
                produksubkonobj = models.BahanBakuSubkon.objects.get(
                    KodeProduk=nama_kode
                    )
            except models.BahanBakuSubkon.DoesNotExist:
                messages.error(request,f'Kode Produk Subkon {nama_kode} tidak ditemukan')
                continue

            new_produk = models.TransaksiBahanBakuSubkon(
                Tanggal=tanggal,
                Jumlah=jumlah,
                KodeBahanBaku=produksubkonobj,
                Keterangan=keterangan
            )
            new_produk.save()
            messages.success(request, "Data berhasil disimpan")

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Transaksi Bahan Baku Subkon. Kode Bahan Baku: {produksubkonobj.KodeProduk} Nama Bahan Baku : {produksubkonobj.NamaProduk}  Jumlah : {jumlah} Keterangan : {keterangan}",
            ).save()
        return redirect("transaksi_subkonbahan_masuk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def update_transaksi_subkonbahan_masuk(request, id):
    produkobj = models.TransaksiBahanBakuSubkon.objects.get(pk=id)
    produkobj.Tanggal = produkobj.Tanggal.strftime("%Y-%m-%d")
    produksubkon = models.BahanBakuSubkon.objects.all()
    if request.method == "GET":
        return render(
            request,
            "produksi/update_transaksisubkonbahan_masuk.html",
            {"produkobj": produkobj, "produksubkon": produksubkon},
        )
    else:
        jumlah = request.POST["jumlah"]
        nama_kode = request.POST["nama_produk"]
        keterangan = request.POST["keterangan"]
        tanggal = request.POST["tanggal"]
        try:
            produksubkonobj = models.BahanBakuSubkon.objects.get(KodeProduk=nama_kode)
        except models.BahanBakuSubkon.DoesNotExist:
            messages.error(request,"Kode produk subkon tidak ditemukan")
            return redirect('update_transaksi_subkonbahan_masuk',id=id)
        produkobj.KodeBahanBaku = produksubkonobj
        produkobj.Jumlah = jumlah
        produkobj.Tanggal = tanggal
        produkobj.Keterangan = keterangan

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Transaksi Bahan Baku Subkon. Kode Bahan Baku: {produksubkonobj.KodeProduk} Nama Bahan Baku : {produksubkonobj.NamaProduk}  Jumlah : {jumlah} Keterangan : {keterangan}",
        ).save()

        produkobj.save()
        messages.success(request,'Data berhasil disimpan')
        return redirect("transaksi_subkonbahan_masuk")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_transaksi_subkonbahan_masuk(request, id):
    produkobj = models.TransaksiBahanBakuSubkon.objects.get(IDTransaksiBahanBakuSubkon=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
        user="Produksi",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Transaksi Bahan Baku Subkon. Kode Bahan Baku: {produkobj.KodeBahanBaku.KodeProduk} Nama Bahan Baku : {produkobj.KodeBahanBaku.NamaProduk}  Jumlah : {produkobj.Jumlah} Keterangan : {produkobj.Keterangan}",
    ).save()
    
    return redirect("transaksi_subkonbahan_masuk")


# Transaksi subkon produk keluar
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def transaksi_subkon_terima(request):
    produkobj = models.TransaksiSubkon.objects.all().order_by("-Tanggal")
    for i in produkobj:
        i.Tanggal = i.Tanggal.strftime("%Y-%m-%d")
    return render(
        request, "produksi/read_transaksisubkon_terima.html", {"produkobj": produkobj}
    )

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
        list_nama_kode = request.POST.getlist("kodebarangHidden")
        listjumlah = request.POST.getlist("jumlah[]")

        print(list_nama_kode)

        for nama_kode, jumlah in zip(list_nama_kode,listjumlah):

            try:
                produksubkonobj = models.ProdukSubkon.objects.get(IDProdukSubkon=nama_kode)

            except models.ProdukSubkon.DoesNotExist:
                messages.error(request, "Kode Produk Subkon tidak ditemukan")
                return redirect("transaksi_subkon_terima")
            
            new_produk = models.TransaksiSubkon(
                Tanggal=tanggal,
                Jumlah=jumlah,
                KodeProduk=produksubkonobj,
            )
            new_produk.save()
            messages.success(request, "Data berhasil disimpan")

            models.transactionlog(
                user="Produksi",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Transaksi Produk Subkon. Nama Produk: {produksubkonobj.NamaProduk} Artikel Peruntukan : {produksubkonobj.KodeArtikel}  Jumlah : {jumlah}",
            ).save()

        return redirect("transaksi_subkon_terima")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
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
        nama_kode = request.POST["kodebarangHidden"]
        tanggal = request.POST["tanggal"]

        try:
            produksubkonobj = models.ProdukSubkon.objects.get(
                IDProdukSubkon=nama_kode
            )
            print(produksubkonobj)
        except models.ProdukSubkon.DoesNotExist:
            messages.error(request, "Kode Produk Subkon tidak ditemukan")
            return redirect("update_transaksi_subkon_terima",id=id)
        
        produkobj.KodeProduk = produksubkonobj
        produkobj.Jumlah = jumlah
        produkobj.Tanggal = tanggal
        
        produkobj.save()
        messages.success(request, "Data berhasil disimpan")

        models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Transaksi Produk Subkon. Nama Produk: {produksubkonobj.NamaProduk} Artikel Peruntukan : {produksubkonobj.KodeArtikel}  Jumlah : {jumlah}",
        ).save()
        
        return redirect("transaksi_subkon_terima")

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def delete_transaksi_subkon_terima(request, id):
    produkobj = models.TransaksiSubkon.objects.get(IDTransaksiProdukSubkon=id)
    produkobj.delete()
    messages.success(request, "Data Berhasil dihapus")

    models.transactionlog(
            user="Produksi",
            waktu=datetime.now(),
            jenis="Delete",
            pesan=f"Transaksi Produk Subkon. Nama Produk: {produkobj.KodeProduk.NamaProduk} Artikel Peruntukan : {produkobj.KodeProduk.KodeArtikel}  Jumlah : {produkobj.Jumlah}",
        ).save()

    return redirect("transaksi_subkon_terima")


# KSBB KSBJ Subkon
@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_ksbjsubkon(request):
    kodeproduk = models.ProdukSubkon.objects.all()
    print(kodeproduk)
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbjsubkon.html", {"kodeprodukobj": kodeproduk})
    else:
        """
        1. Cari 
        """
        nama_kode = request.GET["kodebarangHidden"]
        print(nama_kode)
        try:
            produk = models.ProdukSubkon.objects.get(
               pk = nama_kode
            )
            nama = produk.NamaProduk
            satuan = produk.Unit
        except:
            messages.error(request, "Kode Produk Subkon tidak ditemukan")
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
            KodeProduk=produk.IDProdukSubkon, Tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        dataproduksi = models.DetailSuratJalanPenerimaanProdukSubkon.objects.filter(
            KodeProduk = produk.IDProdukSubkon,
            NoSuratJalan__Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )

        # ''' TANGGAL SECTION '''
        tanggalmasuk = dataterima.values_list("Tanggal", flat=True)
        tanggalkeluar = dataproduksi.values_list("NoSuratJalan__Tanggal", flat=True)
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
            datamasuk = dataproduksi.filter(NoSuratJalan__Tanggal = i)
            for m in datamasuk:
                masuk += m.Jumlah
            sisa  += masuk
            data['Masuk'] = masuk
            
            # Data Keluar
            datakeluar = dataterima.filter(Tanggal=i)
            keluar = 0
            for k in datakeluar:
                keluar += k.Jumlah
            sisa -= keluar
            data['Keluar'] = keluar

            data['Sisa'] = sisa

            listdata.append(data)

        return render(request, "produksi/view_ksbjsubkon.html",{"data":listdata,'saldo':saldoawal,"nama": nama,"satuan": satuan,"artikel":artikel,"kodeprodukobj": kodeproduk, 'produk':produk})

@login_required
@logindecorators.allowed_users(allowed_roles=['produksi'])
def view_ksbbsubkon(request):
    kodeproduk = models.BahanBakuSubkon.objects.all()
    if len(request.GET) == 0:
        return render(request, "produksi/view_ksbbsubkon.html", {"kodeprodukobj": kodeproduk})
    else:
        """
        1. Cari 
        """
        try:
            print(request)
            produk = models.BahanBakuSubkon.objects.get(KodeProduk=request.GET["kodebarang"])
            nama = produk.NamaProduk
            satuan = produk.unit
        except:
            messages.error(request, "Data Bahan tidak ditemukan")
            return redirect("ksbbsubkon")
        
        if request.GET["periode"]:
            tahun = int(request.GET["periode"])
        else:
            sekarang = datetime.now()
            tahun = sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        # Menceri data transaksi gudang dengan kode 
        databahan = models.TransaksiBahanBakuSubkon.objects.filter(
            KodeBahanBaku__KodeProduk=request.GET["kodebarang"], Tanggal__range=(tanggal_mulai, tanggal_akhir)
        )

        datakirim = models.DetailSuratJalanPengirimanBahanBakuSubkon.objects.filter(
            KodeBahanBaku__KodeProduk=request.GET["kodebarang"], NoSuratJalan__Tanggal__range=(tanggal_mulai, tanggal_akhir),
        )

        ''' TANGGAL SECTION '''
        tanggalmasuk = databahan.values_list("Tanggal", flat=True)
        tanggalkeluar = datakirim.values_list("NoSuratJalan__Tanggal", flat=True)

        listtanggal = sorted(
            list(set(tanggalmasuk.union(tanggalkeluar)))
        )

        ''' SALDO AWAL SECTION '''
        try:
            saldoawal = models.SaldoAwalBahanBakuSubkon.objects.get(
                IDBahanBakuSubkon__KodeProduk=request.GET["kodebarang"],
                Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            saldo = saldoawal.Jumlah
            saldoawal.Tanggal = saldoawal.Tanggal.strftime("%Y-%m-%d")

        except models.SaldoAwalBahanBakuSubkon.DoesNotExist:
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
            datamasuk = databahan.filter(Tanggal=i)
            for m in datamasuk:
                masuk += m.Jumlah
            sisa  += masuk
            data['Masuk'] = masuk
            
            # Data Keluar
            keluar = 0
            datakeluar = datakirim.filter(NoSuratJalan__Tanggal = i)
            for k in datakeluar:
                keluar += k.Jumlah
            sisa -= keluar
            data['Keluar'] = keluar

            data['Sisa'] = sisa
            listdata.append(data)

        return render(request, "produksi/view_ksbbsubkon.html",{'data':listdata,'saldo':saldoawal,'kodebarang':request.GET["kodebarang"],"nama": nama,"satuan": satuan,"kodeprodukobj": kodeproduk})

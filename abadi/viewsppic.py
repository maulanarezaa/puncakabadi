from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.urls import reverse
from . import models
from django.db.models import Sum, Max
from io import BytesIO
import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from datetime import datetime, date
import calendar
from . import logindecorators
from django.contrib.auth.decorators import login_required

# Create your views here.


def gethargabahanbaku(
    listtanggal, hargamasukobj, hargakeluarobj, hargaawal, jumlahawal
):
    listdata = []
    totalharga = hargaawal * jumlahawal
    for j in listtanggal:
        jumlahkeluarperhari = 0
        hargakeluartotalperhari = 0
        hargakeluarsatuanperhari = 0
        hargamasuktotalperhari = 0
        hargamasuksatuanperhari = 0
        jumlahmasukperhari = 0

        sjpobj = hargamasukobj.filter(NoSuratJalan__Tanggal=j)
        if sjpobj.exists():
            for k in sjpobj:
                hargamasuktotalperhari += k.Harga * k.Jumlah
                jumlahmasukperhari += k.Jumlah
            hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
            # print("data SJP ada")
            # print(hargamasuksatuanperhari)
            # print(jumlahmasukperhari)
            dumy = {
                "Tanggal": j,
                "Jumlahstokawal": jumlahawal,
                "Hargasatuanawal": round(hargaawal, 2),
                "Hargatotalawal": round(totalharga, 2),
                "Jumlahmasuk": jumlahmasukperhari,
                "Hargamasuksatuan": round(hargamasuksatuanperhari, 2),
                "Hargamasuktotal": round(hargamasuktotalperhari, 2),
                "Jumlahkeluar": jumlahkeluarperhari,
                "Hargakeluarsatuan": round(hargakeluarsatuanperhari, 2),
                "Hargakeluartotal": round(hargakeluartotalperhari, 2),
            }
            jumlahawal += jumlahmasukperhari - jumlahkeluarperhari
            totalharga += hargamasuktotalperhari - hargakeluartotalperhari
            hargaawal = totalharga / jumlahawal

            # print("Sisa Stok Hari Ini : ", jumlahawal)
            # print("harga awal Hari Ini :", hargaawal)
            # print("harga total Hari Ini :", totalharga, "\n")
            dumy["Sisahariini"] = jumlahawal
            dumy["Hargasatuansisa"] = round(hargaawal, 2)
            dumy["Hargatotalsisa"] = round(totalharga, 2)
            listdata.append(dumy)
            print(dumy)

        hargamasuktotalperhari = 0
        hargamasuksatuanperhari = 0
        jumlahmasukperhari = 0

        # print(j)
        transaksigudangobj = hargakeluarobj.filter(tanggal=j)
        if transaksigudangobj.exists():
            for k in transaksigudangobj:
                jumlahkeluarperhari += k.jumlah
                hargakeluartotalperhari += k.jumlah * hargaawal
            hargakeluarsatuanperhari += hargakeluartotalperhari / jumlahkeluarperhari
        else:
            hargakeluartotalperhari = 0
            hargakeluarsatuanperhari = 0
            jumlahkeluarperhari = 0

        # print("Tanggal : ", j)
        # print("Sisa Stok Hari Sebelumnya : ", jumlahawal)
        # print("harga awal Hari Sebelumnya :", hargaawal)
        # print("harga total Hari Sebelumnya :", totalharga)
        # print("Jumlah Masuk : ", jumlahmasukperhari)
        # print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
        # print("Harga Total Masuk : ", hargamasuktotalperhari)
        # print("Jumlah Keluar : ", jumlahkeluarperhari)
        # print("Harga Keluar : ", hargakeluarsatuanperhari)
        # print(
        #     "Harga Total Keluar : ",
        #     hargakeluarsatuanperhari * jumlahkeluarperhari,
        # )
        jumlahawal += jumlahmasukperhari - jumlahkeluarperhari
        totalharga += hargamasuktotalperhari - hargakeluartotalperhari
        try:
            hargaawal = totalharga / jumlahawal
        except ZeroDivisionError:
            hargaawal = 0

        # print("Sisa Stok Hari Ini : ", jumlahawal)
        # print("harga awal Hari Ini :", hargaawal)
        # print("harga total Hari Ini :", totalharga, "\n")
    return hargaawal, jumlahawal, totalharga


@login_required
@logindecorators.allowed_users(allowed_roles=["ppic"])
def dashboard(request):
    data = models.confirmationorder.objects.filter(StatusAktif=True)
    for i in data:
        detailco = models.detailconfirmationorder.objects.filter(confirmationorder=i.id)
        i.detailco = detailco
    print(data)
    for i in data:
        detailcopo = models.detailconfirmationorder.objects.filter(
            confirmationorder=i.id
        )
        i.detailcopo = detailcopo
        i.tanggal = i.tanggal.strftime("%Y-%m-%d")
    return render(request, "ppic/dashboard.html", {"data": data})


def laporanbarangjadi(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_laporanstokfg.html")
    else:
        # Rumus = Saldo awal periode sampai tanggal akhir - Keluar awal periode sampai tanggal akhir
        tanggal_mulai = request.GET["tanggalawal"]
        tanggal_akhir = request.GET["tanggalakhir"]
        data = models.Artikel.objects.all()
        grandtotal = 0
        for i in data:
            mutasifilterobj = models.TransaksiProduksi.objects.filter(
                KodeArtikel=i.id
                # Tanggal__range=(tanggal_mulai, tanggal_akhir),
            )
            print(mutasifilterobj)
            saldomutasimasuktanggalakhir = mutasifilterobj.filter(
                Lokasi=1, Tanggal__lte=(tanggal_akhir), Jenis="Mutasi"
            )
            saldomutasikeluartanggalakhir = mutasifilterobj.filter(
                Lokasi=2, Tanggal__lte=(tanggal_akhir), Jenis="Mutasi"
            )
            jumlahmasuk = 0
            # jUMLAH kELUAR BELUM SYNC DENGAN MUTASI SPPB
            jumlahkeluar = 0
            for j in saldomutasimasuktanggalakhir:
                jumlahmasuk += j.Jumlah
            for K in saldomutasikeluartanggalakhir:
                jumlahkeluar += K.Jumlah
            i.Jumlahakumulasi = jumlahmasuk - jumlahkeluar
            print(jumlahmasuk)
            print(jumlahkeluar)
            # Nilai FG --> penyusun artikel * konversi * harga di akumulasikan semua penyusun
            penyusunfilterobj = models.Penyusun.objects.filter(KodeArtikel=i.id)

            nilaiFG = 0
            for penyusunobj in penyusunfilterobj:
                nilaiFG += gethargafg(penyusunobj)
            i.HargaFG = nilaiFG
            i.NilaiTotal = nilaiFG * i.Jumlahakumulasi
            grandtotal += i.NilaiTotal

        return render(
            request,
            "ppic/views_laporanstokfg.html",
            {
                "data": data,
                "tanggalawal": tanggal_mulai,
                "tanggalakhir": tanggal_akhir,
                "grandtotal": grandtotal,
            },
        )


def excel_laporanbarangmasuk(request):
    if request.method == "POST":
        tanggalawal = request.POST["tanggalawal"]
        tanggalakhir = request.POST["tanggalakhir"]
        dataspk = models.SuratJalanPembelian.objects.filter(
            Tanggal__range=(tanggalawal, tanggalakhir)
        ).order_by("Tanggal")
        # print(dataspk)
        listdetailsjp = []
        grandtotal = 0
        for i in dataspk:
            detailsjpembelianobj = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan=i.NoSuratJalan
            )
            for j in detailsjpembelianobj:
                j.supplier = i.supplier
                j.totalharga = j.Jumlah * j.Harga
                grandtotal += j.totalharga
                listdetailsjp.append(j)

        # print(listdetailsjp)
        listnomor = []
        listsjp = []
        listsupplier = []
        listkodeproduk = []
        listnamabarang = []
        listsatuan = []
        listqty = []
        listhargasatuan = []
        listhargatotal = []
        for no, i in enumerate(listdetailsjp):
            listnomor.append(no)
            listsjp.append(i.NoSuratJalan.NoSuratJalan)
            listsupplier.append(i.supplier)
            listkodeproduk.append(i.KodeProduk.KodeProduk)
            listnamabarang.append(i.KodeProduk.NamaProduk)
            listsatuan.append(i.KodeProduk.unit)
            listqty.append(i.Jumlah)
            listhargasatuan.append(i.Harga)
            listhargatotal.append(i.totalharga)
        tabel = {
            "No": listnomor,
            "SJ Pembelian": listsjp,
            "Supplier": listsupplier,
            "Kode Stok": listkodeproduk,
            "Nama Barang": listnamabarang,
            "Satuan": listsatuan,
            "Kuantitas": listqty,
            "Harga Satuan": listhargasatuan,
            "Harga Total": listhargatotal,
        }
        df = pd.DataFrame(tabel)
        print(df)

        excel_file = BytesIO()
        # df.to_excel('export data.xlsx',index=False)
        wb = Workbook()
        ws = wb.active
        headers = list(df.columns)
        ws.append(headers)
        for r_idx, row in enumerate(df.itertuples(), start=1):
            for c_idx, value in enumerate(row[1:], start=1):
                ws.cell(row=r_idx + 1, column=c_idx, value=value)

        start_row = (
            len(df) + 1
        )  # Ganti angka 2 dengan jumlah baris tambahan sebelum merge
        end_row = start_row  # Ganti angka 4 dengan jumlah baris yang ingin digabungkan
        totalhargacell = f"I{end_row}"
        labeltotalhargacell = f"H{end_row}"
        ws[totalhargacell] = grandtotal
        ws[labeltotalhargacell] = "Total Harga"
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        file_name = f"Laporan_{tanggalawal}-{tanggalakhir}.xlsx"
        response = HttpResponse(
            excel_buffer,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{file_name}"'
        # with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        #     df.to_excel(writer, index=False)
        # excel_file.seek(0)
        # response = HttpResponse(excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # response['Content-Disposition'] = f'attachment; filename="Laporan{tanggalawal}-{tanggalakhir}.xlsx"'

        return response


def laporanbarangmasuk(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_laporanbarangmasuk.html")
    else:
        tanggalawal = request.GET["tanggalawal"]
        tanggalakhir = request.GET["tanggalakhir"]

        dataspk = models.SuratJalanPembelian.objects.filter(
            Tanggal__range=(tanggalawal, tanggalakhir)
        ).order_by("Tanggal")
        print(dataspk)
        listdetailsjp = []
        grandtotal = 0
        for i in dataspk:
            detailsjpembelianobj = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan=i.NoSuratJalan
            )
            for j in detailsjpembelianobj:
                j.supplier = i.supplier
                j.totalharga = j.Jumlah * j.Harga
                grandtotal += j.totalharga
                listdetailsjp.append(j)

        print(listdetailsjp)
        return render(
            request,
            "ppic/views_laporanbarangmasuk.html",
            {
                "data": listdetailsjp,
                "tanggalawal": tanggalawal,
                "tanggalakhir": tanggalakhir,
                "grandtotal": grandtotal,
            },
        )


def gethargafg(penyusunobj):
    # Mengambil data Konversi master
    konversiobj = models.KonversiMaster.objects.get(
        KodePenyusun=penyusunobj.IDKodePenyusun
    )
    # Mengambil kuantitas dan ditambahkan 2.5%
    konversialowance = konversiobj.Kuantitas + (konversiobj.Kuantitas * 0.025)
    # Mengambil data Detail surrat jalan pembelian untuk kode produk sesuai dengan penyusun obj (1 penyusun 1 produk 1 artkel)
    detailsjpembelian = models.DetailSuratJalanPembelian.objects.filter(
        KodeProduk=penyusunobj.KodeProduk
    )
    hargatotalkodeproduk = 0
    jumlahtotalkodeproduk = 0
    for m in detailsjpembelian:
        hargatotalkodeproduk += m.Harga * m.Jumlah
        jumlahtotalkodeproduk += m.Jumlah
    # print("ini jumlah harga total ", hargatotalkodeproduk)
    try:
        rataratahargakodeproduk = hargatotalkodeproduk / jumlahtotalkodeproduk
    except ZeroDivisionError:
        rataratahargakodeproduk = 0
    # print("selesai")
    # print(rataratahargakodeproduk)
    nilaifgperkodeproduk = rataratahargakodeproduk * konversialowance
    # print("Harga Konversi : ", nilaifgperkodeproduk)
    return nilaifgperkodeproduk


def laporanbarangkeluar(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_laporanbarangkeluar.html")
    else:
        tanggalawal = request.GET["tanggalawal"]
        tanggalakhir = request.GET["tanggalakhir"]
        data = models.SPPB.objects.filter(
            Tanggal__range=(tanggalawal, tanggalakhir)
        ).order_by("Tanggal")
        print("ini data", data)
        listharga = []
        listdata = []
        listkodeartikel = []
        listjumlah = []
        listhargafg = []
        listnilaitotal = []
        datakirim = []
        if not data.exists():
            messages.warning(
                request, "Data SPPB tidak ditemukan pada rentang tanggal tersebut"
            )
            return redirect("laporanbarangkeluar")
        for i in data:
            detailsppb = models.DetailSPPB.objects.filter(NoSPPB=i.id)
            a = detailsppb.values("DetailSPK__KodeArtikel").annotate(
                total_jumlah=Sum("Jumlah")
            )
            print("nilai A", a)
            for j in a:
                print(j["DetailSPK__KodeArtikel"])
                kodeartikel = j["DetailSPK__KodeArtikel"]
                penyusunfilterobj = models.Penyusun.objects.filter(
                    KodeArtikel=kodeartikel
                )
                if kodeartikel in listkodeartikel:
                    index = listkodeartikel.index(kodeartikel)
                    jumlah = listjumlah[index] + j["total_jumlah"]
                    listjumlah[index] = jumlah
                    listnilaitotal[index] = jumlah * listhargafg[index]
                else:
                    listkodeartikel.append(kodeartikel)
                    jumlah = j["total_jumlah"]
                    listjumlah.append(jumlah)

                    nilaiFG = 0
                    for penyusunobj in penyusunfilterobj:

                        nilaiFG += gethargafg(penyusunobj)
                    listhargafg.append(nilaiFG)
                    listnilaitotal.append(nilaiFG * jumlah)

            listdata.append(a)
        # print(listdata)
        grandtotal = sum(listnilaitotal)
        print("listkodeartikel", listkodeartikel)
        print("listjumlah", listjumlah)
        print("listnilaitotal", listnilaitotal)
        print("listhargafg", listhargafg)

        for kode_artikel, jumlah, nilai_total, harga_fg in zip(
            listkodeartikel, listjumlah, listnilaitotal, listhargafg
        ):
            artikel = models.Artikel.objects.get(id=kode_artikel)
            datakirim.append(
                {
                    "kode_artikel": artikel,
                    "jumlah": jumlah,
                    "nilai_total": nilai_total,
                    "harga_fg": harga_fg,
                }
            )

        return render(
            request,
            "ppic/views_laporanbarangkeluar.html",
            {
                "tanggalawal": tanggalawal,
                "tanggalakhir": tanggalakhir,
                "data": datakirim,
                "grandtotal": grandtotal,
            },
        )


def laporanpersediaanbarang(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_laporanpersediaan.html")
    else:
        tanggal_mulai = request.GET["tanggalawal"]
        tanggal_akhir = request.GET["tanggalakhir"]
        tanggal_obj = datetime.strptime(tanggal_akhir, "%Y-%m-%d").date()

        # Ambil total harga barang keluar dulu
        data = models.SPPB.objects.filter(
            Tanggal__range=(tanggal_mulai, tanggal_akhir)
        ).order_by("Tanggal")
        if not data.exists():
            messages.warning(
                request, "Data SPPB Tidak ditemukan pada rentang tanggal tersebut"
            )
            return redirect("laporanpersediaanbarang")
        listharga = []
        for i in data:
            detailsppb = models.DetailSPPB.objects.filter(NoSPPB=i.id)
            a = detailsppb.values("DetailSPK__KodeArtikel").annotate(
                total_jumlah=Sum("Jumlah")
            )
            for j in a:
                penyusunfilterobj = models.Penyusun.objects.filter(
                    KodeArtikel=j["DetailSPK__KodeArtikel"]
                )
                nilaiFG = 0
                for penyusunobj in penyusunfilterobj:
                    nilaiFG += gethargafg(penyusunobj)
                j.update({"HargaFG": nilaiFG})
                j.update({"TotalNilai": nilaiFG * j["total_jumlah"]})
                j["DetailSPK__KodeArtikel"] = penyusunobj.KodeArtikel.KodeArtikel
                listharga.append(j["TotalNilai"])
        totalhargabarangkeluar = sum(listharga)

        # Ambil data Bahan masuk
        dataspk = models.SuratJalanPembelian.objects.filter(
            Tanggal__range=(tanggal_mulai, tanggal_akhir)
        ).order_by("Tanggal")
        listdetailsjp = []
        totalhargabarangmasuk = 0
        for i in dataspk:
            detailsjpembelianobj = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan=i.NoSuratJalan
            )
            for j in detailsjpembelianobj:
                j.supplier = i.supplier
                j.totalharga = j.Jumlah * j.Harga
                totalhargabarangmasuk += j.totalharga
                listdetailsjp.append(j)

        # Total Harga Stok Gudang
        dataartikel = models.Artikel.objects.all()
        totalhargabarangjadi = 0
        for i in dataartikel:
            mutasifilterobj = models.TransaksiProduksi.objects.filter(KodeArtikel=i.id)
            saldomutasimasuktanggalakhir = mutasifilterobj.filter(
                Lokasi=1, Tanggal__lte=(tanggal_akhir)
            )
            saldomutasikeluartanggalakhir = mutasifilterobj.filter(
                Lokasi=2, Tanggal__lte=(tanggal_akhir)
            )
            print(mutasifilterobj)
            jumlahmasuk = 0
            jumlahkeluar = 0
            for j in saldomutasimasuktanggalakhir:
                jumlahmasuk += j.Jumlah
            for k in saldomutasikeluartanggalakhir:
                jumlahkeluar += k.Jumlah

            i.Jumlahakumulasi = jumlahmasuk - jumlahkeluar
            penyusunfilterobj = models.Penyusun.objects.filter(KodeArtikel=i.id)

            nilaiFG = 0
            for penyusunobj in penyusunfilterobj:
                nilaiFG += gethargafg(penyusunobj)
            i.Harga = nilaiFG
            i.NilaiTotal = nilaiFG * i.Jumlahakumulasi
            totalhargabarangjadi += i.NilaiTotal

        # Saldo awal Belum dibuat
        Saldoawal = 0
        # Anggap dari
        # Ambil data semua bahan baku di wip
        databahanproduksi = models.Produk.objects.filter(KodeProduk__startswith="A")
        print(databahanproduksi)
        for i in databahanproduksi:
            print("ini i", i)
            datasaldoawaltahun = (
                models.SaldoAwalBahanBaku.objects.filter(
                    Tanggal__lte=tanggal_akhir, IDBahanBaku=i.KodeProduk
                )
                .order_by("-Tanggal")
                .first()
            )
            if (
                not datasaldoawaltahun
                or datasaldoawaltahun.Tanggal.year != tanggal_obj.year
            ):
                print("data tidak ada")
                hargasaldoawalbahanbaku = 0
            else:
                print(datasaldoawaltahun)
                print("data ada")
                hargasaldoawalbahanbaku = (
                    datasaldoawaltahun.Harga * datasaldoawaltahun.Jumlah
                )

            Saldoawal += hargasaldoawalbahanbaku

        #
        saldototal = Saldoawal + totalhargabarangmasuk - totalhargabarangkeluar
        saldowip = saldototal - totalhargabarangjadi

        return render(
            request,
            "ppic/views_laporanpersediaan.html",
            {
                "tanggalawal": tanggal_mulai,
                "tanggalakhir": tanggal_akhir,
                "data": a,
                "barangkeluar": round(totalhargabarangkeluar, 2),
                "barangmasuk": round(totalhargabarangmasuk, 2),
                "barangfg": round(totalhargabarangjadi, 2),
                "saldoawal": round(Saldoawal, 2),
                "saldototal": round(saldototal, 2),
                "saldowip": round(saldowip, 2),
            },
        )


"""
Revisi 4/21/2024
1. Co PO
2. Transaction Log
3. Perhitungan Laporan
"""


def viewconfirmationorder(request):
    data = models.confirmationorder.objects.filter(StatusAktif=True)

    print(data)
    for i in data:
        detailcopo = models.detailconfirmationorder.objects.filter(
            confirmationorder=i.id
        )
        i.detailcopo = detailcopo
        i.tanggal = i.tanggal.strftime("%Y-%m-%d")
    if len(request.GET) == 0:
        return render(request, "ppic/views_confirmationorder.html", {"data": data})


def tambahconfirmationorder(request):
    dataartikel = models.Artikel.objects.all()
    if request.method == "GET":
        return render(request, "ppic/add_co.html", {"dataartikel": dataartikel})
    else:
        print(request.POST)
        tanggaladd = request.POST["tanggal"]
        nomorco = request.POST["nomorco"]
        kepada = request.POST["kepada"]
        perihal = request.POST["perihal"]
        artikel = request.POST.getlist("artikel[]")
        kuantitas = request.POST.getlist("kuantitas[]")
        harga = request.POST.getlist("harga[]")
        deskripsi = request.POST.getlist("deskripsi[]")
        # print(tanggaladd)
        # print(nomorco)
        # print(kepada)
        # print(perihal)
        # print(artikel)
        # print(kuantitas)
        # print(harga)
        # print(deskripsi)

        confirmationorderobj = models.confirmationorder(
            NoCO=nomorco, kepada=kepada, perihal=perihal, tanggal=tanggaladd
        )
        confirmationorderobj.save()
        print(confirmationorderobj.id)
        for artikel, kuantitas, harga, deskripsi in zip(
            artikel, kuantitas, harga, deskripsi
        ):
            # print(artikel, kuantitas, harga, deskripsi)
            detailconfirmationobj = models.detailconfirmationorder(
                confirmationorder=confirmationorderobj,
                Artikel=models.Artikel.objects.get(KodeArtikel=artikel),
                Harga=harga,
                kuantitas=kuantitas,
                deskripsi=deskripsi,
            )
            print(dir(detailconfirmationobj))
            detailconfirmationobj.save()
        return redirect("confirmationorder")


def detailco(request, id):
    data = models.confirmationorder.objects.get(id=id)
    detailcopo = models.detailconfirmationorder.objects.filter(
        confirmationorder=data.id
    )
    data.detailcopo = detailcopo
    data.tanggal = data.tanggal.strftime("%Y-%m-%d")
    detailsppb = models.DetailSPPB.objects.filter(IDCO=data)
    data.detailsppb = detailsppb
    print(detailsppb)
    datajumlah = detailsppb.values("DetailSPK__KodeArtikel__KodeArtikel").annotate(
        total=Sum("Jumlah")
    )
    print(datajumlah)

    return render(request, "ppic/detailco.html", {"dataco": data, "jumlah": datajumlah})


def updateco(request, id):
    data = models.confirmationorder.objects.get(id=id)
    detailcopo = models.detailconfirmationorder.objects.filter(
        confirmationorder=data.id
    )
    data.detailcopo = detailcopo
    data.tanggal = data.tanggal.strftime("%Y-%m-%d")
    print(len(data.detailcopo))
    if request.method == "GET":
        return render(request, "ppic/updateco.html", {"dataco": data})
    else:
        print(request.POST)
        tanggaladd = request.POST["tanggal"]
        nomorco = request.POST["nomorco"]
        kepada = request.POST["kepada"]
        perihal = request.POST["perihal"]
        artikel = request.POST.getlist("artikel[]")
        kuantitas = request.POST.getlist("kuantitas[]")
        harga = request.POST.getlist("harga[]")
        deskripsi = request.POST.getlist("deskripsi[]")
        listid = request.POST.getlist("id[]")
        data.tanggal = tanggaladd
        data.nomorco = nomorco
        data.kepada = kepada
        data.perihal = perihal

        data.save()

        for listid, artikel, kuantitas, harga, deskripsi in zip(
            listid, artikel, kuantitas, harga, deskripsi
        ):
            # print(artikel, kuantitas, harga, deskripsi)
            if listid == "":
                detailconfirmationobj = models.detailconfirmationorder(
                    confirmationorder=data,
                    Artikel=models.Artikel.objects.get(KodeArtikel=artikel),
                    Harga=harga,
                    kuantitas=kuantitas,
                    deskripsi=deskripsi,
                )
            else:
                detailconfirmationobj = models.detailconfirmationorder.objects.get(
                    id=listid
                )
                detailconfirmationobj.confirmationorder = data
                detailconfirmationobj.Artikel = models.Artikel.objects.get(
                    KodeArtikel=artikel
                )
                detailconfirmationobj.Harga = harga
                detailconfirmationobj.kuantitas = kuantitas
                detailconfirmationobj.deskripsi = deskripsi

            detailconfirmationobj.save()

        return redirect("confirmationorder")


def deletedetailco(request, id):
    data = models.detailconfirmationorder.objects.get(id=id)
    idco = data.confirmationorder.id
    data.delete()
    return redirect("updateco", id=idco)


def deleteco(request, id):
    data = models.confirmationorder.objects.get(id=id)
    data.delete()
    return redirect("confirmationorder")


def newlaporanpersediaan(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_newlaporanpersediaan.html")
    else:
        """Initiation"""
        tanggalmulai = request.GET["tanggalawal"]
        tanggalakhir = request.GET["tanggalakhir"]
        bulantahun = request.GET["bulan"]
        tanggal_obj = datetime.strptime(tanggalakhir, "%Y-%m-%d")
        tahun = tanggal_obj.year
        awaltahun = datetime(tahun, 1, 1)
        tanggal_obj.date()

        data = models.SPPB.objects.filter(
            Tanggal__range=(tanggalmulai, tanggalakhir)
        ).order_by("Tanggal")
        if not data.exists():
            messages.warning(
                request, "Data SPPB Tidak ditemukan pada rentang tanggal tersebut"
            )
        """End Initiation"""

        """
        SECTION SJP
        sudah clear.
        SJP Hanya mempertimbangkan transaksi di range tanggal tersebut. Tidak ada cakupan untuk perhitungan yang lain
        """

        datasjp = models.SuratJalanPembelian.objects.filter(
            Tanggal__range=(tanggalmulai, tanggalakhir)
        ).order_by("Tanggal")
        listdetailsjp = []
        totalhargabarangmasuk = 0
        for i in datasjp:
            detailsjpembelianobj = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan=i.NoSuratJalan
            )
            for j in detailsjpembelianobj:
                j.supplier = i.supplier
                j.totalharga = j.Jumlah * j.Harga
                totalhargabarangmasuk += j.totalharga
                listdetailsjp.append(j)
        # print("total barang masuk SJP : ", totalhargabarangmasuk)
        # Output : total barang masuk SJP :  45581000.0
        """ END SECTION SJP """

        """
        TOTAL HARGA STOK
        Belum FIx untuk perhitungan Harga.
        Bisa di cek dulu menggunakan harga terakhir di bulan tersebut. 
        apabila ada harganya maka bisa menggunakan harga tersebut. Apabila tidak ada maka menggunakan harga terbesar tanggal terakhir
        Apabila cek kondisi 0 maka muncul warning dan memilih harga terakhir
        """
        bahanbaku = models.Produk.objects.all()
        # bahanbaku = models.Produk.objects.filter(KodeProduk="coba-001")
        listhargabahanbaku = {}
        stokakhirbahanbakutiapbulan = {}
        hargaakhirbulanperproduk = {}
        """ PERHITUNGAN HARGA BARU """
        for i in bahanbaku:
            hargamasukobj = models.DetailSuratJalanPembelian.objects.filter(
                KodeProduk=i, NoSuratJalan__Tanggal__gte=awaltahun
            )
            hargakeluarobj = models.TransaksiGudang.objects.filter(
                KodeProduk=i, tanggal__gte=awaltahun
            )
            tanggalhargamasukobj = (
                hargamasukobj.filter(NoSuratJalan__Tanggal__lte=tanggalakhir)
                .values_list("NoSuratJalan__Tanggal", flat=True)
                .distinct()
            )
            tanggalhargakeluarobj = (
                hargakeluarobj.filter(tanggal__lte=tanggalakhir)
                .values_list("tanggal", flat=True)
                .distinct()
            )
            listtanggal = sorted(
                list(set(tanggalhargamasukobj.union(tanggalhargakeluarobj)))
            )

            try:
                saldoawalobj = models.SaldoAwalBahanBaku.objects.get(
                    IDBahanBaku=i, Tanggal__gte=awaltahun
                )
                hargaawal = saldoawalobj.Harga
                jumlahawal = saldoawalobj.Jumlah

            except models.SaldoAwalBahanBaku.DoesNotExist:
                hargaawal = 0
                jumlahawal = 0
            # Menghitung harga tanggal akhir
            data = gethargabahanbaku(
                listtanggal,
                hargamasukobj,
                hargakeluarobj,
                hargaawal,
                jumlahawal,
            )
            listhargabahanbaku[i] = data[0]

            """
            V2 List harga bahan baku awal dipisah berdasarkan tanggal
            1. Ambil dulu list tanggal akhir tiap bulan
            2. cek harga tiap akhir bulan 
            A. Filter dari GTE awal taun dan LTE akhir bulan untuk SJP dan Transaksi Gudang
            """
            """ 1. Ambil List Akhir bulan"""
            # print(calendar.monthrange(tahun, 1))
            last_days = []
            for month in range(1, 13):
                last_day = calendar.monthrange(tahun, month)[1]
                last_days.append(date(tahun, month, last_day))

            """ End list akhir bulan"""

            """ 2. Cek harga akhir Bulan"""
            hargaakhirbulan = {}
            maxtanggal = hargamasukobj.aggregate(Max("NoSuratJalan__Tanggal"))[
                "NoSuratJalan__Tanggal__max"
            ].month
            # print("Maksimal data", hargamasukobj)
            # print("Maksimal bulan", maxtanggal)
            # print(last_days[:maxtanggal])
            totalhargabahanbakugudangperbulan = 0
            for j, k in enumerate(last_days[:maxtanggal]):
                suratjalanpembelianakhirbulanobj = hargamasukobj.filter(
                    NoSuratJalan__Tanggal__lte=k
                )
                transaksigudangakhirbulanobj = hargakeluarobj.filter(tanggal__lte=k)
                tanggalsuratjalanpembelianakhirbulanobj = (
                    suratjalanpembelianakhirbulanobj.values_list(
                        "NoSuratJalan__Tanggal", flat=True
                    ).distinct()
                )
                tanggaltransaksigudangakhirbulanobj = (
                    transaksigudangakhirbulanobj.values_list(
                        "tanggal", flat=True
                    ).distinct()
                )
                tanggalkeluarmasukperbulan = sorted(
                    list(
                        set(
                            tanggalsuratjalanpembelianakhirbulanobj.union(
                                tanggaltransaksigudangakhirbulanobj
                            )
                        )
                    )
                )
                datahargaperbulan = gethargabahanbaku(
                    tanggalkeluarmasukperbulan,
                    suratjalanpembelianakhirbulanobj,
                    transaksigudangakhirbulanobj,
                    hargaawal,
                    jumlahawal,
                )
                # print(j, k, datahargaperbulan)
                hargaakhirbulan[j] = {
                    "hargasatuan": datahargaperbulan[0],
                    "jumlah": datahargaperbulan[1],
                    "hargatotal": datahargaperbulan[2],
                }
                totalhargabahanbakugudangperbulan += datahargaperbulan[2]
            hargaakhirbulanperproduk[i] = {
                "data": hargaakhirbulan,
                "total": totalhargabahanbakugudangperbulan,
            }
            # print("data surat jalan pembelian : ", suratjalanpembelianakhirbulanobj)
            # print("data Transaksi Gudang : ", transaksigudangakhirbulanobj)

            """ End harga akhir bulan"""
            """ endsection V2 """

        #     print("\n\nDONES\n\n")
        # print(listhargabahanbaku)
        # print(listhargabahanbakusebelum)
        """ END SECTION PERHITUNGAN HARGA BARU """

        print("Data Rekap Harga Perbulan : ", hargaakhirbulanperproduk)
        # print(asdasdas)
        totalhargabarangjadi = 0
        """
        Data Models harga FG perbulan
        {
            Kode Artikel : [
            { bulan0 :
                {
            item1 : 9000
            item2 : 8000
            }
            HargaFG : 17000
            }
            ]
        }
        """
        dataartikel = models.Artikel.objects.all()
        datahargafgartikel = {}
        for artikel in dataartikel:
            hargafg = 0
            dataperbulan = {}
            """
            Models perbulan
            {}
            """
            modelsperbulan = {}
            for index, hari in enumerate(last_days[: tanggal_obj.month]):
                # Mengambil data terakhir versi penyusun tiap bulannya
                versiterakhirperbulan = (
                    models.Penyusun.objects.filter(KodeArtikel=artikel, versi__lte=hari)
                    .values_list("versi", flat=True)
                    .distinct()
                    .order_by("versi")
                    .last()
                )
                # SEMENTARA PAKAI .LAST()
                penyusunversiterpilih = models.Penyusun.objects.filter(
                    KodeArtikel=artikel, versi=versiterakhirperbulan
                )
                datapenyusun = {}
                for penyusun in penyusunversiterpilih:
                    dummy = {}
                    hargapenyusun = hargaakhirbulanperproduk[penyusun.KodeProduk][
                        "data"
                    ][index]["hargasatuan"]
                    kuantitas = models.KonversiMaster.objects.get(
                        KodePenyusun=penyusun
                    ).Kuantitas
                    hargabahanbakufg = hargapenyusun * kuantitas
                    hargafg += hargabahanbakufg
                    dummy["totalharga"] = hargabahanbakufg
                    dummy["kuantitas"] = kuantitas
                    dummy["harga"] = hargapenyusun
                    datapenyusun[penyusun.KodeProduk] = dummy

                dummy2 = {}
                dummy2["penyusun"] = datapenyusun
                dummy2["hargafg"] = hargafg

                dataperbulan[index] = dummy2
            datahargafgartikel[artikel] = dataperbulan

        # print("versi terakhir ", datahargafgartikel)
        rekapkeluarperbulan = {}
        rekapmutasiperbulan = {}
        sisaperbulan = {}
        bahangudangperbulan = {}
        datarekapbarangmasukperbulan = {}
        penyusunartikelperbulan = {}
        artikelpenyusunperbulan = {}
        rekapdatabahanbakumasukkewip = {}
        rekapprodukkeluarperbulan = {}
        rekappemusnahanartikelperbulan = {}
        rekappemusnahanbahanbakuperbulan = {}

        for index, hari in enumerate(last_days[: tanggal_obj.month]):
            """Section SJP --> Mencari barnag masu tiap bulan"""
            nilaibahanbakumasuk = 0
            dataartikelmasuk = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__lte=hari,
                NoSuratJalan__Tanggal__gte=awaltahun,
            )
            dummy = {}
            for item in dataartikelmasuk:
                biaya = item.Harga * item.Jumlah
                nilaibahanbakumasuk += biaya
                dummy[item] = {
                    "biaya": biaya,
                    "jumlah": item.Jumlah,
                    "harga": item.Harga,
                    "kodeproduk": item.KodeProduk,
                }
            datarekapbarangmasukperbulan[index] = {
                "data": dummy,
                "biayatotal": nilaibahanbakumasuk,
            }
            """Section SPPB --> mencari rekap barnag keluar tiap bulan"""
            if index > 0:
                datadetailsppb = models.DetailSPPB.objects.filter(
                    NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gt=last_days[index - 1]
                )
                datatransaksiproduksi = models.TransaksiProduksi.objects.filter(
                    Tanggal__lte=hari, Tanggal__gt=last_days[index - 1], Jenis="Mutasi"
                )
            else:
                datadetailsppb = models.DetailSPPB.objects.filter(
                    NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gte=awaltahun
                )
                datatransaksiproduksi = models.TransaksiProduksi.objects.filter(
                    Tanggal__lte=hari, Tanggal__gt=awaltahun, Jenis="Mutasi"
                )
            print("Data detail SPPB\n", index, datadetailsppb)
            jumlahkumulatifbiayaperbulan = 0
            if datadetailsppb.exists():
                jumlahartikelkeluarperbulan = datadetailsppb.values(
                    "DetailSPK__KodeArtikel"
                ).annotate(total=Sum("Jumlah"))
                # print(jumlahartikelkeluarperbulan)
                dummy = {}
                for artikel in jumlahartikelkeluarperbulan:
                    dataartikel = models.Artikel.objects.get(
                        id=artikel["DetailSPK__KodeArtikel"]
                    )

                    jumlah = artikel["total"]
                    totalbiaya = (
                        jumlah * datahargafgartikel[dataartikel][index]["hargafg"]
                    )
                    # print(dataartikel, jumlah)
                    # print(datahargafgartikel[dataartikel][index]["hargafg"], totalbiaya)
                    dummy[dataartikel] = {
                        "jumlah": jumlah,
                        "hargafg": datahargafgartikel[dataartikel][index]["hargafg"],
                        "biaya": totalbiaya,
                    }
                    jumlahkumulatifbiayaperbulan += totalbiaya
            else:
                dummy = 0
            rekapkeluarperbulan[index] = {
                "data": dummy,
                "jumlah": jumlahkumulatifbiayaperbulan,
            }
            dummy = {}
            """SECTION Transaksi Produksi --> Untuk mencari data mutasi barang jadi"""
            if datatransaksiproduksi.exists():
                jumlahartikelmutasiperbulan = datatransaksiproduksi.values(
                    "KodeArtikel"
                ).annotate(total=Sum("Jumlah"))
                for artikel in jumlahartikelmutasiperbulan:
                    dataartikel = models.Artikel.objects.get(id=artikel["KodeArtikel"])
                    jumlah = artikel["total"]
                    totalbiaya = (
                        jumlah * datahargafgartikel[dataartikel][index]["hargafg"]
                    )
                    dummy[dataartikel] = {
                        "jumlah": jumlah,
                        "hargafg": datahargafgartikel[dataartikel][index]["hargafg"],
                        "biaya": totalbiaya,
                    }
            else:
                dummy = 0

            rekapmutasiperbulan[index] = dummy
            dataartikel = models.Artikel.objects.all()
            # dataartikel = models.Artikel.objects.all()
            dummy = {}

            totalbiayasisafg = 0
            datapenyusunversiterpilih = {}
            dummypenyusunartikelperbulan = {}
            for artikel in dataartikel:
                if index == 0:
                    dummy[artikel] = {"jumlah": 0, "biaya": 0, "hargafg": 0}
                else:
                    dummy[artikel] = {
                        "jumlah": sisaperbulan[index - 1]["data"][artikel]["jumlah"]
                    }
                # ambil jumlah artikel keluar terkait
                if (
                    datadetailsppb.exists()
                    and artikel in rekapkeluarperbulan[index]["data"]
                ):
                    jumlahartikelkeluar = rekapkeluarperbulan[index]["data"][artikel][
                        "jumlah"
                    ]
                else:
                    jumlahartikelkeluar = 0

                if (
                    datatransaksiproduksi.exists()
                    and artikel in rekapmutasiperbulan[index]
                ):
                    jumlahartikelmasuk = rekapmutasiperbulan[index][artikel]["jumlah"]
                else:
                    jumlahartikelmasuk = 0
                print(artikel, jumlahartikelkeluar, jumlahartikelmasuk)

                # print(dummy)
                dummy[artikel]["jumlah"] += jumlahartikelmasuk - jumlahartikelkeluar
                dummy[artikel]["hargafg"] = datahargafgartikel[artikel][index][
                    "hargafg"
                ]
                dummy[artikel]["biaya"] = (
                    dummy[artikel]["jumlah"]
                    * datahargafgartikel[artikel][index]["hargafg"]
                )
                # print(dummy)
                totalbiayasisafg += dummy[artikel]["biaya"]

                """SECTION PENYUSUN"""
                versiterakhirperbulan = (
                    models.Penyusun.objects.filter(KodeArtikel=artikel, versi__lte=hari)
                    .values_list("versi", flat=True)
                    .distinct()
                    .order_by("versi")
                    .last()
                )
                penyusunversiterpilih = models.KonversiMaster.objects.filter(
                    KodePenyusun__KodeArtikel=artikel,
                    KodePenyusun__versi=versiterakhirperbulan,
                )
                """
                {0 : {A-101:{Artikel1:0.34124,{artikel2:0.12314}}}}
                
                """

                # print(penyusunversiterpilih)
                jumlahpenyusunkuantitasperartikel = penyusunversiterpilih.values(
                    "KodePenyusun__KodeProduk__KodeProduk"
                ).annotate(total=Sum("Kuantitas"))
                print(
                    "Tes Penyusun terpilih", artikel, jumlahpenyusunkuantitasperartikel
                )
                dummypenyusunperartikel = {}
                for penyusun in jumlahpenyusunkuantitasperartikel:
                    kodeprodukterpilih = penyusun[
                        "KodePenyusun__KodeProduk__KodeProduk"
                    ]
                    kuantitasterpilih = penyusun["total"] + 0.025 * penyusun["total"]
                    dummypenyusunperartikel[kodeprodukterpilih] = kuantitasterpilih
                    if kodeprodukterpilih in datapenyusunversiterpilih:
                        dummypenyusun = {}
                        for artikeliterasi, kuantitas in datapenyusunversiterpilih[
                            kodeprodukterpilih
                        ].items():
                            dummypenyusun[artikeliterasi] = kuantitas
                        dummypenyusun[artikel] = kuantitasterpilih
                        datapenyusunversiterpilih[kodeprodukterpilih] = dummypenyusun
                    else:
                        datapenyusunversiterpilih[kodeprodukterpilih] = {
                            artikel: kuantitasterpilih
                        }
                dummypenyusunartikelperbulan[artikel] = dummypenyusunperartikel
                print("ini data penyusun terpilih", datapenyusunversiterpilih)

            # print(dummypenyusunartikelperbulan)
            artikelpenyusunperbulan[index] = dummypenyusunartikelperbulan

            # print(asdasdasd)
            sisaperbulan[index] = {"data": dummy, "total": totalbiayasisafg}
            penyusunartikelperbulan[index] = datapenyusunversiterpilih

            """SECTION Stock Gudang"""
            bahanbaku = models.Produk.objects.all()
            # bahanbaku = models.Produk.objects.filter(KodeProduk="coba-001")
            dummy = {}
            rekaphargabahanbakugudangperbulan = 0
            dummybahanbakumasuk = {}
            for produk in bahanbaku:
                saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
                    IDBahanBaku=produk, Tanggal__gte=awaltahun
                )
                if saldoawalobj.exists():
                    saldoawalobj = saldoawalobj.first()
                    totalbiayaawal = saldoawalobj.Harga * saldoawalobj.Jumlah
                    hargasatuanawal = saldoawalobj.Harga
                    jumlahawal = saldoawalobj.Jumlah
                else:
                    totalbiayaawal = 0
                    hargasatuanawal = 0
                    jumlahawal = 0

                barangmasukobj = models.DetailSuratJalanPembelian.objects.filter(
                    KodeProduk=produk,
                    NoSuratJalan__Tanggal__gte=awaltahun,
                    NoSuratJalan__Tanggal__lte=hari,
                )
                barangkeluarobj = models.TransaksiGudang.objects.filter(
                    KodeProduk=produk, tanggal__gte=awaltahun, tanggal__lte=hari
                )

                tanggalbarangmasukobj = barangmasukobj.values_list(
                    "NoSuratJalan__Tanggal", flat=True
                ).distinct()
                tanggalbarangkeluar = barangkeluarobj.values_list(
                    "tanggal", flat=True
                ).distinct()
                listtanggal = sorted(
                    list(set(tanggalbarangmasukobj.union(tanggalbarangkeluar)))
                )
                print(index, produk, listtanggal)
                for tanggal in listtanggal:
                    jumlahmasukperhari = 0
                    hargamasuktotalperhari = 0
                    hargamasuksatuanperhari = 0
                    jumlahkeluarperhari = 0
                    hargakeluartotalperhari = 0
                    hargakeluarsatuanperhari = 0
                    jumlahmasukperhari = 0

                    sjpobj = barangmasukobj.filter(NoSuratJalan__Tanggal=tanggal)
                    if sjpobj.exists():
                        for k in sjpobj:
                            hargamasuktotalperhari += k.Harga * k.Jumlah
                            jumlahmasukperhari += k.Jumlah
                            hargamasuksatuanperhari += (
                                hargamasuktotalperhari / jumlahmasukperhari
                            )
                    else:
                        hargamasuktotalperhari = 0
                        jumlahmasukperhari = 0
                        hargamasuksatuanperhari = 0

                    transaksigudangobj = barangkeluarobj.filter(tanggal=tanggal)
                    if transaksigudangobj.exists():
                        for k in transaksigudangobj:
                            jumlahkeluarperhari += k.jumlah
                            hargakeluartotalperhari += k.jumlah * hargasatuanawal
                        hargakeluarsatuanperhari += (
                            hargakeluartotalperhari / jumlahkeluarperhari
                        )
                    else:
                        hargakeluartotalperhari = 0
                        hargakeluarsatuanperhari = 0
                        jumlahkeluarperhari = 0

                    # print(produk)
                    # print("Tanggal : ", tanggal)
                    # print("Sisa Stok Hari Sebelumnya : ", jumlahawal)
                    # print("harga awal Hari Sebelumnya :", hargasatuanawal)
                    # print("harga total Hari Sebelumnya :", totalbiayaawal)
                    # print("Jumlah Masuk : ", jumlahmasukperhari)
                    # print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
                    # print("Harga Total Masuk : ", hargamasuktotalperhari)
                    # print("Jumlah Keluar : ", jumlahkeluarperhari)
                    # print("Harga Keluar : ", hargakeluarsatuanperhari)
                    # print(
                    #     "Harga Total Keluar : ",
                    #     hargakeluarsatuanperhari * jumlahkeluarperhari,
                    # )
                    jumlahawal += jumlahmasukperhari - jumlahkeluarperhari
                    totalbiayaawal += hargamasuktotalperhari - hargakeluartotalperhari
                    try:
                        hargasatuanawal = totalbiayaawal / jumlahawal
                    except ZeroDivisionError:
                        hargasatuanawal = 0

                    # print("Sisa Stok Hari Ini : ", jumlahawal)
                    # print("harga awal Hari Ini :", hargasatuanawal)
                    # print("harga total Hari Ini :", totalbiayaawal, "\n")
                dummy[produk] = {
                    "hargasatuan": hargasatuanawal,
                    "jumlah": jumlahawal,
                    "totalbiaya": totalbiayaawal,
                }
                rekaphargabahanbakugudangperbulan += totalbiayaawal

                """ SECTION REKAP WIP """

                # masuk ke wip

                databahanbakumasukkewip = models.TransaksiGudang.objects.filter(
                    tanggal__gte=awaltahun,
                    tanggal__lte=hari,
                    jumlah__gte=0,
                    KodeProduk=produk,
                    Lokasi__IDLokasi__in=(1, 2),
                )
                jumlahbahanbakumasukkewip = databahanbakumasukkewip.aggregate(
                    total=Sum("jumlah")
                )
                print(produk)
                print(databahanbakumasukkewip)
                print(jumlahbahanbakumasukkewip)
                if jumlahbahanbakumasukkewip["total"] == None:
                    jumlahbahanbakumasukkewip["total"] = 0
                # print(asdasd)
                # Saldo Awal Bahan Baku WIP
                datasaldoawalbahanbakuwip = models.SaldoAwalBahanBaku.objects.filter(
                    IDBahanBaku=produk, Tanggal__gte=awaltahun
                )
                jumlahsaldoawalbahanbakuwip = datasaldoawalbahanbakuwip.aggregate(
                    total=Sum("Jumlah")
                )
                if jumlahsaldoawalbahanbakuwip["total"] == None:
                    jumlahsaldoawalbahanbakuwip["total"] = 0

                if index == 0:
                    dummybahanbakumasuk[produk] = (
                        jumlahbahanbakumasukkewip["total"]
                        + jumlahsaldoawalbahanbakuwip["total"]
                    )
                    print("di Awal : ", jumlahbahanbakumasukkewip)
                    # print(asd)
                else:
                    dummybahanbakumasuk[produk] = (
                        jumlahbahanbakumasukkewip["total"]
                        + rekapdatabahanbakumasukkewip[index - 1][produk]
                    )
                    print(jumlahbahanbakumasukkewip)
                    print(rekapdatabahanbakumasukkewip[index - 1])
                    print(dummybahanbakumasuk)
                    # print(asdasd)

                # Keluar dari WIP (iterasi per produk)
                listkonversikeluar = artikelpenyusunperbulan[index]
                barangkeluar = rekapkeluarperbulan[index]["data"]
                print(barangkeluar, "\n")
                print(listkonversikeluar)
                dummy3 = {}
                if barangkeluar == 0:
                    dummy3 = 0
                else:
                    for artikelkeluar, data in barangkeluar.items():
                        # penyusun artikel terkait
                        for (
                            datapenyusunartikel,
                            kuantitaspenyusunartikel,
                        ) in listkonversikeluar[artikelkeluar].items():
                            # print(datapenyusunartikel)
                            kuantitasbahanbakukeluar = (
                                kuantitaspenyusunartikel * data["jumlah"]
                            )
                            if datapenyusunartikel in dummy3:
                                dummy3[datapenyusunartikel] += kuantitasbahanbakukeluar
                            else:
                                dummy3[datapenyusunartikel] = kuantitasbahanbakukeluar

                rekapprodukkeluarperbulan[index] = dummy3
            # print(asdas)
            rekapdatabahanbakumasukkewip[index] = dummybahanbakumasuk
            bahangudangperbulan[index] = {
                "data": dummy,
                "total": rekaphargabahanbakugudangperbulan,
            }
            # Barang Pemusnahan
            """SECTION PEMUSNAHAN ARTIKEL"""
            if index == 0:
                datapemusnahanartikel = models.PemusnahanArtikel.objects.filter(
                    Tanggal__gte=awaltahun, Tanggal__lte=hari
                )
            else:
                datapemusnahanartikel = models.PemusnahanArtikel.objects.filter(
                    Tanggal__gt=last_days[index - 1],
                    Tanggal__lte=hari,
                )
            jumlahpemusnahanartikel = datapemusnahanartikel.values(
                "KodeArtikel__KodeArtikel"
            ).annotate(total=Sum("Jumlah"))
            dummy = {}
            for pemusnahan in jumlahpemusnahanartikel:
                artikelpemusnahan = pemusnahan["KodeArtikel__KodeArtikel"]
                jumlahpemusnahan = pemusnahan["total"]
                dummy[artikelpemusnahan] = jumlahpemusnahan

            print("Jumlah Pemusnahan Artikel", jumlahpemusnahanartikel)

            rekappemusnahanartikelperbulan[index] = dummy
            print(rekapprodukkeluarperbulan)

            """SECTION PEMUSNAHAN BAHAN BAKU"""
            if index == 0:
                datapemusnahanbahanbaku = models.PemusnahanBahanBaku.objects.filter(
                    Tanggal__gte=awaltahun, Tanggal__lte=hari
                )
            else:
                datapemusnahanbahanbaku = models.PemusnahanBahanBaku.objects.filter(
                    Tanggal__gte=last_days[index - 1], Tanggal__lte=hari
                )
            jumlahpemusnahanbahanbaku = datapemusnahanbahanbaku.values(
                "KodeBahanBaku__KodeProduk"
            ).annotate(total=Sum("Jumlah"))
            dummy = {}
            for pemusnahan in jumlahpemusnahanbahanbaku:
                bahanbakupemusnahan = pemusnahan["KodeBahanBaku__KodeProduk"]
                jumlahpemusnahan = pemusnahan["total"]
                dummy[bahanbakupemusnahan] = jumlahpemusnahan

            print("Jumlah Pemusnahan Artikel", jumlahpemusnahanartikel)
            rekappemusnahanbahanbakuperbulan[index] = dummy

            """SECTION PERHITUNGAN STOK REAL DI WIP PERBULAN"""
            # Stok Realtime bahan baku
            stokrealtimeakhirbulanwip = rekapdatabahanbakumasukkewip

            # print(asdas)

        # print(asdasd)
        print("ini rekap keluar perbulan\n", rekapkeluarperbulan)
        print("ini rekap mutasi perbulan\n", rekapmutasiperbulan)
        print("ini rekap Sisa perbulan\n", sisaperbulan)
        print("ini rekap Bahan Gudang perbulan\n", bahangudangperbulan)
        print("ini rekap penyusun per Artikel\n", artikelpenyusunperbulan)
        print("ini rekap Bahan Baku keluar per Artikel\n", rekapprodukkeluarperbulan)
        print("ini rekap pemusnahan Artikel Perbulan\n", rekappemusnahanartikelperbulan)
        print(
            "ini rekap pemusnahan Bahan Baku Perbulan\n",
            rekappemusnahanbahanbakuperbulan,
        )
        print("ini rekap Bahan Baku Masuk WIP Perbulan\n", rekapdatabahanbakumasukkewip)

        # print(asdasd)

        """Rekapitulasi ke Models Akhir
        data models
        {
        Bulan1 : 
        {
        barangkeluar : {
        artikel1 :value,
        artikel2:value,
        dst
        },
        barangmasuk :{}
        bahanproduksi : {}
        baranggudang : {}
        }
        }
        """
        modelakhir = {}
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        for month in range(0, tanggal_obj.month):
            # Data Barang Keluar
            modelakhir[listbulan[month]] = {
                "barangkeluar": rekapkeluarperbulan[month]["jumlah"],
                "barangmasuk": datarekapbarangmasukperbulan[month]["biayatotal"],
                "detailbarangkeluar": rekapkeluarperbulan[month]["data"],
                "sisafg": sisaperbulan[month],
                "stockgudang": bahangudangperbulan[month],
                "penyusun": artikelpenyusunperbulan[month],
                "bahanbakukeluar": rekapprodukkeluarperbulan[month],
                "bahanbakumasukwip": rekapdatabahanbakumasukkewip[month],
                "rekappemusnahanartikel": rekappemusnahanartikelperbulan[month],
                "rekappemusnahanbahanbaku": rekappemusnahanbahanbakuperbulan[month],
            }
        return render(
            request,
            "ppic/views_newlaporanpersediaan.html",
            {
                "modeldata": modelakhir,
                "tanggalawal": tanggalmulai,
                "tanggalakhir": tanggalakhir,
                "bulantahun": bulantahun,
            },
        )


def detaillaporanbarangkeluar(request):
    if len(request.GET) > 0:
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])

        """ SPPB Section """
        datadetailsppb, totalbiayakeluar, datapenyusun, datalistbarangkeluar = (
            getbarangkeluar(last_days, index, awaltahun)
        )
        return render(
            request,
            "ppic/detaillaporanbarangkeluar.html",
            {
                "sppb": datadetailsppb,
                "totalbiayakeluar": totalbiayakeluar[index - 1],
                "bulan": bulan,
                "penyusun": datapenyusun,
            },
        )


def getbarangkeluar(last_days, stopindex, awaltahun):
    biayafgperartikel = gethargafgperbulan(last_days, stopindex, awaltahun)
    # print(biayafgperartikel)
    # print(stopindex, awaltahun)
    # print(asda)
    listdatadetailsppb = []
    datapenyusun = {}
    biayakeluar = {}
    for index, hari in enumerate(last_days[:stopindex]):
        totalbiayakeluar = 0
        if index == 0:
            datadetailsppb = models.DetailSPPB.objects.filter(
                NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gte=awaltahun
            )
        else:
            datadetailsppb = models.DetailSPPB.objects.filter(
                NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gt=last_days[index - 1]
            )
        if datadetailsppb.exists():
            for detailsppb in datadetailsppb:
                print(detailsppb)
                # print(biayafgperartikel)
                harga = (
                    detailsppb.Jumlah
                    * biayafgperartikel[detailsppb.DetailSPK.KodeArtikel][index][
                        "hargafg"
                    ]
                )
                detailsppb.hargafg = biayafgperartikel[
                    detailsppb.DetailSPK.KodeArtikel
                ][index]["hargafg"]
                detailsppb.totalharga = harga
                detailsppb.penyusun = biayafgperartikel[
                    detailsppb.DetailSPK.KodeArtikel
                ][index]["penyusun"]
                totalbiayakeluar += harga
                datapenyusun[detailsppb.DetailSPK.KodeArtikel] = biayafgperartikel[
                    detailsppb.DetailSPK.KodeArtikel
                ][index]
        listdatadetailsppb.append(datadetailsppb)
        biayakeluar[index] = totalbiayakeluar
    return datadetailsppb, biayakeluar, datapenyusun, listdatadetailsppb


def gethargapurchasingperbulan(last_days, stopindex, awaltahun):
    bahanbaku = models.Produk.objects.all()
    # bahanbaku = models.Produk.objects.filter(KodeProduk="A-001-06")

    hargaakhirbulanperproduk = {}
    for i in bahanbaku:
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
            IDBahanBaku=i, Tanggal__gte=awaltahun
        )
        if saldoawalobj.exists():
            saldoawalobj = saldoawalobj.first()
            totalbiayaawal = saldoawalobj.Harga * saldoawalobj.Jumlah
            hargaawal = saldoawalobj.Harga
            jumlahawal = saldoawalobj.Jumlah
        else:
            totalbiayaawal = 0
            hargaawal = 0
            jumlahawal = 0
        hargamasukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=i, NoSuratJalan__Tanggal__gte=awaltahun
        )
        hargakeluarobj = models.TransaksiGudang.objects.filter(
            KodeProduk=i, tanggal__gte=awaltahun
        )
        hargaakhirbulan = {}
        totalhargabahanbakugudangperbulan = 0
        for j, k in enumerate(last_days[:stopindex]):
            tanggalhargamasukobj = (
                hargamasukobj.filter(NoSuratJalan__Tanggal__lte=k)
                .values_list("NoSuratJalan__Tanggal", flat=True)
                .distinct()
            )
            tanggalhargakeluarobj = (
                hargakeluarobj.filter(tanggal__lte=k)
                .values_list("tanggal", flat=True)
                .distinct()
            )
            listtanggal = sorted(
                list(set(tanggalhargamasukobj.union(tanggalhargakeluarobj)))
            )

            suratjalanpembelianakhirbulanobj = hargamasukobj.filter(
                NoSuratJalan__Tanggal__lte=k
            )
            transaksigudangakhirbulanobj = hargakeluarobj.filter(tanggal__lte=k)
            tanggalsuratjalanpembelianakhirbulanobj = (
                suratjalanpembelianakhirbulanobj.values_list(
                    "NoSuratJalan__Tanggal", flat=True
                ).distinct()
            )
            tanggaltransaksigudangakhirbulanobj = (
                transaksigudangakhirbulanobj.values_list(
                    "tanggal", flat=True
                ).distinct()
            )
            tanggalkeluarmasukperbulan = sorted(
                list(
                    set(
                        tanggalsuratjalanpembelianakhirbulanobj.union(
                            tanggaltransaksigudangakhirbulanobj
                        )
                    )
                )
            )
            datahargaperbulan = gethargabahanbaku(
                tanggalkeluarmasukperbulan,
                suratjalanpembelianakhirbulanobj,
                transaksigudangakhirbulanobj,
                hargaawal,
                jumlahawal,
            )
            # print(j, k, datahargaperbulan)
            hargaakhirbulan[j] = {
                "hargasatuan": datahargaperbulan[0],
                "jumlah": datahargaperbulan[1],
                "hargatotal": datahargaperbulan[2],
            }
            totalhargabahanbakugudangperbulan += datahargaperbulan[2]
        hargaakhirbulanperproduk[i] = {
            "data": hargaakhirbulan,
            "total": totalhargabahanbakugudangperbulan,
        }
    # print(hargaakhirbulanperproduk)
    # print(asdasd)
    return hargaakhirbulanperproduk


def gethargafgperbulan(last_days, stopindex, awaltahun):
    hargaakhirbulanperproduk = gethargapurchasingperbulan(
        last_days, stopindex, awaltahun
    )
    # print(hargaakhirbulanperproduk)
    # print(asd)
    dataartikel = models.Artikel.objects.all()
    datahargafgartikel = {}
    for artikel in dataartikel:
        dataperbulan = {}
        """
        Models perbulan
        {}
        """
        modelsperbulan = {}
        for index, hari in enumerate(last_days[:stopindex]):
            # Mengambil data terakhir versi penyusun tiap bulannya
            versiterakhirperbulan = (
                models.Penyusun.objects.filter(KodeArtikel=artikel, versi__lte=hari)
                .values_list("versi", flat=True)
                .distinct()
                .order_by("versi")
                .last()
            )
            # SEMENTARA PAKAI .LAST()
            penyusunversiterpilih = models.Penyusun.objects.filter(
                KodeArtikel=artikel, versi=versiterakhirperbulan
            )
            datapenyusun = {}
            hargafg = 0
            for penyusun in penyusunversiterpilih:
                dummy = {}
                hargapenyusun = hargaakhirbulanperproduk[penyusun.KodeProduk]["data"][
                    index
                ]["hargasatuan"]
                kuantitas = models.KonversiMaster.objects.get(
                    KodePenyusun=penyusun
                ).Kuantitas
                kuantitas += 0.025 * kuantitas
                hargabahanbakufg = hargapenyusun * kuantitas
                hargafg += hargabahanbakufg
                dummy["totalharga"] = hargabahanbakufg
                dummy["kuantitas"] = kuantitas
                dummy["harga"] = hargapenyusun
                datapenyusun[penyusun.KodeProduk] = dummy

            dummy2 = {}
            dummy2["penyusun"] = datapenyusun
            dummy2["hargafg"] = hargafg

            dataperbulan[index] = dummy2
        datahargafgartikel[artikel] = dataperbulan

    """Section Display"""
    datadisplay = models.Display.objects.all()
    datahargafgdisplay = {}

    # for display in datadisplay:
    #     dataperbulan = {}
    #     modelsperbulan = {}
    #     for index,hari in enumerate(last_days[:stopindex]):
    #         ambilpenyu

    # print(datahargafgartikel)
    # print(asdasd)
    return datahargafgartikel


def getbarangmasuk(last_days, stopindex, awaltahun):
    rekapbarangmasukperbulan = {}
    for index, hari in enumerate(last_days[:stopindex]):
        if index == 0:
            databahanbakumasuk = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__lte=hari, NoSuratJalan__Tanggal__gte=awaltahun
            )
        else:
            databahanbakumasuk = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal__lte=hari,
                NoSuratJalan__Tanggal__gt=last_days[index - 1],
            )
        nilaibahanbakumasuk = 0
        for item in databahanbakumasuk:
            biaya = item.Harga * item.Jumlah
            nilaibahanbakumasuk += biaya
            item.totalbiaya = biaya

        rekapbarangmasukperbulan[index] = {
            "data": databahanbakumasuk,
            "total": nilaibahanbakumasuk,
        }
    # print("tes")
    # print(rekapbarangmasukperbulan)
    # print(asdasd)
    return rekapbarangmasukperbulan


def detaillaporanbarangmasuk(request):
    if len(request.GET) > 0:
        print(request.GET)
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])
        bahanbakumasuk = getbarangmasuk(last_days, index, awaltahun)
        print(bahanbakumasuk)

        return render(
            request,
            "ppic/detaillaporanbarangmasuk.html",
            {
                "sjp": bahanbakumasuk[index - 1]["data"],
                "totalbiayamasuk": bahanbakumasuk[index - 1]["total"],
                "bulan": bulan,
            },
        )


def getstokgudang(awaltahun, last_days, stopindex):
    bahanbaku = models.Produk.objects.all()
    bahangudangperbulan = {}
    rekaphargabahanbakugudangperbulan = 0
    for index, hari in enumerate(last_days[:stopindex]):
        dummy = {}
        for produk in bahanbaku:

            barangmasukobj = models.DetailSuratJalanPembelian.objects.filter(
                KodeProduk=produk,
                NoSuratJalan__Tanggal__gte=awaltahun,
                NoSuratJalan__Tanggal__lte=hari,
            )
            barangkeluarobj = models.TransaksiGudang.objects.filter(
                KodeProduk=produk, tanggal__gte=awaltahun, tanggal__lte=hari
            )

            tanggalbarangmasukobj = barangmasukobj.values_list(
                "NoSuratJalan__Tanggal", flat=True
            ).distinct()
            tanggalbarangkeluar = barangkeluarobj.values_list(
                "tanggal", flat=True
            ).distinct()
            listtanggal = sorted(
                list(set(tanggalbarangmasukobj.union(tanggalbarangkeluar)))
            )
            print(index, produk, listtanggal)
            jumlahawal = 0
            totalbiayaawal = 0
            for tanggal in listtanggal:
                jumlahmasukperhari = 0
                hargamasuktotalperhari = 0
                hargamasuksatuanperhari = 0
                jumlahkeluarperhari = 0
                hargakeluartotalperhari = 0
                hargakeluarsatuanperhari = 0
                jumlahmasukperhari = 0

                sjpobj = barangmasukobj.filter(NoSuratJalan__Tanggal=tanggal)
                if sjpobj.exists():
                    for k in sjpobj:
                        hargamasuktotalperhari += k.Harga * k.Jumlah
                        jumlahmasukperhari += k.Jumlah
                        hargamasuksatuanperhari += (
                            hargamasuktotalperhari / jumlahmasukperhari
                        )
                else:
                    hargamasuktotalperhari = 0
                    jumlahmasukperhari = 0
                    hargamasuksatuanperhari = 0

                transaksigudangobj = barangkeluarobj.filter(tanggal=tanggal)
                if transaksigudangobj.exists():
                    for k in transaksigudangobj:
                        jumlahkeluarperhari += k.jumlah
                        hargakeluartotalperhari += k.jumlah * hargasatuanawal
                    hargakeluarsatuanperhari += (
                        hargakeluartotalperhari / jumlahkeluarperhari
                    )
                else:
                    hargakeluartotalperhari = 0
                    hargakeluarsatuanperhari = 0
                    jumlahkeluarperhari = 0

                # print(produk)
                # print("Tanggal : ", tanggal)
                # print("Sisa Stok Hari Sebelumnya : ", jumlahawal)
                # print("harga awal Hari Sebelumnya :", hargasatuanawal)
                # print("harga total Hari Sebelumnya :", totalbiayaawal)
                # print("Jumlah Masuk : ", jumlahmasukperhari)
                # print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
                # print("Harga Total Masuk : ", hargamasuktotalperhari)
                # print("Jumlah Keluar : ", jumlahkeluarperhari)
                # print("Harga Keluar : ", hargakeluarsatuanperhari)
                # print(
                #     "Harga Total Keluar : ",
                #     hargakeluarsatuanperhari * jumlahkeluarperhari,
                # )
                jumlahawal += jumlahmasukperhari - jumlahkeluarperhari
                totalbiayaawal += hargamasuktotalperhari - hargakeluartotalperhari
                try:
                    hargasatuanawal = totalbiayaawal / jumlahawal
                except ZeroDivisionError:
                    hargasatuanawal = 0

                # print("Sisa Stok Hari Ini : ", jumlahawal)
                # print("harga awal Hari Ini :", hargasatuanawal)
                # print("harga total Hari Ini :", totalbiayaawal, "\n")
            dummy[produk] = {
                "hargasatuan": hargasatuanawal,
                "jumlah": jumlahawal,
                "totalbiaya": totalbiayaawal,
            }
            rekaphargabahanbakugudangperbulan += totalbiayaawal
        bahangudangperbulan[index] = {
            "data": dummy,
            "total": rekaphargabahanbakugudangperbulan,
        }
    return bahangudangperbulan


def detaillaporanbaranstokgudang(request):
    if len(request.GET) > 0:
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)

        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"])
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])
        bahanbakuperbulan = getstokgudang(awaltahun, last_days, index + 1)
        print(bahanbakuperbulan)
        return render(
            request,
            "ppic/detaillaporanstokgudang.html",
            {"stokgudang": bahanbakuperbulan, "bulan": bulan},
        )


def detaillaporanstokfg(request):
    if len(request.GET) > 0:
        print(request.GET)
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])
        datastokgudang, bahanbakusisafg = getstokartikelfg(last_days, index, awaltahun)
        return render(
            request,
            "ppic/detaillaporanstokfg.html",
            {
                "stokfg": datastokgudang[index - 1],
                "sisabahafg": bahanbakusisafg,
                "bulan": bulan,
            },
        )


def getstokartikelfg(last_days, stopindex, awaltahun):
    datastokfgperbulan = {}
    datahargafgartikel = gethargafgperbulan(last_days, stopindex, awaltahun)
    hargaakhirbulanperproduk = gethargapurchasingperbulan(
        last_days, stopindex, awaltahun
    )
    # print(hargaakhirbulanperproduk)

    datastokbahanbakufg = {}
    for index, hari in enumerate(last_days[:stopindex]):
        if index == 0:
            datatransaksiproduksi = models.TransaksiProduksi.objects.filter(
                Tanggal__lte=hari, Tanggal__gte=awaltahun, Jenis="Mutasi"
            )
            databarangkeluar = models.DetailSPPB.objects.filter(
                NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gte=awaltahun
            )

        else:
            datatransaksiproduksi = models.TransaksiProduksi.objects.filter(
                Tanggal__lte=hari, Tanggal__gt=awaltahun, Jenis="Mutasi"
            )
            databarangkeluar = models.DetailSPPB.objects.filter(
                NoSPPB__Tanggal__lte=hari, NoSPPB__Tanggal__gte=awaltahun
            )
            print(datatransaksiproduksi)
            print(databarangkeluar)

            # print(asd)

        # print("tes", hari, datahargafgartikel)
        # print(asdas)

        jumlahkumulatifbiayaperbulan = 0
        dumystok = {}
        dummy = {}

        datamodelsisabarangfg = {}
        bahanbakurequestkefg = models.Produk.objects.all()
        listbahanbaku = []
        for bahanbaku in bahanbakurequestkefg:
            stokdifg = 0
            datatransaksigudangfg = models.TransaksiGudang.objects.filter(
                tanggal__gte=awaltahun,
                tanggal__lte=hari,
                Lokasi__NamaLokasi="FG",
                KodeProduk=bahanbaku,
            )
            if datatransaksigudangfg.exists():
                stokdifg = datatransaksigudangfg.aggregate(total=Sum("jumlah"))["total"]
            # print(stokdifg)
            hargasatuan = hargaakhirbulanperproduk[bahanbaku]["data"][index][
                "hargasatuan"
            ]
            datamodelsisabarangfg[bahanbaku] = {
                "stok": stokdifg,
                "Hargasatuan": hargasatuan,
                "Hargatotal": 0,
            }
        datastokbahanbakufg[index] = datamodelsisabarangfg
        # print(datahargafgartikel)

        semuaartikel = models.Artikel.objects.all()
        for dataartikel in semuaartikel:
            # cek mutasi produk
            stokawal = 0
            jumlahartikelmutasiperbulan = datatransaksiproduksi.filter(
                KodeArtikel=dataartikel
            )
            if jumlahartikelmutasiperbulan.exists():
                totaltransaksimutasi = jumlahartikelmutasiperbulan.aggregate(
                    total=Sum("Jumlah")
                )["total"]
                stokawal += totaltransaksimutasi
                
            jumlahkeluarartikelmutasiperbulan = databarangkeluar.filter(
                DetailSPK__KodeArtikel=dataartikel
            )
            if jumlahkeluarartikelmutasiperbulan.exists():
                print(hari, jumlahkeluarartikelmutasiperbulan)
                # print(asdas)
                totaltransaksikeuar = jumlahkeluarartikelmutasiperbulan.aggregate(
                    total=Sum("Jumlah")
                )["total"]
                stokawal -= totaltransaksikeuar
                totalbiaya = datahargafgartikel[dataartikel][index]["hargafg"] * stokawal

                dummy[dataartikel] = {
                "jumlah": stokawal,
                "hargafg": datahargafgartikel[dataartikel][index]["hargafg"],
                "biaya": totalbiaya,
            }
                # for x in datahargafgartikel[dataartikel][index]['penyusun']:
                # print("\n\n", datahargafgartikel.keys)
                versiterakhirperbulan = (
                    models.Penyusun.objects.filter(
                        KodeArtikel=dataartikel, versi__lte=hari
                    )
                    .values_list("versi", flat=True)
                    .distinct()
                    .order_by("versi")
                    .last()
                )
                penyusunversiterpilih = models.Penyusun.objects.filter(
                    KodeArtikel=dataartikel,
                    versi=versiterakhirperbulan,
                    Lokasi__NamaLokasi="FG",
                )
                print('ini versi : ',versiterakhirperbulan)
                print('ini penyusun terpilih : ',penyusunversiterpilih)
                if penyusunversiterpilih.exists():
                    for bahanfg in penyusunversiterpilih:
                        kuantitas = models.KonversiMaster.objects.get(
                            KodePenyusun=bahanfg
                        ).Kuantitas
                        kuantitas += kuantitas * 0.0025
                        datamodelsisabarangfg[bahanfg.KodeProduk]["stok"] -= (
                            kuantitas * totaltransaksikeuar
                        )
                        hargasatuan = datahargafgartikel[dataartikel][index][
                            "penyusun"
                        ][bahanfg.KodeProduk]["harga"]
                        hargatotal = (
                            hargasatuan
                            * datamodelsisabarangfg[bahanfg.KodeProduk]["stok"]
                        )
                        datamodelsisabarangfg[bahanfg.KodeProduk][
                            "Hargasatuan"
                        ] = hargasatuan

                        # print(datamodelsisabarangfg)
                        # print(kuantitas * totaltransaksikeuar)
                # print(datamodelsisabarangfg)

                # print(asdas)
            # print('awal',index,dataartikel,stokawal,datahargafgartikel[dataartikel][index]["hargafg"])
            """Data Request ke FG"""

            jumlahkumulatifbiayaperbulan += totalbiaya
        datastokfgperbulan[index] = {
            "data": dummy,
            "total": jumlahkumulatifbiayaperbulan,
        }
    """Menghitung total persediaan bahan baku fg"""
    total = 0
    for item in datamodelsisabarangfg.values():
        item["Hargatotal"] = item["stok"] * item["Hargasatuan"]
        total += item["Hargatotal"]
    datamodelsisabarangfg["total"] = total
    """
    Data Models
    2: {'data': {<Artikel: 9010/AC>: {'jumlah': 1365, 'hargafg': 40993.59298941417, 'biaya': 55956254.43055034}, <Artikel: 5111/EXP>: {'jumlah': 222, 'hargafg': 400.0974675766822, 'biaya': 88821.63780202346}}, 'total': 56045076.068352364}}  
    """
    print(datastokfgperbulan[1])
    print(asdas)
    return datastokfgperbulan, datamodelsisabarangfg


def getsaldoawalgudang(request):
    if len(request.GET) > 0:
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        data = saldogudang(last_days, index, awaltahun)
        # print(data)
        # print(adas)
        return render(
            request,
            "ppic/detailstockgudang.html",
            {
                "data": data,
            },
        )


def saldogudang(last_days, stopindex, awaltahun):
    saldoawal = {}
    saldoakhirgudang = {}
    totalbiayasaldoawal = 0
    bahanbaku = models.Produk.objects.all()
    for produk in bahanbaku:
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
            IDBahanBaku=produk, Tanggal__gte=awaltahun, IDLokasi__NamaLokasi="Gudang"
        )
        if saldoawalobj.exists():
            saldoawalobj = saldoawalobj.first()
            totalbiayaawal = saldoawalobj.Harga * saldoawalobj.Jumlah
            hargasatuanawal = saldoawalobj.Harga
            jumlahawal = saldoawalobj.Jumlah

        else:
            totalbiayaawal = 0
            hargasatuanawal = 0
            jumlahawal = 0

        totalbiayasaldoawal += totalbiayaawal
        produk.hargasatuanawal = hargasatuanawal
        produk.totalbiayaawal = totalbiayaawal
        produk.jumlahawal = jumlahawal

    hargaakhirbulanperproduk = gethargapurchasingperbulan(
        last_days, stopindex, awaltahun
    )
    print(hargaakhirbulanperproduk)
    # print(asd)
    dataproduk = models.Produk.objects.all()
    for index, hari in enumerate(last_days[:stopindex]):
        totalbiayasaldoakhirperbulan = 0
        for produk in dataproduk:
            hargaproduk = hargaakhirbulanperproduk[produk]["data"][index]["hargatotal"]
            totalbiayasaldoakhirperbulan += hargaproduk
        saldoakhirgudang[index] = totalbiayasaldoakhirperbulan
        if index == 0:
            saldoawal[index] = totalbiayasaldoawal
        else:
            saldoawal[index] = saldoakhirgudang[index - 1]

    # print(saldoawal)
    # print(saldoakhirgudang)

    # print(asdasd)
    hargaakhirperbulan = {}
    # print(hargaakhirbulanperproduk)

    """SAVE ERROR"""
    nilaiakhir = 0
    for artikel, data in hargaakhirbulanperproduk.items():
        hargaakhirperbulan[artikel] = data["data"][index]
        nilaiakhir += data["data"][index]["hargatotal"]

    # print(hargaakhirperbulan)

    data = {
        "saldoawal": saldoawal,
        "saldoakhir": saldoakhirgudang,
        "datasaldoawal": bahanbaku,
        "hargaakhirbulanperproduk": {"data": hargaakhirperbulan, "total": nilaiakhir},
    }
    return data


"""
Perhitungan Saldo Gudang perlu di pecah antara saldo awal dan saldo akhir di laporan besar
"""


def getstokbahanproduksi(last_days, stopindex, awaltahun):
    stokawalbahanproduksi = {}
    totalbiayasaldoawal = 0
    totalbiayasaldoawal = 0
    # print(awaltahun)
    bahanbaku = models.Produk.objects.all()
    # bahanbaku = models.Produk.objects.filter(KodeProduk = 'tesksbb')
    for produk in bahanbaku:
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
            Tanggal__gte=awaltahun,
            IDLokasi__NamaLokasi__in=("WIP", "FG"),
            IDBahanBaku=produk,
        )
        # print(saldoawalobj)
        # print(asdas)
        # print(saldoawalobj)

        totalbiayaawal = 0
        hargasatuanawal = 0
        jumlahawal = 0
        if saldoawalobj.exists():
            # saldoawalobj = saldoawalobj.first()
            # HARGA JANGAN LANGSUNG DI JUMLAH. PAKAI KONSEP KSBB. DI KALI DULU JUMLAH DAN TOTAL BIAYA NANTI HARGA SATUANNYA TOTAL/Jumlah
            for dataproduk in saldoawalobj:
                totalbiayaawal += dataproduk.Harga * dataproduk.Jumlah
                jumlahawal += dataproduk.Jumlah
            hargasatuanawal = totalbiayaawal / jumlahawal

        totalbiayasaldoawal += totalbiayaawal
        produk.hargasatuanawal = hargasatuanawal
        produk.totalbiayaawal = totalbiayaawal
        produk.jumlahawal = jumlahawal

    stokawalbahanproduksi[0] = {"data": bahanbaku, "total": totalbiayasaldoawal}

    stokawalbahanproduksiwip = {}
    totalbiayasaldoawal = 0
    totalbiayasaldoawal = 0
    print(awaltahun)
    bahanbaku = models.Produk.objects.all()
    for produk in bahanbaku:
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
            Tanggal__gte=awaltahun,
            IDLokasi__NamaLokasi="WIP",
            IDBahanBaku=produk,
        )
        print(saldoawalobj)
        # print(saldoawalobj)

        totalbiayaawal = 0
        hargasatuanawal = 0
        jumlahawal = 0
        if saldoawalobj.exists():
            # saldoawalobj = saldoawalobj.first()
            # HARGA JANGAN LANGSUNG DI JUMLAH. PAKAI KONSEP KSBB. DI KALI DULU JUMLAH DAN TOTAL BIAYA NANTI HARGA SATUANNYA TOTAL/Jumlah
            for dataproduk in saldoawalobj:
                totalbiayaawal += dataproduk.Harga * dataproduk.Jumlah
                jumlahawal += dataproduk.Jumlah
            hargasatuanawal = totalbiayaawal / jumlahawal

        totalbiayasaldoawal += totalbiayaawal
        produk.hargasatuanawal = hargasatuanawal
        produk.totalbiayaawal = totalbiayaawal
        produk.jumlahawal = jumlahawal

    stokawalbahanproduksiwip[0] = {"data": bahanbaku, "total": totalbiayasaldoawal}

    stokawalbahanproduksifg = {}
    totalbiayasaldoawal = 0
    totalbiayasaldoawal = 0

    bahanbaku = models.Produk.objects.all()

    for produk in bahanbaku:
        saldoawalobj = models.SaldoAwalBahanBaku.objects.filter(
            Tanggal__gte=awaltahun,
            IDLokasi__NamaLokasi="FG",
            IDBahanBaku=produk,
        )

        # print(saldoawalobj)

        totalbiayaawal = 0
        hargasatuanawal = 0
        jumlahawal = 0
        if saldoawalobj.exists():
            # saldoawalobj = saldoawalobj.first()
            # HARGA JANGAN LANGSUNG DI JUMLAH. PAKAI KONSEP KSBB. DI KALI DULU JUMLAH DAN TOTAL BIAYA NANTI HARGA SATUANNYA TOTAL/Jumlah
            for dataproduk in saldoawalobj:
                totalbiayaawal += dataproduk.Harga * dataproduk.Jumlah
                jumlahawal += dataproduk.Jumlah
            hargasatuanawal = totalbiayaawal / jumlahawal

        totalbiayasaldoawal += totalbiayaawal
        produk.hargasatuanawal = hargasatuanawal
        produk.totalbiayaawal = totalbiayaawal
        produk.jumlahawal = jumlahawal

    stokawalbahanproduksifg[0] = {"data": bahanbaku, "total": totalbiayasaldoawal}

    # pritn(asdas)
    return stokawalbahanproduksi, stokawalbahanproduksiwip, stokawalbahanproduksifg


def detaillaporanbaranstokwip(request):
    if len(request.GET) > 0:
        print(request.GET)

        bulan = request.GET["bulan"]
        waktuobj = datetime.strptime(bulan, "%Y-%m")
        print(waktuobj.month)
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = waktuobj.month
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        datawip = getstokbahanproduksi(last_days, index, awaltahun)
        return render(request, "ppic/detaillaporanstokwip.html")


def perhitunganpersediaan(
    last_days, stopindex, awaltahun, stockgudang, bahanbakumasuk, barangkeluar, barangfg
):
    listbulan = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "Novermber",
        "Desember",
    ]
    datakirim = {}
    datasaldoawalbahanproduksi = {}
    datastokwipawal, datastokwip, datastokfg = getstokbahanproduksi(
        last_days, stopindex, awaltahun
    )
    # print(barangfg)
    # {0: {'data': {<Artikel: 1>: {'jumlah': 2640, 'hargafg': 410000.0, 'biaya': 1082400000.0}, <Artikel: 5171/AC>: {'jumlah': 13571, 'hargafg': 390.31990242, 'biaya': 5297031.39574182}, <Artikel: 5115/AC#1>: {'jumlah': 2130, 'hargafg': 803.5997990999999, 'biaya': 1711667.5720829999}, <Artikel: 9010/ACC>: {'jumlah': 19837, 'hargafg': 1071.739732065, 'biaya': 21260101.064973406}}, 'total': 1110668800.0327983}}

    # print(datastokwipawal)
    # {0: {'data': <QuerySet [<Artikel: 9010/AC>, <Artikel: 5111/EXP>, <Artikel: 1>, <Artikel: 2>, <Artikel: 5111#/AC>, <Artikel: 5171/AC>, <Artikel: 5115/AC#1>, <Artikel: 9010/ACC>, <Artikel: coba1>, <Artikel: coba2>, <Artikel: coba3>, <Artikel: coba4>, <Artikel: coba5>, <Artikel: coba6>]>, 'total': 12951899.692499999}}

    # print(stockgudang)
    # {'saldoawal': {0: 133299998.0, 1: 112960003.06, 2: 103280003.48}, 'saldoakhir': {0: 112960003.06, 1: 103280003.48, 2: 105643301.97218497}}

    # print(bahanbakumasuk)
    # {0: {'data': <QuerySet
    #  []>, 'total': 0}, 1: {'data': <QuerySet []>, 'total': 0}, 2: {'data': <QuerySet [<DetailSuratJalanPembelian: 3/SJP/I-2024 - 2024-03-21 A-101>, <DetailSuratJalanPembelian: 2 - 2024-03-24 A-101>, <DetailSuratJalanPembelian: III/SJP/I-2024 - 2024-03-25 A-001-02>, <DetailSuratJalanPembelian: III/SJP/I-2024 - 2024-03-25 A-101>, <DetailSuratJalanPembelian: IV/SJP/I-2024 - 2024-03-26 A-101>, <DetailSuratJalanPembelian: IV/SJP/I-2024 - 2024-03-26 B-001>, <DetailSuratJalanPembelian: 1 - 2024-03-14 B-001>, <DetailSuratJalanPembelian: 2/SJP/I-2024 - 2024-03-11 coba-001>]>, 'total': 38042000.0}}

    # print(barangkeluar)
    # {0: 255036.39385, 1: 0, 2: 41113622.22968718}
    # print(datastokwipawal)
    datasaldoawalbahanproduksi[0] = datastokwipawal[0]["total"]

    # print(asd)
    for index in range(0, stopindex):
        # print(barangkeluar[index])
        # print(index)
        if index > 0:
            datasaldoawalbahanproduksi[index] = saldowip + jumlahstokfg
        try:
            jumlahbarangkeluar = barangkeluar[index]
        except KeyError:
            jumlahbarangkeluar = 0
        try:
            jumlahbarangmasuk = bahanbakumasuk[index]["total"]
        except KeyError:
            jumlahbarangmasuk = 0
        try:
            jumlahsaldoawalgudang = stockgudang["saldoawal"][index]
        except KeyError:
            jumlahsaldoawalgudang = 0
        try:
            jumlahsaldoakhirgudang = stockgudang["saldoakhir"][index]
        except KeyError:
            jumlahsaldoakhirgudang = 0
        try:
            jumlahstokfg = barangfg[index]["total"]
        except KeyError:
            jumlahstokfg = 0
        try:
            jumlahsaldoawalproduksi = datasaldoawalbahanproduksi[index]
        except KeyError:
            jumlahsaldoawalproduksi = 0
        total = (
            jumlahsaldoawalgudang
            + jumlahsaldoawalproduksi
            + jumlahbarangmasuk
            - jumlahbarangkeluar
        )

        # print("ini total : ", total)
        saldowip = total - jumlahstokfg - jumlahsaldoakhirgudang

        """BELUM MASUKIN DATA TOTAL"""
        # print(asda)
        dummy = {
            "barangkeluar": jumlahbarangkeluar,
            "barangmasuk": jumlahbarangmasuk,
            "saldoawalgudang": jumlahsaldoawalgudang,
            "saldoakhirgudang": jumlahsaldoakhirgudang,
            "stokfg": jumlahstokfg,
            "stokawalproduksi": datasaldoawalbahanproduksi[index],
            "totalsaldo": total,
            "saldowip": saldowip,
        }

        datakirim[listbulan[index]] = dummy
    # print(datakirim)
    return datakirim


def laporanpersediaan(request):
    if len(request.GET) == 0:
        return render(request, "ppic/views_laporanpersediaanperusahaan.html")
    else:

        bulan = request.GET["bulan"]
        waktuobj = datetime.strptime(bulan, "%Y-%m")
        print(waktuobj.month)
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = int(waktuobj.month)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        """SECTION BARANG KELUAR"""
        datadetailsppb, totalbiayakeluar, datapenyusun, datalistbarangkeluar = (
            getbarangkeluar(last_days, index, awaltahun)
        )
        """SECTION BARANG MASUK"""
        barangmasuk = getbarangmasuk(last_days, index, awaltahun)
        """SECTION STOCK GUDANG"""
        baranggudang = saldogudang(last_days, index, awaltahun)
        """SECTION FG"""
        barangfg, bahanbakusisafg = getstokartikelfg(last_days, index, awaltahun)
        """SECTION WIP (Skip dulu)"""
        dataperhitunganpersediaan = perhitunganpersediaan(
            last_days,
            index,
            awaltahun,
            baranggudang,
            barangmasuk,
            totalbiayakeluar,
            barangfg,
        )

        print("\n")
        print(dataperhitunganpersediaan)
        return render(
            request,
            "ppic/views_laporanpersediaanperusahaan.html",
            {
                "modeldata": dataperhitunganpersediaan,
                "waktu": bulan,
                "tahun": waktuobj.year,
            },
        )


def detaillaporanbaranstokawalproduksi(request):
    if len(request.GET) > 0:
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])
        datawip, datastokwip, datastokfg = getstokbahanproduksi(
            last_days, index, awaltahun
        )
        print(dir(datawip[0]["data"][0]))
        return render(
            request,
            "ppic/detailstockawalproduksi.html",
            {
                "stokawal": datawip[0],
            },
        )


def detaillaporanbaranstokawalgudang(request):
    if len(request.GET) > 0:
        bulan = request.GET["bulan"]
        waktu = request.GET["waktu"]
        waktuobj = datetime.strptime(waktu, "%Y-%m")
        awaltahun = datetime(waktuobj.year, 1, 1)
        listbulan = [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "Novermber",
            "Desember",
        ]
        index = listbulan.index(request.GET["bulan"]) + 1
        # print(index)
        last_days = []
        for month in range(1, 13):
            last_day = calendar.monthrange(waktuobj.year, month)[1]
            last_days.append(date(waktuobj.year, month, last_day))
        # print(last_days)
        # print(last_days[:index+1])
        datasaldoawalgudang = saldogudang(last_days, index, awaltahun)
        print(datasaldoawalgudang)
        return render(
            request,
            "ppic/detailstockawalgudang.html",
            {
                "stokawal": datasaldoawalgudang["datasaldoawal"],
                "saldoawal": datasaldoawalgudang["saldoawal"][0],
            },
        )


def read_transactionlog(request):
    dataobj = models.transactionlog.objects.all()
    for i in dataobj:
        i.waktu = i.waktu.strftime("%Y-%m-%d %H:%M:%S")
    return render(request, "ppic/transactionlog.html", {"data": dataobj})


# Export EXCEL BELUM


def exportlaporanbulananexcel(request):
    print(request.GET["bulan"])
    bulan = request.GET["bulan"]
    waktuobj = datetime.strptime(bulan, "%Y-%m")
    print(waktuobj.month)
    awaltahun = datetime(waktuobj.year, 1, 1)
    listbulan = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "Novermber",
        "Desember",
    ]
    index = int(waktuobj.month)
    last_days = []
    for month in range(1, 13):
        last_day = calendar.monthrange(waktuobj.year, month)[1]
        last_days.append(date(waktuobj.year, month, last_day))
    datadetailsppb, totalbiayakeluar, datapenyusun, datalistbarangkeluar = (
        getbarangkeluar(last_days, index, awaltahun)
    )
    """SECTION BARANG MASUK"""
    barangmasuk = getbarangmasuk(last_days, index, awaltahun)
    """SECTION STOCK GUDANG"""
    baranggudang = saldogudang(last_days, index, awaltahun)
    """SECTION FG"""
    barangfg, bahanbakusisafg = getstokartikelfg(last_days, index, awaltahun)
    """SECTION STOK AWAL PRODUKSI"""
    datawip, datastokwiponly, datastokfgonly = getstokbahanproduksi(
        last_days, index, awaltahun
    )
    """SECTION WIP (Skip dulu)"""
    dataperhitunganpersediaan = perhitunganpersediaan(
        last_days,
        index,
        awaltahun,
        baranggudang,
        barangmasuk,
        totalbiayakeluar,
        barangfg,
    )
    print(barangmasuk)

    """PEMBUATAN EXCEL"""
    """ 1. sheet untuk laporan persediaan"""
    df = pd.DataFrame.from_dict(
        dataperhitunganpersediaan[listbulan[waktuobj.month - 1]], orient="index"
    ).T
    """2. Sheet untuk laporan barang masuk"""
    datamodelmasuk = {
        "Tanggal Masuk": [],
        "No Surat Jalan": [],
        "Supplier": [],
        "Kode Produk": [],
        "Satuan": [],
        "Harga Satuan": [],
        "Jumlah": [],
        "Harga Total": [],
    }
    for masuk in barangmasuk[index - 1]["data"]:
        print(masuk)
        datamodelmasuk["Tanggal Masuk"].append(masuk.NoSuratJalan.Tanggal)
        datamodelmasuk["No Surat Jalan"].append(masuk.NoSuratJalan.NoSuratJalan)
        datamodelmasuk["Supplier"].append(masuk.NoSuratJalan.supplier)
        datamodelmasuk["Kode Produk"].append(masuk.KodeProduk.KodeProduk)
        datamodelmasuk["Satuan"].append(masuk.KodeProduk.unit)
        datamodelmasuk["Harga Satuan"].append(masuk.Harga)
        datamodelmasuk["Harga Total"].append(masuk.Harga * masuk.Jumlah)
        datamodelmasuk["Jumlah"].append(masuk.Jumlah)

    print(datamodelmasuk)
    df2 = pd.DataFrame(datamodelmasuk)
    """3. Sheet untuk Barang Keluar"""
    print(datadetailsppb)
    datamodelkeluar = {
        "Tanggal Keluar": [],
        "No SPPB": [],
        "NO SPK": [],
        "Artikel": [],
        "Jumlah": [],
        "Harga FG": [],
        "Total Biaya": [],
    }

    for data in datadetailsppb:
        print(data)
        datamodelkeluar["Jumlah"].append(data.Jumlah)
        datamodelkeluar["Artikel"].append(data.DetailSPK.KodeArtikel)
        datamodelkeluar["Harga FG"].append(data.hargafg)
        datamodelkeluar["NO SPK"].append(data.DetailSPK.NoSPK)
        datamodelkeluar["No SPPB"].append(data.NoSPPB)
        datamodelkeluar["Total Biaya"].append(data.totalharga)
        datamodelkeluar["Tanggal Keluar"].append(data.NoSPPB.Tanggal)

    print(datamodelkeluar)
    totalbiayakeluar = sum(datamodelkeluar["Total Biaya"])
    dfdatakeluar = pd.DataFrame(datamodelkeluar)

    """4. Sheet Stock Awal Gudang"""
    datamodelstockawalgudang = {
        "Kode Produk": [],
        "Nama Produk": [],
        "Unit": [],
        "Harga Satuan": [],
        "Jumlah": [],
        "Total Biaya": [],
    }
    print(baranggudang["datasaldoawal"])
    for item in baranggudang["datasaldoawal"]:
        datamodelstockawalgudang["Kode Produk"].append(item.KodeProduk)
        datamodelstockawalgudang["Unit"].append(item.unit)
        datamodelstockawalgudang["Nama Produk"].append(item.NamaProduk)
        datamodelstockawalgudang["Jumlah"].append(item.jumlahawal)
        datamodelstockawalgudang["Total Biaya"].append(item.totalbiayaawal)
        datamodelstockawalgudang["Harga Satuan"].append(item.hargasatuanawal)

    print(datamodelstockawalgudang)
    dfstokgudang = pd.DataFrame(datamodelstockawalgudang)

    """5. Sheet Stock Awal Produksi"""
    datamodelstockawalwip = {
        "Kode Produk": [],
        "Nama Produk": [],
        "Unit": [],
        "Harga Satuan": [],
        "Jumlah": [],
        "Total Biaya": [],
    }
    for stokawal in datawip[0]["data"]:
        print(stokawal)
        datamodelstockawalwip["Harga Satuan"].append(stokawal.hargasatuanawal)
        datamodelstockawalwip["Jumlah"].append(stokawal.jumlahawal)
        datamodelstockawalwip["Kode Produk"].append(stokawal.KodeProduk)
        datamodelstockawalwip["Nama Produk"].append(stokawal.NamaProduk)
        datamodelstockawalwip["Total Biaya"].append(stokawal.totalbiayaawal)
        datamodelstockawalwip["Unit"].append(stokawal.unit)
    print(datawip)
    dfstokawalwip = pd.DataFrame(datamodelstockawalwip)
    # print(asdas)

    buffer = BytesIO()

    # Use pandas to write DataFrame to the BytesIO buffer
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, startrow=1, sheet_name="Laporan Persediaan")
        df2.to_excel(writer, index=False, startrow=1, sheet_name="Barang Masuk")
        dfdatakeluar.to_excel(
            writer, index=False, startrow=1, sheet_name="Barang Keluar"
        )
        dfstokgudang.to_excel(
            writer, index=False, startrow=1, sheet_name="Saldo Awal Gudang"
        )
        dfstokawalwip.to_excel(writer, index=False, startrow=1, sheet_name="Saldo WIP")

    # Load the workbook from the buffer
    buffer.seek(0)
    wb = load_workbook(buffer)
    ws = wb["Laporan Persediaan"]
    ws2 = wb["Barang Masuk"]
    ws3 = wb["Barang Keluar"]

    # Insert header "Januari" above the table
    ws["A1"] = listbulan[waktuobj.month - 1]
    ws2["A1"] = listbulan[waktuobj.month - 1]
    ws3["A1"] = listbulan[waktuobj.month - 1]

    # Custom WS Barang Keluar
    baristerakhirws3 = ws3.max_row
    kolomterakhirws3 = ws3.max_column
    hurufkolomws3 = get_column_letter(kolomterakhirws3)
    print("Baris Terakhir : ", baristerakhirws3)
    print("Kolom Terakhir : ", kolomterakhirws3)
    print("Huruf Terakhir : ", hurufkolomws3)
    ws3.cell(row=baristerakhirws3 + 1, column=kolomterakhirws3 - 1, value="Total Biaya")
    ws3.cell(row=baristerakhirws3 + 1, column=kolomterakhirws3, value=totalbiayakeluar)
    # print(asdas)
    # Save the workbook back to the buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Create the HTTP response
    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename=laporanpersediaan{bulan}.xlsx"
    )

    return response


def create_dataframeproduksi(data):
    datamodel = {
        "Kode Produk": [],
        "Nama Produk": [],
        "Unit": [],
        "Harga Satuan": [],
        "Jumlah": [],
        "Total Biaya": [],
    }
    for item in data["data"]:
        datamodel["Harga Satuan"].append(item.hargasatuanawal)
        datamodel["Jumlah"].append(item.jumlahawal)
        datamodel["Kode Produk"].append(item.KodeProduk)
        datamodel["Nama Produk"].append(item.NamaProduk)
        datamodel["Total Biaya"].append(item.totalbiayaawal)
        datamodel["Unit"].append(item.unit)
    return pd.DataFrame(datamodel)


# Cek Perhitungan Laporan


def exportlaporanbulananexcelkeseluruhan(request):
    bulan = request.GET["bulan"]
    waktuobj = datetime.strptime(bulan, "%Y-%m")

    awaltahun = datetime(waktuobj.year, 1, 1)
    listbulan = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "Novermber",
        "Desember",
    ]
    index = int(waktuobj.month)
    last_days = []
    for month in range(1, 13):
        last_day = calendar.monthrange(waktuobj.year, month)[1]
        last_days.append(date(waktuobj.year, month, last_day))
    datadetailsppb, totalbiayakeluar, datapenyusun, listdatadetailsppb = (
        getbarangkeluar(last_days, index, awaltahun)
    )
    """SECTION HARGA AKHIR PERBULAN """
    hargaakhirbulan = gethargapurchasingperbulan(last_days, index, awaltahun)
    """SECTION BARANG MASUK"""
    barangmasuk = getbarangmasuk(last_days, index, awaltahun)
    """SECTION STOCK GUDANG"""
    baranggudang = saldogudang(last_days, index, awaltahun)
    print(baranggudang)
    # print(asdas)
    """SECTION FG"""
    barangfg, bahanbakusisafg = getstokartikelfg(last_days, index, awaltahun)
    # print(barangfg)
    # print(asdas)
    """SECTION STOK AWAL PRODUKSI"""
    datawip, datastokwiponly, datastokfgonly = getstokbahanproduksi(
        last_days, index, awaltahun
    )
    """SECTION WIP (Skip dulu)"""
    dataperhitunganpersediaan = perhitunganpersediaan(
        last_days,
        index,
        awaltahun,
        baranggudang,
        barangmasuk,
        totalbiayakeluar,
        barangfg,
    )

    """PEMBUATAN EXCEL"""
    """ 1. sheet untuk laporan persediaan"""
    dfpersediaan = pd.DataFrame.from_dict(
        dataperhitunganpersediaan[listbulan[waktuobj.month - 1]], orient="index"
    ).T
    listpersediaan = []
    for key, value in dataperhitunganpersediaan.items():
        df = pd.DataFrame.from_dict(value, orient="index").T
        listpersediaan.append(df)
    """2. Sheet untuk laporan barang masuk"""
    print(listpersediaan)
    # print(asdas)
    listdatamodelmasuk = []
    # print(barangmasuk)
    for bulan, value in barangmasuk.items():
        datamodelmasuk = {
            "Tanggal Masuk": [],
            "No Surat Jalan": [],
            "Supplier": [],
            "Kode Produk": [],
            "Satuan": [],
            "Harga Satuan": [],
            "Jumlah": [],
            "Harga Total": [],
        }
        key = value["data"]
        # print("\n\n", masuk)
        for masuk in key:
            datamodelmasuk["Tanggal Masuk"].append(masuk.NoSuratJalan.Tanggal)
            datamodelmasuk["No Surat Jalan"].append(masuk.NoSuratJalan.NoSuratJalan)
            datamodelmasuk["Supplier"].append(masuk.NoSuratJalan.supplier)
            datamodelmasuk["Kode Produk"].append(masuk.KodeProduk.KodeProduk)
            datamodelmasuk["Satuan"].append(masuk.KodeProduk.unit)
            datamodelmasuk["Harga Satuan"].append(masuk.Harga)
            datamodelmasuk["Harga Total"].append(masuk.Harga * masuk.Jumlah)
            datamodelmasuk["Jumlah"].append(masuk.Jumlah)
        # print(datamodelmasuk)
        dfmasuk = pd.DataFrame(datamodelmasuk)
        listdatamodelmasuk.append(dfmasuk)

    """3. Sheet untuk Barang Keluar"""
    print("detail sppb \n\n", listdatadetailsppb)
    # print(asdasdas)

    listdatamodelkeluar = []
    for item in listdatadetailsppb:
        datamodelkeluar = {
            "Tanggal Keluar": [],
            "No SPPB": [],
            "NO SPK": [],
            "Artikel": [],
            "Jumlah": [],
            "Harga FG": [],
            "Total Biaya": [],
        }
        for data in item:
            print(data)
            datamodelkeluar["Jumlah"].append(data.Jumlah)
            datamodelkeluar["Artikel"].append(data.DetailSPK.KodeArtikel)
            datamodelkeluar["Harga FG"].append(data.hargafg)
            datamodelkeluar["NO SPK"].append(data.DetailSPK.NoSPK)
            datamodelkeluar["No SPPB"].append(data.NoSPPB)
            datamodelkeluar["Total Biaya"].append(data.totalharga)
            datamodelkeluar["Tanggal Keluar"].append(data.NoSPPB.Tanggal)
        df = pd.DataFrame(datamodelkeluar)
        listdatamodelkeluar.append(df)
    # print(listdatamodelkeluar)
    # print(adsasd)

    """4. Sheet Stock Bahan Baku Gudang"""

    # print(hargaakhirbulan)
    data_per_bulan = {i: {} for i in range(12)}
    for produk, values in hargaakhirbulan.items():
        for bulan_index, detail in values["data"].items():
            if bulan_index not in data_per_bulan:
                data_per_bulan[bulan_index] = {}
            data_per_bulan[bulan_index][produk] = detail

    """5. Sheet Stock Awal Produksi"""
    liststokawalproduksi = []
    dfstokawalproduksi = create_dataframeproduksi(datawip[0])
    liststokawalproduksi.append(dfstokawalproduksi)

    # Proses datastokwiponly
    dfstokawalwip = create_dataframeproduksi(datastokwiponly[0])
    liststokawalproduksi.append(dfstokawalwip)

    # Proses datastokfgonly
    dfstokawalfg = create_dataframeproduksi(datastokfgonly[0])
    liststokawalproduksi.append(dfstokawalfg)
    print(liststokawalproduksi)

    """6. SHEET STOK BARANG FG"""
    # print("\n\n")
    listdataartikelfg = []
    for bulan, data in barangfg.items():
        datamodelsartikelfg = {
            "Kode Artikel": [],
            "Jumlah": [],
            "Harga FG": [],
            "Total Biaya": [],
        }
        for artikel, nilai in data["data"].items():
            # print(artikel, nilai)
            datamodelsartikelfg["Kode Artikel"].append(artikel)
            datamodelsartikelfg["Jumlah"].append(nilai["jumlah"])
            datamodelsartikelfg["Harga FG"].append(nilai["hargafg"])
            datamodelsartikelfg["Total Biaya"].append(nilai["biaya"])
        # print("\n\n")
        df = pd.DataFrame(datamodelsartikelfg)
        listdataartikelfg.append(df)

    # print(listdataartikelfg)
    # print(asd)

    """7. Stok Awal Gudang"""
    datamodelstockawalgudang = {
        "Kode Produk": [],
        "Nama Produk": [],
        "Unit": [],
        "Harga Satuan": [],
        "Jumlah": [],
        "Total Biaya": [],
    }
    # print(baranggudang["datasaldoawal"])
    for item in baranggudang["datasaldoawal"]:
        datamodelstockawalgudang["Kode Produk"].append(item.KodeProduk)
        datamodelstockawalgudang["Unit"].append(item.unit)
        datamodelstockawalgudang["Nama Produk"].append(item.NamaProduk)
        datamodelstockawalgudang["Jumlah"].append(item.jumlahawal)
        datamodelstockawalgudang["Total Biaya"].append(item.totalbiayaawal)
        datamodelstockawalgudang["Harga Satuan"].append(item.hargasatuanawal)

    # print(datamodelstockawalgudang)
    dfstokgudang = pd.DataFrame(datamodelstockawalgudang)

    buffer = BytesIO()

    # Use pandas to write DataFrame to the BytesIO buffer
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        startcol = 0
        for i, datamasuk in enumerate(listpersediaan):
            datamasuk.to_excel(
                writer,
                index=False,
                startcol=startcol,
                startrow=1,
                sheet_name="Laporan Persediaan",
            )
            ws = writer.sheets["Laporan Persediaan"]
            ws.cell(
                row=1, column=startcol + 1, value=f"Laporan Persediaan {listbulan[i]}"
            )
            startcol += datamasuk.shape[1] + 1
        # dfpersediaan.to_excel(
        #     writer, index=False, startrow=1, sheet_name="Laporan Persediaan"
        # )
        # ws = writer.sheets["Laporan Persediaan"]
        # ws.cell(
        #     row=1, column=1, value=f"Laporan Persediaan {listbulan[waktuobj.month - 1]}"
        # )
        pd.DataFrame().to_excel(writer, index=False, sheet_name="Barang Masuk")
        pd.DataFrame().to_excel(writer, index=False, sheet_name="Barang Keluar")

        startcol = 0
        for i, datamasuk in enumerate(listdatamodelmasuk):
            datamasuk.to_excel(
                writer,
                index=False,
                startcol=startcol,
                startrow=1,
                sheet_name="Barang Masuk",
            )
            ws = writer.sheets["Barang Masuk"]
            ws.cell(
                row=1, column=startcol + 1, value=f"Bahan Baku Masuk {listbulan[i]}"
            )
            startcol += datamasuk.shape[1] + 1

        startcol = 0
        for i, daatakeluar in enumerate(listdatamodelkeluar):
            daatakeluar.to_excel(
                writer,
                index=False,
                startcol=startcol,
                startrow=1,
                sheet_name="Barang Keluar",
            )
            ws = writer.sheets["Barang Keluar"]
            ws.cell(
                row=1, column=startcol + 1, value=f"Bahan Baku Keluar {listbulan[i]}"
            )
            startcol += daatakeluar.shape[1] + 1

        startcol = 0  # Mulai dari kolom kedua untuk menambahkan "Kode Bahan Baku" di sebelah kiri
        for bulan_index, bulan_data in data_per_bulan.items():
            if not bulan_data:
                continue
            df = pd.DataFrame.from_dict(bulan_data, orient="index")
            df.index.name = "Kode Bahan Baku"
            df.insert(
                0, "Kode Bahan Baku", df.index
            )  # Tambahkan kolom "Kode Bahan Baku" di sebelah kiri
            df.to_excel(
                writer,
                index=True,
                startcol=startcol,
                startrow=1,
                sheet_name="Bahan Produksi",
            )
            ws = writer.sheets["Bahan Produksi"]
            ws.cell(row=1, column=startcol + 1, value=listbulan[bulan_index])
            startcol += df.shape[1] + 2  # +2 to add some space between columns

        startcol = 0
        for i, daatakeluar in enumerate(listdataartikelfg):
            daatakeluar.to_excel(
                writer,
                index=False,
                startcol=startcol,
                startrow=1,
                sheet_name="Stok Produk FG",
            )
            ws = writer.sheets["Stok Produk FG"]
            ws.cell(row=1, column=startcol + 1, value=f"Stok FG {listbulan[i]}")
            startcol += daatakeluar.shape[1] + 1

        startcol = 0
        datalistheadertabel = [
            "Total Stok Awal Bahan Produksi",
            "Stok Awal WIP",
            "Stok Awal FG",
        ]
        for i, daatakeluar in enumerate(liststokawalproduksi):
            daatakeluar.to_excel(
                writer,
                index=False,
                startcol=startcol,
                startrow=1,
                sheet_name="Stok Awal Bahan Produksi",
            )
            ws = writer.sheets["Stok Awal Bahan Produksi"]
            ws.cell(
                row=1,
                column=startcol + 1,
                value=f"{datalistheadertabel[i]} - {waktuobj.year}",
            )
            startcol += daatakeluar.shape[1] + 1

        dfstokgudang.to_excel(
            writer, startrow=1, index=False, sheet_name="Stock Awal Gudang"
        )
        ws = writer.sheets["Stock Awal Gudang"]
        ws.cell(row=1, column=1, value=f"Stock Awal Gudang {waktuobj.year}")

    # Load the workbook from the buffer
    buffer.seek(0)
    wb = load_workbook(buffer)
    ws = wb["Laporan Persediaan"]
    # ws2 = wb["Barang Masuk"]
    # ws3 = wb["Barang Keluar"]

    # # Insert header "Januari" above the table
    # ws["A1"] = listbulan[waktuobj.month - 1]
    # ws2["A1"] = listbulan[waktuobj.month - 1]
    # ws3["A1"] = listbulan[waktuobj.month - 1]

    # Custom WS Barang Keluar
    # baristerakhirws3 = ws3.max_row
    # kolomterakhirws3 = ws3.max_column
    # hurufkolomws3 = get_column_letter(kolomterakhirws3)
    # print("Baris Terakhir : ", baristerakhirws3)
    # print("Kolom Terakhir : ", kolomterakhirws3)
    # print("Huruf Terakhir : ", hurufkolomws3)
    # ws3.cell(row=baristerakhirws3 + 1, column=kolomterakhirws3 - 1, value="Total Biaya")
    # ws3.cell(row=baristerakhirws3 + 1, column=kolomterakhirws3, value=totalbiayakeluar)
    # # print(asdas)
    # Save the workbook back to the buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Create the HTTP response
    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = (
        f"attachment; filename=laporanpersediaan{bulan}.xlsx"
    )

    return response

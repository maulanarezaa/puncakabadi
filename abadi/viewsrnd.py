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


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
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


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def updatedataartikel(request, id):
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


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def delete_penyusun(request, id):
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
    print(id)
    kodeversi = models.Versi.objects.get(pk = id)
    print(kodeversi.isdefault)
    if kodeversi.isdefault == True:
        dataversibaru = models.Versi.objects.filter(KodeArtikel = kodeversi.KodeArtikel).exclude(pk=id).order_by('Tanggal').first()
        print(dataversibaru)
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
    data = models.SPPB.objects.all()
    for sppb in data:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=sppb.id)
        sppb.Tanggal = sppb.Tanggal.strftime("%Y-%m-%d")
        sppb.detailsppb = detailsppb
    return render(request, "rnd/views_sppb.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def view_spk(request):
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
            return redirect("view_ksbjrnd")

        if request.GET["tahun"]:
            tahun = int(request.GET["tahun"])
        else:
            sekarang = datetime.now()
            tahun - sekarang.year

        tanggal_mulai = datetime(year=tahun, month=1, day=1)
        tanggal_akhir = datetime(year=tahun, month=12, day=31)

        print(tanggal_mulai)
        print(tanggal_akhir)

        lokasi = request.GET['lokasi']
        lokasiobj = models.Lokasi.objects.get(NamaLokasi = lokasi)

        getbahanbakuutama = models.Penyusun.objects.filter(KodeArtikel=artikel.id, Status=1).order_by('-KodeVersi__Tanggal').first()
        print(getbahanbakuutama)
        if not getbahanbakuutama :
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("view_ksbjrnd")
        
        data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id,Jenis = "Mutasi")
        datamasuk = models.TransaksiGudang.objects.filter(DetailSPK__KodeArtikel = artikel.id,KodeProduk = getbahanbakuutama.KodeProduk,tanggal__range=(tanggal_mulai, tanggal_akhir))
        listtanggalmasuk = datamasuk.values_list('tanggal',flat=True).distinct()
        print(datamasuk)
        listdata = []
        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoawalobj = models.SaldoAwalArtikel.objects.get(IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi,Tanggal__range =(tanggal_mulai,tanggal_akhir))
                saldo = saldoawalobj.Jumlah
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.year

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

                # konversimasterobj = models.KonversiMaster.objects.get(KodePenyusun=penyusunfiltertanggal.IDKodePenyusun)
                # konversi =konversimasterobj.Allowance
                konversi = penyusunfiltertanggal.Allowance
                # except:
                #     konversi = round(0)
                #     messages.error(request,'Data allowance belum di set')
                print(getbahanbakuutama)
                # print(asd)d
                penyesuaiaanfilter = models.Penyesuaian.objects.filter(KodeArtikel = artikel.id, KodeProduk = getbahanbakuutama.KodeProduk,TanggalMulai__lte = i, TanggalMinus__gte = i).first()
                print(penyesuaiaanfilter)
                if penyesuaiaanfilter:
                    konversi= penyesuaiaanfilter.konversi
                    print(konversi,penyesuaiaanfilter,i)
                    # print(asd)
            
                masukpcs = math.ceil(jumlahmasuk/konversi)
                if masukpcs != 0 :
                    print(masukpcs)
                    print(jumlahmasuk, konversi)
                    # print(asd)
                
                    
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
                "rnd/view_ksbj.html",
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
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.year
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
                "rnd/view_ksbj.html",
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
            and saldoawalobj is not None
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
                hargasatuanawal = hargatotalawal / saldoawal

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
    produkobj = models.Produk.objects.all()
    print(produkobj[1].keteranganRND)
    return render(request, "rnd/read_produk.html", {"produkobj": produkobj})

def updateversi(request):
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
   

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def views_penyusun(request):
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


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahversi(request, id):
    data = models.Artikel.objects.get(id=id)
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
            "rnd/tambah_versi.html",
            {"data": data, "versi": tanggal, "dataproduk": bahanbaku,'backurl':back_url},
        )
    else:
        print(request.POST)
        kodeproduk = request.POST.getlist("kodeproduk")
        status = request.POST.getlist("Status")
        lokasi = request.POST.getlist("lokasi")
        kuantitas = request.POST.getlist("kuantitas")
        tanggal = request.POST["versi"]
        allowance = request.POST.getlist("allowance")
        # print(asdas)
        if status.count("True") > 1:
            messages.error(request, "Terdapat Artikel utama lebih dari 1")
            return redirect("add_versi", id=id)
        dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas, allowance))
        print(dataproduk)
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
                versi=tanggal,
            )
            newpenyusun.save()
            datanewpenyusun = models.Penyusun.objects.all().last()
            konversimasterobj = models.KonversiMaster(
                KodePenyusun=datanewpenyusun, Kuantitas=i[3], Allowance=i[4]
            )
            konversimasterobj.save()

        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(data.KodeArtikel)}&versi={tanggal}"
        )

@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahversibaru(request, id):
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
        cekexistingdata = models.Versi.objects.filter( KodeArtikel = data, Versi = kodeversi)
        if cekexistingdata.exists():
            messages.error(request,f'Kode versi {kodeversi} pada artikel {data.KodeArtikel} sudah terdaftar pada sistem')
            return redirect("add_versibaru", id=id)
        newversiobj = models.Versi(
            KodeArtikel = data,
            Versi = kodeversi,
            Tanggal = tanggal,
            Keterangan = keteranganversi
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
            

        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(data.KodeArtikel)}&versi={kodeversi}"
        )


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdatapenyusun(request, id, versi):
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
            "rnd/tambah_penyusunversi.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versi,
                'backurl':back_url
            },
        )
    else:
        print(request.POST)
        # print(asd)
        kodeproduk = request.POST.getlist("kodeproduk")
        statusproduk = request.POST.getlist("status")
        listlokasi = request.POST.getlist("lokasi")
        listkuantitas = request.POST.getlist("kuantitas")
        listallowance = request.POST.getlist("allowance")

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, KodeVersi__Versi=versi)
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
                KodeVersi=models.Versi.objects.filter(KodeArtikel = dataartikelobj,Versi =versi).first(),
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
    data = models.Display.objects.all()
    return render(request, "rnd/views_display.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdatadisplay(request):
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
    datakirim = []
    data = models.HargaArtikel.objects.all()
   
    return render(request, "rnd/views_harga.html", {"data": data})


@login_required
@logindecorators.allowed_users(allowed_roles=["rnd",'ppic'])
def tambahdataharga(request):
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
    dataartikel = models.Artikel.objects.all()
    for item in dataartikel:
        print(item)
        dataversifilter = models.Versi.objects.filter(KodeArtikel = item).order_by('Tanggal')
        for i in dataversifilter:
            i.isdefault = False
            i.save()
        dataawal = dataversifilter.first()
        dataawal.isdefault= True
        dataawal.save()

        
    

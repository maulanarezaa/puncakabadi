from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from . import models
from django.db.models import Sum

# Create your views here.


# SPK
def view_spk(request):
    dataspk = models.SPK.objects.all()

    return render(request, "view_spk.html", {"dataspk": dataspk})


def add_spk(request):
    if request.method == "GET":
        return render(request, "add_spk.html")

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
                KeteranganACC=status,
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

    return render(request, "view_sppb.html", {"datasppb": datasppb})


def add_sppb(request):
    if request.method == "GET":
        return render(request, "add_sppb.html")

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
        return render(request, "update_sppb.html")
    else:
        return redirect("view_sppb")


def delete_sppb(request, id):
    datasppb = models.SPPB.objects.get(id=id)
    datasppb.delete()
    return redirect("view_sppb")


# Transaksi Produksi
def view_produksi(request):
    dataproduksi = models.TransaksiProduksi.objects.all()

    return render(request, "view_produksi.html", {"dataproduksi": dataproduksi})


def add_produksi(request):
    if request.method == "GET":
        data_artikel = models.Artikel.objects.all()
        data_lokasi = models.Lokasi.objects.all()

        return render(
            request,
            "add_produksi.html",
            {"kode_artikel": data_artikel, "nama_lokasi": data_lokasi},
        )

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
            KodeArtikel=artikelref,
            Lokasi=lokasiref,
            Tanggal=tanggal,
            Jumlah=jumlah,
            Keterangan=keterangan,
            Jenis=jenis,
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


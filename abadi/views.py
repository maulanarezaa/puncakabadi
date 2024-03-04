from django.shortcuts import render, redirect
from django.contrib import messages
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
        data = models.Artikel.objects.filter(KodeArtikel=kodebaru).exists()
        if data:
            messages.error(request, "Kode Artikel sudah ada")
            return redirect("tambahdataartikel")
        else:
            messages.success(request, "Data berhasil disimpan")
            return redirect("views_artikel")


def updatedataartikel(request, id):
    if request.method == "GET":
        return render(request, "updatedataartikel.html")
    else:
        return redirect("views_artikel")


def deleteartikel(request, id):
    print(id)
    return redirect("views_artikel")

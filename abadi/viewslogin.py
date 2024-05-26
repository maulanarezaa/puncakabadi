# myapp/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        print(request.POST)

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        # form = AuthenticationForm(request, data=request.POST)
        if user is not None:
            print(user.groups)
            print(user.groups.all())
            print(user.groups.all().exists())

            if user.groups.all().exists():
                login(request, user)
                selectedgrup = str(user.groups.all()[0])
                print(selectedgrup)
                if selectedgrup == "rnd":
                    return redirect("dashboardrnd")
                elif selectedgrup == "produksi":
                    return redirect("dashboardproduksi")
                elif selectedgrup == "gudang":
                    return redirect("viewgudang")
                elif selectedgrup == "purchasing":
                    return redirect("notif_purchasing")
                elif selectedgrup == "ppic":
                    return redirect("dashboardppic")
            else:
                return redirect("guestpage")
        else:
            messages.error(request, "Login Gagal. Username atau Password Salah")
            return redirect("login")
        # else:

        #     return redirect("logout")
        # if form.is_valid():
        #     username = form.cleaned_data.get("username")
        #     password = form.cleaned_data.get("password")
        #     user = authenticate(request, username=username, password=password)
        #     print(user)
        #     if user == "rnd":
        #         return redirect("dashboardrnd")
        #     elif user is not None:
        #         login(request, user)
        #         return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "login/login.html", {"form": form})


def guestpage(request):
    return render(request, "login/guestpage.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
        else:
            print(form)
    else:
        form = UserCreationForm()
    return render(request, "login/register.html", {"form": form})


@login_required
def home_view(request):
    return render(request, "myapp/home.html")

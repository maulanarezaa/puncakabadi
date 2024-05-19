# myapp/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.method == "POST":
        print(request.POST)

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        # form = AuthenticationForm(request, data=request.POST)
        print(user.groups)
        print(user.groups.all())
        print(user.groups.all())
        if user is not None:

            login(request, user)
            # if user.groups.filter(name="rnd").exists():
            return redirect("dashboardrnd")
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

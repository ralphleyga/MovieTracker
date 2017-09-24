from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import UserCreationForm
from MovieTracker import settings
from django.contrib.auth.decorators import login_required
from django import forms
from tracker.models import UserWatched
import requests
import json
from django.core.urlresolvers import reverse




# Keys:
#
# API Key (v3 auth)
# ca59847d10d1b5321571a0a279c95e61
# API Read Access Token (v4 auth)
# eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjYTU5ODQ3ZDEwZDFiNTMyMTU3MWEwYTI3OWM5NWU2MSIsInN1YiI6IjU5YzYzN2E2OTI1MTQxNWI2ZTAzZDc4NSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.5pcWArPylqn1BxS5Lgsdn90li5_YfXD34OPhYG76-uY
# example request
# https://api.themoviedb.org/3/movie/550?api_key=ca59847d10d1b5321571a0a279c95e61

# Example Image url
# https://image.tmdb.org/t/p/w150/nl79FQ8xWZkhL3rDr1v2RFFR6J0.jpg

#Get movie detail
# https://api.themoviedb.org/3/movie/278?api_key=ca59847d10d1b5321571a0a279c95e61&language=en-US
class ColorForm(forms.Form):
    fav_color = forms.CharField(label='Fav Color', max_length=100)


def Login(request):
    next = request.GET.get('next', '/unwatched/')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(next)
            else:
                return HttpResponse("Inactive user.")
        else:
            return HttpResponseRedirect(settings.LOGIN_URL)

    return render(request, "tracker/login.html", {'redirect_to': next})

def Logout(request):
    logout(request)
    return HttpResponseRedirect(settings.LOGIN_URL)


# login is required for the following function Watched
@login_required
def Watched(request):
    # if request.method == 'POST':
    #
    #     form = ColorForm(request.POST)
    #     # check whether it's valid:
    #     if form.is_valid():
    #         # process the data in form.cleaned_data as required
    #         # ...
    #         # redirect to a new URL:
    #         request.session["fav_color"] = request.POST['fav_color']
    #
    #         # return HttpResponseRedirect('/watched/')
    # else:
    #     form = ColorForm()
    #
    # if(not "fav_color" in request.session.keys()):
    #     # print "relksal;dfkm"
    #     request.session["fav_color"] = "Empty"

    watchedMovieIds = UserWatched.objects.values_list('movie_id', flat=True).filter(username=request.user)
    if(not watchedMovieIds):
        movies_list = None
    else:
        movies_list = getWatchedMovies(set(watchedMovieIds))

    return render(request, "tracker/watched.html", {'current_user':request.user,
                                                    'movies_list' : movies_list})

@login_required
def AddToWatched(request, movieid):


    b = UserWatched(username=request.user, movie_id=movieid, movie_rating=10)
    b.save()

    return HttpResponseRedirect(reverse('unwatched'))

@login_required
def Unwatched(request,pageNumber=1):
    if request.method == 'POST':

        form = ColorForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            request.session["fav_color"] = request.POST['fav_color']

            # return HttpResponseRedirect('/watched/')
    else:
        form = ColorForm()

    if(not "fav_color" in request.session.keys()):
        # print "relksal;dfkm"
        request.session["fav_color"] = "Empty"

    movies_list = getTopRated(request,pageNumber)
    return render(request, "tracker/unwatched.html", {'current_user':request.user,
                                                      'movies_list' : movies_list})

@login_required
def Movie(request):
    if request.method == 'POST':

        form = ColorForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            request.session["fav_color"] = request.POST['fav_color']

            # return HttpResponseRedirect('/watched/')
    else:
        form = ColorForm()

    if(not "fav_color" in request.session.keys()):
        # print "relksal;dfkm"
        request.session["fav_color"] = "Empty"

    return render(request, "tracker/unwatched.html", {'current_user':request.user})


def Signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            # return redirect('tracker/home')
            return render(request, "tracker/watched.html", {})
    else:

        form = UserCreationForm()
    return render(request, 'tracker/signup.html', {'form': form})


def getTopRated(request,pageNumber):

    watchedMovieIds = UserWatched.objects.values_list('movie_id', flat=True).filter(username=request.user)

    god = []

    while(len(god)<100):
        r = requests.get("https://api.themoviedb.org/3/movie/top_rated?api_key=ca59847d10d1b5321571a0a279c95e61&language=en-US&page="+str(pageNumber))
        movies = json.loads(r.text)
        if pageNumber>movies['total_pages']:
            return god
        else:
            for i in range(len(movies['results'])):
                if(movies['results'][i]['id'] in watchedMovieIds):
                    continue
                else:
                    movies['results'][i]['poster_path'] = "https://image.tmdb.org/t/p/w150" + movies['results'][i]['poster_path']
                    god.append(movies['results'][i])

        pageNumber+=1

    return god

def getWatchedMovies(idList):

    results = []

    for id in idList:
        url = "https://api.themoviedb.org/3/movie/" + str(id) + "?api_key=ca59847d10d1b5321571a0a279c95e61&language=en-US"
        r = requests.get(url)
        movie = json.loads(r.text)
        movie['poster_path'] = "https://image.tmdb.org/t/p/w150" + movie['poster_path']
        results.append(movie)


    return results
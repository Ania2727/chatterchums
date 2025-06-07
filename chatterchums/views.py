import requests
from django.shortcuts import render, redirect
from django.http import JsonResponse


def get_forum_recommendations(request):
    interests = request.GET.getlist("interests")

    response = requests.post("http://localhost:5000/get-recommendations", json={"interests": interests})

    return JsonResponse(response.json())


def about_view(request):
    return render(request, 'about.html')
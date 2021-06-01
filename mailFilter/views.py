from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from config import settings
from google_auth_oauthlib.flow import InstalledAppFlow

# Create your views here.

def home(request):
    return render(request, 'login.html')

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes = ['https://mail.google.com/'],
    redirect_uri = 'http://localhost:8000/callback/')

def authenticate(request):
    auth_url, state = flow.authorization_url(prompt='consent')
    return HttpResponseRedirect(auth_url)

def callback(request):
    return render(request, 'test.html')
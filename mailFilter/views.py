from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from config import settings
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json',
    scopes = ['https://mail.google.com/'],
    redirect_uri = json.load(open('client_secret.json'))['web']['redirect_uris'][0])

def home(request):
    if 'credentials' in request.session:
        return redirect('/table/')
    else:
        return render(request, 'login.html')

def authenticate(request):
    auth_url, state = flow.authorization_url(prompt='consent')
    return HttpResponseRedirect(auth_url)

def callback(request):
    flow.fetch_token(code=request.GET['code'])
    request.session['credentials'] = flow.credentials.token
    return redirect('/table/')

def table(request):
    credentials = Credentials(request.session['credentials'])
    service = build('gmail', 'v1', credentials = credentials)
    api_response = service.users().getProfile(userId = "me").execute()
    print(api_response)
    return render(request, 'test.html')
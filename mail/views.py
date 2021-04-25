from __future__ import print_function
from django.shortcuts import render, redirect
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from oauth2client.client import AccessTokenCredentials
from datetime import datetime
from googleapiclient.http import BatchHttpRequest
from mailFilter import settings
from django.http import HttpResponseRedirect, HttpResponse
from mail.models import user
from datetime import datetime
from dateutil import tz
import config
import os.path
import json
import re
import copy
import pickle
import base64
import httplib2
 
service = None
currentId = None
info = {}

def login(request):
	return render(request, 'login.html', {})

def clearSession():
	global currentId, info, service
	service = None
	info = {}
	currentId = None
	try:	
		del request.session['creds']
	except:
		pass	

def authentication(request):
	global service, currentId
	utc_tz= tz.gettz('UTC')
	india_tz= tz.gettz('Asia/Kolkata')
	SCOPES = ['https://mail.google.com/']
	session = request.session.get('creds', None)
	oauthKey = {"installed":{"client_id":"1075784616082-pbr5t05fmtskhj7286chu9u3qhbbthk1.apps.googleusercontent.com","project_id":"quickstart-1605459866785","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"e9dcafB8VSnsEJifpNZoRrry","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
	creds = None
	if session is not None:
		creds = session[0]
		time = session[1]
		creds = AccessTokenCredentials(creds, 'user-agent-value')
		now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		newTime = datetime.strptime(now,"%Y-%m-%d %H:%M:%S") - datetime.strptime(time,"%Y-%m-%d %H:%M:%S")
		newTimeInSec = newTime.total_seconds()
		minutes = newTimeInSec/60
		if minutes > 50:
			flow = InstalledAppFlow.from_client_config(oauthKey, SCOPES)
			creds = flow.run_local_server(port=0)
			request.session['creds'] = [creds.token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
	else :
		flow = InstalledAppFlow.from_client_config(oauthKey, SCOPES)
		creds = flow.run_local_server(port=0)
		request.session['creds'] = [creds.token, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
	service = build('gmail', 'v1', credentials=creds)
	response = service.users().getProfile(userId = "me").execute()
	currentId = response['emailAddress']
	return redirect("/table/")

def mycallback(id, sender, execp):
	global info
	sender = sender['payload']['headers'][0]['value']
	sender = re.sub('[!<>]', '', sender)
	if sender in info:
		info[sender]['mailIds'].append(id)
		info[sender]['mailCount'] += 1
	else:
		temp = {}
		temp['mailIds'] = [id]
		temp['mailCount'] = 1
		info[sender] = temp

def table(request):
	global currentId, info, service
	if service == None:
		clearSession()
		return redirect("/")	
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])
	labelId = ['INBOX']
	query = user.objects.filter(userName = currentId)
	toSend = {}
	data = []
	refreshTime = ""
	if len(query) == 0:
		utc_tz= tz.gettz('UTC')
		india_tz= tz.gettz('Asia/Kolkata')
		response = service.users().messages().list(userId="me", maxResults = 500, labelIds = labelId).execute()
		messages = []
		if 'messages' in response:
			messages.extend(response['messages'])
		while 'nextPageToken' in response:
			page_token = response['nextPageToken']
			response = service.users().messages().list(userId='me', maxResults = 500, labelIds = labelId, pageToken=page_token).execute()
			messages.extend(response['messages'])
		for i in range(0, len(messages), 100):
			newMessages = messages[i:i+100]
			batch = service.new_batch_http_request(callback = mycallback)
			for message in newMessages:
				batch.add(service.users().messages().get(userId='me', id=message['id'], format="metadata",metadataHeaders = ["From"], fields="payload/headers/value"), request_id=message['id'])
			batch.execute()
		totalCount = len(messages)
		index = 0
		mailIds = []
		for i in info.keys():
			temp = []
			mail = re.findall('\S+@\S+', i)
			name = i.replace(mail[0],'')
			if len(name) == 0:
				name = mail[0]
			temp.append(index)
			index+=1
			name = re.sub('["]', '', name)
			mail = re.sub('["]', '', mail[0])
			temp.append(name)
			temp.append(mail)
			temp.append(str(info[i]['mailCount']))
			mailIds.append(info[i]['mailIds'])
			data.append(temp)
		toSend['data'] = list(data)
		refreshTime = datetime.now().strftime("%b %d %Y %I:%M%p")
		query = user.objects.create(userName = currentId, creationTime = refreshTime, mailCount = totalCount, mailBox = toSend, mailIds = mailIds)
	else:
		index = 0
		query = user.objects.filter(userName = currentId).values()[0]
		toSend = query['mailBox']
		totalCount = query['mailCount']
		refreshTime = query['creationTime']
	return render(request, 'table.html', {"time" :refreshTime,"totalCount":totalCount, "data" : json.dumps(toSend)})

def delete(request):
	global currentId, service,info
	if service == None:
		clearSession()
		return redirect("/")		
	selected = request.POST.getlist('id[]')
	selected = list(map(lambda x: int(x), selected))
	query = user.objects.filter(userName = currentId).values()[0]
	mailCount = query['mailCount']
	mailIds = query['mailIds']
	mailBox = query['mailBox']
	info = mailBox['data']
	refreshTime = query['creationTime']
	if len(selected) == 0:
		return render(request, 'table.html', {"time" :refreshTime,"totalCount":mailCount,"data" : json.dumps(mailBox)})
	forDeletion = []
	deletionCount = 0
	for i in sorted(selected, reverse = True):
		ids = mailIds.pop(i)
		data = info.pop(i)
		deletionCount += len(ids)
		forDeletion.extend(ids)
	for i in range(0, len(forDeletion),500):
		newDelition = forDeletion[i:i+500]
		body = {"ids" : newDelition}
		service.users().messages().batchDelete(userId='me', body = body).execute()
	index = 0
	for i in range(len(info)):
		info[i][0] = index
		index+=1
	toSend = {}
	toSend['data'] = info
	query = user.objects.get(userName = currentId)
	mailCount-=deletionCount
	if mailCount < 1:
		query = user.objects.filter(userName = currentId)
		mailCount = 0
		query.delete()
	else:
		query.mailCount = mailCount
		query.mailBox = toSend
		query.mailIds = mailIds
		query.save()
	return render(request, 'table.html', {"time" :refreshTime,"totalCount":mailCount, "data" : json.dumps(toSend)})

def move(request):
	global service, currentId, info

	if service == None:
		clearSession()
		return redirect("/")		
	label = {'messageListVisibility': 'show',
           'name': 'Mail Filter',
           'labelListVisibility': 'labelShow'}
	try:
		results = service.users().labels().create(userId='me', body = label).execute()
	except:
		a = None
	results = service.users().labels().list(userId='me').execute()
	labels = results.get('labels', [])
	toId = ""
	for i in labels:
		if i['name'] == 'Mail Filter':
			toId = i['id']
			break
	selected = request.POST.getlist('moveId[]')
	selected = list(map(lambda x: int(x), selected))
	query = user.objects.filter(userName = currentId).values()[0]
	mailCount = query['mailCount']
	mailIds = query['mailIds']
	mailBox = query['mailBox']
	info = mailBox['data']
	refreshTime = query['creationTime']
	if len(selected) == 0:
		return render(request, 'table.html', {"time" :refreshTime,"totalCount":mailCount,"data" : json.dumps(mailBox)})
	forMove = []
	moveCount = 0
	for i in sorted(selected, reverse = True):
		ids = mailIds.pop(i)
		data = info.pop(i)
		moveCount += len(ids)
		forMove.extend(ids)
	for i in range(0, len(forMove),500):
		newMove = forMove[i:i+500]
		body = {"ids" : newMove,
			"addLabelIds": [toId],
  			"removeLabelIds": ["INBOX"]
  			}
		service.users().messages().batchModify(userId='me', body = body).execute()
	index = 0
	for i in range(len(info)):
		info[i][0] = index
		index+=1
	toSend = {}
	toSend['data'] = info
	query = user.objects.get(userName = currentId)
	mailCount-=moveCount
	if mailCount < 1:
		query = user.objects.filter(userName = currentId)
		mailCount = 0
		query.delete()
	else:
		query.mailCount = mailCount
		query.mailBox = toSend
		query.mailIds = mailIds
		query.save()
	return render(request, 'table.html', {"time" :refreshTime,"totalCount":mailCount, "data" : json.dumps(toSend)})

def logout(request):
	global service, info, currentId

	if service == None:
		clearSession()
		return redirect("/")		
	service = None
	info = {}
	currentId = None
	del request.session['creds']
	return redirect("/")

def refresh(request):
	global service, currentId, info
	if service == None:
		clearSession()
		return redirect("/")		
	info = {}
	query = user.objects.filter(userName = currentId)
	query.delete()
	return redirect("/table/")


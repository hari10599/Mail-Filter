from django.db import models
from django.db.models import JSONField

# Create your models here.
class User(models.Model):
    userName = models.TextField(primary_key=True)
    createdTime = models.DateTimeField()
    lastUpdatedTime = models.DateTimeField()

class Mail(models.Model):
    userName = models.OneToOneField(User, on_delete = models.CASCADE, primary_key = True)
    mailCount = models.IntegerField(default = 0)
    mailBox = JSONField(default = dict)
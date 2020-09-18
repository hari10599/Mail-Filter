from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
class user(models.Model):
    userName = models.TextField()
    creationTime = models.TextField()
    mailCount = models.IntegerField(default = 0)
    mailBox = JSONField(default = dict)
    mailIds = JSONField(default = dict)


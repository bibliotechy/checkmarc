from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
  user = models.OneToOneField(User)

class Field(models.Model):
  field = models.CharField(max_length=50)

class Value(models.Model):
  value = models.CharField(max_length=50)

class Check(models.Model):

  OPS = (
    ('eq' , 'is equal to'),
    ('nq' , 'is not equal to'),
    ('ex' , 'exists'),
    ('nx' , 'does not exist'),
    ('cn' , 'contains'),
    ('dc' , 'doesn\'t contain'),
  )
  title = models.CharField(max_length=100)
  desc  = models.TextField(blank=True)
  fields = models.ManyToManyField(Field)
  operator = models.CharField(max_length=2, choices=OPS)
  values   = models.ManyToManyField(Value)


class Report(models.Model):
  title       = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  creator     = models.ForeignKey(UserProfile, related_name='+')
  checks      = models.ManyToManyField(Check)
  using       = models.ForeignKey(UserProfile, related_name='+')

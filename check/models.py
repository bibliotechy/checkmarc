from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.db.models.signals import post_save
from operator import *
from check.extraOperators import *

class UserProfile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(User, related_name='profile')
    pic_url = models.URLField(blank=True)
    home_url = models.URLField(blank=True)
    twitter_id = models.CharField(max_length=100, blank=True)
    facebook_id = models.CharField(max_length=100, blank=True)
    linkedin_id= models.CharField(max_length=100, blank=True)
    github_id = models.CharField(max_length=100, blank=True)

def create_user_profile(sender, created, instance, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)

class Check(models.Model):

    OPS = (
        (0, 'Select an operator'),
        ('eq' , 'is'),
        ('nq' , 'is not'),
        ('ex' , 'exists'),
        ('nx' , 'does not exist'),
        ('cn' , 'contains any of the following'),
        ('dc' , 'does not contain any of the following'),
        ('em', 'is empty'),
        ('sw', 'starts with'),
        ('ew', 'ends with')
        )

    title       = models.CharField(max_length=100, verbose_name="Check Title", blank=True )
    description = models.TextField(blank=True, verbose_name="Check Description")
    leader      = models.IntegerField(blank=True, null=True, verbose_name="MARC Record leader")
    field       = models.CharField(max_length=10, blank=True, help_text="A MARC field")
    subfield    = models.CharField(max_length=10,blank=True)
    indicator   = models.CharField(max_length=10,blank=True,
                    choices=(('1','indicator1'),('2','indicator2')))
    operator    = models.CharField(max_length=2, choices=OPS, default=0)
    values      = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        result = ""
        if not self.title:
          if self.leader:
            result += "leader position " + str(self.leader)
          if self.field:
            result += self.field
          if self.subfield:
            result += " " + self.subfield
          if self.indicator:
            result += " " + self.get_indicator_display()
          result += " " +self.get_operator_display()
          if self.values:
            result += " " +self.values
        else:
            result = self.title
        return result

    def run_check(self, record):
        if self._run_operation(record):
            return self
        else:
            return ""

    def _run_operation(self, record):
        operation = self._select_operation_function()
        if self._leader():
            return operation_wrapper(operation, record.leader[self.leader], self.values)
        if self._field():
            return operation_wrapper(operation, record[self.field], self.values)
        if self._subfield():
            return operation_wrapper(operation, record[self.field][self.subfield], self.values)
        if self._indicator():
            return operation_wrapper(operation, record[self.field].indicators[int(self.indicator)], self.values )

    def _select_operation_function(self):
        """ Choose the function to be called base on check's operator """
        operator_functions = dict(eq=eq, nq=ne, ex=truth, nx=not_, cn=is_in, dc=is_not_in, em=is_empty,
            sw=starts_with, ew=ends_with)
        return operator_functions[self.operator]

    def _leader(self):
        return bool(self.leader)

    def _field(self):
        return bool(not self.subfield and not self.indicator)

    def _subfield(self):
        return bool(self.subfield and not self.indicator)

    def _indicator(self):
        return bool(self.indicator and not self.subfield)


class Report(models.Model):
    title       = models.CharField(max_length=100, verbose_name="Report Title")
    description = models.TextField(blank=True, verbose_name="Report Description")
    creator     = models.ForeignKey(User, null=True,blank=True,verbose_name="Report Creator")
    checks      = models.ManyToManyField(Check, related_name='+')
    using       = models.ManyToManyField(User, related_name='+')

    def __unicode__(self):
        return self.title

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('title','description')

class CheckForm(forms.ModelForm):
    class Meta:
        model  = Check

class RunReportForm(forms.ModelForm):

    def __init__(self, report_id, *args, **kwargs):
        super(RunReportForm, self).__init__(*args, **kwargs)
        self.fields['report'] = forms.ModelChoiceField(
            queryset=Report.objects.filter(pk=report_id), empty_label=None )

    OUTPUTS = (
        ('scr', 'Print the results to screen'),
        ('jsn','Output to a json file' ),
        ('xml', 'Output to an XML file'),
        ('csv', 'Output an XML file' ),
    )
    class Meta:
        model = Report
        fields = ()
    file   = forms.FileField()
    output = forms.ChoiceField(choices=OUTPUTS)

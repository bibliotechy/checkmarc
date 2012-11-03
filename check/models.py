from django.db import models
from django.contrib.auth.models import User
from django import forms


class Check(models.Model):

    OPS = (
        ('eq' , 'is'),
        ('nq' , 'is not'),
        ('ex' , 'exists'),
        ('nx' , 'does not exist'),
        ('cn' , 'contains any of the following'),
        ('dc' , 'does not contain any of the following'),
        ('em', 'is empty'),
        )

    title = models.CharField(max_length=100)
    desc  = models.TextField(blank=True)
    fields = models.CharField(max_length=100)
    operator = models.CharField(max_length=2, choices=OPS)
    values   = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.title

class Report(models.Model):
    title       = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator     = models.ForeignKey(User)
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

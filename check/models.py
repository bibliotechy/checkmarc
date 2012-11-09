from django.db import models
from django.contrib.auth.models import User
from django import forms


class Check(models.Model):

    OPS = (
        ('eq' , 'is' ),
        ('nq' , 'is not'),
        ('ex' , 'exists'),
        ('nx' , 'does not exist'),
        ('cn' , 'contains any of the following'),
        ('dc' , 'does not contain any of the following'),
        ('em', 'is empty'),
        )

    title       = models.CharField(max_length=100, verbose_name="Check Title" )
    description = models.TextField(blank=True, verbose_name="Check Description")
    field       = models.CharField(max_length=100)
    subfield    = models.CharField(max_length=100,blank=True)
    operator    = models.CharField(max_length=2, choices=OPS)
    values      = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.title

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

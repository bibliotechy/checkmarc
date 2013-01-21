from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.db.models.signals import post_save

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
        )

    title       = models.CharField(max_length=100, verbose_name="Check Title", blank=True )
    description = models.TextField(blank=True, verbose_name="Check Description")
    field       = models.CharField(max_length=10, help_text="A MARC field, (or header")
    subfield    = models.CharField(max_length=10,blank=True)
    indicator   = models.CharField(max_length=10,blank=True,
        choices=(('1','indicator1'),('2','indicator2')))
    operator    = models.CharField(max_length=2, choices=OPS, default=0)
    values      = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        if not self.title:
          result = self.field
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

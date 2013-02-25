from django.db import models
from django.contrib.auth.models import User
from django import forms
from django.db.models.signals import post_save
import operator
from check import extraOperators as exop

class Check(models.Model):
    """ Defines an individual check to perform on a record.
     Must contain either a field or leader value and an operator."""

    OPS = (
        (0, 'Select an operator'),
        ('eq' , 'is'),
        ('nq' , 'is not'),
        ('ex' , 'exists'),
        ('nx' , 'does not exist'),
        ('cn' , 'contains any of the following'),
        ('dc' , 'does not contain any of the following'),
        ('em' , 'is empty'),
        ('sw' , 'starts with'),
        ('ew' , 'ends with'),
        #('re' , 'matches regular expression pattern') removed till fix the regex fucntion
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
            result += u"Leader position " + unicode(self.leader)
          if self.field:
            result += self.field
          if self.subfield:
            result += u" " + self.subfield
          if self.indicator:
            result += u" " + self.get_indicator_display()
          result += u" " +self.get_operator_display()
          if self.values:
            result += u" " +self.values
        else:
            result = self.title
        return result

    def run(self, record):
        """
        Method to run the check as defined by the check instances properties
        """
        try:
            if self._run_operation(record):
                return self
            else:
               return ""
        except TypeError:
            #HACK - Need to handle fields / subfields that do not exist and
            # bubble that up into a meaningful messages out to user.
            return False

    def _run_operation(self, record):
        """ Perform the checks instances operation on the check's fields and values """
        operation = self._select_operation_function()
        if self._leader():
            return exop.operation_wrapper(operation,
                    record.leader[self.leader], self.values)
        if self._field():
            if record[self.field]:
                return exop.operation_wrapper(operation,
                    record[self.field], self.values)
            else:
                return self.field + " does not exist"

        if self._subfield():
            if record[self.field] and record[self.field][self.subfield]:
                return exop.operation_wrapper(operation,
                    record[self.field][self.subfield],self.values)
            else:
                return self.field + " or " + self.subfield + "does not exist"

        if self._indicator():
            return exop.operation_wrapper(operation,
                    record[self.field].indicators[int(self.indicator)], self.values)

    def _select_operation_function(self):
        """ Choose the function to be called based on check's operator """
        operator_functions = {'eq': operator.eq,
                              'nq': operator.ne,
                              'ex': operator.truth,
                              'nx': operator.not_,
                              'cn': exop.is_in,
                              'dc': exop.is_not_in,
                              'em': exop.is_empty,
                              'sw': exop.starts_with,
                              'ew': exop.ends_with,
                              're': exop.regex_match
                            }
        return operator_functions[self.operator]

    def _leader(self):
        """The MARC record leader should be inspected. Mutually exclusive with field """
        return bool(self.leader)

    def _field(self):
        """The MARC record field should be inspected. Mutually exclusive with leader
           This indicates that the data of interest is the field as a whole, not any
           of its constituent parts like subfields or indicators
        """
        return bool(not self.subfield and not self.indicator)

    def _subfield(self):
        """The subfield of the indicated field should be inspected.
           Mutually exclusive with indicator"""
        return bool(self.subfield and not self.indicator)

    def _indicator(self):
        """ An indicator of the specified field should be inspected.
            Mutually exclusive with subfield.
        """
        return bool(self.indicator and not self.subfield)


class Report(models.Model):
    """ A collection of checks that should be performed on a record.  """
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

    #Doesn't actually do anything with this yet.
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

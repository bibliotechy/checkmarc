from check.models import *
from django.shortcuts import render, render_to_response, HttpResponseRedirect, redirect, get_object_or_404
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.contrib import auth
from django.contrib.auth.decorators import login_required
import pymarc

def home(request):
    return render(request, 'home.html')

def report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render_to_response('report.html',
        {'report':report},  context_instance=RequestContext(request))

#Really, I only want login on POST, so that you don't need
#to register
@login_required
def add_report(request):
    """
    Create a new report with an arbitrary  number of checks that you want to run on MARC records
    """
    if request.method == 'GET':
        CheckFormSet = formset_factory(CheckForm)
        report       = ReportForm(prefix='report')
        formset      = CheckFormSet(prefix='checks')

        return render_to_response('reports.html',
            {'report_form': report, 'checks' : formset}, context_instance=RequestContext(request))

    if request.method == 'POST':
        check_formset = formset_factory(CheckForm)
        report_data   = ReportForm(request.POST, prefix='report')
        checks_data   = check_formset(request.POST, prefix='checks')

        if report_data.is_valid() and checks_data.is_valid():
            title       = report_data.cleaned_data['title']
            description = report_data.cleaned_data['description']
            creator     = request.user
            report      = Report(title=title, description = description, creator = creator)
            report.save()

            for i in range(0, checks_data.total_form_count()):
                new_check = _build_new_check(checks_data, i)
                new_check.save()
                report.checks.add(new_check)

            report.save()

            return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

        else:
            report_form  = ReportForm(request.POST, prefix="report")
            checks_forms = check_formset(request.POST, prefix="checks")

            return render_to_response('reports.html',
                {'report_form' : report_form, 'checks': checks_forms}, context_instance=RequestContext(request))

@login_required
def edit_report(request, report_id=''):
    """ Edit an existing Report instance, including its check objects"""
    if request.method == 'GET':
        report = get_object_or_404(Report, pk=report_id)

        if request.user == report.creator:
            report_form   = ReportForm(instance=report, prefix="report")
            check_formset = modelformset_factory(Check, extra=0)
            checks        = check_formset(queryset=report.checks.all(), prefix='checks')
            return render_to_response('reports.html',
                {'report_form':report_form,'checks' : checks}, context_instance=RequestContext(request))
        else:
            return HttpResponseRedirect('/') #Add error message about report ownership - maybe switch to fork?

    if request.method == 'POST':
        report        = Report(pk=report_id)
        check_formset = modelformset_factory(Check, extra=0)
        report_data   = ReportForm(request.POST, prefix='report')
        checks_data   = check_formset(request.POST, prefix='checks')

        if report_data.is_valid() and checks_data.is_valid():
            report.title       = report_data.cleaned_data['title']
            report.description = report_data.cleaned_data['description']
            report.creator     = request.user
            report.save()

            for i in range(0,checks_data.total_form_count()):
                try:
                    check = report.checks.all()[i]
                    check = _edit_check(checks_data,i, check)
                    check.save()

                except IndexError:
                    new_check = _build_new_check(checks_data, i)
                    new_check.save()
                    report.checks.add(new_check)
            report.save()

        else:
            error_form = ReportForm(request.POST)
            return render_to_response('reports.html',
                {'form' : error_form}, context_instance=RequestContext(request))

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

@login_required
def fork_report(request, report_id):
    """
    Forks a report and then routes user to edit page for the new report.
    """
    if request.method == "POST":
        new_report = _fork_report(request,report_id)
        return HttpResponseRedirect("/report/" + str(new_report.pk) + "/edit/")
    else:
        #add a nice message about only accepting post here.
        return redirect("/")

@login_required
def myreports(request):
    reports = Report.objects.filter(creator=request.user)
    return  render_to_response('myreports.html',
        {'reports':reports}, context_instance= RequestContext(request))


def run_report(request, report_id):
    """
    Takes an existing report and a MARC file.

    Runs the checks from that report on the MARC records.
    """
    if request.method == 'GET':
        report     = Report(pk=report_id)
        run_report = RunReportForm(report_id=report_id)
        return render_to_response('run_report.html',
            {'run_report' : run_report, 'report' : report},
            context_instance=RequestContext(request))

    if request.method == 'POST':
        data    = RunReportForm(report_id, request.POST, request.FILES)
        results = {}

        if data.is_valid():
            report = data.cleaned_data['report']
            f      = request.FILES['file']
            file   = f.read()
            reader = pymarc.MARCReader(file, to_unicode=True)

            for record in reader:
                name          = record.title()
                results[name] = {}

                for check in report.checks.all():
                    result = check.run(record)

                    if result:
                        results[name][check.__unicode__()] = result

            return render_to_response('result.html',
                {'results': results },  context_instance=RequestContext(request))

        else:
            error_form = RunReportForm(report_id, request.POST, request.FILES)
            return render_to_response('run_report.html',
                {'run_report' : error_form}, context_instance=RequestContext(request))

def login(request):
    if request.user.is_authenticated():
        logout(request)
    next = request.GET.get('next', '')
    return render(request, 'login.html', {'next': next})

def logout(request):
    auth.logout(request)
    return redirect('/')

def about(request):
    return

def walkthrough(request):
    return

def _build_new_check(checks_data, i):
    """
    Helper function to build a new check for a report.
    Must still be saved to the report.
    """

    check_title = checks_data[i].cleaned_data['title']
    description = checks_data[i].cleaned_data['description']
    field       = checks_data[i].cleaned_data['field']
    leader      = checks_data[i].cleaned_data['leader']
    subfield    = checks_data[i].cleaned_data['subfield']
    indicator   = checks_data[i].cleaned_data['indicator']
    operator    = checks_data[i].cleaned_data['operator']
    values      = checks_data[i].cleaned_data['values']

    new_check = Check(leader=leader,
        field=field,
        subfield=subfield,
        indicator=indicator,
        operator=operator,
        values=values)
    return new_check

def _edit_check(checks_data, i, check):
    """
    Helper function to edit an existing check that is part of a report.
    """
    check.check_title = checks_data[i].cleaned_data['title']
    check.description = checks_data[i].cleaned_data['description']
    check.leader      = checks_data[i].cleaned_data['leader']
    check.field       = checks_data[i].cleaned_data['field']
    check.subfield    = checks_data[i].cleaned_data['subfield']
    check.indicator   = checks_data[i].cleaned_data['indicator']
    check.operator    = checks_data[i].cleaned_data['operator']
    check.values      = checks_data[i].cleaned_data['values']
    return check

def _fork_report(request, report_id):
    """
    Create copy of an object, but issue new pk, creator and possibly title
    """
    forked_report         = Report(pk=report_id)
    checks_to_copy         = forked_report.checks.all()
    forked_report.pk      = None #setting pk to None, then saving te object creates a new object. django++
    forked_report.creator = request.user
    forked_report.save()

    forked_report.checks = checks_to_copy
    forked_report.save()
    return forked_report
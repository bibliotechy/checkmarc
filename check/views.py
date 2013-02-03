from check.models import *
from django.shortcuts import render, render_to_response, HttpResponseRedirect, redirect, get_object_or_404
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict
from django.contrib import auth
from django.contrib.auth.decorators import login_required
import operator
import pymarc


def home(request):
    return render(request, 'home.html')

def report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render_to_response('report.html',
        {'report':report},  context_instance=RequestContext(request))

@login_required
def add_report(request):
    check_formset = formset_factory(CheckForm)
    if request.method == 'GET':
        report = ReportForm(prefix='report')
        formset  = check_formset(prefix='checks')
        return render_to_response('reports.html',
            {'report_form': report, 'checks' : formset}, context_instance=RequestContext(request))

    if request.method == 'POST':
        report_data = ReportForm(request.POST, prefix='report')
        checks_data = check_formset(request.POST, prefix='checks')

        if report_data.is_valid() and checks_data.is_valid():
            title       = report_data.cleaned_data['title']
            description = report_data.cleaned_data['description']
            creator     = request.user
        else:
            report_form = ReportForm(request.POST, prefix="report")
            checks_forms = check_formset(request.POST, prefix="checks")
            return render_to_response('reports.html',
                {'report_form' : report_form, 'checks': checks_forms}, context_instance=RequestContext(request))

        report = Report(title=title, description = description, creator = creator)
        report.save()

        for i in range(0, checks_data.total_form_count()):
            new_check = _build_new_check(checks_data, i)
            new_check.save()
            report.checks.add(new_check)
            report.save()

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

@login_required
def edit_report(request, report_id=''):
    """ Edit an existing Report instance, including its check objects"""
    check_formset = formset_factory(CheckForm, can_delete=True, can_order=True)

    if request.method == 'GET':
        report = get_object_or_404(Report, pk=report_id)
        if request.user != report.creator:
            return HttpResponseRedirect('/') #Add error message about report ownership
        else:
            form = ReportForm(instance=report, prefix="report")
            existing_checks = _bind_formset_with_object_instance(report, 'checks')
            formset  = check_formset(existing_checks,prefix='checks' )
            return render_to_response('reports.html',
                {'report_form':form,'checks' : formset}, context_instance=RequestContext(request))

    if request.method == 'POST':
        report = Report(pk=report_id)
        report_data = ReportForm(request.POST, prefix='report')
        checks_data = check_formset(request.POST, prefix='checks')

        if report_data.is_valid() and checks_data.is_valid():
            report.title       = report_data.cleaned_data['title']
            report.description = report_data.cleaned_data['description']
            report.creator     = request.user
            report.save()

            for i in range(0,checks_data.total_form_count()):
                try:
                    check = report.checks.all()[i]
                    check = _edit_check(checks_data,i, check)
                    report.checks.all()[i].save()
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

def _edit_check(checks_data, i, check):
    check.check_title = checks_data[i].cleaned_data['title']
    check.description = checks_data[i].cleaned_data['description']
    check.leader      = checks_data[i].cleaned_data['leader']
    check.field       = checks_data[i].cleaned_data['field']
    check.subfield    = checks_data[i].cleaned_data['subfield']
    check.indicator   = checks_data[i].cleaned_data['indicator']
    check.operator    = checks_data[i].cleaned_data['operator']
    check.values      = checks_data[i].cleaned_data['values']
    return check



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

def _fork_report(request, report_id):
    """
    Create copy of an object, but issue new pk, creator and possibly title
    """
    report_to_copy = Report(pk=report_id)
    checks_to_copy = report_to_copy.checks.all()
    #setting pk to None, then saving te object creates a new object. django++
    report_to_copy.pk = None
    report_to_copy.creator = request.user
    report_to_copy.save()
    report_to_copy.checks = checks_to_copy
    report_to_copy.save()
    return report_to_copy



@login_required
def myreports(request):
    reports = Report.objects.filter(creator=request.user)
    return  render_to_response('myreports.html',
        {'reports':reports}, context_instance= RequestContext(request))

def checks(request):
    if request.method == 'GET':
        checks = Check.objects.all()
        c = CheckForm()
        return render_to_response('checks.html',
            {'checks': checks ,'checkform': c}, context_instance=RequestContext(request))

    if request.method == 'POST':
        data= CheckForm(request.POST)

        if data.is_valid():
            title       = data.cleaned_data['title']
            description = data.cleaned_data['desc']
            leader       = data.cleaned_data['leader']
            field       = data.cleaned_data['field']
            subfield    = data.cleaned_data['subfield']
            indicator   = data.cleaned_data['indicator']
            operator    = data.cleaned_data['operator']
            values      = data.cleaned_data['values']

            new_check = Check(
                title     = title,
                desc      = description,
                leader    = leader,
                field     = field,
                subfield  = subfield,
                indicator = indicator,
                operator  = operator,
                values    = values)
            new_check.save()

        return HttpResponseRedirect('/checks/') # Redirect after POST

def run_report(request, report_id):
    if request.method == 'GET':
        report = Report(pk=report_id)
        run_report = RunReportForm(report_id=report_id)
        return render_to_response('run_report.html',
            {'run_report' : run_report, 'report' : report},
            context_instance=RequestContext(request))

    if request.method == 'POST':
        data = RunReportForm(report_id, request.POST, request.FILES)
        results = {}

        if data.is_valid():
            report = data.cleaned_data['report']
            f = request.FILES['file']
            file = f.read()
            reader = pymarc.MARCReader(file, to_unicode=True)

            for record in reader:
                name = record.title()
                results[name] = {}
                for check in report.checks.all():
                    result = check.run_check(record)
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

def _bind_formset_with_object_instance(report, prefix='form' ):

    forms = [model_to_dict(check) for check in report.checks.all()]

    new_formset_bind_data = {
        prefix+'-TOTAL_FORMS': unicode(len(forms)),
        prefix+'-INITIAL_FORMS': unicode(len(forms)),
        prefix+'-MAX_NUM_FORMS': u''
    }

    for index, form in enumerate(forms):
        check_dict = _build_formset_dict_from_check(form, index, prefix)
        new_formset_bind_data.update(check_dict)

    return new_formset_bind_data

def _build_formset_dict_from_check(check, index, prefix="form"):
    check_dict = {}
    for key, value in check.iteritems():
        check_dict.update({prefix + '-' + str(index) + '-' + key : value})
    return check_dict

def _build_new_check(checks_data, i):

    check_title = checks_data[i].cleaned_data['title']
    description = checks_data[i].cleaned_data['description']
    field       = checks_data[i].cleaned_data['field']
    leader      = checks_data[i].cleaned_data['leader']
    subfield    = checks_data[i].cleaned_data['subfield']
    indicator   = checks_data[i].cleaned_data['indicator']
    operator    = checks_data[i].cleaned_data['operator']
    values      = checks_data[i].cleaned_data['values']

    new_check = Check(title=check_title,
        description=description,
        leader=leader,
        field=field,
        subfield=subfield,
        indicator=indicator,
        operator=operator,
        values=values)
    return new_check




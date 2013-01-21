from check.models import *
from django.shortcuts import render, render_to_response, HttpResponseRedirect, redirect, get_object_or_404
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict
from django.contrib import auth
from django.contrib.auth.decorators import login_required
import pymarc


def home(request):
    return render(request, 'home.html')


def list_reports(request):
    reports = Report.objects.order_by('title')[:10]
    return render_to_response('list_reports.html',
        {'reports' : reports},  context_instance=RequestContext(request))

def report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render_to_response('report.html',
        {'report':report},  context_instance=RequestContext(request))

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

        if request.user.is_authenticated():
            user = request.user
        else:
            user = None

        if report_data.is_valid() and checks_data.is_valid():
            title       = report_data.cleaned_data['title']
            description = report_data.cleaned_data['description']
            creator     = user

        else:
            report_form = ReportForm(request.POST, prefix="report")
            checks_forms = check_formset(request.POST, prefix="checks")
            return render_to_response('reports.html',
                {'report_form' : report_form, 'checks': checks_forms}, context_instance=RequestContext(request))

        report = Report(title=title, description = description, creator = creator)
        report.save()

        for i in range(0,checks_data.total_form_count()):

            new_check = _build_new_check(checks_data, i)

            new_check.save()

            report.checks.add(new_check)
            report.save()

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

def edit_report(request, report_id=''):
    user = request.user
    check_formset = formset_factory(CheckForm, can_delete=True, can_order=True)
    if request.method == 'GET':
        report = get_object_or_404(Report, pk=report_id)
        form = ReportForm(instance=report, prefix="report")
        prefix = 'check'
        new_form = _bind_check_formset_with_report_checks(report, prefix)
        formset  = check_formset(new_form,prefix=prefix )
        return render_to_response('reports.html',
            {'report_form':form,'checks' : formset}, context_instance=RequestContext(request))

    if request.method == 'POST':
        report = Report(pk=report_id)
        report_data = ReportForm(request.POST, prefix='report')
        checks_data = check_formset(request.POST, prefix='checks')

        if report_data.is_valid() and checks_data.is_valid():
            report.title       = report_data.cleaned_data['title']
            report.description = report_data.cleaned_data['description']
            report.save()

            for i in range(0,checks_data.total_form_count()):
                try:
                    _edit_check(checks_data,i)
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

def fork_report(request, report_id):

    return

@login_required
def myreports(request):
    user = request.user
    reports = Report.objects.filter(creator=user)
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
            field       = data.cleaned_data['field']
            subfield    = data.cleaned_data['subfield']
            indicator   = data.cleaned_data['indicator']
            operator    = data.cleaned_data['operator']
            values      = data.cleaned_data['values']

            new_check = Check(
                title     = title,
                desc      = description,
                field     = field,
                subfield  = subfield,
                indicator = indicator,
                operator  = operator,
                values    = values)
            new_check.save()

        return HttpResponseRedirect('/checks/') # Redirect after POST

def ajax_check(request):
     form = CheckForm()



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

            for r in reader:
                name = r.title()
                results[name] = {}
                for check in report.checks.all():
                    result = _response_builder(r, check)
                    if result:
                        results[name][check.field] = result
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

def _bind_check_formset_with_report_checks(report, prefix='form' ):

    checkforms = [model_to_dict(check) for check in report.checks.all()]

    new_formset_bind_data = {
        prefix+'-TOTAL_FORMS': unicode(len(checkforms)),
        prefix+'-INITIAL_FORMS': unicode(len(checkforms)),
        prefix+'-MAX_NUM_FORMS': u''
    }

    for index, checkform in enumerate(checkforms):
        check_dict = _build_formset_dict_from_check(checkform, index, prefix)
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
    subfield    = checks_data[i].cleaned_data['subfield']
    indicator   = checks_data[i].cleaned_data['indicator']
    operator    = checks_data[i].cleaned_data['operator']
    values      = checks_data[i].cleaned_data['values']

    new_check = Check(title=check_title,
        description=description,
        field=field,
        subfield=subfield,
        indicator=indicator,
        operator=operator,
        values=values)
    return new_check

def _edit_check(checks_data, i, report):
    report.checks.all()[i].check_title = checks_data[i].cleaned_data['title']
    report.checks.all()[i].description = checks_data[i].cleaned_data['description']
    report.checks.all()[i].field       = checks_data[i].cleaned_data['field']
    report.checks.all()[i].subfield    = checks_data[i].cleaned_data['subfield']
    report.checks.all()[i].indicator   = checks_data[i].cleaned_data['indicator']
    report.checks.all()[i].operator    = checks_data[i].cleaned_data['operator']
    report.checks.all()[i].values      = checks_data[i].cleaned_data['values']
    return True


def _response_builder(record, check):

    response = ""

    if check.operator == 'eq':
        if __equals(record,check):
            response = check

    elif check.operator == 'nq':
        if _doesNotEqual(record,check):
            response = check

    elif check.operator == 'ex':
        if _exists(record, check):
            response = check

    elif check.operator == 'nx':
        if _doesNotExist(record, check):
            response = check

    elif check.operator == 'cn':
        if _contains(record, check):
            response = check

    elif check.operator == 'dc':
        if _doesNotContain(record, check):
            response = check

    elif check.operator == 'em':
        if _isEmpty(record, check):
            response = check

    return response

def _neither(check):
    return bool(not check.subfield and not check.indicator)

def _subfield(check):
    return bool(check.subfield and not check.indicator)

def _indicator(check):
    return bool(check.indicator and not check.subfield)


def __equals(record, check):
    if _neither(check):
        return record[check.field].value() == check.values
    if _subfield(check):
        return record[check.field][check.subfield] == check.values
    if _indicator(check):
        return record[check.field].indicators[int(check.indicator)] == check.values

def _doesNotEqual(record, check):
    if _neither(check):
        return record[check.field].value() != check.values
    elif _subfield(check):
        return record[check.field][check.subfield] != check.values
    elif _indicator(check):
        return record[check.field].indicators[int(check.indicator)] == check.values

def _exists(record, check):
    if _neither(check):
        return record[check.field]
    elif _subfield(check):
        return record[check.field][check.subfield]
    elif _indicator(check):
        return record[check.field].indicators[int(check.indicator)] == check.values

def _doesNotExist(record, check):
    if _neither(check):
        return not record[check.field]
    elif _subfield(check):
        return not record[check.field][check.subfield]
    elif _indicator(check):
        return not record[check.field].indicators[int(check.indicator)]

def _contains(record, check):
    if _neither(check):
        return record[check.field].value() in check.values.split(",")
    elif _subfield(check):
        return record[check.field][check.subfield] in check.values.split(",")
    elif _indicator(check):
        return record[check.field].indicators[int(check.indicator)] in check.values.split(",")

def _doesNotContain(record, check):
    if _neither(check):
        return record[check.field].value() not in check.values.split(",")
    elif _subfield(check):
        return record[check.field][check.subfield] not in check.values.split(",")
    elif _indicator(check):
        return record[check.field].indicators[int(check.indicator)] not in check.values.split(",")

def _isEmpty(record, check):
    if _neither(check):
        return record[check.field].value() == ""
    elif _subfield(check):
        return record[check.field][check.subfield] == ""
    elif _indicator(check):
        return record[check.field].indicators[int(check.indicator)] == ""

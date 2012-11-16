from check.models import *
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict
from ast import literal_eval
import pymarc


def home(request):
    return render_to_response('home.html');


def list_reports(request):
    reports = Report.objects.order_by('title')[:10]
    return render_to_response('list_reports.html', {'reports' : reports},  context_instance=RequestContext(request))

def report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render_to_response('report.html',{'report':report},  context_instance=RequestContext(request))

def add_report(request):
    check_formset = formset_factory(CheckForm)
    if request.method == 'GET':
        report = ReportForm(prefix='report')
        formset  = check_formset(prefix='checks')

        return render_to_response('reports.html',{'report_form': report, 'checks' : formset}, context_instance=RequestContext(request))

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
            error_form = ReportForm(request.POST)
            return render_to_response('reports.html',{'form' : error_form}, context_instance=RequestContext(request))

        report = Report(title=title, description = description, creator = creator)
        report.save()

        for i in range(0,checks_data.total_form_count()):

            new_check = _build_new_check(checks_data, i)

            new_check.save()

            report.checks.add(new_check)
            report.save()

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

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


def edit_report(request, report_id=''):
    check_formset = formset_factory(CheckForm)
    if request.method == 'GET':
        report = get_object_or_404(Report, pk=report_id)
        form = ReportForm(instance=report, prefix="report")
        formset  = check_formset(initial=[model_to_dict(check) for check in report.checks.all()] ,prefix='checks')

        return render_to_response('reports.html',{'report_form':form,'checks' : formset}, context_instance=RequestContext(request))

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
                    if report.checks.all()[i]:
                        report.checks.all()[i].check_title = checks_data[i].cleaned_data['title']
                        report.checks.all()[i].description = checks_data[i].cleaned_data['description']
                        report.checks.all()[i].field       = checks_data[i].cleaned_data['field']
                        report.checks.all()[i].subfield    = checks_data[i].cleaned_data['subfield']
                        report.checks.all()[i].indicator   = checks_data[i].cleaned_data['indicator']
                        report.checks.all()[i].operator    = checks_data[i].cleaned_data['operator']
                        report.checks.all()[i].values      = checks_data[i].cleaned_data['values']

                        report.checks.all()[i].save()

                except IndexError:
                    new_check = _build_new_check()
                    new_check.save()

                    report.checks.add(new_check)
            report.save()

        else:
            error_form = ReportForm(request.POST)
            return render_to_response('reports.html',{'form' : error_form}, context_instance=RequestContext(request))

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

def fork_report(request, report_id):

    return



def checks(request):
    if request.method == 'GET':
        checks = Check.objects.all()
        c = CheckForm()
        return render_to_response('checks.html',{'checks': checks ,'checkform': c}, context_instance=RequestContext(request))

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

        new_check = Check(title=title,desc=description,field=field,subfield=subfield,indicator=indicator,operator=operator,values=values)
        new_check.save()

        return HttpResponseRedirect('/checks/') # Redirect after POST




def run_report(request, report_id):
    if request.method == 'GET':
        report = Report(pk=report_id)
        run_report = RunReportForm(report_id=report_id)
        return render_to_response('run_report.html',{'run_report' : run_report, 'report' : report}, context_instance=RequestContext(request))

    if request.method == 'POST':
        data = RunReportForm(report_id, request.POST, request.FILES)
        results = {}

        if data.is_valid():
            report = data.cleaned_data['report']


            f = request.FILES['file']
            file = f.read()

            reader = pymarc.MARCReader(file)

            for r in reader:

                name = r.title()
                results[name] = {}
                for check in report.checks.all():
                    results[name][check.field] =  logic_builder(r, check.field, check.operator,check.subfield,check.indicator, check.values)
            return render_to_response('result.html',{'results': results },  context_instance=RequestContext(request))

        else:
            error_form = RunReportForm(report_id, request.POST, request.FILES)
            return render_to_response('run_report.html',{'run_report' : error_form}, context_instance=RequestContext(request))






def operator_logic(r, op, field, subfield='',indicator='',values=''):

    response = ""

    if not r[field]:
        response = field + ' does not exist'
    else:
        pass


    if op == 'eq':
        if not subfield:
            if r[field] == values:
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield] == values:
                response = response_builder(op, field, subfield, values)
            else:
                pass

    if op == 'nq':
        if not subfield:
            if r[field] != values:
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield] != values:
                response = response_builder(op, field, subfield, values)
            else:
                pass


    if op == 'ex':
        if not subfield:
            if r[field]:
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield]:
                response = response_builder(op, field, subfield, values)
            else:
                pass

    if op == 'nx':
        if subfield:
            if not r[field][subfield]:
                response = response_builder(op, field, subfield, values)
            else:
                pass

    if op == 'cn':
        if not subfield:
            if r[field] in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield] in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                pass

    if op == 'dc':
        if not subfield:
            if r[field] not in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield] not in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                pass

    if op == 'em':
        if not subfield:
            if r[field] == '':
                response = response_builder(op, field, subfield, values)
            else:
                pass
        else:
            if r[field][subfield] == '':
                response = response_builder(op, field, subfield, values)
            else:
                pass

    return response


def response_builder(op, field, subfield="", values=""):
    response = field + " "
    if subfield:
        response += subfield + " "
    response += [check[1] for check in Check.OPS if op in check][0] + " "
    if values:
        response += values + ""
    return response


def logic_builder(r, field, op, subfield='', indicator='', values='' ):

    if not subfield:
        if eval(op+'(r,field,subfield,values)'):
            response = response_builder(op,field,subfield,values)
        else:
            pass
    else:
        fun = "sub" + op
        if eval(fun+'(r,field,subfield,values)'):
            response = response_builder(op,field,subfield,values)
        else:
            pass

    return response


def eq(r, field, subfield='', values='' ):
    return r[field].value() == values

def nq(r, field, subfield='', values=''):
    return r[field].value() != values

def ex(r, field, subfield='', values='' ):
    return  bool(r[field])

def nx(r, field, subfield='', values='' ):
    return bool(not r[field])

def cn(r, field, subfield='', values='' ):
    return bool(r[field].value() in values.split(","))

def dc(r, field, subfield='', values='' ):
    return bool(r[field].value() not in values.split(","))

def em(r, field, subfield='', values='' ):
    return bool(r[field].value() == "")

def subeq(r, field, subfield='', values='' ):
    return r[field][subfield] == values

def subnq(r, field, subfield='', values=''):
    return r[field][subfield] != values

def subex(r, field, subfield='', values='' ):
    return  bool(r[field][subfield])

def subnx(r, field, subfield='', values='' ):
    return bool(not r[field][subfield])

def subcn(r, field, subfield='', values='' ):
    return bool(r[field][subfield] in values.split(","))

def subdc(r, field, subfield='', values='' ):
    return bool(r[field][subfield] not in values.split(","))

def subem(r, field, subfield='', values='' ):
    return bool(r[field][subfield] == "")

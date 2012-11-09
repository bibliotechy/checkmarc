from check.models import *
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext
from django.forms.formsets import formset_factory
import pymarc

def home(request):
    return render_to_response('home.html');

def report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    return render_to_response('report.html',{'report':report})

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
            user = User(name="anonymous")

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
            check_title = checks_data[i].cleaned_data['title']
            description = checks_data[i].cleaned_data['description']
            field       = checks_data[i].cleaned_data['field']
            subfield    = checks_data[i].cleaned_data['subfield']
            operator    = checks_data[i].cleaned_data['operator']
            values      = checks_data[i].cleaned_data['values']

            new_check = Check(title=check_title, description=description,field=field,subfield=subfield,operator=operator,values=values)
            new_check.save()

            report.checks.add(new_check)
            report.save()

        return HttpResponseRedirect('/report/'+ str(report.pk) +'/') # Redirect after POST

def edit_report(request, report_id=''):
    if request.method == 'GET':
        report = get_object_or_404(Report, pk=report_id)
        form = ReportForm(instance=report)
        return render_to_response('reports.html',{'form':form})

    if request.method == 'POST':
        return

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
            operator    = data.cleaned_data['operator']
            values      = data.cleaned_data['values']

        new_check = Check(title=title,desc=description,field=field,subfield=subfield,operator=operator,values=values)
        new_check.save()

        return HttpResponseRedirect('/checks/') # Redirect after POST




def run_report(request, report_id):
    if request.method == 'GET':
        run_report = RunReportForm(report_id=report_id)
        return render_to_response('run_report.html',{'run_report' : run_report}, context_instance=RequestContext(request))

    if request.method == 'POST':
        data = RunReportForm(request.POST, request.FILES)
        results = {}

        if data.is_valid():
            report = data.cleaned_data['report']


            f = request.FILES['file']
            file = f.read()

            reader = pymarc.MARCReader(file)

            for r in reader:
                results[r.title()] = {}
                for check in report.checks.all():
                    results[r.title()][check.fields] =  operator_logic(r, check.operator, check.fields, check.values)
            return render_to_response('result.html',{'results': results })

        else:
            error_form = RunReportForm(request.POST, request.FILES)
            return render_to_response('run_report.html',{'run_report' : error_form}, context_instance=RequestContext(request))






def operator_logic(r, op, field, subfield='',values=''):

    response = "Haven't defined that yet"

    if not r[field]:
        response = field + ' does not exist'
    else:
        pass


    if op == 'eq':
        if not subfield:
            if r[field] == values:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield] == values:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

    if op == 'nq':
        if not subfield:
            if r[field] != values:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield] != values:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"


    if op == 'ex':
        if not subfield:
            if r[field]:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield]:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

    if op == 'nx':
        if subfield:
            if not r[field][subfield]:
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

    if op == 'cn':
        if not subfield:
            if r[field] in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield] in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

    if op == 'dc':
        if not subfield:
            if r[field] not in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield] not in values.split(','):
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

    if op == 'em':
        if not subfield:
            if r[field] == '':
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"
        else:
            if r[field][subfield] == '':
                response = response_builder(op, field, subfield, values)
            else:
                response = "BOOOOOOM"

        return response


def response_builder(op, field, subfield="", values=""):
    response = field + " "
    if subfield:
        response += subfield + " "
    response += [Check.OPS[index] for index, check in enumerate(Check.OPS) if op in check][0][1] + " "
    response += values + "."
    return response








('em', 'is empty'),
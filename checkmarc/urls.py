from django.conf.urls import patterns, include, url
from django.views.generic import ListView
from check.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('check.views',
    # Examples:
    url(r'^$', 'home'),
    url(r'$wtf/$','walkthrough'),
    url(r'$about/$','about'),



    url(r'^login/$', 'login'),
    url(r'^logout/$', 'logout'),

    url(r'^checks/$','checks'),

    url(r'^report/list/$', 'list_reports'),
    url(r'^report/add/$', 'add_report'),
    url(r'^report/(?P<report_id>\d+)/$','report'),
    url(r'^report/(?P<report_id>\d+)/run/$','run_report'),
    url(r'^report/(?P<report_id>\d+)/edit/$', 'edit_report'),
    url(r'^report/(?P<report_id>\d+)/fork/$', 'fork_report'),

    url(r'^myreports/$','myreports'),

    url(r'', include('social_auth.urls')),
    # url(r'^checkmarc/', include('checkmarc.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),
)

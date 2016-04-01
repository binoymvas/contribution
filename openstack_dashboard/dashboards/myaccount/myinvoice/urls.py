"""
url file
File: url.py
Description: defining the urls 
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from django.conf.urls import patterns
from django.conf.urls import url
from openstack_dashboard.dashboards.myaccount.myinvoice import views

#defining the urls
urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<invoice_id>[^/]+)/update_invoice/$', views.UpdateInvoiceView.as_view(), name='update_invoice'),
    url(r'^(?P<id>[^/]+)/detail_invoice/$', views.DetailInvoiceView.as_view(), name='detail_invoice'),
)
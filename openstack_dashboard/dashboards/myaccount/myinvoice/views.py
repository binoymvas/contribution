"""
view file
File: view.py
Description: Logic comes 
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from horizon import tabs
from openstack_dashboard.dashboards.myaccount.myinvoice import tabs as myaccount_tabs
import json
from cloudkittyclient import client
from cloudkittyclient.common import utils
import ConfigParser
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from openstack_dashboard import api
from openstack_dashboard.dashboards.myaccount.myinvoice import forms as project_forms
from openstack_dashboard.dashboards.myaccount.myinvoice import tables as invoice_tables
from bson import json_util
import simplejson as json
from cloudkittydashboard.api import cloudkitty as kittyapi

#Class to make the class objects
class InvoiceData:

    def __init__(self, infos):
        """
        Desc: Method to cret the class objects
        params: 
            infos: Details of the invoices
        Return : NA
        """
        
        #setting the class bojects
        self.id = infos['invoice_id']
        self.name = infos['tenant_name']
        self.tenant_id = infos['tenant_id']
        self.paid_cost = infos['paid_cost']
        self.balance_cost = infos['balance_cost']
        self.invoice_date = infos['invoice_date']
        
        #Setting the payment_status text depend on the value
        self.payment_status = 'NEW'
        if infos['payment_status'] == 1:
            self.payment_status = 'PAID'
        elif infos['payment_status'] == 2:
            self.payment_status = 'DECLINED'
        elif infos['payment_status'] == 3:
            self.payment_status = 'REFUNDED'
            
        self.invoice_data = infos['invoice_data']
        self.total_cost = infos['total_cost']
        self.invoice_period_to = infos['invoice_period_to']
        self.invoice_period_from = infos['invoice_period_from']

#Class for the tabbed table view
class IndexView(tabs.TabbedTableView):
    
    #Setting the properties
    tab_group_class = myaccount_tabs.MyinvoiceTabs
    template_name = 'myaccount/myinvoice/index.html'
     
#Class for the update invoice
class UpdateInvoiceView(forms.ModalFormView):
    
    #Setting the properties
    form_class = project_forms.UpdateInvoice
    template_name = 'myaccount/myinvoice/update_invoice.html'
    success_url = reverse_lazy("horizon:myaccount:myinvoice:index")
    modal_id = "create_snapshot_modal"
    modal_header = _("Update Invoice")
    submit_label = _("Update Invoice")
    submit_url = "horizon:myaccount:myinvoice:update_invoice"

    @memoized.memoized_method
    def get_object(self):
        """
        Method: get_object
        Desc: Getting the object details
        Params: self
        Return: Class objects
        """

        try:

            #Making the cloudkitty connection
            cloudkitty_conn = kittyapi.cloudkittyclient(self.request)
            
            #Getting the invoice data
            invoice = cloudkitty_conn.reports.get_invoice(invoice_id=self.kwargs["invoice_id"])
            
            #Making the invoice data type to json
            invoice_details_full = json.loads(invoice, object_hook=json_util.object_hook, use_decimal=True) # invoice full

            #Iterating through the invoice and setting the dictionary 
            for tenant in invoice_details_full:
                for tenant_data in invoice_details_full[tenant]:
                    
                    # Necessary variables with necesary values
                    # Assigned necessary values for reusing the same
                    info = {}
                    info['balance_cost'] = tenant_data['balance_cost']
                    info['invoice_id'] = tenant_data['invoice_id']
                    info['paid_cost'] = tenant_data['paid_cost']
                    info['tenant_name'] = tenant_data['tenant_name']
                    info['invoice_date'] = tenant_data['invoice_date'].strftime('%B-%d-%Y')
                    info['invoice_data'] = tenant_data['invoice_data']
                    info['payment_status'] = tenant_data['payment_status']
                    info['total_cost'] = tenant_data['total_cost']
                    info['tenant_id'] = tenant_data['tenant_id']
                    info['invoice_period_to'] = tenant_data['invoice_period_to'].strftime('%B-%d-%Y')
                    info['invoice_period_from'] = tenant_data['invoice_period_from'].strftime('%B-%d-%Y')

            #Calling class with data. To make the class objects
            InvoiceData(info)
            return info 
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve invoices."))

    def get_initial(self):
        """
        Method: get_initial
        Desc: Getting the object details to show in the update form
        Params: self
        Return: data dictionary
        """
        
        #Getting the object details to show in the update form
        invoices = self.get_object()
        
        #Setting the data to show in update form
        data = {'invoice_id': invoices['invoice_id'],
                'tenant_name': invoices['tenant_name'], 
                'total_cost': invoices['invoice_data'],
                'balance_cost': invoices['balance_cost'],
                'paid_cost': invoices['paid_cost'],
                'payment_status': invoices['payment_status']}
        return data

    def get_context_data(self, **kwargs):
        """
        Method: get_context_data
        Desc: Setting the context data
        Params: self, 
            wargs: details if the invoice
        Return: context
        """
        
        #Setting the context
        context = super(UpdateInvoiceView, self).get_context_data(**kwargs)
        invoice_id = self.kwargs['invoice_id']
        context['invoice_id'] = invoice_id
        context['invoice'] = self.get_object()
        context['submit_url'] = reverse(self.submit_url, args=[invoice_id])
        return context

#Class for the detailed view
class DetailInvoiceView(tabs.TabView):
    
    #Setting the properties
    tab_group_class = myaccount_tabs.MyinvoiceDetailsTabs
    template_name = 'myaccount/myinvoice/details.html'
    page_title = _("Invoice Details: {{ invoice.name }}")
    
    def get_context_data(self, **kwargs):
        """
        Method: get_context_data
        Desc: Setting the context data
        Params: self, 
            wargs: details if the invoice
        Return: context
        """
        
	#Setting the context
        context = super(DetailInvoiceView, self).get_context_data(**kwargs)

	try:
	    invoice = self.get_data()
            table = invoice_tables.InvoicesTable(self.request)
            context["invoice"] = invoice
            context["url"] = self.get_redirect_url()
            context["actions"] = table.render_row_actions(invoice)
            invoice.status_label = 'True'
            return context
	except Exception:
            exceptions.handle(self.request, _("No invoice data for the available invoice id."))
	    return context

    @staticmethod
    def get_redirect_url():
        """
        Method: get_redirect_url
        Desc: Getting the redirect url
        Params: NA
        Return: detail url
        """
        
        #getting the redirect url
        return reverse_lazy('horizon:myaccount:myinvoice:detail_invoice')

    @memoized.memoized_method
    def get_data(self):
        """
        Method: get_data
        Desc: Getting the data
        Params: self
        Return: invoice data (dictionary)
        """
   
    	try:        
	    #connecting to the cloudkitty api and getting the invoice details
            cloudkitty_conn = kittyapi.cloudkittyclient(self.request)
            invoice = cloudkitty_conn.reports.get_invoice(invoice_id=self.kwargs['id'])
            invoice_details_full = json.loads(invoice, object_hook=json_util.object_hook, use_decimal=True)
            #going through the invoice details and setting the dictionary
            invoice_data = ''
            for tenant in invoice_details_full:
                for tenant_data in invoice_details_full[tenant]:
            
                    #Necessary variables with necesary values
                    #Assigned necessary values for reusing the same
                    info = {}
                    info['balance_cost'] = tenant_data['balance_cost']
                    info['invoice_id'] = tenant_data['invoice_id']
                    info['paid_cost'] = tenant_data['paid_cost']
                    info['tenant_name'] = tenant_data['tenant_name']
                    info['tenant_id'] = tenant_data['tenant_id']	
                    info['invoice_date'] = tenant_data['invoice_date'].strftime('%B-%d-%Y')
                    info['invoice_data'] = tenant_data['invoice_data']
                    info['payment_status'] = tenant_data['payment_status']
                    info['total_cost'] = tenant_data['total_cost']
                    info['invoice_period_to'] = tenant_data['invoice_period_to'].strftime('%B-%d-%Y')
                    info['invoice_period_from'] = tenant_data['invoice_period_from'].strftime('%B-%d-%Y')
                    invoice_data =  InvoiceData(info)
            return invoice_data
	except Exception:
            exceptions.handle(self.request, _("No invoice data for the available invoice id."))
	    return invoice_data

    def get_tabs(self, request, *args, **kwargs):
        """
        Method: get_tabs
        Desc: Getting the tab to show the details
        Params: self, request, *args, **kwargs(invoice details)
        Return: tab with details
        """
       	try: 
            invoice = self.get_data()
            return self.tab_group_class(request, invoice=invoice, **kwargs)
	except Exception:
            exceptions.handle(self.request, _("No invoice data for the available invoice id."))

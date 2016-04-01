"""
table file
File: tables.py
Description: table file 
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from horizon import tables
from django.utils.translation import ungettext_lazy
from cloudkittyclient import client
from cloudkittydashboard.api import cloudkitty as kittyapi

#Defining the classes for action
#class for update
class UpdateInvoiceAction(tables.LinkAction):
    
    #Defining the url, name etc 
    name = "invoice"
    verbose_name = _("Update Invoice")
    url = "horizon:myaccount:myinvoice:update_invoice"
    classes = ("ajax-modal",)
    icon = "camera"

    def allowed(self, request, invoice=None):
        """
        Method: Allowed
        desc: Used to give the permission for user. true means to show the button
        params:
            self, request and invoice
        return: True/False
        """
        
        #Checking the current logged in user is admin. And giving permission accordingly
        #Return True to allow table-level update action to appear.
    	if str(request.user) == 'admin':
            return True 
        else:
            return False

#class for filter
class InvoiceFilterAction(tables.FilterAction):
    
    #Defining the filter_type, filter_choices etc 
    filter_type = "server"
    filter_choices = (('select', _('Select'), True),
                      ('invoice_id', _("Invoice ID = "), True),
                      ('payment_status', _("Payment Status ="), True),
                      ('tenant_id', _("Tenant Id ="), True))
    name = "myfilter"

#class for delete
class DeleteInvoice(tables.DeleteAction):
    
    #help text to some batch/delete actions.
    help_text = _("Deleted invoices are not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Invoice",
            u"Delete Invoice",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Invoice",
            u"Deleted Invoice",
            count
        )

    def allowed(self, request, invoice=None):
        """
        Method: Allowed
        desc: Used to give the permission for user. true means to show the button
        params:
            self, request and invoice
        return: True/False
        """
        
        #Checking the current logged in user is admin. And giving permission accordingly
        #Return True to allow table-level bulk delete action to appear.
        if str(request.user) == 'admin':
            return True 
        else:
            return False

    def delete(self, request, invoice_id):
        """
        Method: delete
        desc: Used to delete the invoice.
        params:
            self, request and invoice_id
        return: True/False
        """
        cloudkitty_conn = kittyapi.cloudkittyclient(request)
        cloudkitty_conn.reports.delete_invoice(invoice_id=invoice_id)
	
def get_paid_cost(invoice):
    """
    Method: get_paid_cost
    desc: Used to show the $ infront of paid cost
    params: invoice
    return: cost with $
    """
    return _("$%s") % (invoice.paid_cost)

def get_balance_cost(invoice):
    """
    Method: get_balance_cost
    desc: Used to show the $ infront of balance cost
    params: invoice
    return: cost with $
    """
    return _("$%s") % (invoice.balance_cost)

#DataTable
class InvoicesTable(tables.DataTable):

    #Defining the fields to show in the table
    STATUS_DISPLAY_CHOICES = (
        ("new", pgettext_lazy("Current status of an Invoice", u"NEW")),
        ("paid", pgettext_lazy("Current status of an Invoice", u"PAID")),
        ("declined", pgettext_lazy("Current status of an Invoice", u"DECLINED")),
        ("refunded", pgettext_lazy("Current status of an Invoice", u"REFUNDED")),)
    invoice_id = tables.Column('id', verbose_name=_("Invoice Id"), link="horizon:myaccount:myinvoice:detail_invoice")
    name = tables.Column('tenant_name', verbose_name=_("Tenant Name"))
    status = tables.Column('payment_status', verbose_name=_("Paid Status"),  status=True, display_choices=STATUS_DISPLAY_CHOICES)
    paid_cost = tables.Column(get_paid_cost, verbose_name=_("Paid Cost"))
    balance_cost = tables.Column(get_balance_cost, verbose_name=_("Balance Cost"))
    invoice_date = tables.Column('invoice_date', verbose_name=_("invoice Date"))
    
    class Meta(object):
        
        #Table properties
        name = "invoices"
        verbose_name = _("Invoices")
        
        #Action for the table
        table_actions = (InvoiceFilterAction, DeleteInvoice)
        
        #Action for each row
        row_actions = (UpdateInvoiceAction, DeleteInvoice,)
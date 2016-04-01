"""
view file
File: forms.py
Description: Form for the update  
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from horizon import forms
from horizon import exceptions
from cloudkittyclient import client
from cloudkittydashboard.api import cloudkitty as kittyapi
from django.utils.translation import ugettext_lazy as _

#update invoice class
class UpdateInvoice(forms.SelfHandlingForm):
    
    #Defining the form fields
    invoice_id = forms.CharField(label=_("Invoice ID"),  widget=forms.TextInput(attrs={'readonly':'readonly'}), required=False)
    paid_cost = forms.FloatField(label=_("Paid  Cost"))
    paid_status = (('0', 'New'), ('1', 'Paid'), ('2', 'Declined'), ('3', 'Refunded'))
    payment_status = forms.ChoiceField(choices=paid_status, required=True )

    def handle(self, request, data):
        """
        method : handle
        desc: To handle the update
        params:
            self - self
            request - request data
            data - update datas
        return: Update o/p
        """
        
        try:
            
            #Making the connection with the cloudkitty
            cloudkitty_conn = kittyapi.cloudkittyclient(self.request)
            
            #updating the invoice
            invoice = cloudkitty_conn.reports.update_invoice(invoice_id=data['invoice_id'], payment_status=data['payment_status'], paid_cost=data['paid_cost'])
            return invoice
        except Exception:
            exceptions.handle(request, _('Unable to update invoice.'))

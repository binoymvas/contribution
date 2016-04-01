"""
view file
File: forms.py
Description: Form for the update  
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from django.utils.translation import ugettext_lazy as _
import horizon
from openstack_dashboard.dashboards.myaccount import dashboard

#class to show invoices
class Myinvoice(horizon.Panel):
    
    #Defining the variables
    name = _("Invoice")
    slug = "myinvoice"

#Registering the panel
dashboard.Myaccount.register(Myinvoice)
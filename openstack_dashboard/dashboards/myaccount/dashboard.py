"""
view file
File: dashboard.py
Description: Dash board menu 
Created On: 09-March-2016
Created By: binoy@nephoscale.com
"""

#importing the packages
from django.utils.translation import ugettext_lazy as _
import horizon

#My account class
class Myaccount(horizon.Dashboard):
    
    #Defining the panels
    name = _("My Account")
    slug = "myaccount"
    panels = ('myinvoice',)
    default_panel = 'myinvoice'

#Registering the panel
horizon.register(Myaccount)
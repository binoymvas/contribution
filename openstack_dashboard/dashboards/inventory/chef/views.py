# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
#from horizon import forms
#from horizon import messages
from horizon import tables
from horizon.utils import memoized
from horizon import views

from openstack_dashboard.dashboards.inventory.chef.tables import ChefTable

from datetime import datetime
import chef
import json

import operator as op

import openstack_dashboard.local.local_settings as local_settings


chef_url = local_settings.INVENTORY_CHEF_URL
chef_key = local_settings.INVENTORY_CHEF_KEY
chef_usr = local_settings.INVENTORY_CHEF_USER

def toDict(node):
    if isinstance(node, chef.node.NodeAttributes):
        n = {}
        for k, v in node.iteritems():
            n[k] =toDict(v)
        return n
    return node

class ChefNode:

    def __init__(self, id, platform, fqdn, ipaddr, uptime, lstchk, roles, attrs):
        self.id = id
        self.platform = platform
        self.fqdn = fqdn
        self.ipaddr = ipaddr
        self.uptime = uptime
        self.lstchk = lstchk
        self.roles = roles
        self.attrs = json.dumps(toDict(attrs), indent=4)


def initChefNode(node):
    id = node.__str__()
    platform =  node.attributes['platform'] + ' ' + node.attributes['platform_version'] if 'platform' in node.attributes else ''
    fqdn = node.attributes['fqdn'] if 'fqdn' in node.attributes else ''
    ipaddr = node.attributes['ipaddress'] if 'ipaddress' in node.attributes else ''
    uptime = node.attributes['uptime_seconds'] if 'uptime_seconds' in node.attributes else 0
    try:
        if uptime <= 0:
            uptime = ''
        elif uptime < 60:
            uptime = '%d %s' % (uptime, 'seconds')
        elif uptime < 60 * 60:
            uptime = '%d %s' % (uptime // 60,  'minutes')
        elif uptime < 60 * 60 * 24:
            uptime = '%d $s' % (uptime // (60 * 60), 'hours')
        else:
            uptime = '%d %s' % (uptime // (60 * 60 * 24), 'days')
    except:
        uptime = ''
    return ChefNode(
        id,
        platform,
        fqdn,
        ipaddr,
        uptime,
        datetime.fromtimestamp((node.attributes['ohai_time'])).strftime("%Y-%m-%d %H:%M:%S") if 'ohai_time' in node.attributes else '',
        ", ".join(node.attributes['roles']) if 'roles' in node.attributes else '',
        node.attributes
    )

class DetailView(views.HorizonTemplateView):
    template_name = 'inventory/chef/detail.html'
    page_title = _("Node Details: {{ node.id }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        node = self.get_data()
        context["node"] = initChefNode(node)
        return context

    @memoized.memoized_method
    def get_data(self):
        try:
            node_id = self.kwargs['id']
            chefapi = chef.ChefAPI(chef_url, chef_key, chef_usr)
            node = chef.Node(node_id, api=chefapi)
        except Exception:
            #redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve node details.'),
                              redirect=redirect)
        return node


class IndexView(tables.DataTableView):
    # A very simple class-based view...
    table_class= ChefTable
    template_name = 'inventory/chef/index.html'
    page_title = _("chef")

    def get_data(self):
        nodes = []
        chefapi = chef.ChefAPI(chef_url, chef_key, chef_usr)
        for name in  chef.Node.list(api=chefapi):
            node = chef.Node(name)
            nodes.append(initChefNode(node))
        nodes.sort(key=op.attrgetter('id'))
        return nodes


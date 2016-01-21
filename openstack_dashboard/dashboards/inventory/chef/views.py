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

from horizon import tables
from horizon import views

from openstack_dashboard.dashboards.inventory.chef.tables import ChefTable

from datetime import datetime
import chef
import json

import openstack_dashboard.local.local_settings as local_settings


chef_url = local_settings.INVENTORY_CHEF_URL
chef_key = local_settings.INVENTORY_CHEF_KEY
chef_usr = local_settings.INVENTORY_CHEF_USER


class ChefNode:

    def __init__(self, id, platform, fqdn, ipaddr, uptime, lstchk, roles):
        self.id = id
        self.platform = platform
        self.fqdn = fqdn
        self.ipaddr = ipaddr
        self.uptime = uptime
        self.lstchk = lstchk
        self.roles = roles

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
            id = node.__str__()
            platform =  node.attributes['platform'] + ' ' + node.attributes['platform_version'] if 'platform' in node.attributes else ''
            fqdn = node.attributes['fqdn'] if 'fqdn' in node.attributes else ''
            ipaddr = node.attributes['ipaddress'] if 'ipaddress' in node.attributes else ''
            uptime = node.attributes['uptime_seconds'] if 'uptime_seconds' in node.attributes else 0
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
            nodes.append(
                ChefNode(
                    id,
                    platform,
                    fqdn,
                    ipaddr,
                    uptime,
                    datetime.fromtimestamp((node.attributes['ohai_time'])).strftime("%Y-%m-%d %H:%M:%S") if 'ohai_time' in node.attributes else '',
                    ", ".join(node.attributes['roles']) if 'roles' in node.attributes else ''
                )
            )
        return nodes


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

from openstack_dashboard.dashboards.inventory.nodes.tables import NodesTable

import brew.maas

import openstack_dashboard.local.local_settings as local_settings


maas_key = local_settings.INVENTORY_MAAS_KEY
maas_url = local_settings.INVENTORY_MAAS_URL


class Node:

    def __init__(self, id, hostname, mgmtIP, ipmiIP, status):
        self.id = id
        self.hostname = hostname
        self.mgmtIP = mgmtIP
        self.ipmiIP = ipmiIP
        self.status = status

class IndexView(tables.DataTableView):
    # A very simple class-based view...
    table_class= NodesTable
    template_name = 'inventory/nodes/index.html'
    page_title = _("nodes")

    def get_data(self):
        nodes = []
	maas = brew.maas.MAAS(maas_key, maas_url)
        for node in  maas.nodes():
            nodes.append(
                Node(
                    node['system_id'],
                    node['hostname'],
                    maas.get_node_mgmt_ip(node['system_id']),
                    maas.get_node_ipmi_ip(node['system_id']),
                    node['substatus_name']
                )
            )
        return nodes


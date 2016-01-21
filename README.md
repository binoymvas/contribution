Horizon plugins consist a bunch of files. `openstack_dashboard` dir 'mirrors' corresponding directory structure of Horizon installation.

Directories under `openstack_dashboard/dashboards` are actual dashboards implementations (top level main menu items and its views).

`openstack_dashboard/dashboards/inventory` directory:

1. `dashboard.py` - Inventory dashboard declaration module.
2. `chef` and `nodes` - Inventory dashboard views modules for Inventory/Chef and Inventory/Nodes.
3. `templates/*` - Inventory views templates.
4. `static/*` - support files and libs.

`openstack_dashboard/enabled` direcoty contains dashboards and their views 'triggers` -- files for enabling plugins:

1. `_5000_inventory.py` - Inventory dashboard 'trigger'.
2. `_5010_inventory_nodes.py` - Inventory/Nodes view 'trigger'.
3. `_5020_inventory_chef.py` - Inventory/Chef view 'trigger'.

Files should be respectively placed under OpenStack Horizon root `openstack_dashboards` directory.

`openstack_dashboard/local/local_settings.py` must provide following configuration options:


Inventory/Chef options:

- INVENTORY_CHEF_URL
- INVENTORY_CHEF_KEY
- INVENTORY_CHEF_USER


Inventory/Nodes options:

- INVENTORY_MAAS_KEY
- INVENTORY_MAAS_URL

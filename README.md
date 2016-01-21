Horizon plugins consis a bunch of files. `openstack_dashboard` mirrors corresponding directory of Horizon installation. Directories under `openstack_dashboard/dashboards` directory are actual dashboards implementations (top level main menu items).

`openstack_dashboard/dashboards/inventory` directory:

1. `dashboard.py` - Inventory dashboard declaration module.
2. `chef` and `nodes` - Inventory dashboard views for Chef and Nodes.
3. `templates/*` - Inventory views templates.
4. `static` - support files and libs.

`openstack_dashboard/enabled` direcoty contains Dashboard and its views 'triggers` -- files for enabling plugins:

1. `_5000_inventory.py` - Inventory dashboard 'trigger'.
2. `_5010_inventory_nodes.py` - Inventory / Nodes view 'trigger'.
3. `_5020_inventory_chef.py` - Inventory / Chef view 'trigger'.

Files should be respectively placed under OpenStack Horizon root `openstack_dashboards` directory.

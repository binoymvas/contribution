# The slug of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'nodes'
# The slug of the dashboard the PANEL associated with. Required.
PANEL_GROUP = 'default'
# The slug of the panel group the PANEL is associated with.
PANEL_DASHBOARD = 'inventory'

# Python panel class of the PANEL to be added.
ADD_PANEL = 'openstack_dashboard.dashboards.inventory.nodes.panel.NodesPanel'


from django.utils.translation import ugettext_lazy as _

from horizon import tables


class ChefTable(tables.DataTable):

    id = tables.Column('id',
        link = "horizon:inventory:chef:detail",
        verbose_name = _('Node Name'),
        cell_attributes_getter = lambda v: {"nowrap": True},
    )
    platform = tables.Column('platform',
        verbose_name = _('Platform'),
        cell_attributes_getter = lambda v: {"nowrap": True},
    )
    ipaddr = tables.Column('ipaddr',
        verbose_name = _('IP Address'),
        cell_attributes_getter = lambda v: {"nowrap": True},
    )
    uptime = tables.Column('uptime',
        verbose_name = _('Uptime'),
        cell_attributes_getter = lambda v: {"nowrap": True},
    )
    lstchk = tables.Column('lstchk',
        verbose_name = _('Last Check-In'),
        cell_attributes_getter = lambda v: {"nowrap": True},
    )
    roles = tables.Column('roles', verbose_name = _('Roles'),)


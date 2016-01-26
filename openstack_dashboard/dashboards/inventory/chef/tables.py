from django.utils.translation import ugettext_lazy as _

from horizon import tables


class ChefTable(tables.DataTable):

    id = tables.Column('id',
        link = "horizon:inventory:chef:detail",
        verbose_name = _('Node Name'),
    )
    platform = tables.Column('platform', verbose_name = _('Platform'),)
    #fqdn = tables.Column('fqdn', verbose_name = _('Node FQDN'),)
    ipaddr = tables.Column('ipaddr', verbose_name = _('IP Address'),)
    uptime = tables.Column('uptime', verbose_name = _('Uptime'),)
    lstchk = tables.Column('lstchk', verbose_name = _('Last Check-In'),)
    roles = tables.Column('roles', verbose_name = _('Roles'),)


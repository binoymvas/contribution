from django.utils.translation import ugettext_lazy as _

from horizon import tables


class NodesTable(tables.DataTable):

    nodeUUID = tables.Column('id', verbose_name = _('Node UUID'),)
    hostname = tables.Column('hostname', verbose_name = _('Hostname'),)
    mgmtIP   = tables.Column('mgmtIP', verbose_name = _('Mgmt IP'),)
    ipmiIP   = tables.Column('ipmiIP', verbose_name = _('IPMI IP'),)
    status   = tables.Column('status', verbose_name = _('Status'),)


"""
IPMI Library
"""

from brew.log import logger
from subprocess import Popen, PIPE

class IPMIError(Exception):
    pass

class IPMI(object):

    # define path to ipmitool
    IPMITOOL_PATH = 'ipmitool'

    def __init__(self, name, ipmi_host, ipmi_user, ipmi_pass):
        '''Initialize the IPMI class'''

        # store some settings
        self.name = name
        self.ipmi_host = ipmi_host
        self.ipmi_user = ipmi_user
        self.ipmi_pass = ipmi_pass

    def _run(self, ipmi_cmd):
        '''Helper method to run a command against ipmitool'''

        cmd = self.IPMITOOL_PATH
        cmd += (' -I lan')
        cmd += (' -H %s' % self.ipmi_host)
        cmd += (' -U %s' % self.ipmi_user)
        cmd += (' -P %s' % self.ipmi_pass)
        cmd += (' %s' % ipmi_cmd)

        # run the command, return the return code
        child = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        child.communicate()       
        return child.returncode

    def reset(self, pxe_boot=False):
        '''Reset (soft) a host'''

        # if pxe_boot is true, then we should request the system boot from
        # the pxe network prior to resetting it
        if pxe_boot:
            self.boot_from_pxe()

        if self._run('chassis power reset'):
            logger.warn("failed to chassis power reset %s" % self.name)

    def boot_from_pxe(self):
        '''Force system to boot from pxe on the next reset'''
        if self._run('chassis bootparam set bootflag force_pxe'):
            logger.warn('failed to chassis bootparam set bootflag force_pxe %s' % self.name)
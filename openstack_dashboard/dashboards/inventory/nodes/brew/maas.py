"""
MaaS Functions for Brewer
"""

APIKEY = "Cfh7E8DMG5KFcGfWB2:XbusEZ8R6hpmZaqqN7:ucs9eBd8TPLJusDMNb6NEmLxh2WjBqDR"
MAAS_URL = "http://127.0.0.1/MAAS/api/1.0"

from apiclient import maas_client

#try:
#    from apiclient import maas_client
#except ImportError:
#    print "You probably need to apt-get install python-maas-client"
#    raise
import urllib2
import json
import netaddr
import yaml
import logging
import time

from log import logger


# there is a bug in the current version of the maas client
# causing POST operations to submit URLs with the parameters
# in them just as if it was a GET request, so we override
# the method that builds the URLs and use our own overridden
# class
class MAASClientOverride(maas_client.MAASClient):
    def _formulate_change(self, path, params, as_json=False):
        """Return URL, headers, and body for a non-GET request.

        This is similar to _formulate_get, except parameters are encoded as
        a multipart form body.

        :param path: Path to the object to issue a GET on.
        :param params: A dict of parameter values.
        :param as_json: Encode params as application/json instead of
            multipart/form-data. Only use this if you know the API already
            supports JSON requests.
        :return: A tuple: URL, headers, and body for the request.
        """
        url = self._make_url(path)
        # the following code is removed from our method
        # if 'op' in params:
        #    params = dict(params)
        #    op = params.pop('op')
        #    url += '?' + urlencode([('op', op)])
        if as_json:
            body, headers = maas_client.encode_json_data(params)
        else:
            body, headers = maas_client.encode_multipart_data(params, {})
        self.auth.sign_request(url, headers)
        return url, headers, body

class MAASError(Exception):
	pass

class MAAS(object):

    def __init__(self, api_key, maas_url):

        # store values
        self.api_key = api_key
        self.maas_url = maas_url
        self.oauth = maas_client.MAASOAuth(*APIKEY.split(":"))

        # create client for this class
        self.client = MAASClientOverride(self.oauth, maas_client.MAASDispatcher(), self.maas_url)

    def sync(self, config_file):
        '''
        This method is the main entry point for syncing data inside maas based
        on a yaml file (path stored in args.config_file).
        '''
    
        # open the config file and assume its yml
        f_yml = open(config_file, 'r')
        data = yaml.load(f_yml.read())
        f_yml.close()       

        # map node_ipmi -> node_id
        # based on the data in maas
        node_ipmi_map = {}
        for node in self.nodes():
          node_id = node['system_id']
          node_ipmi_ip = self.get_node_ipmi_ip(node_id)
          node_ipmi_map[node_ipmi_ip] = node_id

        # sanity check the yml file - it should have
        # a nodes section
        if not data.has_key('nodes'):
            raise MAASError, "No 'nodes' section found in config file"

        # iterate over the yml data, linking the nodes
        # to our maas nodes based on the ipmi ip
        power_ips_encountered = []
        for node in data['nodes']:

            # keep track of power ips we've seen
            power_ips_encountered.append(node['power_ip'])

            # link node in yml data with a maas node
            if node.get('power_ip', None) and node_ipmi_map.has_key(node['power_ip']):

                maas_node_id = node_ipmi_map[node['power_ip']]
                maas_node_data = self.get_node(maas_node_id)

                # we have a link, update maas with yml data
                # but we must check the state of the node


                # set hostname
                # generate maas hostname from node name and internal dns name
                node_hostname = node['name'] + '.' + data['domain_name_templates']['internal']
                if node_hostname != maas_node_data['hostname']:
                    self.set_node_hostname(maas_node_id, node_hostname)

                # set boot device
                node_status = maas_node_data['substatus_name'] 
                if node_status in ['Ready']:
                    self.set_boot_disk(maas_node_id, tag=node['boot_disk_tag'])
                else:
                    logger.warn("Unable to set boot disk on node %s, status is %s" % (node['name'], node_status))

            else:
                raise MAASError, "Node %s not found in MaaS or has invalid power_ip data" % node['name']

        for maas_power_ip in node_ipmi_map.keys():
            if maas_power_ip not in power_ips_encountered:
                logger.warn("Encountered an unknown node '%s' in MaaS" % node_ipmi_map[maas_power_ip])


    def nodes(self):
    	'''Return all maas nodes'''
    	return json.loads(self.client.get(u"nodes/", "list").read())

    def get_node(self, node_id):
        return json.loads(self.client.get(u"nodes/%s/" % node_id).read())

    def get_node_ipmi_ip(self, node_id):
    	return json.loads(self.client.get(u"nodes/%s/" % node_id, "power_parameters").read())['power_address']

    def get_node_mgmt_ip(self, node_id):
    	node = json.loads(self.client.get(u"nodes/%s/" % node_id).read())
        if node.has_key('ip_addresses'):
    	   if len(node['ip_addresses']) > 0:
             return node['ip_addresses'][0]
           else:
    		 return None
    	else:
    	   return None

    def node_redeploy(self, node_id):
        '''
        Redeploy a node
        '''

        # start by releasing it irregardless of its deployed/currently active
        op = {'op': 'release'}
        self.client.post(u"nodes/%s/" % node_id, **op).read()

        # wait a bit
        time.sleep(5)

        op = {
            'op': 'acquire',
            'name': self.get_node(node_id)['hostname']
        }
        self.client.post(u"nodes/", **op).read()

        # wait a bit
        time.sleep(5)

        op = {'op': 'start'}
        self.client.post(u"nodes/%s/" % node_id, **op).read()

    def get_node_disks(self, node_id):
    	'''Return all disks for a node'''
    	return json.loads(self.client.get(u"nodes/%s/blockdevices/" % node_id).read())

    def set_node_hostname(self, node_id, hostname):
        '''
        Set the hostname for a node
        '''
        update = {'hostname': hostname}
        self.client.put(u"nodes/%s/" % node_id, **update)

    def set_boot_disk(self, node_id, tag='sata'):
    	'''
    	Set the boot disk for a node to a disk containing tag

    	MaaS will select /dev/sda by default, and this can be different devices
    	on different systems, including the RAID array which we usually store
    	instance disks on - sometimes it is ideal to target a specific disk
    	for OS installation and normally thats the onboard SATA disks which
    	receive a special tag in MaaS 1.9
    	'''

    	# iterate over the block devices, looking for our tag
    	disks = self.get_node_disks(node_id)

    	id_to_boot = None
    	for disk in disks:
    	   if tag in disk['tags']:
    	       id_to_boot = disk['id']


    	if not id_to_boot:
    	   raise MAASError, "Could not find disk with tag %s to mark bootable" % tag

    	post = {'op': 'set_boot_disk'}
       	self.client.post(u"nodes/%s/blockdevices/%s/" % (node_id, id_to_boot), **post).read()

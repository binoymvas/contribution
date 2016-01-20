'''
Methods for parsing the nodes.yml configuration file
'''

import yaml

class YMLParserError(Exception):
    pass

class YMLParser(object):

    def __init__(self, config_file_path):
	
    	self.config_file_path = config_file_path

        # open the config file and assume its yml
        f_yml = open(config_file_path, 'r')
        self.data = yaml.load(f_yml.read())
        f_yml.close() 

    def get_power_credentials(self):
        '''Return site wide default power credentials'''
        return self.data['power_credentials']['username'], self.data['power_credentials']['password'] 

    def get_node(self, name):
        nodes = self._all_nodes()
    	for node in nodes:
    		if node['name'] == name:
    			return node
    	raise YMLParserError, "Could not find node named %s" % name

    def get_nodes(self, filters={}):
    	nodes=self._all_nodes()
    	# support filtering by rack
    	if filters.has_key('rack_num'):
    		for node in nodes:
    			if int(node['rack_num']) != filters['rack_num']:
    				nodes.remove(node)

    def _all_nodes(self):
	   return self.data['nodes']



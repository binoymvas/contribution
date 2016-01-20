from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

import os
import chef
import json
import yaml
import time
import itertools

from brew.log import logger

# define period we must sleep for new data bags and roles to become available
WAIT = 5

# internal node role
INTERNAL_NODE_ROLE = 'internal-node'

#Compare node roles with exiting roles in chef server
def role_validator(data):
    result = True
    for key in data:
        if key.find('role') == 0:
            role_name = key[key.find('[')+1:-1]
            if len(chef.Search('role', 'name:%s' % role_name)) == 0:
                logger.error("Role '%s' does not exist on chef server. Skipping node" % role_name)
                result = False
                break
    return result

#creating new role or updating exitint one
def create_role(chefapi, role_data, force_update=False):
    roles_list = chef.Role.list(api=chefapi)
    created = False
    if role_data['name'] in roles_list and not force_update:
        logger.warning("Role '%s' already exist on chef server. Skipping it" % role_data['name'])
    else:
        roles_success = True
        if 'run_list' in role_data and force_update:
            if not role_validator(role_data['run_list']):
                roles_success = False
        if 'env_run_list' in role_data:
            for env in role_data['env_run_list']:
                if not role_validator(env):
                    roles_success = False
        if roles_success:
            if not role_data['name'] in roles_list:
                logger.info("Role with name '%s' not found on chef server" % role_data['name'])
                logger.info("Addind role '%s' to chef server" % role_data['name'])
                new_role = chef.Role.create(name=role_data['name'], api=chefapi)
            else:
                logger.info("Role with name '%s' found on chef server and will be updated" % role_data['name'])
                logger.info("Updating role '%s' on chef server" % role_data['name'])
                new_role = chef.Role(name=role_data['name'], api=chefapi)
            if 'description' in role_data:
                new_role.description = role_data['description']
            elif not 'description' in role_data and force_update:
                new_role.description = ""
            if 'default_attributes' in role_data:
                new_role.default_attributes = role_data['default_attributes']
            elif not 'default_attributes' in role_data and force_update:
                new_role.default_attributes = {}
            if 'override_attributes' in role_data:
                new_role.override_attributes = role_data['override_attributes']
            elif not 'override_attributes' in role_data and force_update:
                new_role.override_attributes = {}
            if 'run_list' in role_data:
                new_role.run_list = role_data['run_list']
            elif not 'run_list' in role_data and force_update:
                new_role.run_list = []
            if 'env_run_lists' in role_data:
                new_role.env_run_lists = role_data['env_run_lists']
            elif not 'env_run_lists' in role_data and force_update:
                new_role.env_run_lists = {}
            new_role.save()
            created = True
    return created

#Creating new data bag or updating exiting one
def create_data_bag(chefapi, data_bag_data, force_update=False):
    #Checking, chef server has this data bag and will we update it if necessary
    data_bag_list = chef.DataBag.list(api=chefapi)
    if data_bag_data['id'] in data_bag_list and not force_update:
        logger.warning("Found data bag with name '%s'. Skipping it" % data_bag_data['id'])
    else:
        if not data_bag_data['id'] in data_bag_list:
            logger.info("Data bag with name '%s' not found on chef server" % data_bag_data['id'])
            logger.info("Adding data bag '%s' to chef server" % data_bag_data['id'])
            new_data_bag = chef.DataBag.create(name=data_bag_data['id'], api=chefapi)
            bag = chef.DataBagItem.create(new_data_bag,data_bag_data['id'], api=chefapi)
        else:
            logger.info("Data bag with name '%s' found on chef server and will be updated" % data_bag_data['id'])
            logger.info("Updating data bag '%s' on chef server" % data_bag_data['id'])
            new_data_bag = chef.DataBag(name=data_bag_data['id'], api=chefapi)
            bag = chef.DataBagItem(new_data_bag,data_bag_data['id'], api=chefapi)
            bag.clear()
        bag.update(data_bag_data)
        bag.save()

#Creating new node or updating existing one
def create_node(chefapi, node_data, internal_dns_suffix, force_update=False):
    nodes_list = chef.Node.list(api=chefapi)
    #Checking, chef server has this node and will we update it if necessary

    node_name = node_data['name'] + '.' + internal_dns_suffix

    # calculate actual node name
    if node_name in nodes_list and not force_update:
        logger.warning("Found node with name '%s'. Skipping it" % node_name)
    else:
        if role_validator(node_data['chef']['run_list']):
            if not node_name in nodes_list:
                logger.info("Node with name '%s' not found on chef server" % node_name)
                logger.info("Addind node '%s' to chef server" % node_name)
                new_node = chef.Node.create(name=node_name, api=chefapi)
            else:
                logger.info("Node with name '%s' found on chef server and will be updated" % node_name)
                logger.info("Updating node '%s' on chef server" % node_name)
                new_node = chef.Node(name=node_name, api=chefapi)
            if 'chef_environment' in node_data['chef']:
                new_node.chef_environment = node_data['chef']['chef_environment']
            elif not 'chef_environment' in node_data['chef'] and force_update:
                new_node.chef_environment = "_default" 
            if 'default' in node_data['chef']:
                new_node.default = node_data['chef']['default']
            elif not 'default' in node_data['chef'] and force_update:
                new_node.default = {}
            if 'override' in node_data['chef']:
                new_node.override = node_data['chef']['override']
            elif not 'override' in node_data['chef'] and force_update:
                new_node.override = {}
            if 'normal' in node_data['chef']:
                new_node.normal = node_data['chef']['normal']
            elif not 'normal' in node_data['chef'] and force_update:
                new_node.normal = {}
            new_node.normal['reboot-handler']['post_boot_runlist'] = node_data['chef']['run_list']
            new_node.save()

def process_nodes(chefapi, data, config_file, internal_dns_suffix, force_update=False):
    #Searching 'nodes' section
    if not 'nodes' in data:
       logger.info("'nodes' section is absent in input file '%s', skipping it" % config_file)
       return

    else:

        for node in data['nodes']:
            if not 'chef' in node:
                logger.info("'chef' section is absent in input file '%s', skipping it" % config_file)
                continue

            else:

                #Searching for nodes and adding it to server
                if 'name' in node:
                    logger.info("Found information about NODE '%s', processing it" % node['name'])
                    create_node(chefapi, node, internal_dns_suffix, force_update)
                else:
                    logger.warn("Found malformed node entry, missing name attribute in '%s'" % config_file)
                    continue

def process_virtual(chefapi, data, config_file, internal_dns_suffix, force_update=False):

    assign_dict = {}

    # find all internal nodes
    internal_nodes = chef.Search('node', 'role:%s' % INTERNAL_NODE_ROLE, api=chefapi)

    nodes = itertools.cycle(list(internal_nodes))

    # walk all virtual machines, slotting them to internal_nodes
    for machine in data['virtual']:

        node_to_assign = nodes.next()
        node_name = node_to_assign['name']
        logger.info("Assigning virtual machine '%s' to node %s'" % (machine['name'], node_name))

        if not assign_dict.has_key(node_name):
            assign_dict[node_name] = []

        assign_dict[node_name].append(machine)

        # create chef entry for the virtual machine itself
        virtual_name = machine['name'] + '.' + internal_dns_suffix
        chef_node_obj = chef.Node(name=virtual_name, api=chefapi)
        chef_node_obj.run_list = machine['chef']['run_list']
        chef_node_obj.save()

    for node in assign_dict:

        attrib_dict = {

        'internal-node': {
            'virtual_machines': assign_dict[node]
            }
        }

        chef_node_obj = chef.Node(name=node, api=chefapi)
        chef_node_obj.normal.update(attrib_dict)
        chef_node_obj.save()


def process_chef_environment(chefapi, data, config_file, force_update=False):

    sleep_needed = False

    if not 'chef_environment' in data:
        logger.info("'chef_environment section is action in input file '%s', skipping role/databag creation" % config_file)
        return

    else:
        if 'roles' in data['chef_environment']:
            for role in data['chef_environment']['roles']:
                logger.info("Found information about ROLE '%s', processing it" % role['name'])
                if create_role(chefapi, role, force_update):
                    sleep_needed = True
        if 'data_bags' in data['chef_environment']:
           for data_bag in data['chef_environment']['data_bags']:
               logger.info("Found information about DATA BAG '%s', processing it" % data_bag['id'])
               create_data_bag(chefapi, data_bag, force_update) 

    return sleep_needed



def process_yaml(config_file, chef_config_file, force_update=False):
    '''
    Main method called to compare exiting switches with node file in yaml format
    '''

    chefapi = chef.api.ChefAPI.from_config_file(chef_config_file)

    # immediately validate chef connectivity
    try:
        chef.Node.list(api=chefapi)
    except:
        logger.error("There is likely a communication error with the chef server configured in '%s.'  Try running 'knife node list -c <config file>'" % (chef_config_file))
        raise

    f_yml = open(config_file, 'r')
    data = yaml.load(f_yml.read())
    f_yml.close()

    internal_dns_suffix = data['domain_name_templates']['internal']

    logger.info("Processing chef environment records (roles/data bags)")
    if process_chef_environment(chefapi, data, config_file, force_update=force_update):
        logger.info("Roles were created or updated, sleeping %s seconds before processing nodes" % WAIT)
        time.sleep(WAIT)

    logger.info("Processing node records")
    process_nodes(chefapi, data, config_file, internal_dns_suffix, force_update=force_update)

    logger.info("Processing any virtual machine records")
    process_virtual(chefapi, data, config_file, internal_dns_suffix, force_update=force_update)
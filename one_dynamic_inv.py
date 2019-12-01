#!/usr/bin/env python



"""
one Server external inventory script.
========================================
Returns hosts and hostgroups in format of ansible inventory from opennebula server.
Configuration is read from `one.ini`.

"""

import os
import sys
import argparse
from ansible.module_utils.six.moves import configparser
import pyone
import ssl
import json


class OneInventory(object):

    def read_settings(self):
        config = configparser.SafeConfigParser()
        conf_path = './one.ini'
        if not os.path.exists(conf_path):
            conf_path = os.path.dirname(os.path.realpath(__file__)) + '/one.ini'
        if os.path.exists(conf_path):
            config.read(conf_path)
        # server configuration
        if config.has_option('one', 'server'):
            self.one_server = config.get('one', 'server')

        # login information
        if config.has_option('one', 'username'):
            self.one_username = config.get('one', 'username')
        if config.has_option('one', 'password'):
            self.one_password = config.get('one', 'password')
        # ssl valid-certs
        if config.has_option('one', 'validate_certs'):
            if config.get('one', 'validate_certs') in ['false', 'False', False]:
                self.validate_certs = False
    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action='store_true')
        self.options = parser.parse_args()

    def hoststub(self):
        return {
            'hosts': []
        }

    def get_list(self, one):

	    if self.one_server and self.one_username:
            try:
                one = pyone.OneServer(self.one_server, session=self.one_username+":"+self.one_password)
            except (Exception, SystemExit) as e:
                print("Error: Could not login to One server. Check your one.ini.", file=sys.stderr)
                sys.exit(1)


        hosts_data = one.vmpool.info(-1,-1,-1,3)
        data2 = {'_meta': {'hostvars': {}}}
        data2[self.defaultgroup] = self.hoststub()
        for host in range(len(hosts_data.VM)):
            hostname = hosts_data.VM[host].get_NAME()
            hostvars = dict()
            data2[hostname[0:4]] =  self.hoststub()
  	    for i in range(len(hosts_data.VM)):
		hostname2 = hosts_data.VM[i].get_NAME()
		if hostname[0:4] in hostname2:       
	            data2[hostname[0:4]]['hosts'].append(hostname2)
            if isinstance(hosts_data.VM[host].TEMPLATE['NIC'], list):
               hostvars['ansible_ssh_host'] = hosts_data.VM[host].TEMPLATE['NIC'][0]['IP']
               data2['_meta']['hostvars'][hostname] = hostvars

        return data2

    def __init__(self):

        self.defaultgroup = 'group_all'
        self.one_server = None
        self.one_username = None
        self.one_password = None
        self.validate_certs = True
        self.read_host_inventory = False
        self.use_host_interface = True
        self.meta = {}
        self.read_settings()
        self.read_cli()

        if self.one_server and self.one_username:
            try:
                one = pyone.OneServer(self.one_server, session=self.one_username+":"+self.one_password)
            except (Exception, SystemExit) as e:
                print("Error: Could not login to One server. Check your one.ini.", file=sys.stderr)
                sys.exit(1)

            
	    if self.options.list:
	        vm = self.get_list(one)
 	        print(json.dumps(vm, indent=2))

		
            else:
                print("usage: --list>", file=sys.stderr)
                sys.exit(1)

        else:
            print("Error: credentials are required.", file=sys.stderr)
            sys.exit(1)


OneInventory()

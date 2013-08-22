#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import sys
import json
import platform
import socket

import common
from common import SOSError
from network import Network
from host import Host
from viprinfo import _get_vipr_info as VIPRINFO

from nova.virt.libvirt import utils as libvirt_utils

class Openstack(object):
    '''
    The class definition for operations related to 'Openstack'. 
    '''

    #Commonly used URIs for the 'Openstack' module
    URI_HOST_SEARCH = '/compute/hosts/search?name={0}'
    URI_HOST_BULK = '/compute/hosts/bulk'
    URI_NETWORK_BULK = '/vdc/networks/bulk'
    URI_NETWORK_PORTS = '/vdc/networks/{0}/storage-ports'    
    URI_STORAGEPORT_ALL = '/vdc/storage-ports'
    URI_STORAGEPORT_BULK = '/vdc/storage-ports/bulk'

    VIPR_CONFIG_FILE = '/etc/cinder/cinder_emc_vipr_config.xml'

        
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        self.__host = Host(self.__ipAddr, self.__port)
        self.__network = Network(self.__ipAddr, self.__port)
        
    def get_hostname(self, hostname = None):
        if (not hostname):
            return socket.getfqdn()
        else:
            return hostname
    
    def add_host(self, host_param, connector, vipr_param):
        # Find or create host.
        host = self.create_host(host_param['hostname'])
        self.log_info('Created/Found host ' + host['name'])
                
        # Find or create initiator.
        initiator = self.create_initiator(host, connector)    
        self.log_info('Added initiator ' + initiator['initiator_port'] + ' to host ' + host['name'])
         
        # Find network
        network = self.find_iscsi_network(vipr_param['varray'], vipr_param['network'])
        self.log_info('Found network ' + network['name'])
 
        # add initiator to network
        self.add_initiator_to_network(host, initiator, network, vipr_param['varray'])
        self.log_info('Added initiator ' + initiator['initiator_port'] + ' to network ' + network['name'])
             
    def create_host(self, hostname, ostype='linux'):
        # find host
        host = self.find_host(hostname)
        if (not host):
            if (not ostype) :
                ostype = "linux"
            
                # host not found, create a new one.
            task_rep = self.__host.host_create(hostname, None, None, hostname, ostype, None)
            host = common.show_by_href(self.__ipAddr, self.__port, task_rep['resource']) 
        return host                
    
    '''
        Find host by name of host object in ViPR, normally the hostname of the host.
        Parameters:
            name: name of the host
        Returns:
            host details in JSON
    '''
    def find_host(self, hostname):
        shortname = hostname[:hostname.find(".")]
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_HOST_SEARCH.format(hostname), 
                                             None)
        o = common.json_decode(s);
        ids = []
        for host in o['resource'] :
            ids.append(host['id'])
    
        body = json.dumps({'id' : ids})    
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             self.URI_HOST_BULK, 
                                             body)
        o = common.json_decode(s)
        for host in o['host']:
            if (host['inactive']):
                continue
            if (hostname in host['host_name'] or host['host_name'] in hostname ):     
                return host
               
    def get_localhost_initiator(self, protocol='iSCSI'):
        if (protocol == 'iSCSI'):
            wwpn = libvirt_utils.get_iscsi_initiator()
            initiator = {'wwpn' : wwpn}
            return initiator
    
    def find_initiator(self, hosturi, wwpn):
        initiators = self.__host.host_query_initiators(hosturi)
        for initiator in initiators:
            if (initiator['name'] == wwpn):
                return initiator
        return None    
    
    def create_initiator(self, host, connector):
        initiator = self.find_initiator(host['id'], connector['wwpn'])
        if (not initiator):
            # Add initiator. Support only iscsi for now.
            if (not connector) :
                protocol = 'iSCSI'
                connector = self.get_localhost_initiator(protocol)
            initiator = self.__host.host_add_initiator(host['name'], connector['wwpn'])
        return common.show_by_href(self.__ipAddr, self.__port, initiator)
    
    '''
        Find network for a given network name. If network name is not specified 
    '''
    def find_iscsi_network(self, varray, network_name):
        if (network_name):
            return self.__network.search(network_name)      
        for port in self.get_varray_iscsi_storageports(varray):
            try:
                network = port['network']
                # Return the first one found. 
                # TODO: ping storage port IP to determine the network to choose.
                return common.show_by_href(self.__ipAddr, self.__port, network)
            except KeyError: 
                continue
 
    
    def get_ip_networks(self, varray):
        networks = self.__network.list_networks(varray)
        ip_networks = []
        resources = self.get_bulk_details(networks, self.URI_NETWORK_BULK)                         
        for x in resources['network']:
            if (x['transport_type'] == 'IP'):
                ip_networks.append(x)
                    
        return ip_networks
        
    def get_bulk_details(self, resources, bulkuri):
        ids = []
        for each in resources :
            ids.append(each['id'])
    
        body = json.dumps({'id' : ids})    
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             bulkuri, 
                                             body)
        return common.json_decode(s)          

    '''
        Attach host initiators to a network
        Parameters:
            name: name of the host
            network: name of the network to be attached
        Return:
            network details in JSON
    '''
    def add_initiator_to_network(self, host, initiator, network, varray):
        if (network['transport_type'] == 'IP' and initiator['protocol'] == 'iSCSI'):
            return self.__network.add_endpoint(varray, network['name'], initiator['initiator_port'])
    
    def get_varray_iscsi_storageports(self, varray):
        iscsi_ports = []
        for port in self.get_varray_storageports(varray):
            if (port['transport_type'] != 'IP'):
                continue
            if ('iqn' not in port['port_network_id']):
                continue
            if ('Not Available' in port['ip_address'] ):
                continue
            iscsi_ports.append(port)
        return iscsi_ports
         
    """
        Get all storage ports
        Returns:
            Storage ports in JSON
    """
    def get_varray_storageports(self, varray):
        #varray_obj = VirtualArray(self.__ipAddr,self.__port)
        networks = self.__network.list_networks(varray)
        ids = []
        for net in networks:
            net_id = net['id']
            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                                 "GET",
                                                 self.URI_NETWORK_PORTS.format(net_id) , None)
            o = common.json_decode(s)
            for port in o['storage_port']:
                ids.append(port['id'])
                
        body = json.dumps({'id' : ids})
                
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             self.URI_STORAGEPORT_BULK,
                                             body)
        o = common.json_decode(s)
        return o['storage_port']
    
    def log_info(self, message):
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(timestamp + ': ' + message + '\n')
    
# list command parser
def add_host_parser(subcommand_parsers, common_parser):
    add_host_parser = subcommand_parsers.add_parser('add_host',
                                description='ViPR Add Openstack Host CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Add Openstack compute node to ViPR')
    add_host_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             help='List hosts with details',
                             action='store_true')
    add_host_parser.add_argument('-name', '-host_name',
                                metavar='<hostname>',
                                dest='hostname',
                                help='The hostname of Openstack compute node')
    add_host_parser.add_argument('-ostype', '-os',
                                metavar='<ostype>',
                                dest='ostype',
                                help='The OS type of the host: linux, windows, esx, other')
    add_host_parser.add_argument('-initiatorPort', '-wwpn',
                                metavar='<wwpn>',
                                dest='wwpn',
                                help='The initiator port')
    add_host_parser.add_argument('-network', '-nw',
                                metavar='<network>',
                                dest='network',
                                help='The ViPR network name to add the host initiators to')
    add_host_parser.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='The ViPR virtual array name')
    add_host_parser.set_defaults(func=add_host)


def add_host(args):
    obj = Openstack(args.ip, args.port)
    if (not args.hostname) :
        hostname = obj.get_hostname()
        ostype = platform.system()
    else:
        hostname = args.hostname
        ostype = args.ostype
        
    if (not args.wwpn):
        connector = obj.get_localhost_initiator()
    else:
        connector = {'wwpn' : args.wwpn}
   
    host_param = dict()
    host_param['hostname'] = hostname
    host_param['ostype'] = ostype

    vipr_param = dict()
    if (not args.varray):
        viprinfo = VIPRINFO(obj.VIPR_CONFIG_FILE)
        varray = viprinfo['varray']
    else:
        varray = args.varray
    vipr_param['varray'] = varray
    vipr_param['network'] = args.network
    
    try:
        host = obj.add_host(host_param, connector, vipr_param)
        return host          
    except SOSError as e:
        raise e
    

# Host Main parser routine
def openstack_parser(parent_subparser, common_parser):
    # main host parser

    parser = parent_subparser.add_parser('openstack',
                                description='ViPR Openstack CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations related to openstack')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

  
    # list command parser
    add_host_parser(subcommand_parsers, common_parser)

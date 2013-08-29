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
import logging

from nova.virt.libvirt import utils as libvirt_utils
from nova import utils

import common
from common import SOSError
from network import Network
from host import Host
from hostinitiators import HostInitiator
import viprinfo as _viprinfo

'''
LOG = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s : %(message)s')
LOG.addHandler(ch)
'''

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

    VIPR_CONFIG_FILE = '/etc/cinder/cinder.conf'

        
    def __init__(self, ipAddr, port, verbose):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        self._host = Host(self.__ipAddr, self.__port)
        self._hostinitiator = HostInitiator(self.__ipAddr, self.__port)
        self._network = Network(self.__ipAddr, self.__port)
        self._execute = utils.execute
        self.set_logging(verbose)
            
    def set_logging(self, verbose):
        self._logger = logging.getLogger(__name__)
        if (verbose):
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger.setLevel(logging.INFO)
        logging.basicConfig(format='%(asctime)s:%(levelname)s: %(message)s')
    def get_logger(self):
        return self._logger    
                
    def get_hostname(self, hostname = None):
        if (not hostname):
            return socket.getfqdn()
        else:
            return hostname
    
    def add_host(self, host_param, connector, vipr_param):
        
        varray = vipr_param['varray']
        
        # Find or create host.
        host = self.create_host(host_param['hostname'], vipr_param['tenant'], vipr_param['project'])
        self._logger.info('Created/found host %s', host['name'])
        self._logger.debug('Details of host %s: %s', host_param['hostname'], host)     
                
        # Find or create initiator.
        initiator = self.create_initiator(host, connector)    
        self._logger.info('Added initiator %s to host %s', initiator['initiator_port'], host['name'])
        self._logger.debug('Details of initiator %s', initiator)
         
        # Find network
        network = self.find_iscsi_network(vipr_param['varray'], vipr_param['network']) 
        if (network):
            self._logger.info('Found network %s in virtual array %s', network['name'], varray)
        else:
            self._logger('Cannot find a network in virtual array %s to place the initiator', varray)
            exit(1)
            
        # add initiator to network
        if (initiator['initiator_port'] not in network['endpoints']):
            self.add_initiator_to_network(host, initiator, network, vipr_param['varray'])
        self._logger.info('Added initiator %s to network %s', initiator['initiator_port'], network['name'])
        self._logger.debug('Network details %s: ', network)
             
    def create_host(self, hostname, tenant, project, ostype='Linux'):
        # find host
        host = self.find_host(hostname)
        if (not host):
            if (not ostype) :
                ostype = "Linux"
            
                # host not found, create a new one.
            task_rep = self._host.create(hostname, ostype, hostname, tenant, project, None, None, None, None, None, None, None, None)
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
                                             self.URI_HOST_SEARCH.format(shortname), 
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
    
    def find_initiator(self, host, wwpn):
        initiators = self._host.list_initiators(host)
        for initiator in initiators:
            if (initiator['name'] == wwpn):
                return initiator
        return None    
    
    def create_initiator(self, host, connector):
        initiator = self.find_initiator(host['name'], connector['wwpn'])
        if (not initiator): 
            initiator = self._hostinitiator.create(host['name'], 'iSCSI', None, connector['wwpn'])
        return common.show_by_href(self.__ipAddr, self.__port, initiator)
    
    '''
        Find network for a given network name. If network name is not specified 
    '''
    def find_iscsi_network(self, varray, network_name):
        if (network_name):
            try:
                return self._network.network_query(network_name, varray)
            except SOSError:
                # TODO: re-raise the exception with correct name. To be removed
                raise SOSError(SOSError.NOT_FOUND_ERR, "Network {0} not found".format(network_name))
            
        storage_ports = self.get_varray_iscsi_storageports(varray)
        for port in storage_ports:
            port_info = dict()
            port_info['native_guid'] = port['native_guid']
            port_info['port_name'] = port['port_name']
            try:
                ip_address = port['ip_address'] 
                port_info['ip_address'] = ip_address             
                if (self.is_ip_pingable(ip_address)):
                    network = port['network']
                    network_detail = common.show_by_href(self.__ipAddr, self.__port, network)
                    port_info['network'] = network_detail['name']
                    self._logger.debug('Select storage port %s: ', port_info)
                    return network_detail
                else:    
                    self._logger.debug('Skip storage port %s: ', port_info)
 
            except KeyError:
                self._logger.debug('Skip storage port %s: ', port_info)
                continue
 
    def is_ip_pingable(self, ip_address):
        self._logger.debug('ping ip address %s ', ip_address)
        try:
            (out, err) = self._execute('ping', '-c', '2', ip_address)
            self._logger.debug(out)
            return True
        except Exception as ex:
            return False
    
    def get_ip_networks(self, varray):
        networks = self._network.list_networks(varray)
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
            return self._network.add_endpoint(varray, network['name'], initiator['initiator_port'])
    
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
        networks = self._network.list_networks(varray)
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
                                 help='Print details for debugging',
                                 action='store_true')
    add_host_parser.add_argument('-name', '-host_name',
                                 metavar='<host_name>',
                                 dest='host_name',
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
    obj = Openstack(args.ip, args.port, args.verbose)
    is_localhost = False
    if (not args.host_name) :
        hostname = obj.get_hostname()
        ostype = platform.system()
        is_localhost = True
    else:
        hostname = args.host_name
        ostype = args.ostype
        if (hostname in obj.get_hostname()):
            is_localhost = True
            
    if (not args.wwpn and is_localhost):
        # support only iSCSI
        connector = obj.get_localhost_initiator()
    else:
        connector = {'wwpn' : args.wwpn}
           
    if(args.host_name and not args.wwpn and not is_localhost):
        raise SOSError(SOSError.CMD_LINE_ERR,
                       "ERROR: argument -wwpn/-initiatorPort is required for %s" %(hostname))
    
    host_param = dict()
    host_param['hostname'] = hostname
    host_param['ostype'] = ostype
    host_param['is_localhost'] = is_localhost
    if (args.verbose):
        obj.get_logger().debug('Host parameters: %s', host_param)
    vipr_param = dict()
    viprinfo = _viprinfo._get_vipr_info(obj.VIPR_CONFIG_FILE)
    vipr_param['varray'] = args.varray if args.varray else viprinfo['varray']
    vipr_param['network'] = args.network
    vipr_param['port'] = args.port if args.port else viprinfo['port']
    vipr_param['hostname'] = args.ip if args.ip else viprinfo['FQDN'] 
    vipr_param['tenant'] = viprinfo['tenant']
    vipr_param['project'] = viprinfo['project']  

    if (args.verbose):
        obj.get_logger().debug('ViPR parameters: %s', vipr_param)
        
    try:
        host = obj.add_host(host_param, connector, vipr_param)
        return host          
    except SOSError as e:
        obj.get_logger().error(e.err_text)
        sys.exit(e.err_code)
    
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

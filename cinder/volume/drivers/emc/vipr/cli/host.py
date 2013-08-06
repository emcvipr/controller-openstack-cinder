#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import common
from common import SOSError
import json
import platform
import socket
from tenant import Tenant
from project import Project
from cluster import Cluster


class Host(object):
    '''
    The class definition for operations on 'Host'. 
    '''

    #Commonly used URIs for the 'Host' module
    URI_TENANT_HOSTS = '/tenants/{0}/hosts'
    URI_HOST = '/compute/hosts/{0}'
    URI_HOST_INITIATORS = URI_HOST + '/initiators'
    URI_HOST_DEACTIVATE = URI_HOST + '/deactivate'
    
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def host_create(self, name=None, host_name=None, ostype='Linux', cluster_name=None, project_name=None, tenant_name=None):
        '''
        Makes REST API call to create a host under a tenant
        Parameters:
            name: name of host
            tenant_name: name of the tenant under which the host 
                         is to be created
        Returns:
            Created host details in JSON response payload
        '''

        if (not name):
            if (host_name):
                name = host_name
            else:
                name = socket.gethostname()

        if (not host_name):
            # fill in the localhost info if host_name isn't provided
            host_name = socket.getfqdn()
            # override the ostype
            ostype = platform.system()

        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e

        host_already_exists = True

        try:
            if(not tenant_name):
                tenant_name = ""
            self.host_query(tenant_name + "/" + name)
        except SOSError as e:
            if (e.err_code == SOSError.NOT_FOUND_ERR):
                host_already_exists = False
            else:
                raise e

        if (host_already_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Host with name: " + name + " already exists")

        createParams = dict()
        createParams['name'] = name
        createParams['host_name'] = host_name
        createParams['type'] = ostype
        if (cluster_name):
            cluster_obj = Cluster(self.__ipAddr, self.__port)
            try:
                cluster_uri = cluster_obj.cluster_query(cluster_name)
            except SOSError as e:
                raise e
            createParams['cluster'] = cluster_uri
        if (project_name):
            project_obj = Project(self.__ipAddr, self.__port)
            try:
                project_uri = project_obj.project_query(project_name)
            except SOSError as e:
                raise e
            createParams['project'] = project_uri
        body = json.dumps(createParams)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Host.URI_TENANT_HOSTS.format(tenant_uri), body)
        o = common.json_decode(s)
        return o
    

    def host_list(self, tenant_name):
        '''
        Makes REST API call and retrieves hosts based on tenant UUID
        Parameters: None
        Returns:
            List of host UUIDs in JSON response payload 
        '''
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_TENANT_HOSTS.format(tenant_uri), None)
        o = common.json_decode(s)
        
        if('host' in o):        
            return common.get_list(o, 'host')
        return []
        

    def host_show_by_uri(self, uri, xml=False):
        '''
        Makes REST API call and retrieves host derails based on UUID
        Parameters:
            uri: UUID of the host
        Returns:
            Host details in JSON response payload
        '''
        if(xml):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Host.URI_HOST.format(uri), None, None, xml)
            return s
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Host.URI_HOST.format(uri), None)
        o = common.json_decode(s)
        inactive = common.get_node_value(o, 'inactive')
        if(inactive == True):
            return None
        
        return o
        

    def host_show(self, name, xml=False):
        '''
        Retrieves host details based on host name
        Parameters:
            name: name of the host
        Returns:
            Host details in JSON response payload
        '''
        host_uri = self.host_query(name)
        host_detail = self.host_show_by_uri(host_uri, xml)
        return host_detail


    def host_query(self, name):
        '''
        Retrieves UUID of host based on its name
        Parameters:
            name: name of host
        Returns: UUID of host
        Throws:
            SOSError - when host name is not found 
        '''
        if (common.is_uri(name)):
            return name
        (tenant_name, host_name) = common.get_parent_child_from_xpath(name)
        
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
            hosts = self.host_list(tenant_uri)
            if(hosts and len(hosts) > 0):
                for host in hosts:
                    if (host):
                        host_detail = self.host_show_by_uri(host['id'])
                        if(host_detail and host_detail['name'] == host_name):
                            return host_detail['id']
            raise SOSError(SOSError.NOT_FOUND_ERR, 'Host: ' + host_name + ' not found')
        except SOSError as e:
            raise e
        

    def host_delete_by_uri(self, uri):
        '''
        Deletes a host based on host UUID
        Parameters:
            uri: UUID of host
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST", Host.URI_HOST_DEACTIVATE.format(uri), None)
        return


    def host_delete(self, name):
        '''
        Deletes a host based on host name
        Parameters:
            name: name of host
        '''
        host_uri = self.host_query(name)
        return self.host_delete_by_uri(host_uri)


    def host_add_initiator(self, name, initiatorPort, protocol='iSCSI', initiatorNode=None):
        #construct the body 
        
        initiatorParams = dict()
        if (not protocol):
            protocol = 'iSCSI'
        initiatorParams['protocol'] = protocol
        if (initiatorNode):
            initiatorParams['initiator_node'] = initiatorNode  
        initiatorParams['initiator_port'] = initiatorPort 

        body = json.dumps(initiatorParams)
        uri = self.host_query(name)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                        "POST", self.URI_HOST_INITIATORS.format(uri), body)
        o = common.json_decode(s)
        return o


def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Host Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a host')
    create_parser.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of Host (default: localhost name)')
    create_parser.add_argument('-noh', '-nameofhost',
                                metavar='<host_name>',
                                dest='host_name',
                                help='Hostname (default: localhost fqdn)')
    create_parser.add_argument('-t', '-ostype',
                                metavar='<ostype>',
                                dest='ostype',
                                help='The Type of the Host (default: Linux)')
    create_parser.add_argument('-cl', '-cluster',
                                metavar='<cluster>',
                                dest='clustername',
                                help='Name of Cluster')
    create_parser.add_argument('-pr', '-project',
                                metavar='<project>',
                                dest='projectname',
                                help='Name of Project')
    create_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenantname',
                                help='Name of Tenant (default: Provider Tenant)')
    create_parser.set_defaults(func=host_create)


def host_create(args):
    obj = Host(args.ip, args.port)
    try:
        obj.host_create(args.name, args.host_name, args.ostype, args.clustername, args.projectname, args.tenantname)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code,
                           "Host create failed: " + e.err_text)
        else:
            raise e


def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR Host Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a host')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of Host',
                                required=True)
    delete_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                help='Name of tenant')
    delete_parser.set_defaults(func=host_delete)

def host_delete(args):
    obj = Host(args.ip, args.port)
    try:
        if(not args.tenant):
            args.tenant=""
        obj.host_delete(args.tenant + "/" + args.name)

    except SOSError as e:
        if (e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Host delete failed: " + e.err_text)
        else:
            raise e


# show command parser
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Host Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show host details')
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of host',
                                required=True)
    show_parser.add_argument('-tn', '-tenant',
                                metavar='tenant',
                                dest='tenant',
                                help='Name of tenant')
    show_parser.set_defaults(func=host_show)


def host_show(args):
    obj = Host(args.ip, args.port)
    try:
        if(not args.tenant):
            args.tenant=""
        res = obj.host_show(args.tenant + "/" + args.name, args.xml)
        if(res):
            if (args.xml == True):
                return common.format_xml(res)
            return common.format_json_object(res)
    except SOSError as e:
        raise e
        

# list command parser
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='ViPR Host List CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists hosts under a tenant')
    list_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             help='List hosts with details',
                             action='store_true')
    list_parser.add_argument('-l', '-long',
                             dest='largetable',
                             help='List hosts in table format',
                             action='store_true')
    #mandatory_args = list_parser.add_argument_group('mandatory arguments')
    list_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenantname',
                                help='Name of tenant')
    list_parser.set_defaults(func=host_list)


def host_list(args):
    obj = Host(args.ip, args.port)
    try:
        from common import TableGenerator
        hosts = obj.host_list(args.tenantname)
        records = []
        for host in hosts:
            proj_detail = obj.host_show_by_uri(host['id'])
            if(proj_detail):
                if("tenant" in proj_detail and "name" in proj_detail["tenant"]):
                    del proj_detail["tenant"]["name"]
                records.append(proj_detail)
                
        if(len(records) > 0):
            if(args.verbose == True):
                return common.format_json_object(records)
                
            elif(args.largetable == True):
                TableGenerator(records, ['name', 'owner']).printTable()
            else:
                TableGenerator(records, ['name']).printTable()
                    
        else:
            return
            
    except SOSError as e:
        raise e
    

def add_initiator_parser(subcommand_parsers, common_parser):
    # add initiator command parser
    add_initiator_parser = subcommand_parsers.add_parser('add_initiator',
                description='ViPR Host Add Initiator cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add an initiator to host')
    mandatory_args = add_initiator_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<name>',
                dest='name',
                help='name of Host',
                required=True)  
    mandatory_args.add_argument('-initiatorPort', '-inp',
                metavar='<InitiatorPort>',
                dest='initiatorPort',
                help='Initiator Port',
                required=True)
    add_initiator_parser.add_argument('-protocol', '-pl',
                metavar='<Protocol>',
                dest='protocol',
                help='Protocol (default: iSCSI)')
    add_initiator_parser.add_argument('-initiatorNode', '-inn',
                metavar='<InitiatorNode>',
                dest='initiatorNode',
                help='Initiator Node')
    add_initiator_parser.set_defaults(func=host_add_initiator)

def host_add_initiator(args):
    try:
        obj = Host(args.ip, args.port)
        if(args.protocol == "FC" and args.initiatorNode == None):
            return SOSError(SOSError.SOS_FAILURE_ERR, "argument -initiatorNode/-inn is required for " + args.protocol + " protocol")

        res = obj.host_add_initiator(args.name,
                                     args.initiatorPort,
                                     args.protocol, 
                                     args.initiatorNode)
    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR, "Add initiator " + str(args.initiatorPort) + ": failed:\n" + e.err_text)
        
# Host Main parser routine
def host_parser(parent_subparser, common_parser):
    # main host parser

    parser = parent_subparser.add_parser('host',
                                description='ViPR Host CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Host')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # add initiators to host command parser
    add_initiator_parser(subcommand_parsers, common_parser)


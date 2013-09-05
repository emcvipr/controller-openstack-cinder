#!/usr/bin/python
# Copyright (c)2012 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import json
import common
import sys
import getpass


from common import SOSError
class VCenter(object):
    '''
    The class definition for operations on 'VCenter'. 
    '''

    #Commonly used URIs for the 'vcenters' module
    URI_SERVICES_BASE               = ''
    URI_TENANTS                     = URI_SERVICES_BASE + '/tenants/{0}'
    URI_TENANT                      = URI_SERVICES_BASE + '/tenant'
    URI_TENANTS_VCENTERS            = URI_TENANTS      + '/vcenters'
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'
    URI_VCENTERS                    = URI_SERVICES_BASE   + '/compute/vcenters'
    URI_VCENTER                     = URI_SERVICES_BASE   + '/compute/vcenters/{0}'
    URI_VCENTER_DATACENTERS         = URI_VCENTER         + '/vcenter-data-centers'
    URI_DATACENTERS                 = URI_SERVICES_BASE   + '/compute/vcenter-data-centers'
    URI_DATACENTER                  = URI_SERVICES_BASE   + '/compute/vcenter-data-centers/{0}'
    URI_VCENTER_HOSTS		    = URI_VCENTER + '/hosts'
    URI_VCENTER_CLUSTERS		    = URI_VCENTER + '/clusters'
    URI_VCENTER_DATACENTERS		    = URI_VCENTER + '/vcenter-data-centers'



    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
         
       
        
    def vcenter_query(self, name, tenantname):
        '''
        Returns the UID of the vcenter specified by the name
        '''
        if (common.is_uri(name)):
            return name

	from tenant import Tenant
	obj = Tenant(self.__ipAddr, self.__port)

        tenanturi = obj.tenant_query(tenantname)

	vcenters = self.vcenter_list(tenanturi)
        for vcenter in vcenters:
            if (vcenter['name'] == name):
                return vcenter['id']
	
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "vcenter " + name + ": not found")

	
    def vcenter_list(self, tenant):
        '''
        Returns all the vcenters associated with a tenant
        Parameters:           
        Returns:
                JSON payload of vcenter list
        '''
	from tenant import Tenant
        obj = Tenant(self.__ipAddr, self.__port)

	uri = obj.tenant_query(tenant)
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VCenter.URI_TENANTS_VCENTERS.format(uri), None)

        o = common.json_decode(s)
	
	return o['vcenter']



    def vcenter_get_details_list(self, detailslst):
        rsltlst= []
        for iter in detailslst:
	    tmp = self.vcenter_show(iter['id'], None)
	    if(tmp):
                rsltlst.append(tmp)

        return rsltlst



    def vcenter_get_datacenters(self, label,tenantname, xml=False):
        '''
        Makes a REST API call to retrieve details of a vcenter  based on its UUID
        '''
	
        uri = self.vcenter_query(label, tenantname)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VCenter.URI_VCENTER_DATACENTERS.format(uri),
                                             None, None, xml)

	o = common.json_decode(s)

	from vcenterdatacenter import VcenterDatacenter
	obj = VcenterDatacenter(self.__ipAddr, self.__port)

	dtlslst = obj.vcenterdatacenter_get_details(o['vcenter_data_center'])

        return dtlslst


    def vcenter_get_clusters(self, label, tenantname, xml=False):
        '''
        Makes a REST API call to retrieve details of all clusters associated with a vcenter
        '''
	
        uri = self.vcenter_query(label, tenantname)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VCenter.URI_VCENTER_CLUSTERS.format(uri),
                                             None, None, xml)


        o = common.json_decode(s)

        from cluster import Cluster
        obj = Cluster(self.__ipAddr, self.__port)

        dtlslst = obj.cluster_get_details_list(o['cluster'])

        return dtlslst


    def vcenter_get_hosts(self, label, tenantname):
        '''
        Makes a REST API call to retrieve details of a vcenter  based on its UUID
        '''
	
        uri = self.vcenter_query(label, tenantname)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VCenter.URI_VCENTER_HOSTS.format(uri),
                                             None, None, False)

	from host import Host
	obj = Host(self.__ipAddr, self.__port)

	o = common.json_decode(s)
	hostsdtls = obj.show(o['host'])

	return hostsdtls



    def vcenter_show(self, label, tenantname, xml=False):
        '''
        Makes a REST API call to retrieve details of a vcenter  based on its UUID
        '''
	
        uri = self.vcenter_query(label, tenantname)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VCenter.URI_VCENTER.format(uri),
                                             None, None, xml)

	if(xml==False):
            o = common.json_decode(s)
        
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s
    
        return o


    def vcenter_create(self, label, tenant, ipaddress, devport, username, password, osversion, usessl):
        '''
        creates a vcenter
        parameters:    
            label:  label of the vcenter
        Returns:
            JSON payload response
        '''
        try:     
            check = self.vcenter_show(label, tenant)
	    if(not check):
        	raise SOSError(SOSError.NOT_FOUND_ERR,
                       "vcenter " + label + ": not found")

        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
		from tenant import Tenant
        	obj = Tenant(self.__ipAddr, self.__port)

        	uri = obj.tenant_query(tenant)

                var = dict()
                params = dict()
	        params = { 'name'            : label,
                   'ip_address'     : ipaddress,
                   'os_version'     : osversion,
                   'port_number'    : devport,
                   'user_name'      : username,
                   'password'       : password,
                   'use_ssl'        : usessl
                   }

	
                body = json.dumps(params)
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                                     VCenter.URI_TENANTS_VCENTERS.format(uri) , body)
                o = common.json_decode(s)
                return o
		
            else:
                raise e

	if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "vcenter with name " + label + " already exists")
        


    def vcenter_delete(self, label, tenantname):
        '''
        Makes a REST API call to delete a vcenter by its UUID
        '''
        uri = self.vcenter_query(label, tenantname)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
					     self.URI_RESOURCE_DEACTIVATE.format(VCenter.URI_VCENTER.format(uri)),
                                             None)
        return str(s) + " ++ " + str(h)
    
# vcenter Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR vcenter Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a vcenter')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of vcenter',
                                metavar='<vcentername>',
                                dest='name',
                                required=True)

    create_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    mandatory_args.add_argument('-vcenter_ip', '-vcip',
                                help='IP of Vcenter',
                                metavar='<vcenter_ip>',
                                dest='vcenter_ip',
                                required=True)

    mandatory_args.add_argument('-vcenter_port', '-vcpo',
                                help='Port of Vcenter',
                                metavar='<vcenter_port>',
                                dest='vcenter_port',
                                required=True)

    mandatory_args.add_argument('-user', '-u',
                                help='Name of user',
                                metavar='<user>',
                                dest='user',
                                required=True)

    create_parser.add_argument('-osversion','-ov',
                                 help='osversion',
                                 dest='osversion',
                                 metavar='<osversion>',
				 default=None)

    create_parser.add_argument('-ssl', '-usessl',
                               dest='usessl',
                               action='store_true',
                               help='Use SSL or not')


    create_parser.set_defaults(func=vcenter_create)

def vcenter_create(args):
    obj = VCenter(args.ip, args.port)
    try:
	passwd = None

	if sys.stdin.isatty():
            passwd = getpass.getpass(prompt="Enter password of the VCenter: ")
        else:
            passwd = sys.stdin.readline().rstrip()

        res = obj.vcenter_create(args.name, args.tenant, args.vcenter_ip, args.vcenter_port, args.user, passwd , args.osversion , args.usessl)
    except SOSError as e:
        common.format_err_msg_and_raise("create", "vcenter", e.err_text, e.err_code)



# vcenter Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR vcenter Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a vcenter')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    delete_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    delete_parser.set_defaults(func=vcenter_delete)

def vcenter_delete(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_delete(args.name, args.tenant)
    except SOSError as e:
        common.format_err_msg_and_raise("delete", "vcenter", e.err_text, e.err_code)


def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR vcenter Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a vcenter')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    show_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')

    show_parser.set_defaults(func=vcenter_show)


def vcenter_show(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_show(args.name, args.tenant, args.xml)

	if(res is None):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                       "vcenter " + args.name + ": not found")

	if(args.xml):
            return common.format_xml(res)

        return common.format_json_object(res)
    except SOSError as e:
        common.format_err_msg_and_raise("show", "vcenter", e.err_text, e.err_code)



def get_hosts_parser(subcommand_parsers, common_parser):
    # get hosts command parser
    get_hosts_parser = subcommand_parsers.add_parser('get-hosts',
                                description='ViPR vcenter get hosts CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show the hosts of a vcenter')

    mandatory_args = get_hosts_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    get_hosts_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    get_hosts_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List vcenters with more details in tabular form',
                             dest='long')

    get_hosts_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List vcenters with details',
                             dest='verbose')

    get_hosts_parser.set_defaults(func=vcenter_get_hosts)


def vcenter_get_hosts(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_get_hosts(args.name, args.tenant)
	
        if(len(res) > 0):
            if(args.verbose == True):
                return common.format_json_object(res)
            elif(args.long == True):
                from common import TableGenerator
                TableGenerator(res, [ 'name', 'type', 'job_discovery_status', 'job_metering_status']).printTable()
            else:
                from common import TableGenerator
                TableGenerator(res, [ 'name']).printTable()

    except SOSError as e:
        common.format_err_msg_and_raise("get hosts", "vcenter", e.err_text, e.err_code)


def get_datacenters_parser(subcommand_parsers, common_parser):
    # show command parser
    get_datacenters_parser = subcommand_parsers.add_parser('get-datacenters',
                                description='ViPR vcenter get clusters CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show the clusters of  a vcenter')

    mandatory_args = get_datacenters_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    get_datacenters_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    get_datacenters_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List vcenters with more details in tabular form',
                             dest='long')

    get_datacenters_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List vcenters with details',
                             dest='verbose')



    get_datacenters_parser.set_defaults(func=vcenter_get_datacenters)

def vcenter_get_datacenters(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_get_datacenters(args.name, args.tenant)

        if(len(res) > 0):
            if(args.verbose == True):
                return common.format_json_object(res)
            elif(args.long == True):
                from common import TableGenerator
                TableGenerator(res, [ 'name']).printTable()
            else:
                from common import TableGenerator
                TableGenerator(res, [ 'name']).printTable()

    except SOSError as e:
        common.format_err_msg_and_raise("get clusters", "vcenter", e.err_text, e.err_code)


# vcenter get clusters routines

def get_clusters_parser(subcommand_parsers, common_parser):
    # get clusters  command parser
    get_clusters_parser = subcommand_parsers.add_parser('get-clusters',
                                description='ViPR vcenter get clusters CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show the clusters of  a vcenter')

    mandatory_args = get_clusters_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    get_clusters_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)
    get_clusters_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List vcenters with more details in tabular form',
                             dest='long')

    get_clusters_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List vcenters with details',
                             dest='verbose')



    get_clusters_parser.set_defaults(func=vcenter_get_clusters)

def vcenter_get_clusters(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_get_clusters(args.name, args.tenant)

        if(len(res) > 0):
            if(args.verbose == True):
                return common.format_json_object(res)
            elif(args.long == True):
                from common import TableGenerator
                TableGenerator(res, [ 'name']).printTable()
            else:
                from common import TableGenerator
                TableGenerator(res, [ 'name']).printTable()

    except SOSError as e:
        common.format_err_msg_and_raise("get clusters", "vcenter", e.err_text, e.err_code)


# vcenter query routines

def query_parser(subcommand_parsers, common_parser):
    # query command parser
    query_parser = subcommand_parsers.add_parser('query',
                                description='ViPR vcenter Query CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Query a vcenter')

    mandatory_args = query_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of vcenter',
                                dest='name',
                                metavar='<vcentername>',
                                required=True)

    query_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    query_parser.set_defaults(func=vcenter_query)



def vcenter_query(args):
    obj = VCenter(args.ip, args.port)
    try:
        res = obj.vcenter_query(args.name, args.tenant)
        return common.format_json_object(res)
    except SOSError as e:
        common.format_err_msg_and_raise("query", "vcenter", e.err_text, e.err_code)

# vcenter List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='ViPR vcenter List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of vcenters')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List vcenters with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List vcenters with more details in tabular form',
                             dest='long')

    list_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
				default=None)

    list_parser.set_defaults(func=vcenter_list)

def vcenter_list(args):
    obj = VCenter(args.ip, args.port)
    try:
        uris = obj.vcenter_list(args.tenant)
        output = []
        outlst = []

        for uri in uris:
	    temp = obj.vcenter_show(uri['id'], uri)
	    if(temp):
                output.append(temp)


        if(len(output) > 0):
            if(args.verbose == True):
		return common.format_json_object(output)
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'name', 'ip_address', 'job_discovery_status', 'job_metering_status']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'name']).printTable()

    except SOSError as e:
        common.format_err_msg_and_raise("list", "vcenter", e.err_text, e.err_code)


#
# vcenter Main parser routine
#

def vcenter_parser(parent_subparser, common_parser):
    # main vcenter parser
    parser = parent_subparser.add_parser('vcenter',
                                        description='ViPR vcenter CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on vcenter')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # list clusters command parser
    get_clusters_parser(subcommand_parsers, common_parser)

    # list hosts  command parser
    get_hosts_parser(subcommand_parsers, common_parser)

    # list datacemters  command parser
    get_datacenters_parser(subcommand_parsers, common_parser)


#!/usr/bin/python

#
# Copyright (c) 2013 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.
#

import common
import json
from argparse import ArgumentParser
from common import SOSError
from tenant import Tenant
from project import Project
from cluster import Cluster
from vcenterdatacenter import VcenterDatacenter
import getpass
import sys

'''
The class definition for the operation on the ViPR Host
'''
class Host(object):
    #Indentation START for the class
    
    # All URIs for the Host operations
    URI_TENANT_HOSTS = "/tenants/{0}/hosts"
    URI_HOSTS_SEARCH_FOR_PROJECT = "/compute/hosts/search?project={0}"
    URI_HOST_DETAILS = "/compute/hosts/{0}"
    URI_HOST_DEACTIVATE = "/compute/hosts/{0}/deactivate"
    URI_HOST_LIST_INITIATORS = "/compute/hosts/{0}/initiators"
    URI_HOST_LIST_IPINTERFACES = "/compute/hosts/{0}/ip-interfaces"
    URI_HOSTS_SEARCH_BY_NAME = "/compute/hosts/search?name={0}"
    
    HOST_TYPE_LIST = ['Windows', 'HPUX', 'Linux', 'Esx', 'Other']
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API
        '''
        self.__ipAddr = ipAddr
        self.__port = port
    
    '''
    Search the host matching the hostName and
    tenant if tenantName is provided. tenantName is optional
    '''
    def query_by_name(self, hostName, tenant=None):
        
        hostList = self.list_all(tenant, None)
        
        for host in hostList:
            hostUri = host['id']
            hostDetails = self.show_by_uri(hostUri)
            if(hostDetails):
                if(hostDetails['name'] == hostName):
                    return hostUri
        
        raise SOSError(SOSError.NOT_FOUND_ERR, "Host with name '" +hostName+ "' not found")
        
    
    '''
    List of host uris/ids
    '''
    def list_host_uris(self):
        hostUris = []
        hostList = self.list_all(None, None)
        
        if(hostList.__len__>0):
            for host in hostList:
                hostUri = host['id']
                hostUris.append(hostUri)        
        
        return hostUris
    
    
    '''
    Host creation operation
    '''
    def create(self, hostname, hosttype, label, tenant, project, port, 
                username, passwd, usessl, osversion, cluster, datacenter, vcenter):
        
        '''
        Takes care of creating a host system.
        Parameters:
            hostname: The short or fully qualified host name or IP address of the host management interface.
            hosttype : The host type.
            label : The user label for this host.
            osversion : The operating system version of the host.
            port: The integer port number of the host management interface.
            username: The user credential used to login to the host.
            passwd: The password credential used to login to the host. 
            tenant: The tenant name to which the host needs to be assigned
            project: The project to which the host should be assigned. 
            cluster: The id of the cluster if the host is in a cluster.
            use_ssl: One of {True, False}
            datacenter: The id of a vcenter data center if the host is an ESX host in a data center. 
        Reurns:
            Response payload
        '''
        
        '''
        check if the host is already present in this tenant
        '''
        tenantId = self.get_tenant_id(tenant)
                
        request = {'host_name'      : hostname,
                   'type'           : hosttype,
                   'name'           : label,  
                   'port_number'    : port,
                   'user_name'      : username,
                   'password'       : passwd,                   
                   }
        
        
        if(osversion):
            request['os_version'] = osversion
        
        if(usessl):
            request['use_ssl'] = usessl
        
        if(project):
            project_uri = self.get_project_id(tenant+"/"+project)
            request['project'] = project_uri
            
        if(cluster):
            request['cluster'] = self.get_cluster_id(cluster, project, tenant)
        
        if(datacenter):
            request['vcenter_data_center'] = self.get_vcenterdatacenter_id(datacenter, vcenter, tenant)
        
        
        body = json.dumps(request)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Host.URI_TENANT_HOSTS.format(tenantId),
                                             body)
        o = common.json_decode(s)
        return o
    
    
    '''
    Host update operation
    '''
    def update(self, hostname, hosttype, label, tenant, project, port, 
                username, passwd, usessl, osversion, cluster, datacenter, vcenter, newlabel):
        
        '''
        Takes care of creating a host system.
        Parameters:
            hostname: The new short or fully qualified host name or IP address of the host management interface.
            hosttype : The new host type.
            label : The user label to be searched.
            osversion : The new operating system version of the host.
            port: The new integer port number of the host management interface.
            username: The new user credential used to login to the host.
            passwd: The new password credential used to login to the host. 
            tenant: The tenant name in which the host needs to be searched
            project: The new project to which the host should be assigned. 
            cluster: The new id of the cluster if the host is in a cluster.
            use_ssl: One of {True, False}
            datacenter: The new id of a vcenter data center if the host is an ESX host in a data center. 
        Reurns:
            Response payload
        '''
        
        hostUri = self.query_by_name(label, tenant)
                
        request = dict()
        
        if(newlabel):
            request['name'] = newlabel
        
        if(hostname):
            request['host_name'] = hostname
            
        if(port):
            request['port_number'] = port
        
        if(username):
            request['user_name'] = username
            request['password'] = passwd
        
        if(osversion):
            request['os_version'] = osversion
        
        if(usessl):
            request['use_ssl'] = usessl
        
        if(project):
            project_uri = self.get_project_id(tenant+"/"+project)
            request['project'] = project_uri
            
        if(cluster):
            request['cluster'] = self.get_cluster_id(cluster, project, tenant)
        
        if(datacenter):
            request['vcenter_data_center'] = self.get_vcenterdatacenter_id(datacenter, vcenter, tenant)
        
        
        body = json.dumps(request)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "PUT",
                                             Host.URI_HOST_DETAILS.format(hostUri),
                                             body)
        o = common.json_decode(s)
        return o
    
    '''
    Deletes the host
    '''
    def delete(self, host_uri):
        '''
        Makes a REST API call to delete a storage system by its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Host.URI_HOST_DEACTIVATE.format(host_uri),
                                              None)
        return
    
    
    '''
    Lists all the hosts belonging to a tenant and its associated project
    
    #case 1 : only tenant is input
    # List all hosts belonging to tenant
    
    #case 2 : only project is input
    # search the project in default tenant, if it is not found, throw the error
    
    #case 3 : both tenant and project are inputs
    # check the tenant and project relationship, if they do relate then query the hosts
    
    #case 4: No tenant and No project
    # query the list from the default tenant
    '''    
    def list_all(self, tenant, project):
        tenantName = None
        hostList = []
        
        if(tenant is None and project is None):
            tenantName = ""
        elif(tenant and project is None):
            tenantName = tenant
        
        if(tenantName is not None):
            hostList = self.list_by_tenant(tenantName) 
            return hostList
        
        fullProjectPath = None
        if(project and tenant is None):
            fullProjectPath = "/"+project
        elif(tenant and project):
            fullProjectPath = tenant+"/"+project
        
        if(fullProjectPath is not None):
            project_uri = self.get_project_id(fullProjectPath)
            hostList = self.list_by_project_uri(project_uri)
            return hostList
            
        return hostList
    
    '''
    Gets list of hosts from all tenants in the system
    '''
    def list_from_all_tenants(self):
        hostList = []
        from tenant import Tenant
        obj = Tenant(self.__ipAddr, self.__port)
        
        tenants = obj.tenant_list()
        uris = []
        
        for tenant in tenants:
            uris.append(tenant['id'])

        defaultTenantId = obj.tenant_getid()
        uris.append(defaultTenantId)
        
        for uri in uris:
            if(hostList.__len__()==0):
                hostList = self.list_by_tenant(uri)
            else:
                tempList = self.list_by_tenant(uri)
                for tempHost in tempList:
                    hostList.append(tempHost)
        
        return hostList
        
        
    
    '''
    Gets the list of Hosts belonging to a given tenant
    '''
    def list_by_tenant(self, tenantName):
        
        '''
         Lists all the hosts
         Parameters
             tenant : The name of the tenant for which host list to be returned
        '''
        tenantId = self.get_tenant_id(tenantName)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_TENANT_HOSTS.format(tenantId),
                                             None)
        o = common.json_decode(s)
        
        if(not o or "host" not in o):
            return []
        
        return common.get_node_value(o, 'host')
    
    
    '''
    Gets the list of Initiators belonging to a given Host
    '''
    def list_initiators(self, hostName):
        
        '''
         Lists all initiators
         Parameters
             hostName : The name of the host for which initiators to be returned
        '''
        if(common.is_uri(hostName)==False):
            hostUri = self.query_by_name(hostName, None)
        else:
            hostUri = hostName
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_HOST_LIST_INITIATORS.format(hostUri),
                                             None)
        o = common.json_decode(s)
        
        if(not o or "initiator" not in o):
            return []
        
        return common.get_node_value(o, 'initiator')
    
    
    '''
    Gets the list of IP-Interfaces belonging to a given Host
    '''
    def list_ipinterfaces(self, hostName):
        
        '''
         Lists all IPInterfaces belonging to a given host
         Parameters
             hostName : The name of the host for which ipinterfaces to be returned
        '''
        if(common.is_uri(hostName)==False):
            hostUri = self.query_by_name(hostName, None)
        else:
            hostUri = hostName
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_HOST_LIST_IPINTERFACES.format(hostUri),
                                             None)
        o = common.json_decode(s)
        
        if(not o or "ip_interface" not in o):
            return []
        
        return common.get_node_value(o, 'ip_interface')
    
    
    '''
    Lists the hosts for a given project
    '''
    def list_by_project_uri(self, project_uri):
        '''
        Searches all hosts those belong to a project
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_HOSTS_SEARCH_FOR_PROJECT.format(project_uri), None)
        o = common.json_decode(s)
        if not o:
            return []
        
        return common.get_node_value(o, "resource")
    
    
    '''
    search the hosts for a given name
    '''
    def search_by_name(self, host_name):
        '''
        Search host by its name
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_HOSTS_SEARCH_BY_NAME.format(host_name), None)
        o = common.json_decode(s)
        if not o:
            return []
        return common.get_node_value(o, "resource")
    
    '''
    show the host details for a given list of hosts
    '''
    def show(self, hostList):        
        hostListDetails = []
        if(hostList is not None):
            for host in hostList:
                hostUri = host['id']
                hostDetail = self.show_by_uri(hostUri)
                if(hostDetail is not None and len(hostDetail)>0):
                        hostListDetails.append(hostDetail)
        
        return hostListDetails
    
    '''
    Get the details of hosts matching the host-type
    '''
    def show_by_type(self, hostList, type):        
        hostListDetails = []
        if(hostList is not None):
            for host in hostList:
                hostUri = host['id']
                hostDetail = self.show_by_uri(hostUri)
                if(hostDetail is not None and len(hostDetail)>0 and hostDetail['type'] == type):
                        hostListDetails.append(hostDetail)
        
        return hostListDetails
    
    
    '''
    Get the details of host matching the host-type and name
    '''
    def show_by_type_and_name(self, hostList, type, name, xml):        
        hostListDetails = None
        if(hostList is not None):
            for host in hostList:
                hostUri = host['id']
                hostDetail = self.show_by_uri(hostUri)
                if(hostDetail is not None and len(hostDetail)>0 
                   and hostDetail['type'] == type
                   and hostDetail['name'] == name):
                    if(xml):
                        hostListDetails = self.show_by_uri(hostUri, xml)
                    else:
                        hostListDetails = hostDetail
                    break
        
        return hostListDetails
    
    
    '''
    Gets the host system details, given its uri/id
    '''
    def show_by_uri(self, uri, xml=False):
        '''
        Makes a REST API call to retrieve details of a Host based on its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_HOST_DETAILS.format(uri),
                                             None, None)        
        o = common.json_decode(s)
        inactive = common.get_node_value(o, 'inactive')
        
        if(inactive == True):
            return None
        if(xml == True):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Host.URI_HOST_DETAILS.format(uri),
                                             None, None, xml)
            return s
        else:
            return o
        
    
    def get_tenant_id(self, tenantName):
        '''
         Fetch the tenant id
        '''
        tenantObj = Tenant(self.__ipAddr, self.__port)
        tenantId = tenantObj.get_tenant_by_name(tenantName)    
        
        return tenantId
    
    def get_project_id(self, projectName):
        
        projectObj = Project(self.__ipAddr, self.__port)
        projectId = projectObj.project_query(projectName)
    
        return projectId
    
    def get_cluster_id(self, clusterName, projectName, tenantName):
        
        clusterObj = Cluster(self.__ipAddr, self.__port)
        clusterId = clusterObj.cluster_query(clusterName, projectName, tenantName)
        
        return clusterId
    
    def get_vcenterdatacenter_id(self, datacenterName, vcenterName, tenantName):
        
        vcenterDatacenterObj = VcenterDatacenter(self.__ipAddr, self.__port)
        vcenterDatacenterId = vcenterDatacenterObj.vcenterdatacenter_query(datacenterName, vcenterName, tenantName)
        
        return vcenterDatacenterId
    
    #Indentation END for the class
    

#Start Parser definitions
def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Host create CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Creates a Host')
    
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-hn', '-viprhostname',
                                help='FQDN of host or IP address of management interface',
                                metavar='<viprhostname>',
                                dest='viprhostname',
                                required=True)
    mandatory_args.add_argument('-t', '-type',
                               choices=Host.HOST_TYPE_LIST,
                               dest='type',
                               help='Type of host',
                               required=True)
    
    mandatory_args.add_argument('-hl', '-hostlabel',
                                help='Label for the host',
                                dest='hostlabel',
                                metavar='<hostlabel>',
                                required=True)
    
    mandatory_args.add_argument('-hp', '-hostport',
                                help='Management interface port for the host',
                                dest='hostport',
                                metavar='<hostport>',
                                required=True)
    
    mandatory_args.add_argument('-un', '-hostusername',
                                help='User name for the host',
                                dest='hostusername',
                                metavar='<hostusername>',
                                required=True)
    
    create_parser.add_argument('-t', '-tenant',
                                help='Tenant for the host',
                                dest='tenant',
                                metavar='<tenant>',
                                default = None)
    
    create_parser.add_argument('-hostssl', '-hostusessl',
                                help='SSL flag for the host: true or false',
                                dest='hostusessl',
                                metavar='<hostusessl>',
                                default=False)
    
    create_parser.add_argument('-ov', '-osversion',
                                help='Host OS version',
                                dest='osversion',
                                metavar='<osversion>')
    
    create_parser.add_argument('-pr', '-project',
                                help='Name of the project to which the host needs to be assigned to',
                                dest='project',
                                metavar='<project>')
    
    create_parser.add_argument('-c', '-cluster',
                                help='Name of the cluster for the host',
                                dest='cluster',
                                metavar='<cluster>')
    
    create_parser.add_argument('-dc', '-datacenter',
                                help='Name of the datacenter for the host',
                                dest='datacenter',
                                metavar='<datacenter>')
    
    create_parser.add_argument('-vc', '-vcenter',
                                help='Name of the vcenter for datacenter name search',
                                dest='vcentername',
                                metavar='<vcentername>')
    
    create_parser.set_defaults(func=host_create)

'''
Preprocessor for the host create operation
'''
def host_create(args):
       
    if(not args.tenant):
        tenant = ""
    
    if(args.datacenter and args.vcentername is None):
        raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                           " " + sys.argv[2] + ": error:"+ "-vcentername is required to search the datacenter for the host")
        
        
    passwd = None
    if (args.hostusername and len(args.hostusername) > 0):
        passwd = common.get_password("host")
    
    hostObj = Host(args.ip, args.port)
    try:
        hostObj.create(args.viprhostname, args.type, args.hostlabel, tenant, args.project, args.hostport, 
                       args.hostusername, passwd, args.hostusessl, args.osversion, 
                       args.cluster, args.datacenter, args.vcentername)
    except SOSError as e:
        common.format_err_msg_and_raise("create", "host", e.err_text, e.err_code)


# list command parser
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='ViPR Host List CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists hosts')
    list_parser.add_argument('-ht', '-hosttype',
                               choices=Host.HOST_TYPE_LIST,
                               dest='hosttype',
                               help='Type of Host')
    list_parser.add_argument('-t', '-tenant',
                               dest='tenant',
                               metavar='<tenant>',
                               help='Tenant for which hosts to be listed',
                               default=None)
    list_parser.add_argument('-pr', '-project',
                               dest='project',
                               metavar='<project>',
                               help='Project for which hosts to be listed',
                               default=None)
    list_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             action='store_true',
                             help='Lists Hosts with details')
    list_parser.add_argument('-l', '-long',
                             dest='largetable',
                             action='store_true',
                             help='Lists Hosts in a large table')
    list_parser.set_defaults(func=host_list)

    
'''
Preprocessor for hosts list operation
'''
def host_list(args):
    
    hostList = None
    hostObj = Host(args.ip, args.port)
    from common import TableGenerator
    
    try:
        hostList = hostObj.list_all(args.tenant, args.project)
        
        if(len(hostList)>0):
            hostListDetails = []
            if(args.hosttype is None):
                hostListDetails = hostObj.show(hostList)
            else:
                hostListDetails = hostObj.show_by_type(hostList, args.hosttype)
            
            if(args.verbose == True):
                return common.format_json_object(hostListDetails)
            else:
                if(args.largetable == True):
                    TableGenerator(hostListDetails, ['name', 'host_name','type', 'user_name','registration_status']).printTable()
                else:
                    TableGenerator(hostListDetails, ['name', 'host_name', 'type']).printTable()
       
        
    except SOSError as e:
        common.format_err_msg_and_raise("list", "host", e.err_text, e.err_code)
        
        
# show command parser
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Host Show CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show Host details')
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    mutex_group = show_parser.add_mutually_exclusive_group(required=True)
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-t', '-type',
                                dest='type',
                                help='Type of Host',
                                choices=Host.HOST_TYPE_LIST,
                                required=True)
    
    mutex_group.add_argument('-n', '-name',
                             metavar='<name>',
                             dest='name',
                             help='Name of Host')
    
    show_parser.add_argument('-tenant', '-tn',
                              metavar='<tenantname>',
                              dest='tenant',
                              help='Name of tenant',
                              default=None)
    
    show_parser.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                default=None)
    
    show_parser.set_defaults(func=host_show)
    

def host_show(args):
    
    try:
        hostList = []
        hostObj = Host(args.ip, args.port)
    
        hostList = hostObj.list_all(args.tenant, args.project)
        
        hostdetails = None
        if(len(hostList)>0):
            hostdetails = hostObj.show_by_type_and_name(hostList, args.type, args.name, args.xml)
            
        if(hostdetails is None):
            raise SOSError(SOSError.NOT_FOUND_ERR, "Could not find the matching host")
    
        if(args.xml):
            return common.format_xml(hostdetails)
        return common.format_json_object(hostdetails)
    except SOSError as e:
        common.format_err_msg_and_raise("show", "host", e.err_text, e.err_code)
    
    return

def delete_parser(subcommand_parsers, common_parser):
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR Host delete CLI usage ',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Deletes a Host')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-n', '-name',
                             metavar='<name>',
                             dest='name',
                             help='Name of Host',
                             required=True)
    mandatory_args.add_argument('-t', '-type',
                               choices=Host.HOST_TYPE_LIST,
                               dest='type',
                               help='Type of Host',
                               required=True)
    delete_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant')
    delete_parser.add_argument('-project', '-pr',
                                metavar='<project>',
                                dest='project',
                                help='Name of project')
    delete_parser.set_defaults(func=host_delete)
    
    
def host_delete(args):
    try:
        hostList = []
        hostObj = Host(args.ip, args.port)
    
        hostList = hostObj.list_all(args.tenant, args.project)
    
        if(len(hostList)>0):
            hostdetails = hostObj.show_by_type_and_name(hostList, args.type, args.name, False)
            if(hostdetails):
                hostObj.delete(hostdetails['id'])
            else:
               raise SOSError(SOSError.NOT_FOUND_ERR, "Could not find the matching host")
        else:
            raise SOSError(SOSError.NOT_FOUND_ERR, "Could not find the matching host")
    
    except SOSError as e:
        common.format_err_msg_and_raise("delete", "host", e.err_text, e.err_code)
    
    return


'''
Update Host Parser
'''    
def update_parser(subcommand_parsers, common_parser):
    # create command parser
    update_parser = subcommand_parsers.add_parser('update',
                                description='ViPR Host update CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Updates a Host')
    
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    update_parser.add_argument('-nhn', '-newviprhostname',
                                help='New FQDN of host or IP address of management interface',
                                metavar='<newviprhostname>',
                                dest='newviprhostname')
    update_parser.add_argument('-nt', '-newtype',
                               choices=Host.HOST_TYPE_LIST,
                               dest='newtype',
                               help='New type of host')
    
    mandatory_args.add_argument('-hl', '-hostlabel',
                                help='search label for the host',
                                dest='hostlabel',
                                metavar='<hostlabel>',
                                required=True)
    
    update_parser.add_argument('-nl', '-newlabel',
                                help='New label for the host',
                                dest='newlabel',
                                metavar='<newlabel>')
    
    update_parser.add_argument('-nhp', '-newhostport',
                                help='New Management interface port for the host',
                                dest='newhostport',
                                metavar='<newhostport>')
    
    update_parser.add_argument('-nun', '-newhostusername',
                                help='New user name for the host',
                                dest='newhostusername',
                                metavar='<newhostusername>')
    
    update_parser.add_argument('-t', '-tenant',
                                help='Tenant in which host needs to be searched',
                                dest='tenant',
                                metavar='<tenant>',
                                default=None)
    
    update_parser.add_argument('-nhostssl', '-newhostusessl',
                                help='New SSL flag for the host: true or false',
                                dest='newhostusessl',
                                metavar='<newhostusessl>',
                                default=False)
    
    update_parser.add_argument('-nov', '-newosversion',
                                help='New Host OS version',
                                dest='newosversion',
                                metavar='<newosversion>')
    
    update_parser.add_argument('-npr', '-newproject',
                                help='New name of the project to which the host needs to be assigned to',
                                dest='newproject',
                                metavar='<newproject>')
    
    update_parser.add_argument('-nc', '-newcluster',
                                help='New name of the cluster for the host',
                                dest='newcluster',
                                metavar='<cluster>')
    
    update_parser.add_argument('-ndc', '-newdatacenter',
                                help='New name of the datacenter for the host',
                                dest='newdatacenter',
                                metavar='<newdatacenter>')
    
    update_parser.add_argument('-vc', '-vcenter',
                                help='Name of the vcenter for datacenter name search',
                                dest='vcentername',
                                metavar='<vcentername>')
    
    update_parser.set_defaults(func=host_update)
    
    
'''
Preprocessor for the host update operation
'''
def host_update(args):
    
    if(args.tenant is None and args.newviprhostname is None and args.newtype is None and args.newproject is None
       and args.newhostport is None and args.newhostusername is None and
       args.newosversion is None and args.newcluster is None and args.newdatacenter is None
       and args.newlabel is None):
        raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                           " " + sys.argv[2] + ": error:"+ "At least one of the arguments :" 
                                                                                "-tenant -newviprhostname -newtype -newhostusessl"
                                                                                "-newproject -newhostport -newhostusername"
                                                                                "-newosversion -newcluster -newdatacenter -newlabel"
                                                                                " should be provided to update the Host")
    if(args.newdatacenter and args.vcentername is None):
        raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                           " " + sys.argv[2] + ": error:"+ "-vcentername is required to search the datacenter for the host")
        
    passwd = None
    if (args.newhostusername and len(args.newhostusername) > 0):
        passwd = common.get_password("host")
    
    hostObj = Host(args.ip, args.port)
    try:
        hostObj.update(args.newviprhostname, args.newtype, args.hostlabel, args.tenant, args.newproject, args.newhostport, 
                       args.newhostusername, passwd, args.newhostusessl, args.newosversion, 
                       args.newcluster, args.newdatacenter, args.vcentername, args.newlabel)
    except SOSError as e:
        common.format_err_msg_and_raise("update", "host", e.err_text, e.err_code)
        

# list initiators command parser
def list_initiator_parser(subcommand_parsers, common_parser):
    list_initiator_parser = subcommand_parsers.add_parser('list-initiators',
                                description='ViPR Host list-initiator CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists Initiators')
    mandatory_args = list_initiator_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-hl', '-hostlabel',
                               dest='hostlabel',
                               help='Label of the host for which initiators to be listed',
                               required=True)
    list_initiator_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             action='store_true',
                             help='Lists initiators with details')
    list_initiator_parser.add_argument('-l', '-long',
                             dest='largetable',
                             action='store_true',
                             help='Lists initiators in a large table')
    list_initiator_parser.set_defaults(func=host_list_initiators)
    

def host_list_initiators(args):
    hostObj = Host(args.ip, args.port)
    from common import TableGenerator
    
    try:
        initiatorList = hostObj.list_initiators(args.hostlabel)
        
        if(len(initiatorList)>0):
            initiatorListDetails = []
            from hostinitiators import HostInitiator
            hostInitiatorObj = HostInitiator(args.ip, args.port)
            initiatorListDetails = hostInitiatorObj.show(initiatorList)
            
            if(args.verbose == True):
                return common.format_json_object(initiatorListDetails)
            else:
                if(args.largetable == True):
                    TableGenerator(initiatorListDetails, ['name', 'protocol','initiator_node', 'initiator_port','host_name']).printTable()
                else:
                    TableGenerator(initiatorListDetails, ['name', 'protocol','host_name']).printTable()
       
        
    except SOSError as e:
        common.format_err_msg_and_raise("list-initiators", "host", e.err_text, e.err_code)
        
        
# list initiators command parser
def list_ipinterfaces_parser(subcommand_parsers, common_parser):
    list_ipinterfaces_parser = subcommand_parsers.add_parser('list-ipinterfaces',
                                description='ViPR Host list-ipinterfaces CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists ipinterfaces')
    mandatory_args = list_ipinterfaces_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-hl', '-hostlabel',
                               dest='hostlabel',
                               help='Label of the host for which ipinterfaces to be listed',
                               required=True)
    list_ipinterfaces_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             action='store_true',
                             help='Lists Hosts with details')
    list_ipinterfaces_parser.add_argument('-l', '-long',
                             dest='largetable',
                             action='store_true',
                             help='Lists Hosts in a large table')
    list_ipinterfaces_parser.set_defaults(func=host_list_ipinterfaces)
    

def host_list_ipinterfaces(args):
    hostObj = Host(args.ip, args.port)
    from common import TableGenerator
    
    try:
        ipinterfacesList = hostObj.list_ipinterfaces(args.hostlabel)
        
        if(len(ipinterfacesList)>0):
            ipinterfacesListDetails = []
            from hostipinterfaces import HostIPInterface
            hostIpinterfaceObj = HostIPInterface(args.ip, args.port)
            ipinterfacesListDetails = hostIpinterfaceObj.show(ipinterfacesList)
            
            if(args.verbose == True):
                return common.format_json_object(ipinterfacesListDetails)
            else:
                if(args.largetable == True):
                    TableGenerator(ipinterfacesListDetails, ['name', 'ip_address', 'protocol','netmask', 'prefix_length']).printTable()
                else:
                    TableGenerator(ipinterfacesListDetails, ['name', 'ip_address', 'protocol']).printTable()
       
        
    except SOSError as e:
        common.format_err_msg_and_raise("list-ipinterfaces", "host", e.err_text, e.err_code)

        
    
#
# Host Main parser routine
#
def host_parser(parent_subparser, common_parser):
    
    parser = parent_subparser.add_parser('host',
                                description='ViPR host CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on host')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)
    
    # list command parser
    list_parser(subcommand_parsers, common_parser)
    
    #show parser
    show_parser(subcommand_parsers, common_parser)
    
    #delete parser
    delete_parser(subcommand_parsers, common_parser)
    
    #update parser
    update_parser(subcommand_parsers, common_parser)
    
    #List Initiators parser
    list_initiator_parser(subcommand_parsers, common_parser)
    
    #List ipinterfaces parser
    list_ipinterfaces_parser(subcommand_parsers, common_parser)
    
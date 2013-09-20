#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import common
import json
from common import SOSError
from tenant import Tenant
from project import Project
from vcenterdatacenter import VcenterDatacenter
from common import TableGenerator


class Cluster(object):
    '''
    The class definition for operations on 'Cluster'. 
    '''
    URI_SERVICES_BASE       = ''
    URI_TENANT              = URI_SERVICES_BASE + '/tenant'
    URI_TENANTS             = URI_SERVICES_BASE + '/tenants/{0}'
    URI_TENANTS_CLUSTERS    = URI_TENANTS      + '/clusters'
    
    URI_CLUSTERS            = URI_SERVICES_BASE   + '/compute/clusters'
    URI_CLUSTER             = URI_SERVICES_BASE   + '/compute/clusters/{0}'
    URI_CLUSTERS_BULKGET    = URI_CLUSTERS        + '/bulk'
    
    URI_CLUSTER_SEARCH     = URI_SERVICES_BASE + '/compute/clusters/search'
    URI_CLUSTER_SEARCH_PROJECT      = URI_CLUSTER_SEARCH  + '?project={0}'
    URI_CLUSTER_SEARCH_NAME         = URI_CLUSTER_SEARCH  + '?name={0}'

    URI_RESOURCE_DEACTIVATE = '{0}/deactivate' 

    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
        '''
        create cluster action
        Parameters:
            name      : Name of the cluster
            tenant    : name of tenant
            project   : Name of the project
            datacenter: Name of datacenter
            vcenter   : name of vcenter
        Returns:
            result of the action.
        '''
  
    def cluster_create(self, label, tenant, project, datacenter, vcenter):
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        vdatacenterobj = VcenterDatacenter(self.__ipAddr, self.__port)
        projectobj = Project(self.__ipAddr, self.__port)

        if(tenant == None):
            tenant_uri = tenant_obj.tenant_getid()
        else:
            tenant_uri = tenant_obj.tenant_query(tenant)
                
        parms = { 'name'            : label
                   }
        #project
        if(project):
            if(tenant):
                projectname = tenant + "/" + project
            else:
                projectname = "" + "/" + project
            #on failure, query raise exception
            parms['project'] = projectobj.project_query(projectname)
            
        #datacenter
        if(datacenter):
            #on failure, query raise exception
            parms['vcenter_data_center'] = vdatacenterobj.vcenterdatacenter_query(datacenter, vcenter)

        body = json.dumps(parms)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Cluster.URI_TENANTS_CLUSTERS.format(tenant_uri),
                                             body)
        o = common.json_decode(s)

    '''
        list cluster action 
        Parameters:
            tenant : name of tenant
        Returns:
            return cluster id list
        '''    
    def cluster_list(self, tenant):
        uri = Tenant(self.__ipAddr, self.__port).tenant_query(tenant)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Cluster.URI_TENANTS_CLUSTERS.format(uri), None)
        o = common.json_decode(s)
        return o['cluster']
    
        '''
        show cluster action 
        Parameters:
            label : Name of the cluster
            tenant : name of tenant
            xml    : content-type
        Returns:
            cluster detail information
        '''
    def cluster_show(self, label, project, tenant =None, xml=False):

        uri = self.cluster_query(label, project, tenant)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Cluster.URI_CLUSTER.format(uri),
                                             None, None, xml)

        if(xml==False):
            o = common.json_decode(s)
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
        else:
            return s
        return o
    '''
        Makes a REST API call to retrieve details of a cluster  based on its UUID
        Parameters:
            uri : uri of the cluster
        Returns:
            cluster detail information
        '''
    def cluster_show_uri(self, uri):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Cluster.URI_CLUSTER.format(uri),
                                             None, None, False)
        return common.json_decode(s)
    
    '''
        search cluster action 
        Parameters:
            name : Name of the cluster
            project: name of project
        Returns:
            return clusters list 
        '''
    def cluster_search(self, name, project):
        

        if(project):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Cluster.URI_CLUSTER_SEARCH_PROJECT.format(project), None)
        else:
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Cluster.URI_CLUSTER_SEARCH_NAME.format(name), None)
        o = common.json_decode(s)
        return o['resource']
    
        '''
        query cluster action 
        Parameters:
            name : Name of the cluster
            tenant : name of tenant
            project: name of project
        Returns:
            return cluster id or uri
        '''
    #default = None(provider tenant)
    def cluster_query(self, name, project, tenant = None):
        #search by project
        if(project):
            if(tenant):
                projectname = tenant + "/" + project
            else:
                projectname = "" + "/" + project
            project_uri = Project(self.__ipAddr, self.__port).project_query(projectname)
            resources = self.cluster_search(None, project_uri)
            for resource in resources:
                cluster = self.cluster_show_uri(resource['id'])
                if (cluster['name'] == name):
                    return cluster['id']
        else:#search by resource name
            resources = self.cluster_search(name, None)
            for resource in resources:
                if (resource['match'] == name):
                    return resource['id']
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "cluster " + name + ": not found")

        
        '''
        delete cluster action 
        Parameters:
            name : Name of the cluster
            tenant : name of tenant
        Returns:
            result of the action.
        '''
    def cluster_delete(self, name, project, tenant=None):

        uri = self.cluster_query(name, project, tenant)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                         self.URI_RESOURCE_DEACTIVATE.format(Cluster.URI_CLUSTER.format(uri)),
                                             None)
        
    def cluster_update(self, name, tenant, project, datacenter, vcenter, label):
        '''
        update cluster with project, datacenter, label
        Parameters:
            name      : Name of the cluster
            tenant    : name of tenant
            project   : Name of the project
            datacenter: Name of datacenter
            vcenter   : name of vcenter
            label     : new name to existing cluster
        Returns:
            result of the action.
        '''
        parms = {}
        #new name 
        if(label):
            parms['name'] = label
  
        #project
        if(project):
            if(tenant):
                projectname = tenant + "/" + project
            else:
                projectname = "" + "/" + project
            parms['project'] = Project(self.__ipAddr, self.__port).project_query(projectname)
            
        #datacenter
        if(datacenter):
            vdatacenterobj = VcenterDatacenter(self.__ipAddr, self.__port)
            data_uri = vdatacenterobj.vcenterdatacenter_query(datacenter, vcenter)
            parms['vcenter_data_center'] = data_uri
        
        #get the cluster uri
        cluster_uri = self.cluster_query(name, project, tenant)
        
        body = json.dumps(parms)
        common.service_json_request(self.__ipAddr, self.__port, "PUT", 
                                             Cluster.URI_CLUSTER.format(cluster_uri),
                                             body)
        return
    
    '''
        get the uri of a datacenter
        Parameters:
            datacenter : Name of the datacenter
            vcenter : name of vcenter

        Returns:
            uri of datacenter
        '''
    def get_datacenter_uri(self, datacenter, vcenter):
        vdatacenterobj = VcenterDatacenter(self.__ipAddr, self.__port)
        return vdatacenterobj.vcenterdatacenter_query(datacenter, vcenter)


    def cluster_get_details_list(self, detailslst):
	rsltlst= []
	for iter in detailslst:
	    rsltlst.append(self.cluster_show_uri(iter['id']))

        return rsltlst

         
        
# create command parser   
def create_parser(subcommand_parsers, common_parser):
    
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Cluster Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a Cluster')
    
    mandatory_args = create_parser.add_argument_group('mandatory arguments') 
    mandatory_args.add_argument('-name',  '-n', 
                               metavar='<name>', 
                               dest='name', 
                               help = 'name for the cluster',
                               required=True)
    create_parser.add_argument('-tenant', '-tn', 
                               metavar='<tenantname>', 
                               dest='tenant', 
                               help = 'name of tenant', 
                               default = None)
    create_parser.add_argument('-project', '-pr', 
                               metavar='<projectname>', 
                               dest='project', 
                               help = 'name of a datacenter')
    create_parser.add_argument('-datacenter', '-dc', 
                               metavar='<datacentername>', 
                               dest='datacenter',    
                               help='name of a datacenter')
    create_parser.add_argument('-vcenter','-vc',
                                 help='name of a vcenter',
                                 dest='vcenter',
                                 metavar='<vcentername>')
    
    create_parser.set_defaults(func=cluster_create)  
def cluster_create(args):
    obj = Cluster(args.ip, args.port)
    try:
        if(args.datacenter or args.vcenter):
            if(args.datacenter == None or args.vcenter == None):
                print "Both vCenter and Data Center details are required"
                return
        obj.cluster_create(args.name, args.tenant, args.project, args.datacenter, args.vcenter)
    except SOSError as e:
        common.format_err_msg_and_raise("create", "cluster", e.err_text, e.err_code)  
         
# delete command parser    
def delete_parser(subcommand_parsers, common_parser):

    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR Cluster Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a Cluster')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name',  '-n', 
                               metavar='<name>', 
                               dest='name', 
                               help = 'name of a the cluster', 
                               required=True)
    delete_parser.add_argument('-tenant', '-tn', 
                               metavar='<tenantname>', 
                               dest='tenant', 
                               help = 'name of tenant', 
                               default = None)
    delete_parser.add_argument('-project', '-pr',
                                help='Name of project',
                                metavar='<projectname>',
                                dest='project')
    delete_parser.set_defaults(func=cluster_delete)
def cluster_delete(args):
    obj = Cluster(args.ip, args.port)
    try:
        obj.cluster_delete(args.name, args.project, args.tenant)
    except SOSError as e:
        common.format_err_msg_and_raise("delete", "cluster", e.err_text, e.err_code)
        
# show command parser        
def show_parser(subcommand_parsers, common_parser):

    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Cluster Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a Cluster')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name',  '-n', 
                               metavar='<name>', 
                               dest='name', 
                               help = 'name of a the cluster',
                               required=True)
    show_parser.add_argument('-tenant', '-tn', 
                               metavar='<tenantname>', 
                               dest='tenant', 
                               help = 'name of tenant', 
                               default = None)
    show_parser.add_argument('-project', '-pr',
                                help='Name of project',
                                metavar='<projectname>',
                                dest='project')
    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')
    show_parser.set_defaults(func=cluster_show)
    
def cluster_show(args):
    obj = Cluster(args.ip, args.port)
    try:
        res = obj.cluster_show(args.name, args.project, args.tenant,  args.xml)
        
        if(args.xml):
            return common.format_xml(res)
        
        return common.format_json_object(res)
    except SOSError as e:
        common.format_err_msg_and_raise("show", "cluster", e.err_text, e.err_code)
        
# list command parser
def list_parser(subcommand_parsers, common_parser):

    list_parser = subcommand_parsers.add_parser('list',
                                                description='StorageOS Cluster List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of vcenters')
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List vcenters with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List cluster with more details in tabular form',
                             dest='long')

    list_parser.add_argument('-tenant', '-tn',
                                help='Name of Tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                default=None)

    list_parser.set_defaults(func=cluster_list)

def cluster_list(args):
    obj = Cluster(args.ip, args.port)
    try:
        clusters = obj.cluster_list(args.tenant)
        output = []
        vdatacenterobj = VcenterDatacenter(args.ip, args.port)
        for cluster_uri in clusters:
            clobj = obj.cluster_show_uri(cluster_uri['id'])
            if(clobj):
                # add vdatacenter name to cluster object
                if('vcenter_data_center' in clobj and args.long):
                    vobj = vdatacenterobj.vcenterdatacenter_show_by_uri(clobj['vcenter_data_center']['id'])
                    clobj['vcenter_data_center'] = vobj['name']
                output.append(clobj)

        if(len(output) > 0):
            if(args.verbose == True):
                return common.format_json_object(output)
            elif(args.long == True):
                
                TableGenerator(output, [ 'name', 'vcenter_data_center'] ).printTable()
            else:
                TableGenerator(output, [ 'name']).printTable()
        
        
    except SOSError as e:
        common.format_err_msg_and_raise("list", "cluster", e.err_text, e.err_code)
        
# update command parser
def update_parser(subcommand_parsers, common_parser):

    update_parser = subcommand_parsers.add_parser('update',
                                description='ViPR Cluster Update CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Update a Cluster')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name',  '-n', 
                               metavar='<name>', 
                               dest='name', 
                               help = 'name of a the cluster', 
                               required= True)
    
    update_parser.add_argument('-tenant', '-tn', 
                               metavar='<tenantname>', 
                               dest='tenant', 
                               help = 'new name of tenant', 
                               default = None)
    update_parser.add_argument('-project', '-pr', 
                               metavar='<projectname>', 
                               dest='project', 
                               help = 'new name of project')
    update_parser.add_argument('-datacenter', '-dc', 
                               metavar='<datacentername>', 
                               dest='datacenter',    
                               help='new name of datacenter')
    update_parser.add_argument('-label',  '-l', 
                               metavar='<label>', 
                               dest='label', 
                               help = 'new label for the cluster')
    update_parser.add_argument('-vcenter','-vc',
                                 help='new name of a vcenter',
                                 dest='vcenter',
                                 metavar='<vcentername>')
    
    update_parser.set_defaults(func=cluster_update)
def cluster_update(args):
    obj = Cluster(args.ip, args.port)
    try:
        if(args.datacenter or args.vcenter):
            if(args.datacenter == None or args.vcenter == None):
                print "Both vCenter and Data Center details are required"
                return
                
        obj.cluster_update(args.name, args.tenant, args.project, args.datacenter, args.vcenter, args.label)
    except SOSError as e:
        common.format_err_msg_and_raise("update", "cluster", e.err_text, e.err_code)
        
  
    
def cluster_parser(parent_subparser, common_parser): 
    # main cluster parser
    parser = parent_subparser.add_parser('cluster',
                                description='ViPR Cluster CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Cluster')
    subcommand_parsers = parser.add_subparsers(help='Use one of sub commands(create, list, show, delete, update)') 
    
    # create command parser
    create_parser(subcommand_parsers, common_parser)
    
    # list command parser
    list_parser(subcommand_parsers, common_parser)
    
    # show command parser
    show_parser(subcommand_parsers, common_parser)
    
    # delete command parser
    delete_parser(subcommand_parsers, common_parser)
    
    # update command parser
    update_parser(subcommand_parsers, common_parser)


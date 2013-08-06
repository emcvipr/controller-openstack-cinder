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


class Cluster(object):
    '''
    The class definition for operations on 'Cluster'. 
    '''

    #Commonly used URIs for the 'Cluster' module
    URI_TENANT_CLUSTERS = '/tenants/{0}/clusters'
    URI_CLUSTER = '/compute/clusters/{0}'
    URI_CLUSTER_DEACTIVATE = URI_CLUSTER + '/deactivate'
    
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def cluster_create(self, name, project_name=None, tenant_name=None):
        '''
        Makes REST API call to create a cluster under a tenant
        Parameters:
            name: name of cluster
            project_name: name of the project with which the cluster is associated
            tenant_name: name of the tenant under which the cluster 
                         is to be created
        Returns:
            Created cluster details in JSON response payload
        '''

        from tenant import Tenant
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e

        cluster_already_exists = True

        try:
            if(not tenant_name):
                tenant_name = ""
            self.cluster_query(tenant_name + "/" + name)
        except SOSError as e:
            if (e.err_code == SOSError.NOT_FOUND_ERR):
                cluster_already_exists = False
            else:
                raise e

        if (cluster_already_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Cluster with name: " + name + 
                           " already exists")

        createParams = dict()
        createParams['name'] = name
        if (project_name):
            from project import Project
            project_obj = Project(self.__ipAddr, self.__port)
            try:
                project_uri = project_obj.project_query(project_name)
            except SOSError as e:
                raise e
            createParams['project'] = project_uri
        body = json.dumps(createParams)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Cluster.URI_TENANT_CLUSTERS.format(tenant_uri), body)
        o = common.json_decode(s)
        return o
    

    def cluster_list(self, tenant_name):
        '''
        Makes REST API call and retrieves clusters based on tenant UUID
        Parameters: None
        Returns:
            List of cluster UUIDs in JSON response payload 
        '''
        from tenant import Tenant
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Cluster.URI_TENANT_CLUSTERS.format(tenant_uri), None)
        o = common.json_decode(s)
        
        if('cluster' in o):        
            return common.get_list(o, 'cluster')
        return []
        

    def cluster_show_by_uri(self, uri, xml=False):
        '''
        Makes REST API call and retrieves cluster derails based on UUID
        Parameters:
            uri: UUID of the cluster
        Returns:
            Cluster details in JSON response payload
        '''
        if (xml):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Cluster.URI_CLUSTER.format(uri), None, None, xml)
            return s
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Cluster.URI_CLUSTER.format(uri), None)
        o = common.json_decode(s)
        inactive = common.get_node_value(o, 'inactive')
        if (inactive == True):
            return None
        
        return o
        

    def cluster_show(self, name, xml=False):
        '''
        Retrieves cluster details based on cluster name
        Parameters:
            name: name of the cluster
        Returns:
            Cluster details in JSON response payload
        '''
        cluster_uri = self.cluster_query(name)
        cluster_detail = self.cluster_show_by_uri(cluster_uri, xml)
        return cluster_detail


    def cluster_query(self, name):
        '''
        Retrieves UUID of cluster based on its name
        Parameters:
            name: name of cluster
        Returns: UUID of cluster
        Throws:
            SOSError - when cluster name is not found 
        '''
        if (common.is_uri(name)):
            return name
        (tenant_name, cluster_name) = common.get_parent_child_from_xpath(name)
        
        from tenant import Tenant
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
            clusters = self.cluster_list(tenant_uri)
            if(clusters and len(clusters) > 0):
                for cluster in clusters:
                    if (cluster):
                        cluster_detail = self.cluster_show_by_uri(cluster['id'])
                        if(cluster_detail and cluster_detail['name'] == cluster_name):
                            return cluster_detail['id']
            raise SOSError(SOSError.NOT_FOUND_ERR, 'Cluster: ' + cluster_name + ' not found')
        except SOSError as e:
            raise e
        

    def cluster_delete_by_uri(self, uri):
        '''
        Deletes a cluster based on cluster UUID
        Parameters:
            uri: UUID of cluster
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST", Cluster.URI_CLUSTER_DEACTIVATE.format(uri), None)
        return


    def cluster_delete(self, name):
        '''
        Deletes a cluster based on cluster name
        Parameters:
            name: name of cluster
        '''
        cluster_uri = self.cluster_query(name)
        return self.cluster_delete_by_uri(cluster_uri)


def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Cluster Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a cluster')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of Cluster',
                                required=True)
    create_parser.add_argument('-pr', '-project',
                                metavar='<project>',
                                dest='projectname',
                                help='Name of Project')
    create_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenantname',
                                help='Name of Tenant (default: Provider Tenant)')
    create_parser.set_defaults(func=cluster_create)


def cluster_create(args):
    obj = Cluster(args.ip, args.port)
    try:
        obj.cluster_create(args.name, args.projectname, args.tenantname)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code,
                           "Cluster create failed: " + e.err_text)
        else:
            raise e


def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR Cluster Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a cluster')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of Cluster',
                                required=True)
    delete_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenant',
                                help='Name of tenant')
    delete_parser.set_defaults(func=cluster_delete)


def cluster_delete(args):
    obj = Cluster(args.ip, args.port)
    try:
        if(not args.tenant):
            args.tenant=""
        obj.cluster_delete(args.tenant + "/" + args.name)

    except SOSError as e:
        if (e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Cluster delete failed: " + e.err_text)
        else:
            raise e


# show command parser
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Cluster Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show cluster details')
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of cluster',
                                required=True)
    show_parser.add_argument('-tn', '-tenant',
                                metavar='tenant',
                                dest='tenant',
                                help='Name of tenant')
    show_parser.set_defaults(func=cluster_show)


def cluster_show(args):
    obj = Cluster(args.ip, args.port)
    try:
        if(not args.tenant):
            args.tenant=""
        res = obj.cluster_show(args.tenant + "/" + args.name, args.xml)
        if(res):
            if (args.xml == True):
                return common.format_xml(res)
            return common.format_json_object(res)
    except SOSError as e:
        raise e
        

# list command parser
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='ViPR Cluster List CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists clusters under a tenant')
    list_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             help='List clusters with details',
                             action='store_true')
    list_parser.add_argument('-l', '-long',
                             dest='largetable',
                             help='List clusters in table format',
                             action='store_true')
    #mandatory_args = list_parser.add_argument_group('mandatory arguments')
    list_parser.add_argument('-tn', '-tenant',
                                metavar='<tenant>',
                                dest='tenantname',
                                help='Name of tenant')
    list_parser.set_defaults(func=cluster_list)


def cluster_list(args):
    obj = Cluster(args.ip, args.port)
    try:
        from common import TableGenerator
        clusters = obj.cluster_list(args.tenantname)
        records = []
        for cluster in clusters:
            proj_detail = obj.cluster_show_by_uri(cluster['id'])
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
    

# Cluster Main parser routine
def cluster_parser(parent_subparser, common_parser):
    # main cluster parser

    parser = parent_subparser.add_parser('cluster',
                                description='ViPR Cluster CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Cluster')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)


#!/usr/bin/python

# Copyright (c) 2012 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


#import python system modules

import common
import argparse
import sys
import os
from common import SOSError
from neighborhood import Neighborhood
from storagepool import StoragePool
from storagesystem import StorageSystem
import json
from tenant import Tenant

class Cos(object):
    '''
    The class definition for operations on 'Class of Service'. 
    '''
    
    URI_COS             = "/{0}/cos"
    URI_COS_SHOW        = URI_COS + "/{1}"
    URI_COS_STORAGEPOOL = URI_COS_SHOW + "/storage-pools"
    URI_COS_ACL         = URI_COS_SHOW + "/acl"
    URI_TENANT          = '/tenants/{0}'
    URI_COS_DEACTIVATE  = URI_COS_SHOW + '/deactivate'
    URI_COS_REFRESH_POOLS = URI_COS_SHOW + "/refresh-matched-pools"
    URI_COS_ASSIGN_POOLS  = URI_COS_SHOW + "/assign-matched-pools"
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    def cos_list_uris(self, type):
        '''
        This function will give us the list of COS uris
        separated by comma.
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "GET", self.URI_COS.format(type), None)
        
        o = common.json_decode(s)
        return o['cos']

    def cos_list(self, type):
        '''
        this function is wrapper to the cos_list_uris
        to give the list of cos uris.
        '''
        uris = self.cos_list_uris(type)
        return uris
        
    def cos_show_uri(self, type, uri, xml=False):
        '''
        This function will take uri as input and returns with 
        all parameters of COS like lable, urn and type.
        parameters
            uri : unique resource identifier.
        return
            returns with object contain all details of CoS.
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "GET", 
                                             self.URI_COS_SHOW.format(type, uri), None, None)
        
        o = common.json_decode(s)
        if( o['inactive']):
            return None
        
        if(xml == False):
            return o
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_COS_SHOW.format(type, uri), None, None, xml)
        return s
     
    def cos_show(self, name, type, xml=False):
        '''
        This function is wrapper to  with cos_show_uri. 
        It will take cos name as input and do query for uri,
        and displays the details of given cos name.
        parameters
            name : Name of the CoS.
            type : Type of the CoS { 'file', 'block' or 'object'}
        return
            returns with object contain all details of COS.
        '''
        uri = self.cos_query(name, type)
        cos = self.cos_show_uri(type, uri, xml)
        return cos
  
    def cos_list_by_hrefs(self, hrefs):
        res =  common.list_by_hrefs(self.__ipAddr, self.__port, hrefs) 
        return res



    def cos_get_tenant(self, type, cosuri):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_COS_ACL.format(type, cosuri), None, None)
        o = common.json_decode(s)
        tenantids=[]
        acls = common.get_node_value(o, "acl")
        for acl in acls:
            tenantids.append(acl['tenant'])

	return tenantids
        
    def cos_get_tenant_name(self, tenanturi):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_TENANT.format(tenanturi), None, None)
        o = common.json_decode(s)
        return o['name']


    def cos_allow_tenant(self, name, type, tenant):
        '''
        This function is allow given cos to use by given tenant.
        It will take cos name, tenant  as inputs and do query for uris.
        parameters
            name : Name of the CoS.
            type : Type of the CoS { 'file' or 'block' }
            tenant : Name of the tenant
        '''
        uri = self.cos_query(name, type)
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)
        parms = {
            'add':[{
                'privilege': ['USE'],
                'tenant': tenanturi, 
                }]
            }

        body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             self.URI_COS_ACL.format(type, uri), body)
        return s
    
    def cos_remove_tenant(self, name, type, tenant):
        '''
        This function is dis-allow given cos to use by given tenant.
        It will take cos name, tenant  as inputs and do query for uris.
        parameters
            name : Name of the CoS.
            type : Type of the CoS { 'file' or 'block' }
            tenant : Name of the tenant
        '''
        uri = self.cos_query(name, type)
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)
        parms = {
            'remove':[{
                'privilege': ['USE'],
                'tenant': tenanturi,
                }]
            }

        body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             self.URI_COS_ACL.format(type, uri), body)
        return s  

    def cos_getpools(self, name, type):
        '''
        This function will Returns list of computed id's for all 
        storage pools matching with the CoS.
        This list of pools will be used to do create Volumes.
        parameters
             Name : Name of CoS.
             type : type of CoS.
        return
            Returns list of computed id's for all
            storage pools matching with the CoS.
        '''
        uri = self.cos_query(name, type)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_COS_STORAGEPOOL.format(type, uri), None, None)

        o = common.json_decode(s)
        output = common.list_by_hrefs(self.__ipAddr, self.__port, 
                                      common.get_node_value(o, "storage_pool"))
        return output
 
    def cos_refreshpools(self, name, type):
        '''
        This method re-computes the matched pools for this CoS and returns this information.
        This list of pools will be used to do create Volumes.
        parameters
             Name : Name of CoS.
             type : type of CoS.
        '''
        uri = self.cos_query(name, type)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_COS_REFRESH_POOLS.format(type, uri), None, None)

        o = common.json_decode(s)
        output = common.list_by_hrefs(self.__ipAddr, self.__port,
                                      common.get_node_value(o, "storage_pool"))
        return output
 
    def cos_addpools(self, name, type, pools, serialno, devicetype):
        '''
        This method allows a user to update assigned matched pools.
        This list of pools will be used to do create Volumes.
        parameters
             Name : Name of CoS.
             type : type of CoS.
             pools: Storage pools to be added to CoS.          
        '''
        poolidlist = []
        spobj = StoragePool(self.__ipAddr, self.__port)        
        for pname in pools:
            (sid, pid) = spobj.storagepool_query(pname, None, serialno, devicetype)
            poolidlist.append(pid)
        
        #Get the existing assigned pools, so that this call wont overwrite. 
        uri = self.cos_query(name, type)
        cos = self.cos_show_uri(type, uri)
        if(cos and 'assigned_storage_pools' in cos ) :
            for matpool in cos['assigned_storage_pools']:
                poolidlist.append(matpool['id'])
 
        parms = {'assigned_pool_changes':
                    {'add': {
                     'storage_pool': poolidlist}}}

        body = json.dumps(parms)
        uri = self.cos_query(name, type)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "PUT",
                                             self.URI_COS_ASSIGN_POOLS.format(type, uri), body, None)

        o = common.json_decode(s)
        return o
    
    def cos_removepools(self, name, type, pools, serialno, devicetype):
        '''
        This method allows a user to update assigned matched pools.
        This list of pools will be used to do create Volumes.
        parameters
             Name : Name of CoS.
             type : type of CoS.
             pools: Storage pools to be added to CoS.
        '''
        poolidlist = []
        spobj = StoragePool(self.__ipAddr, self.__port)

        for pname in pools:
            (sid, pid) = spobj.storagepool_query(pname, None, serialno, devicetype)
            poolidlist.append(pid)

        parms = {'assigned_pool_changes':
                         {'remove': {
                           'storage_pool': poolidlist}}}

        body = json.dumps(parms)
        uri = self.cos_query(name, type)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "PUT",
                                             self.URI_COS_ASSIGN_POOLS.format(type, uri), body, None)

        o = common.json_decode(s)
        return o
 
    def cos_create(self, name, description,  type, protocols, 
                   multipaths, neighborhoods, provisiontype, protection,
                   systemtype, raidlevel, fastpolicy, drivetype, expandable):
        '''
        This is the function will create the COS with given name and type.
        It will send REST API request to StorageOS instance.
        parameters:
            name : Name of the CoS.
            type : Type of the CoS { 'file', 'block' or 'object'}
        return
            returns with COS object with all details.
        '''
        # check for existance of cos.
        try:
            status = self.cos_show(name, type)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                parms = dict()
                if (name):
                    parms['name'] = name
                if (description):
                    parms['description'] = description
                if (protocols):
                    parms['protocols'] = protocols
                if (multipaths):
                    parms['num_paths'] = multipaths
                if(type == 'block' and provisiontype == None):
                    raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS create error: argument -provisiontype/-pt is required")
                if(provisiontype):
                    pt = None
                    if( provisiontype.upper() == 'THICK'):
                        pt = 'Thick'
                    elif ( provisiontype.upper() == 'THIN'):
                        pt = 'Thin'
                    else:
                        raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS create error: Invalid provisiontype: " + provisiontype)
                    parms['provisioning_type'] = pt    
                if(neighborhoods):
                    urilist = []
                    nh_obj = Neighborhood(self.__ipAddr, self.__port)
                    for neighborhood in neighborhoods:
                        nhuri = nh_obj.neighborhood_query(neighborhood)
                        urilist.append(nhuri)
                    parms['neighborhoods'] = urilist
                if(protection):
                    mirval = None
                    contval = None
                    for mapentry in protection:
                        (name, value) = mapentry.split('=', 1)
                        if(name == 'mirror'):
                            mirval = value
                        elif (name == 'continuous'):
                            contval = value
                        else:
                            raise SOSError(SOSError.VALUE_ERR, "CoS create error: Invalid argument " + 
                                           "'" + str(mapentry) + "'" + " for protection ")
                    parms['protection'] = { 'mirror': mirval, 'continuous': contval}

                if(systemtype):
                    parms['system_type'] = systemtype
                if(raidlevel):
                    if(systemtype == None):
                        raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS create error: argument -systemtype/-st is required ")
                    parms['raid_levels'] = raidlevel
                if(fastpolicy):
                    parms['auto_tiering_policy_name'] = fastpolicy
                if(drivetype):
                    parms['drive_type'] = drivetype 
                
                if(expandable):
                    parms['expandable'] = expandable
                  
                body = json.dumps(parms)
                
                (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST", self.URI_COS.format(type), body)
                o = common.json_decode(s)
                return o
            else:
                raise e
        if(status):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "CoS with name " + name + " ("+ type + ") " + "already exists")

    
    def cos_update(self, name, description,  type, protocol_add, protocol_remove, 
                   neighborhood_add, neighborhood_remove, multipaths, use_matched_pools):
        '''
        This is the function will update the COS.
        It will send REST API request to StorageOS instance.
        parameters:
            name : Name of the CoS.
            type : Type of the CoS { 'file', 'block' or 'object'}
            desc : Description of CoS
            protocol_add : Protocols to be added
            protocol_remove : Protocols to be removed
            neighborhood_add: Neighborhood to  be added
            neighborhood_remove : Neighborhoods to be removed
            multipaths: No of multi paths
        return
            returns with COS object with all details.
        '''
        # check for existance of cos.
        cosuri = self.cos_query(name, type)
        parms = dict()
        if (description):
            parms['description'] = description
        if (protocol_add):
            protocollist = []
            cos = self.cos_show_uri(type, cosuri)
            if( cos != None):
                protocollist = cos['protocols']
                for protocol in protocol_add:
                    if( not  protocol in protocollist):
                        protocollist.append(protocol)
            parms['protocol_changes'] = { 'add' : { 'protocol': protocollist } }

        if (protocol_remove):
            cos = self.cos_show_uri(type, cosuri)
            if( cos != None):
                protocollist = cos['protocols']
                for protocol in protocol_remove:
                    if( not  protocol in protocollist):
                        raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS update error: Invalid protocol (" + protocol + ") to remove: " )

            parms['protocol_changes'] = { 'remove' : { 'protocol': protocol_remove } }
        
        nhobj = Neighborhood(self.__ipAddr, self.__port)
        neighborhoods = neighborhood_add
        if( neighborhoods == None):
            neighborhoods = neighborhood_remove
        nhurilist = []
        if( neighborhoods != None):
            for neighborhood in neighborhoods:
                nhurilist.append(nhobj.neighborhood_query(neighborhood))
        
        if (neighborhood_add):
            parms['neighborhood_changes'] = { 'add' : { 'neighborhood': nhurilist } }

        if (neighborhood_remove):
            parms['neighborhood_changes'] = { 'add' : { 'neighborhood': nhurilist } }

        if (multipaths):
            parms['num_paths'] = multipaths

        if ( use_matched_pools != None):
            parms['use_matched_pools'] = use_matched_pools


        body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                            "PUT", self.URI_COS_SHOW.format(type, cosuri), body)
        o = common.json_decode(s)
        return o

    def cos_delete_uri(self, type, uri):
        '''
        This function will take uri as input and deletes that particular COS
        from StorageOS database.
        parameters:
            uri : unique resource identifier for given COS name.
        return
            return with status of the delete operation.
            false incase it fails to do delete.
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "POST", 
                                             self.URI_COS_DEACTIVATE.format(type, uri), 
                                             None)
        return str(s) + " ++ " + str(h)
    
    def cos_delete(self, name, type):
        uri = self.cos_query(name, type)
        res = self.cos_delete_uri(type, uri)
        return res  
   
  
    def cos_query(self, name, type):
        '''
        This function will take the CoS name and type of CoS
        as input and get uri of the first occurance of given CoS.
        paramters:
             name : Name of the CoS.
             type : Type of the CoS { 'file', 'block' or 'object'}
        return
            return with uri of the given cos.
        '''
        if (common.is_uri(name)):
            return name

        uris = self.cos_list_uris(type)
        for uri in uris:
            cos = common.show_by_href(self.__ipAddr, self.__port, uri)
	    if(cos):
                if (cos['name'] == name):
                    return cos['id']    
        raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS " + name + 
		      " ("+ type + ") " + ": not found")
       

    
# COS Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                description='StorageOS CoS Create cli usage',
                parents=[common_parser],
                conflict_handler='resolve',
		help='Create a CoS')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='Name of CoS',
                metavar='<cosname>',
                dest='name',
                required=True)
    mandatory_args.add_argument('-protocol','-pl',
                help='Protocol used {NFS,CIFS for file; FC, iSCSI for block',
                metavar='<protocol>',
                dest='protocol',
                nargs='+',
                required=True)
    create_parser.add_argument('-neighborhoods','-nh',
                help='neighborhoods',
                metavar='<neighborhoods>',
                dest='neighborhoods',
                nargs='+' )
    create_parser.add_argument('-multipaths','-mp',
                help='Multipaths',
                metavar='<multipaths>',
                dest='multipaths')
    create_parser.add_argument('-provisiontype','-pt',
                help='Provision type Values can be Thin or Thick(mandatory for block CoS)',
                metavar='<provisiontype>',
                dest='provisiontype')
    create_parser.add_argument('-protection','-prot',
                help='Protection values can be mirror=value1 continuous=value2',
                metavar='<protection>',
                nargs='+',
                dest='protection')
    create_parser.add_argument('-systemtype','-st',
                help='Supported System Types',
                metavar='<systemtype>',
                choices=StorageSystem.SYSTEM_TYPE_LIST,
                dest='systemtype')

    create_parser.add_argument('-raidlevel','-rl',
                help='Posible values RAID1, RAID2, RAID3, RAID4, RAID5, RAID6, RAID10',
                metavar='<raidlevel>',
                nargs='+',
                dest='raidlevel')
    create_parser.add_argument('-fastpolicy','-fp',
                help='AutoTiering Policy Name can be specified, only if SystemType is specified',
                metavar='<fastpolicy>',
                dest='fastpolicy')

    create_parser.add_argument('-drivetype','-dt',
                help='Supported Drive Types',
                metavar='<drivetype>',
                choices=['SSD', 'FC', 'SAS', 'NL_SAS', 'SATA', 'HARD_DISK_DRIVE'], 
                dest='drivetype')

    create_parser.add_argument('-usematchedpools','-ump',
                help='CoS uses matched pools',
                metavar='<useMatchedPools>',
                dest='usematchedpools',
                choices=['true', 'false', 'True', 'False', 'TRUE', 'FALSE'] )
    create_parser.add_argument( '-type', '-t',
                                help='Type of the CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])   
    create_parser.add_argument( '-description', '-desc',
                                help='Description of CoS',
                                dest='description',
                                metavar='<description>')
    create_parser.add_argument('-expandable','-ex',
                               help='Indicates if non disruptive volume expansion should be supported',
                               dest='expandable',
                               action='store_true') 

    create_parser.set_defaults(func=cos_create)

def cos_create(args):
    try:
        obj = Cos(args.ip, args.port)
        res = obj.cos_create(args.name, 
                             args.description,
                             args.type,
                             args.protocol,
                             args.multipaths,
                             args.neighborhoods,
                             args.provisiontype,
                             args.protection,
                             args.systemtype,
                             args.raidlevel,
                             args.fastpolicy,
                             args.drivetype,
                             args.expandable )
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS " + args.name + 
 			  " ("+ args.type + ") " + ": Create failed\n" + e.err_text )
        else:
            raise e
        
# COS Update routines

def update_parser(subcommand_parsers, common_parser):
    # create command parser
    update_parser = subcommand_parsers.add_parser('update',
                description='StorageOS CoS Update cli usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Update a CoS')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='Name of CoS',
                metavar='<cosname>',
                dest='name',
                required=True)
    
    protocol_exclgroup = update_parser.add_mutually_exclusive_group(required=False)
    protocol_exclgroup.add_argument('-protocol_add', '-pa',
                                help='Protocol to be added to CoS',
                                dest='protocol_add',
                                nargs='+',
                                metavar='<protocol_add>')
    protocol_exclgroup.add_argument('-protocol_remove', '-prm',
                                metavar="<protocol_remove>",
                                help='Protocol to be removed from CoS',
                                nargs='+',
                                dest='protocol_remove')

    nh_exclgroup = update_parser.add_mutually_exclusive_group(required=False)
    nh_exclgroup.add_argument('-neighborhood_add', '-nh_add',
                                help='Neighborhood to be added to CoS',
                                dest='neighborhood_add',
                                nargs='+',
                                metavar='<neighborhood_add>')
    nh_exclgroup.add_argument('-neighborhood_remove', '-nh_rm',
                                metavar="<neighborhood_remove>",
                                help='Neighborhood to be removed from CoS',
                                nargs='+',
                                dest='neighborhood_remove')

    update_parser.add_argument('-usematchedpools','-ump',
                help='CoS uses matched pools',
                metavar='<useMatchedPools>',
                dest='usematchedpools',
                choices=['true', 'false', 'True', 'False', 'TRUE', 'FALSE'] )
    update_parser.add_argument('-multipaths','-mp',
                help='Multipaths',
                metavar='<multipaths>',
                dest='multipaths')
    update_parser.add_argument( '-type', '-t',
                                help='Type of the CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    update_parser.add_argument( '-description', '-desc',
                                help='Description of CoS',
                                dest='description',
                                metavar='<description>')

    update_parser.set_defaults(func=cos_update)

def cos_update(args):
    try:
        obj = Cos(args.ip, args.port)
        res = obj.cos_update(args.name,
                             args.description,
                             args.type,
                             args.protocol_add,
                             args.protocol_remove,
                             args.neighborhood_add,
                             args.neighborhood_remove,
                             args.multipaths,
                             args.usematchedpools)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS " + args.name +
                          " ("+ args.type + ") " + ": Update failed\n" + e.err_text )
        else:
            raise e


# COS Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                description='StorageOS CoS Delete CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
		help='Delete a CoS')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    delete_parser.add_argument('-type','-t',
                                help='Type of the CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    delete_parser.set_defaults(func=cos_delete)

def cos_delete(args):
    obj = Cos(args.ip, args.port)
    try:
        obj.cos_delete(args.name, args.type)
       # return "CoS " + args.name + " of type " + args.type + ": Deleted"
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS " + args.name + 
                          " ("+ args.type + ") " + ": Delete failed\n"  + e.err_text)
        else:
            raise e
        

# COS Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                description='StorageOS CoS Show CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
		help='Show details of a CoS')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    show_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')
    show_parser.set_defaults(func=cos_show)

def cos_show(args):
    
    obj = Cos(args.ip, args.port)
    try:
        res = obj.cos_show(args.name, args.type, args.xml)
        if(args.xml):
            return common.format_xml(res)
        return common.format_json_object(res)
    except SOSError as e:
        raise e


# COS get pools routines

def getpools_parser(subcommand_parsers, common_parser):
    # show command parser
    getpools_parser = subcommand_parsers.add_parser('get_pools',
                description='StorageOS CoS Get storage pools CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Get the storage pools of a CoS')
    mandatory_args = getpools_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    getpools_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    getpools_parser.set_defaults(func=cos_getpools)

def cos_getpools(args):

    obj = Cos(args.ip, args.port)
    try:
        pools = obj.cos_getpools(args.name, args.type)
        if(len(pools) > 0):
            for pool in pools:
                ssobj = StorageSystem(args.ip, args.port)
                storagesys = ssobj.show_by_uri(pool['storage_system']['id'])
                pool['storagesystem_guid'] = storagesys['native_guid']
            from common import TableGenerator
            TableGenerator(pools, ['pool_name','supported_volume_types','operational_status','storagesystem_guid']).printTable() 
    except SOSError as e:
        raise e

# COS refresh pools routines

def refreshpools_parser(subcommand_parsers, common_parser):
    # show command parser
    refreshpools_parser = subcommand_parsers.add_parser('refresh_pools',
                description='StorageOS CoS refresh  storage pools CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Refresh assigned matched storage pools of a CoS')
    mandatory_args = refreshpools_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    refreshpools_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    refreshpools_parser.set_defaults(func=cos_refreshpools)

def cos_refreshpools(args):

    obj = Cos(args.ip, args.port)
    try:
        pools = obj.cos_refreshpools(args.name, args.type)
        if(len(pools) > 0):
            for pool in pools:
                ssobj = StorageSystem(args.ip, args.port)
                storagesys = ssobj.show_by_uri(pool['storage_system']['id'])
                pool['storagesystem_guid'] = storagesys['native_guid'] 
            from common import TableGenerator
            TableGenerator(pools, ['pool_name','supported_volume_types','operational_status','storagesystem_guid']).printTable()
    except SOSError as e:
        raise e

# COS add pools routines

def addpools_parser(subcommand_parsers, common_parser):
    # show command parser
    addpools_parser = subcommand_parsers.add_parser('add_pools',
                description='StorageOS CoS add  storage pools CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add assinged  storage pools of a CoS')
    mandatory_args = addpools_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    mandatory_args.add_argument('-pools',
                help='Pools to be added',
                dest='pools',
                metavar='<pools>',
                nargs='+',
                required=True)
    addpools_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    mandatory_args.add_argument('-serialnumber','-sn',
                help='Native GUID of Storage System',
                metavar='<serialnumber>',
                dest='serialnumber',
                required=True)
    mandatory_args.add_argument('-devicetype','-dt',
                                help = 'device type',
                                dest='devicetype',
                                choices=StorageSystem.SYSTEM_TYPE_LIST,
                                required=True)
    addpools_parser.set_defaults(func=cos_addpools)

def cos_addpools(args):

    obj = Cos(args.ip, args.port)
    try:
        res = obj.cos_addpools(args.name, args.type, 
                               args.pools, args.serialnumber, 
                               args.devicetype)
        #return common.format_json_object(res)
    except SOSError as e:
        raise e

# COS remove pools routines

def removepools_parser(subcommand_parsers, common_parser):
    # show command parser
    removepools_parser = subcommand_parsers.add_parser('remove_pools',
                description='StorageOS CoS remove  storage pools CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove assinged  storage pools of a CoS')
    mandatory_args = removepools_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    mandatory_args.add_argument('-pools',
                help='Pools to be added',
                dest='pools',
                metavar='<pools>',
                nargs='+',
                required=True)
    removepools_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    mandatory_args.add_argument('-serialnumber','-sn',
                help='Native GUID of Storage System',
                metavar='<serialnumber>',
                dest='serialnumber',
                required=True)
    mandatory_args.add_argument('-devicetype','-dt',
                                help = 'device type',
                                dest='devicetype',
                                choices=['isilon', 'vnxblock', 'vnxfile', 'vmax'],
                                required=True)
    removepools_parser.set_defaults(func=cos_removepools)

def cos_removepools(args):

    obj = Cos(args.ip, args.port)
    try:
        res = obj.cos_removepools(args.name, args.type, 
                                  args.pools, args.serialnumber,
                                  args.devicetype)
        #return common.format_json_object(res)
    except SOSError as e:
        raise e





# COS allow tenant  routines

def allow_parser(subcommand_parsers, common_parser):
    # allow tenant command parser
    allow_parser = subcommand_parsers.add_parser('allow',
                description='StorageOS CoS Allow Tenant CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Allow Tenant to use a CoS')
    mandatory_args = allow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    allow_parser.add_argument('-tenant', '-tn',
                               dest='tenant',
                               metavar='<tenant>',
                               help='Name of the Tenant')

    allow_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    allow_parser.set_defaults(func=cos_allow_tenant)

def cos_allow_tenant(args):

    obj = Cos(args.ip, args.port)
    try:
        res = obj.cos_allow_tenant(args.name, args.type, args.tenant)
    except SOSError as e:
        raise e


# COS remove tenant  routines

def disallow_parser(subcommand_parsers, common_parser):
    # allow tenant command parser
    allow_parser = subcommand_parsers.add_parser('disallow',
                description='StorageOS CoS disallow  Tenant CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove Tenant to use a CoS')
    mandatory_args = allow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name','-n',
                help='name of CoS',
                dest='name',
                metavar='<cosname>',
                required=True)
    allow_parser.add_argument('-tenant', '-tn',
                               dest='tenant',
                               metavar='<tenant>',
                               help='Name of the Tenant')

    allow_parser.add_argument('-type','-t',
                                help='Type of CoS (default:file)',
                                default='file',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    allow_parser.set_defaults(func=cos_remove_tenant)

def cos_remove_tenant(args):

    obj = Cos(args.ip, args.port)
    try:
        res = obj.cos_remove_tenant(args.name, args.type, args.tenant)
    except SOSError as e:
        raise e


# COS List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                description='StorageOS CoS List CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
		help='List Classes of Service')
    list_parser.add_argument('-type','-t',
                                help='Type of CoS',
                                dest='type',
                                metavar='<costype>',
                                choices=['file', 'block', 'object'])
    list_parser.add_argument('-v', '-verbose',
                                dest='verbose',
                                help='List CoS with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List CoS with details in table format',
                             dest='long')
    list_parser.set_defaults(func=cos_list)

def cos_list(args):
    obj = Cos(args.ip, args.port)
    try:
        if(args.type): 
            types = [ args.type ]
        else:
            types = [ 'block', 'file'] 

        output = []
        for type in types:
            uris = obj.cos_list(type)
            if(len(uris) > 0):
                for item in obj.cos_list_by_hrefs(uris):
                    tenanturis = obj.cos_get_tenant(type, item['id'])
                    if(tenanturis):
                        tenantlist = []
                        for tenanturi in tenanturis:
                            tenantname = obj.cos_get_tenant_name(tenanturi)
                            tenantlist.append(tenantname) 
                        item['tenants_allowed']=tenantlist  
                    output.append(item);
        if(len(output) > 0):
            if(args.verbose == True):
                return common.format_json_object(output)
            if(args.long == True):
                from common import TableGenerator
                TableGenerator(output, ['name', 'type', 'protocols', 'tenants_allowed', 'num_paths', 
                                       'provisioning_type', 'continuous', 'mirror' ]).printTable()
            
	    else:
	        from common import TableGenerator
                TableGenerator(output, ['name', 'type', 'protocols', 'tenants_allowed']).printTable()
            
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "CoS list failed\n"  + e.err_text)
        else:
            raise e
      
#
# Cos Main parser routine
#

def cos_parser(parent_subparser, common_parser):

    # main cos parser
    parser = parent_subparser.add_parser('cos',
                description='StorageOS CoS cli usage',
                parents=[common_parser],
                conflict_handler='resolve',
		help='Operations on CoS')
    subcommand_parsers = parser.add_subparsers(help='Use one of commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # allow tenant command parser
    allow_parser(subcommand_parsers, common_parser)

    # remove tenant command parser
    disallow_parser(subcommand_parsers, common_parser)

    # remove tenant command parser
    update_parser(subcommand_parsers, common_parser)

    # remove tenant command parser
    getpools_parser(subcommand_parsers, common_parser)
 
    # remove tenant command parser
    refreshpools_parser(subcommand_parsers, common_parser)

    # remove tenant command parser
    addpools_parser(subcommand_parsers, common_parser)

    # remove tenant command parser
    removepools_parser(subcommand_parsers, common_parser)


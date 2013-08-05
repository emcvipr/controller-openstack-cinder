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

from common import SOSError

class VirtualArray(object):
    '''
    The class definition for operations on 'VirtualArray'. 
    '''

    #Commonly used URIs for the 'varrays' module
    URI_VIRTUALARRAY = '/vdc/varrays'
    URI_VIRTUALARRAY_URI = '/vdc/varrays/{0}'
    URI_VIRTUALARRAY_ACLS = URI_VIRTUALARRAY_URI + '/acl'
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'
    URI_AUTO_TIER_POLICY = "/vdc/varrays/{0}/auto-tier-policies"

    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
    def get_autotier_policy_by_uri(self, nhuri):
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port ,"GET", 
                         VirtualArray.URI_AUTO_TIER_POLICY.format(nhuri), None)
        o = common.json_decode(s)
	return o["auto_tier_policy"]
         
       
        
    def varray_query(self, name):
        '''
        Returns the UID of the varray specified by the name
        '''
        if (common.is_uri(name)):
            return name

        uris = self.varray_list()

        for uri in uris:
            varray = self.varray_show(uri, False) 
	    if(varray):
                if(varray['name'] == name):
                    return varray['id']
    
        raise SOSError(SOSError.NOT_FOUND_ERR, 
                       "varray " + name + ": not found")

        

    def varray_list(self):
        '''
        Returns all the varrays in a vdc
        Parameters:           
        Returns:
                JSON payload of varray list
        '''
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VirtualArray.URI_VIRTUALARRAY, None)

        o = common.json_decode(s)
	
	returnlst = []
	for iter in o['varray']:
	    returnlst.append(iter['id'])

        return returnlst
        #return common.get_object_id(o['varray'])


    def varray_show(self, label, xml=False):
        '''
        Makes a REST API call to retrieve details of a varray  based on its UUID
        '''
        uri = self.varray_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             VirtualArray.URI_VIRTUALARRAY_URI.format(uri),
                                             None, None, xml)

	if(xml==False):
            o = common.json_decode(s)
        
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s
    
        return o


    def varray_get_acl(self, label):
        '''
        Makes a REST API call to retrieve details of a varray  based on its UUID
        '''
        uri = self.varray_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_VIRTUALARRAY_ACLS.format(uri),
                                             None, None, None)

        o = common.json_decode(s)

        return o


    def varray_allow_tenant(self, varray, tenant):
        '''
        Makes a REST API call to retrieve details of a varray  based on its UUID
        '''
        uri = self.varray_query(varray)

	from tenant import Tenant
	tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)

	parms = {
            'add':[{
                'privilege': ['USE'],
                'tenant': tenanturi, 
                }]
            }

        body = json.dumps(parms)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT", 
                                             self.URI_VIRTUALARRAY_ACLS.format(uri),
                                             body)
	
	return s


    def varray_disallow_tenant(self, varray, tenant):
        '''
        Makes a REST API call to retrieve details of a varray  based on its UUID
        '''
        uri = self.varray_query(varray)

	from tenant import Tenant
	tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)

	parms = {
            'remove':[{
                'privilege': ['USE'],
                'tenant': tenanturi, 
                }]
            }

        body = json.dumps(parms)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             self.URI_VIRTUALARRAY_ACLS.format(uri),
                                             body)
	
	return s

    def varray_create(self, label, autosanzoning):
        '''
        creates a varray
        parameters:    
            label:  label of the varray
        Returns:
            JSON payload response
        '''
        try:     
            check = self.varray_show(label)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                var = dict()
                params = dict()
                params['name'] = label
		if(autosanzoning):
		    params['auto_san_zoning'] = autosanzoning

                body = json.dumps(params)
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                                     VirtualArray.URI_VIRTUALARRAY , body)
                o = common.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "varray with name " + label + " already exists")
        

    def varray_update(self, label, autosanzoning):
        '''
        creates a varray
        parameters:    
            label:  label of the varray
        Returns:
            JSON payload response
        '''
	uri = self.varray_query(label)

        var = dict()
        params = dict()
        params['name'] = label
	if(autosanzoning):
	    params['auto_san_zoning'] = autosanzoning

        body = json.dumps(params)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT", 
                                                     VirtualArray.URI_VIRTUALARRAY_URI.format(uri) , body)
        o = common.json_decode(s)
        return o

            


    def varray_delete(self, label):
        '''
        Makes a REST API call to delete a varray by its UUID
        '''
        uri = self.varray_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
					     self.URI_RESOURCE_DEACTIVATE.format(VirtualArray.URI_VIRTUALARRAY_URI.format(uri)),
                                             None)
        return str(s) + " ++ " + str(h)
    
# VIRTUALARRAY Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR varray Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a varray')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of varray',
                                metavar='<varrayname>',
                                dest='name',
                                required=True)

    create_parser.add_argument('-autosanzoning',
                                 help='Boolean to allow automatic SAN zoning',
                                 dest='autosanzoning',
                                 metavar='<autosanzoning>',
				 choices=['true','false'],
				 default='true')

    create_parser.set_defaults(func=varray_create)

def varray_create(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_create(args.name, args.autosanzoning)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "varray " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e


# VIRTUALARRAY Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR varray Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a varray')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)

    delete_parser.set_defaults(func=varray_delete)

def varray_delete(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_delete(args.name)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "VirtualArray delete failed: " + e.err_text)
        else:
            raise e

# VIRTUALARRAY Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR varray Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a varray')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)

    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')

    show_parser.set_defaults(func=varray_show)

def varray_show(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_show(args.name, args.xml)
	if(args.xml):
            return common.format_xml(res)

        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "varray show failed: " + e.err_text)
        else:
            raise e



def allow_parser(subcommand_parsers, common_parser):
    # allow command parser
    allow_parser = subcommand_parsers.add_parser('allow',
                                description='ViPR varray allow tenant CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Allow varray access to a Tenant')

    mandatory_args = allow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)

    
    allow_parser.add_argument('-tenant', '-tn',
                                help='name of Tenant',
                                dest='tenant',
                                metavar='<tenant>')

    allow_parser.set_defaults(func=varray_allow_tenant)



def varray_allow_tenant(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_allow_tenant(args.name, args.tenant)
    except SOSError as e:
            raise e


def disallow_parser(subcommand_parsers, common_parser):
    # disallow command parser
    disallow_parser = subcommand_parsers.add_parser('disallow',
                                description='ViPR varray disallow tenant CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Allow varray access to a Tenant')

    mandatory_args = disallow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)

    
    disallow_parser.add_argument('-tenant', '-tn',
                                help='name of Tenant',
                                dest='tenant',
                                metavar='<tenant>')

    disallow_parser.set_defaults(func=varray_disallow_tenant)



def varray_disallow_tenant(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_disallow_tenant(args.name, args.tenant)
    except SOSError as e:
            raise e

# VIRTUALARRAY Query routines

def query_parser(subcommand_parsers, common_parser):
    # query command parser
    query_parser = subcommand_parsers.add_parser('query',
                                description='ViPR varray Query CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Query a varray')

    mandatory_args = query_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)

    query_parser.set_defaults(func=varray_query)



def varray_query(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_query(args.name)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "varray query failed: " + e.err_text)
        else:
            raise e

# VIRTUALARRAY List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='ViPR varray List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of varrays')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List varrays with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List varrays with more details in tabular form',
                             dest='long')

    list_parser.set_defaults(func=varray_list)

def varray_list(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        uris = obj.varray_list()
        output = []
        outlst = []
        for uri in uris:
	    temp = obj.varray_show(uri)
	    if(temp):
                # add column for auto_tier_policy
                if(args.long):
                    autotierlist = [] 
                    returnlist =  obj.get_autotier_policy_by_uri(uri)
                    # get auto_tier policy object list
                    for item in returnlist:
                        autotierlist.append(item['name'])
                    # append new column 
                    temp["auto_tier_policy"] = autotierlist

                output.append(temp)

        if(len(output) > 0):
            if(args.verbose == True):
		return common.format_json_object(output)
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'name', 'auto_san_zoning', 'auto_tier_policy']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'name']).printTable()

    except SOSError as e:
        raise e


def get_acl_parser(subcommand_parsers, common_parser):
    # list command parser
    get_acl_parser = subcommand_parsers.add_parser('get-acl',
                                                description='ViPR varray Get ACL CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Get ACL of varray')
 
    mandatory_args = get_acl_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',

                                help='name of varray',
                                dest='name',
                                metavar='<varrayname>',
                                required=True)
    get_acl_parser.set_defaults(func=varray_get_acl)


def varray_get_acl(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_get_acl(args.name)

	output = res['acl']
	from tenant import Tenant
	tenant_obj = Tenant(args.ip, args.port)

	for iter in output:
            tenantval =  tenant_obj.tenant_show(iter['tenant'])
	    iter['tenantname'] = tenantval['name']


	from common import TableGenerator
        TableGenerator(output, [ 'tenantname', 'privilege']).printTable()

    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "varray Get ACL failed: " + e.err_text)
        else:
            raise e




def update_parser(subcommand_parsers, common_parser):
    # update command parser
    update_parser = subcommand_parsers.add_parser('update',
                                description='ViPR varray Update CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Update a varray')

    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of varray',
                                metavar='<varrayname>',
                                dest='name',
                                required=True)

    update_parser.add_argument('-autosanzoning',
                                 help='Boolean to allow automatic SAN zoning',
                                 dest='autosanzoning',
                                 metavar='<autosanzoning>',
				 choices=['true','false'],
				 default='true')

    update_parser.set_defaults(func=varray_update)

def varray_update(args):
    obj = VirtualArray(args.ip, args.port)
    try:
        res = obj.varray_update(args.name, args.autosanzoning)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "varray " + 
                           args.name + ": Update failed\n" + e.err_text)
        else:
            raise e

#
# varray Main parser routine
#

def varray_parser(parent_subparser, common_parser):
    # main varray parser
    parser = parent_subparser.add_parser('varray',
                                        description='ViPR varray CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on varray')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # update command parser
    update_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # allow command parser
    allow_parser(subcommand_parsers, common_parser)

    # disallow command parser
    disallow_parser(subcommand_parsers, common_parser)

    # get roles command parser
    get_acl_parser(subcommand_parsers, common_parser)

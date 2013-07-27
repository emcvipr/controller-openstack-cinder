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

class Neighborhood(object):
    '''
    The class definition for operations on 'Neighborhood'. 
    '''

    #Commonly used URIs for the 'Neighborhoods' module
    URI_NEIGHBORHOOD = '/zone/neighborhoods'
    URI_NEIGHBORHOOD_URI = '/zone/neighborhoods/{0}'
    URI_NEIGHBORHOOD_ACLS = URI_NEIGHBORHOOD_URI + '/acl'
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
       
        
    def neighborhood_query(self, name):
        '''
        Returns the UID of the neighborhood specified by the name
        '''
        if (common.is_uri(name)):
            return name

        uris = self.neighborhood_list()

        for uri in uris:
            neighborhood = self.neighborhood_show(uri, False) 
	    if(neighborhood):
                if(neighborhood['name'] == name):
                    return neighborhood['id']
    
        raise SOSError(SOSError.NOT_FOUND_ERR, 
                       "Neighborhood " + name + ": not found")

        

    def neighborhood_list(self):
        '''
        Returns all the neighborhoods in a zone
        Parameters:           
        Returns:
                JSON payload of neighborhood list
        '''
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Neighborhood.URI_NEIGHBORHOOD, None)

        o = common.json_decode(s)
	
	returnlst = []
	for iter in o['neighborhood']:
	    returnlst.append(iter['id'])

        return returnlst
        #return common.get_object_id(o['neighborhood'])


    def neighborhood_show(self, label, xml=False):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Neighborhood.URI_NEIGHBORHOOD_URI.format(uri),
                                             None, None, xml)

	if(xml==False):
            o = common.json_decode(s)
        
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s
    
        return o


    def neighborhood_get_acl(self, label):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_NEIGHBORHOOD_ACLS.format(uri),
                                             None, None, None)

        o = common.json_decode(s)

        return o


    def neighborhood_allow_tenant(self, neighborhood, tenant):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(neighborhood)

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

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             self.URI_NEIGHBORHOOD_ACLS.format(uri),
                                             body)
	
	return s


    def neighborhood_disallow_tenant(self, neighborhood, tenant):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(neighborhood)

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
                                             self.URI_NEIGHBORHOOD_ACLS.format(uri),
                                             body)
	
	return s

    def neighborhood_create(self, label, autosanzoning):
        '''
        creates a neighborhood
        parameters:    
            label:  label of the neighborhood
        Returns:
            JSON payload response
        '''
        try:     
            check = self.neighborhood_show(label)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                var = dict()
                params = dict()
                params['name'] = label
		if(autosanzoning):
		    params['auto_san_zoning'] = autosanzoning

                body = json.dumps(params)
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                                     Neighborhood.URI_NEIGHBORHOOD , body)
                o = common.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "Neighborhood with name " + label + " already exists")
        
            
    def neighborhood_delete(self, label):
        '''
        Makes a REST API call to delete a neighborhood by its UUID
        '''
        uri = self.neighborhood_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
					     self.URI_RESOURCE_DEACTIVATE.format(Neighborhood.URI_NEIGHBORHOOD_URI.format(uri)),
                                             None)
        return str(s) + " ++ " + str(h)
    
# NEIGHBORHOOD Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='StorageOS Neighborhood Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a neighborhood')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of Neighborhood',
                                metavar='neighborhoodname',
                                dest='name',
                                required=True)

    create_parser.add_argument('-autosanzoning',
                                 help='Boolean to allow automatic SAN zoning',
                                 dest='autosanzoning',
                                 metavar='<autosanzoning>',
				 choices=['true','false'],
				 default='true')

    create_parser.set_defaults(func=neighborhood_create)

def neighborhood_create(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_create(args.name, args.autosanzoning)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Neighborhood " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e


# NEIGHBORHOOD Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='StorageOS NeighborhoodDelete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a neighborhood')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)

    delete_parser.set_defaults(func=neighborhood_delete)

def neighborhood_delete(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_delete(args.name)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Neighborhood delete failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='StorageOS Neighborhood Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a Neighborhood')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)

    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')

    show_parser.set_defaults(func=neighborhood_show)

def neighborhood_show(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_show(args.name, args.xml)
	if(args.xml):
            return common.format_xml(res)

        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Neighborhood show failed: " + e.err_text)
        else:
            raise e



def allow_parser(subcommand_parsers, common_parser):
    # allow command parser
    allow_parser = subcommand_parsers.add_parser('allow',
                                description='StorageOS Neighborhood allow tenant CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Allow Neighborhood access to a Tenant')

    mandatory_args = allow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)

    
    allow_parser.add_argument('-tenant', '-tn',
                                help='name of Tenant',
                                dest='tenant',
                                metavar='tenant')

    allow_parser.set_defaults(func=neighborhood_allow_tenant)



def neighborhood_allow_tenant(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_allow_tenant(args.name, args.tenant)
    except SOSError as e:
            raise e


def disallow_parser(subcommand_parsers, common_parser):
    # disallow command parser
    disallow_parser = subcommand_parsers.add_parser('disallow',
                                description='StorageOS Neighborhood disallow tenant CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Allow Neighborhood access to a Tenant')

    mandatory_args = disallow_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)

    
    disallow_parser.add_argument('-tenant', '-tn',
                                help='name of Tenant',
                                dest='tenant',
                                metavar='tenant')

    disallow_parser.set_defaults(func=neighborhood_disallow_tenant)



def neighborhood_disallow_tenant(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_disallow_tenant(args.name, args.tenant)
    except SOSError as e:
            raise e

# NEIGHBORHOOD Query routines

def query_parser(subcommand_parsers, common_parser):
    # query command parser
    query_parser = subcommand_parsers.add_parser('query',
                                description='StorageOS Neighborhood Query CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Query a Neighborhood')

    mandatory_args = query_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)

    query_parser.set_defaults(func=neighborhood_query)



def neighborhood_query(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_query(args.name)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Neighborhood query failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='StorageOS Neighborhood List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of neighborhoods')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List Neighborhoods with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List Neighborhoods with more details in tabular form',
                             dest='long')

    list_parser.set_defaults(func=neighborhood_list)

def neighborhood_list(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        uris = obj.neighborhood_list()
        output = []
        outlst = []
        for uri in uris:
	    temp = obj.neighborhood_show(uri)
	    if(temp):
                output.append(temp)

        if(len(output) > 0):
            if(args.verbose == True):
		return common.format_json_object(output)
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'name', 'auto_san_zoning']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'name']).printTable()

    except SOSError as e:
        raise e


def get_acl_parser(subcommand_parsers, common_parser):
    # list command parser
    get_acl_parser = subcommand_parsers.add_parser('get-acl',
                                                description='StorageOS Neighborhood Get ACL CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Get ACL of neighborhood')
 
    mandatory_args = get_acl_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',

                                help='name of Neighborhood',
                                dest='name',
                                metavar='neighborhoodname',
                                required=True)
    get_acl_parser.set_defaults(func=neighborhood_get_acl)


def neighborhood_get_acl(args):
    obj = Neighborhood(args.ip, args.port)
    try:
        res = obj.neighborhood_get_acl(args.name)

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
                           "Neighborhood Get ACL failed: " + e.err_text)
        else:
            raise e


#
# Neighborhood Main parser routine
#

def neighborhood_parser(parent_subparser, common_parser):
    # main neighborhood parser
    parser = parent_subparser.add_parser('neighborhood',
                                        description='StorageOS Neighborhood CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on Neighborhood')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

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

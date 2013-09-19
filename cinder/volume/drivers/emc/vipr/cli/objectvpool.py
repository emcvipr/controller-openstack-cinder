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

class ObjectVpool(object):
    '''
    The class definition for operations on 'ObjectVpool'. 
    '''

    #Commonly used URIs for the 'objectvpool' module

    URI_SERVICES_BASE               = '' 
    URI_VPOOLS                         = URI_SERVICES_BASE + '/{0}/vpools'
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'
    URI_OBJ_VPOOL                     = URI_SERVICES_BASE + '/{0}/data-services-vpools'
    URI_VPOOL_INSTANCE                = URI_VPOOLS + '/{1}'
    URI_OBJ_VPOOL_INSTANCE            = URI_OBJ_VPOOL + '/{1}'
    URI_VPOOL_ACLS                    = URI_VPOOL_INSTANCE + '/acl'



    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        


    def objectvpool_list(self):
        '''
        Makes a REST API call to retrieve list of objectvpool
        '''
	(s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             ObjectVpool.URI_OBJ_VPOOL.format('object'), None)

	o = common.json_decode(s)

	if (not o):
            return {};
        else:
            return o['data_services_vpool']



    def objectvpool_query(self, name):
	if (common.is_uri(name)):
            return name

	objcoslst = self.objectvpool_list()

	for cs in objcoslst:
	    cos_res = self.objectvpool_show_by_uri(cs['id'])
	    if ( (cos_res['name'] == name) and (cos_res['inactive'] == False) ):
                return cos_res['id']

        raise SOSError(SOSError.NOT_FOUND_ERR,
                      "Object Vpool query failed: object vpool with name "+name+" not found")


    def objectvpool_show_by_uri(self, uri):
	(s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             self.URI_OBJ_VPOOL_INSTANCE.format('object', uri) , None)

	o = common.json_decode(s)
	
	return o

    def objectvpool_show(self, name):
	uri = self.objectvpool_query(name)
	
	return  self.objectvpool_show_by_uri(uri)



    def objectvpool_add(self, name, description ):



	objcoslst = self.objectvpool_list()

	for cs in objcoslst:
	    if( (cs['name'] == name) and (cs['inactive'] == False) ):
                raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                            "ObjectVpool create failed: object vpool with same name already exists")
		
	parms = dict()
        if (name):
            parms['name'] = name
        if (description):
            parms['description'] = description

	body = None

        if (parms):
            body = json.dumps(parms)


        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT , "POST",
                                                     self.URI_OBJ_VPOOL.format('object') , body)
       
	o = common.json_decode(s)

	return o



            
    def objectvpool_delete(self, name):
        '''
        Makes a REST API call to delete a objectvpool by its UUID
        '''
	uri = self.objectvpool_query(name)
        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "POST",
                                             self.URI_OBJ_VPOOL_INSTANCE.format('object', uri) + "/deactivate",
                                             None)

	return str(s) + " ++ " + str(h)
	    

	

    # add command parser
def add_parser(subcommand_parsers, common_parser):
    add_parser = subcommand_parsers.add_parser('create',
                                description='SOS ObjectVpool Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create an objectvpool')

    mandatory_args = add_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name','-n',
                                help='name',
                                metavar='<name>',
                                dest='name',
                                required=True)

    mandatory_args.add_argument('-description','-desc',
                                help='description of object vpool',
                                metavar='<description>',
                                dest='description',
                                required=True)

    add_parser.set_defaults(func=objectvpool_add)

def objectvpool_add(args):
    obj = ObjectVpool(args.ip, args.port)
    try:
        res = obj.objectvpool_add(args.name, args.description)
    except SOSError as e:
        common.format_err_msg_and_raise("add", "object vpool", e.err_text, e.err_code)


# objectvpool Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='SOS ObjectVpool delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete an objectvpool')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name','-n',
                                help='name of object vpool',
                                metavar='<name>',
                                dest='name',
                                required=True)

    delete_parser.set_defaults(func=objectvpool_delete)

def objectvpool_delete(args):
    obj = ObjectVpool(args.ip, args.port)
    try:
        res = obj.objectvpool_delete(args.name)
    except SOSError as e:
	common.format_err_msg_and_raise("delete", "object vpool", e.err_text, e.err_code)


    # show command parser
def show_parser(subcommand_parsers, common_parser):

    show_parser = subcommand_parsers.add_parser('show',
                                description='SOS ObjectVpool show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show an objectvpool')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name','-n',
                                help='name of object vpool',
                                metavar='<name>',
                                dest='name',
                                required=True)

    show_parser.set_defaults(func=objectvpool_show)

def objectvpool_show(args):
    obj = ObjectVpool(args.ip, args.port)
    try:
        res = obj.objectvpool_show(args.name)
	return common.format_json_object(res)
    except SOSError as e:
	common.format_err_msg_and_raise("show", "object vpool", e.err_text, e.err_code)


# list command parser 
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='SOS ObjectVpool List CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='List an ObjectVpool')

    list_parser.set_defaults(func=objectvpool_list)

def objectvpool_list(args):
    obj = ObjectVpool(args.ip, args.port)
    try:
        res = obj.objectvpool_list()

   	output = []

	for iter in res:
	    tmp = dict()
	    tmp['objectvpool']=iter['name']
	    if(iter['inactive']==False):
                output.append(tmp)
	
	if(res):
	    from common import TableGenerator
            TableGenerator(output, [ 'objectvpool']).printTable()

    except SOSError as e:
        common.format_err_msg_and_raise("list", "object vpool", e.err_text, e.err_code)




#
# ObjectVpool Main parser routine
#

def objectvpool_parser(parent_subparser, common_parser):
    # main objectvpool parser
    parser = parent_subparser.add_parser('objectvpool',
                                        description='SOS ObjectVpool CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on ObjectVpool')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # add command parser
    add_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

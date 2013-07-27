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

class Objectuser(object):
    '''
    The class definition for operations on 'Objectuser'. 
    '''

    #Commonly used URIs for the 'objectuser' module

    URI_SERVICES_BASE               = '' 

    URI_WEBSTORAGE_USER             = URI_SERVICES_BASE + '/object/users'
    URI_WEBSTORAGE_USER_DEACTIVATE  = URI_WEBSTORAGE_USER + '/deactivate'


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        


    def objectuser_list(self):
        '''
        Makes a REST API call to retrieve details of a objectuser  based on its UUID
        '''
	uri = self.URI_WEBSTORAGE_USER

	(s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             Objectuser.URI_WEBSTORAGE_USER, None)

	o = common.json_decode(s)

	return o['users_list']


    def objectuser_query(self, uid):
	users = self.objectuser_list()

	for user in users:
	    if(user == uid):
		return user

        raise SOSError(SOSError.NOT_FOUND_ERR,
                      "Object user query failed: object user with name "+uid+" not found")


    def objectuser_add(self, uid, namespace ):

	uri = self.URI_WEBSTORAGE_USER

	users = self.objectuser_list()

	for user in users:
	    if(user == uid):
                raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                            "Objectuser  create failed: object user with same name already exists")
		
	parms = {
                'user': uid,
                'namespace': namespace
                }

	body = None

        if (parms):
            body = json.dumps(parms)


        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT , "POST",
                                                     uri , body)
       
	o = common.json_decode(s)

	return o



            
    def objectuser_delete(self, uid):
        '''
        Makes a REST API call to delete a objectuser by its UUID
        '''
	uri = self.URI_WEBSTORAGE_USER_DEACTIVATE
	
	parms = {
                'user': uid
                }

	body = None

        if (parms):
            body = json.dumps(parms)

        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "POST",
                                             uri,
                                             body)

	return str(s) + " ++ " + str(h)
	    

	

def add_parser(subcommand_parsers, common_parser):
    # add command parser
    add_parser = subcommand_parsers.add_parser('add',
                                description='SOS Objectuser Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create an objectuser')

    mandatory_args = add_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-uid',
                                help='UID',
                                metavar='<uid>',
                                dest='uid',
                                required=True)

    mandatory_args.add_argument('-namespace',
                                help='namespace',
                                metavar='<namespace>',
                                dest='namespace',
                                required=True)

    add_parser.set_defaults(func=objectuser_add)

def objectuser_add(args):
    obj = Objectuser(args.ip, args.port)
    try:
        res = obj.objectuser_add(args.uid, args.namespace)
    except SOSError as e:
        if (e.err_code in [SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Objectuser " + 
                           args.uid + ": Add user failed\n" + e.err_text)
        else:
            raise e


# NEIGHBORHOOD Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='SOS Objectuser delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete an objectuser')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-uid',
                                help='UID',
                                metavar='<uid>',
                                dest='uid',
                                required=True)

    delete_parser.set_defaults(func=objectuser_delete)

def objectuser_delete(args):
    obj = Objectuser(args.ip, args.port)
    try:
        res = obj.objectuser_delete(args.uid)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Objectuser delete failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Show routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                description='SOS Objectuser Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show an Objectuser')

    list_parser.set_defaults(func=objectuser_list)

def objectuser_list(args):
    obj = Objectuser(args.ip, args.port)
    try:
        res = obj.objectuser_list()

   	output = []

	for iter in res:
	    tmp = dict()
	    tmp['name']=iter
            output.append(tmp)
	
	from common import TableGenerator
        TableGenerator(output, [ 'name']).printTable()

    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Objectuser list failed: " + e.err_text)
        else:
            raise e



#
# Objectuser Main parser routine
#

def objectuser_parser(parent_subparser, common_parser):
    # main objectuser parser
    parser = parent_subparser.add_parser('objectuser',
                                        description='SOS Objectuser CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on Objectuser')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # add command parser
    add_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)


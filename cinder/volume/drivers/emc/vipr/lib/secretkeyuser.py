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

class Secretkeyuser(object):
    '''
    The class definition for operations on 'Secretkeyuser'. 
    '''

    #Commonly used URIs for the 'secretkeyuser' module

    URI_SERVICES_BASE               = '' 

    URI_SECRET_KEY                  = URI_SERVICES_BASE + '/object/secret-keys'
    URI_SECRET_KEY_USER             = URI_SERVICES_BASE + '/object/user-secret-keys/{0}'
    URI_DELETE_SECRET_KEY_USER             = URI_SERVICES_BASE + '/object/user-secret-keys/{0}/deactivate'


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        


    def secretkeyuser_show(self, uid):
        '''
        Makes a REST API call to retrieve details of a secretkeyuser  based on its UUID
        '''

	from objectuser import Objectuser
        objObjUser = Objectuser(self.__ipAddr, self.__port)

	try:
	    objuserval = objObjUser.objectuser_query(uid)
	except SOSError as e:
	    raise e

	uri = self.URI_SECRET_KEY_USER.format(uid)

  	(s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             uri,
                                             None, None, None)

	o = common.json_decode(s)

        return o



    def secretkeyuser_add(self, uid, expiryforexistingkey):

	from objectuser import Objectuser
        objObjUser = Objectuser(self.__ipAddr, self.__port)

	try:
	    objuserval = objObjUser.objectuser_query(uid)
	except SOSError as e:
	    raise e
	    
	secretkeyrslt = self.secretkeyuser_show(uid)
	if ( (secretkeyrslt['secret_key_1'] != "") and (secretkeyrslt['secret_key_2'] != "") ):
	    raise SOSError(SOSError.MAX_COUNT_REACHED,
                       "Already two secret keys exist for the uid "+uid)

	
	uri = self.URI_SECRET_KEY_USER.format(uid)

	body = None

	parms = {
                    'existing_key_expiry_time_mins'              : expiryforexistingkey
                }

        if (parms):
            body = json.dumps(parms)


        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT , "POST",
                                                     uri , body)
       
	o = common.json_decode(s)

	return o



            
    def secretkeyuser_delete(self, uid, secretkeytodelete):
        '''
        Makes a REST API call to delete a secretkeyuser by its UUID
        '''
	from objectuser import Objectuser
        objObjUser = Objectuser(self.__ipAddr, self.__port)

	try:
	    objuserval = objObjUser.objectuser_query(uid)
	except SOSError as e:
	    raise e

	uri = self.URI_DELETE_SECRET_KEY_USER.format(uid)

        parms = {
                        'secret_key': secretkeytodelete
            }
	    
	body = None

        if (parms):
            body = json.dumps(parms)


        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "POST",
                                             uri, body)

	return str(s) + " ++ " + str(h)
	    

	

def add_parser(subcommand_parsers, common_parser):
    # add command parser
    add_parser = subcommand_parsers.add_parser('add',
                                description='SOS Secretkeyuser Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create an secretkey for an user')

    mandatory_args = add_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-uid',
                                help='UID',
                                metavar='<uid>',
                                dest='uid',
                                required=True)

    add_parser.add_argument('-existingkeyexpiry',
                                help='Key expiry in minutes',
				default=None,
                                metavar='<existingkeyexpiry>',
                                dest='existingkeyexpiry')

    add_parser.set_defaults(func=secretkeyuser_add)

def secretkeyuser_add(args):
    obj = Secretkeyuser(args.ip, args.port)
    try:
        res = obj.secretkeyuser_add(args.uid, args.existingkeyexpiry)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR,
			   SOSError.MAX_COUNT_REACHED]):
            raise SOSError(e.err_code, "Secret key " + 
                           ": Add secret key failed\n" + e.err_text)
        else:
            raise e


# NEIGHBORHOOD Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='SOS Secretkeyuser delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete an secretkey for an user')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-uid',
                                help='UID',
                                metavar='<uid>',
                                dest='uid',
                                required=True)

    mandatory_args.add_argument('-secretkey', '-sk',
                                help='Secret Key to delete',
                                metavar='<secretkey>',
                                dest='secretkey',
                                required=True)

    delete_parser.set_defaults(func=secretkeyuser_delete)

def secretkeyuser_delete(args):
    obj = Secretkeyuser(args.ip, args.port)
    try:
        res = obj.secretkeyuser_delete(args.uid, args.secretkey)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Secretkey delete failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='SOS Secretkeyuser Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show an Secretkey of a user')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-uid',
                                help='UID',
                                metavar='<uid>',
                                dest='uid',
                                required=True)

    show_parser.set_defaults(func=secretkeyuser_show)

def secretkeyuser_show(args):
    obj = Secretkeyuser(args.ip, args.port)
    try:
        res = obj.secretkeyuser_show(args.uid)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Secret key show failed: " + e.err_text)
        else:
            raise e



#
# Secretkeyuser Main parser routine
#

def secretkeyuser_parser(parent_subparser, common_parser):
    # main secretkeyuser parser
    parser = parent_subparser.add_parser('secretkeyuser',
                                        description='SOS Secretkeyuser CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on Secretkeyuser')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # add command parser
    add_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)


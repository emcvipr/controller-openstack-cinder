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

class Objectpool(object):
    '''
    The class definition for operations on 'Objectpool'. 
    '''

    #Commonly used URIs for the 'objectpool' module

    URI_SERVICES_BASE               = '' 

    URI_OBJECT_POOL_LIST            = URI_SERVICES_BASE   + '/vdc/object-pools'
    URI_OBJECT_POOL                 = URI_SERVICES_BASE   + '/vdc/object-pools/{0}'

    URI_RESOURCE_DEACTIVATE         = '{0}/deactivate'

    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        

    def objectpool_query(self, type, name ):
        '''
        Returns the UID of the objectpool specified by the name
        '''
        if (common.is_uri(name)):
            return name

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                                     URI_OBJECT_POOL_LIST , None)

	o = common.json_decode(s)

        pools = o['object_pool']
        ids = []

        if (not o):
           return ()
        else :
           if (type(pools) != list):
              pools = [pools]
           for pool in pools:
	       try:
	           pool_details = self.objectpool_show_by_uri(self.URI_OBJECT_POOL_LIST + '/' + type + '/' + uri)
                   if (pool_details['name'] == name):
                       return pool.get('id')
		except:
		   pass

        raise Exception('Bad Object Pool name')


    def objectpool_show(self, type , poolname):
        '''
        Makes a REST API call to retrieve details of a objectpool  based on its UUID
        '''
	uri = bourne.objectpool_query(type , poolname)
    	objectpool_show_by_uri(uri)


    def objectpool_show_by_uri(showuri):
	#showuri = URI_OBJECT_POOL_LIST + "/" + type + "/" + uri
	(s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             showuri ,
                                             None)
        o = common.json_decode(s)

        if('inactive' in o):
            if(o['inactive'] == True):
                return None
	
	return o


    def objectpool_create(self, type, label, varray, cos, size, token, mountpoint):

	if ( (varray) and (not common.is_uri(varray)) ):
            from virtualarray import VirtualArray
            obj = VirtualArray(self.__ipAddr, self.__port)
            nbhinst = obj.varray_show(varray)
            varray = nbhinst['id']


	if(not common.is_uri(cos)):
 	    from cos import Cos
            obj = Cos(self.__ipAddr, self.__port)
	    #check this
	    cosinst = obj.cos_show(cos, 'object')
            cos_uri = cosinst['id']

 	parms = {
            'name'              : label,
            'object_cos'       : cos_uri,
        }

	if (size):
            parms['size'] = size

        if (varray):
            parms['varray'] = varray

        if (mountpoint):
            parms['mount_point']  = mountpoint


        if (not token):
            token = 'cli-create-' + cos


        body = json.dumps(parms)

        uri = self.URI_OBJECT_POOL_LIST + "/" + type 

	qparms = { 'task' : token}

        if (qparms):
            for qk in qparms.iterkeys():
                if (qparms[qk] != None):
                            uri += '&' if ('?' in uri) else '?'
                            uri += qk + '=' + qparms[qk]

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                                     uri , body)
       
	o = common.json_decode(s)

        #return (o, s)



    def objectpool_list(self):
        '''
        Returns all the objectpools in a vdc
        Parameters:           
        Returns:
                JSON payload of objectpool list
        '''

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                                     self.URI_OBJECT_POOL_LIST , None)

	o = common.json_decode(s)

        pools = o['object_pool']

        ids = []
        if (not o):
           return ()
        else :
           if (type(pools) != list):
              pools = [pools]
           for pool in pools:
              ids.append(pool.get('id'))
        return ids

            
            
    def objectpool_delete(self, type, poolname):
        '''
        Makes a REST API call to delete a objectpool by its UUID
        '''
	uri = bourne.objectpool_query(type, poolname)
    	objectpool_delete_by_uri(uri)

    

    def objectpool_delete_by_uri(uri):
	deleteuri = URI_RESOURCE_DEACTIVATE.format(self.URI_OBJECT_POOL.format(uri))
	token = 'cli-delete-' + uri

	qparms = { 'task' : token}

	if (qparms):
            for qk in qparms.iterkeys():
                if (qparms[qk] != None):
                    deleteuri += '&' if ('?' in uri) else '?'
                    deleteuri += qk + '=' + qparms[qk]

	(s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                             deleteuri,
                                             None)

        #return str(s) + " ++ " + str(h)


# NEIGHBORHOOD Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='SOS Objectpool Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create an objectpool')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',
                                help='Name of objectpool',
                                metavar='objectpoolname',
                                dest='name',
                                required=True)

    mandatory_args.add_argument('-type', '-t',
                                help='Type of Device',
                                metavar='<devicetype>',
                                dest='type',
                                choices=['local', 'nfs','file'],
				required=True)

    mandatory_args.add_argument('-cos',
                                help='Name of COS',
                                metavar='<cos>',
                                dest='cos',
                                required=True)

    create_parser.add_argument('-varray', '-va',
                                help='Name of varray',
                                metavar='varrayname',
                                dest='varray')

    create_parser.add_argument('-size', '-s',
                                help='size of object pool',
                                metavar='size',
                                dest='size')

    create_parser.add_argument('-token', '-tk',
                               help='Token',
                               dest='token', 
			       metavar='token')

    create_parser.add_argument('-mountpoint', '-mp',
                               help='Mount Point',
                               dest='mountpoint', metavar='<mountpoint>')

    create_parser.set_defaults(func=objectpool_create)

def objectpool_create(args):
    obj = Objectpool(args.ip, args.port)
    try:
        res = obj.objectpool_create(args.type, args.name, args.varray, args.cos, args.size, args.token, args.mountpoint )
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Objectpool " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e


# NEIGHBORHOOD Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='SOS Objectpool delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete an objectpool')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-type', '-t',
                                help='Type of Object Pool',
                                metavar='<pooltype>',
                                dest='type',
                                choices=['local', 'nfs','file'],
                                required=True)

    mandatory_args.add_argument('-name', '-n',
                                help='name of objectpool',
                                dest='name',
                                metavar='objectpoolname',
                                required=True)

    delete_parser.set_defaults(func=objectpool_delete)

def objectpool_delete(args):
    obj = Objectpool(args.ip, args.port)
    try:
        res = obj.objectpool_delete(args.type, args.name)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Objectpool delete failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='SOS Objectpool Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show an Objectpool')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')


    mandatory_args.add_argument('-type', '-t',
                                help='Type of pool',
                                metavar='<pooltype>',
                                dest='type',
                                choices=['local', 'nfs','file'],
                                required=True)

    mandatory_args.add_argument('-name', '-n',
                                help='name of Objectpool',
                                dest='name',
                                metavar='objectpoolname',
                                required=True)

    show_parser.set_defaults(func=objectpool_show)

def objectpool_show(args):
    obj = Objectpool(args.ip, args.port)
    try:
        res = obj.objectpool_show(args.type, args.name)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Objectpool show failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Query routines

def query_parser(subcommand_parsers, common_parser):
    # query command parser
    query_parser = subcommand_parsers.add_parser('query',
                                description='SOS Objectpool Query CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Query a Objectpool')

    mandatory_args = query_parser.add_argument_group('mandatory arguments')


    mandatory_args.add_argument('-type', '-t',
                                help='Type of Device',
                                metavar='<devicetype>',
                                dest='type',
                                choices=['local', 'nfs','file'],
                                required=True)

    mandatory_args.add_argument('-name', '-n',
                                help='name of Objectpool',
                                dest='name',
                                metavar='objectpoolname',
                                required=True)

    query_parser.set_defaults(func=objectpool_query)



def objectpool_query(args):
    obj = Objectpool(args.ip, args.port)
    try:
        res = obj.objectpool_query(args.name)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Objectpool query failed: " + e.err_text)
        else:
            raise e

# KEYPOOL List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='SOS Objectpool List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of objectpools')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List Objectpools with details',
                             dest='verbose')


    list_parser.add_argument('-long','-l',
                             action='store_true',
                             help='List storagepools with more details in tabular form',
                             dest='long')


    list_parser.set_defaults(func=objectpool_list)

def objectpool_list(args):
    obj = Objectpool(args.ip, args.port)
    #TO BE COMPLETED AFTER LOOKING AT THE OBJECTPOOL LIST DATA FORMAT
    try:
        uris = obj.objectpool_list()
        output = []
        outlst = []
        for uri in uris:
	    temp = obj.objectpool_show(uri)
	    if(temp):
                output.append(temp)

        if(len(output) > 0):
            if(args.verbose == True):
                return common.format_json_object(output)
            else:
                outlst = []
        	for record in output: 
		    if(record):
            	        outlst.append(common.format_json_object(record['name']))
        	return outlst

    except SOSError as e:
        raise e


#
# Objectpool Main parser routine
#

def objectpool_parser(parent_subparser, common_parser):
    # main objectpool parser
    parser = parent_subparser.add_parser('objectpool',
                                        description='SOS Objectpool CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on Objectpool')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

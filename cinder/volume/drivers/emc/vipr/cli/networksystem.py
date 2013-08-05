#!/usr/bin/python
# Copyright (c)2012 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import json
import getpass
import sys
import common

from common import SOSError

class Networksystem(object):
    '''
    The class definition for operations on 'Networksystem'. 
    '''

    #Commonly used URIs for the 'Networksystems' module
    URI_SERVICES_BASE               = ''
    URI_NETWORKSYSTEMS              = URI_SERVICES_BASE   + '/vdc/network-systems'
    URI_NETWORKSYSTEM               = URI_NETWORKSYSTEMS  + '/{0}'
    URI_NETWORKSYSTEM_DISCOVER             = URI_NETWORKSYSTEMS  + '/{0}/discover'
    URI_NETWORKSYSTEM_FCENDPOINTS         = URI_NETWORKSYSTEMS  + '/{0}/fc-endpoints'
    URI_NETWORKSYSTEM_VDCREFERENCES = URI_NETWORKSYSTEMS + '/san-references/{0},{1}'
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'
	


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
       
        
    def networksystem_query(self, name):
        '''
        Returns the UID of the networksystem specified by the name
        '''
	if (common.is_uri(name)):
            return name

        systems = self.networksystem_list()
        for system in systems:
            if (system['name'] == name):
		ret = self.networksystem_show(system['id'])
		if(ret):
                    return system['id']

        raise SOSError(SOSError.NOT_FOUND_ERR, "Networksystem "+name+" not found: ")


        

    def networksystem_list(self):
        '''
        Returns all the networksystems in a vdc
        Parameters:           
        Returns:
                JSON payload of networksystem list
        '''
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Networksystem.URI_NETWORKSYSTEMS, None)

        o = common.json_decode(s)
	

	if (not o):
            return {};
        systems = o['network_system'];

	if(type(systems) != list):
            return [systems];
        return systems;



    def networksystem_show(self, label, xml=False):
        '''
        Makes a REST API call to retrieve details of a networksystem  based on its UUID
        '''
        uri = self.networksystem_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Networksystem.URI_NETWORKSYSTEM.format(uri),
                                             None, None, False)

        o = common.json_decode(s)
        
        if('inactive' in o):
            if(o['inactive'] == True):
                return None

	if(xml == False):
	    return o


        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Networksystem.URI_NETWORKSYSTEM.format(uri),
                                             None, None, xml)

	return s
    


    def networksystem_create(self, label, type, deviceip, deviceport, username, password, smisip, smisport, smisuser, smispw, smisssl):
        '''
        creates a networksystem
        parameters:    
            label:  label of the networksystem
        Returns:
            JSON payload response
        '''

        try:     
            check = self.networksystem_show(label)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                var = dict()
                params = dict()

 		parms = { 'name'             : label,
                   'system_type'        : type,
                   'ip_address'         : deviceip,
                   'port_number'        : deviceport,
                   'user_name'          : username,
                   'password'          : password,
                   }
        	if(smisip):
            	    parms['smis_provider_ip'] = smisip
        	if(smisport):
            	    parms['smis_port_number'] = smisport
        	if (smisuser):
            	    parms['smis_user_name'] = smisuser
        	if (smispw):
            	    parms['smis_password'] = smispw
        	if (smisssl):
                    parms['smis_use_ssl'] = smisssl

                body = json.dumps(parms)
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                                     Networksystem.URI_NETWORKSYSTEMS , body)
                o = common.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "Networksystem with name " + label + " already exists")
        
            
    def networksystem_delete(self, label):
        '''
        Makes a REST API call to delete a networksystem by its UUID
        '''
        uri = self.networksystem_query(label)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
					     Networksystem.URI_RESOURCE_DEACTIVATE.format(Networksystem.URI_NETWORKSYSTEM.format(uri)),
                                             None)
        return str(s) + " ++ " + str(h)
    

    def networksystem_discover(self, label):
	'''
        Makes a REST API call to discover a networksystem by its UUID
	'''
        
        uri = self.networksystem_query(label)

	(s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Networksystem.URI_NETWORKSYSTEM_DISCOVER.format(uri) , None)
         
        o = common.json_decode(s)

	return o


    def networksystem_listconnections(self, label):
	'''
        Makes a REST API call to list connections of a switch
	'''
        uri = self.networksystem_query(label)

	(s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Networksystem.URI_NETWORKSYSTEM_FCENDPOINTS.format(uri) , None)
         
        o = common.json_decode(s)
	
	return o



    def networksystem_vdcreferences(self , initiator, target):
	'''
        Makes a REST API call to list vdc references
	'''
	(s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Networksystem.URI_NETWORKSYSTEM_VDCREFERENCES.format(initiator, target) , None)
         
        o = common.json_decode(s)

	return o

# Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Networksystem Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a networksystem')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of Networksystem',
                                metavar='<networksystemname>',
                                dest='name',
                                required=True)

    mandatory_args.add_argument('-type', '-t',
                                help='Type of Network System',
                                metavar='<type>',
                                dest='type',
                                required=True)


    mandatory_args.add_argument('-deviceip', '-dip',
                                help='Device IP of Network System',
                                metavar='<deviceip>',
                                dest='deviceip',
                                required=True)


    mandatory_args.add_argument('-deviceport', '-dp',
                                help='Device Port of Network System',
                                metavar='<deviceport>',
                                dest='deviceport',
                                required=True)


    mandatory_args.add_argument('-user', 
                                help='User of Network System',
                                metavar='<user>',
                                dest='user',
                                required=True)


    create_parser.add_argument('-smisip',
                                help='smis IP of Network System',
                                metavar='<smisip>',
                                dest='smisip')

    create_parser.add_argument('-smisport',
                                help='smis port of Network System',
                                metavar='<smisport>',
                                dest='smisport')

    create_parser.add_argument('-smisuser',
                                help='smis user of Network System',
                                metavar='<smisuser>',
                                dest='smisuser')


    create_parser.add_argument('-smisssl',
                               dest='smisssl',
                               action='store_true',
                               help='user SMIS SSL')

    create_parser.set_defaults(func=networksystem_create)

def networksystem_create(args):
    obj = Networksystem(args.ip, args.port)
    try:
	passwd = None
	smispassword = None
	if (args.user and len(args.user) > 0):
	    if sys.stdin.isatty():
                passwd = getpass.getpass(prompt="Enter password of the network system: ")
            else:
                passwd = sys.stdin.readline().rstrip()

	if (args.smisuser and len(args.smisuser) > 0):
	    if sys.stdin.isatty():
                smispassword = getpass.getpass(prompt="Enter SMIS password of the network system: ")
            else:
                smispassword = sys.stdin.readline().rstrip()


        res = obj.networksystem_create(args.name,args.type, args.deviceip, args.deviceport, args.user, passwd, args.smisip, args.smisport,
					args.smisuser, smispassword , args.smisssl)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR, 
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Networksystem " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e


# NEIGHBORHOOD Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR NetworksystemDelete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a networksystem')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of networksystem',
                                dest='name',
                                metavar='networksystemname',
                                required=True)

    delete_parser.set_defaults(func=networksystem_delete)

def networksystem_delete(args):
    obj = Networksystem(args.ip, args.port)
    try:
        res = obj.networksystem_delete(args.name)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Networksystem delete failed: " + e.err_text)
        else:
            raise e

# NEIGHBORHOOD Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Networksystem Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a Networksystem')

    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Networksystem',
                                dest='name',
                                metavar='networksystemname',
                                required=True)

    show_parser.add_argument('-xml',  
                               dest='xml',
                               action='store_true',
                               help='XML response')

    show_parser.set_defaults(func=networksystem_show)

def networksystem_show(args):
    obj = Networksystem(args.ip, args.port)
    try:
        res = obj.networksystem_show(args.name, args.xml)
	if( (res) and (args.xml) ):
            return common.format_xml(res)

	if(res):
            return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Networksystem "+ args.name+ " show failed: " + e.err_text)
        else:
            raise e


def discover_parser(subcommand_parsers, common_parser):
    # show command parser
    discover_parser = subcommand_parsers.add_parser('discover',
                                description='ViPR Networksystem discover CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Discover a Networksystem')

    mandatory_args = discover_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Networksystem',
                                dest='name',
                                metavar='networksystemname',
                                required=True)

    discover_parser.set_defaults(func=networksystem_discover)

def networksystem_discover(args):
    obj = Networksystem(args.ip, args.port)
    try:
        res = obj.networksystem_discover(args.name)

        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, 
                           "Networksystem "+ args.name+ " show failed: " + e.err_text)
        else:
            raise e


def vdcreferences_parser(subcommand_parsers, common_parser):
    # show command parser
    vdcreferences_parser = subcommand_parsers.add_parser('vdcreferences',
                                description='ViPR Networksystem vdc references CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Discover a Networksystem')

    mandatory_args = vdcreferences_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-initiator', '-in',
                                help='name of initiator',
                                dest='initiator',
                                metavar='initiator',
                                required=True)

    mandatory_args.add_argument('-target', '-tg',
                                help='name of target',
                                dest='target',
                                metavar='target',
                                required=True)

    '''vdcreferences_parser.add_argument('-tenant',
                                help='name of Tenant',
                                dest='tenant',
                                metavar='tenant')'''

    vdcreferences_parser.set_defaults(func=networksystem_vdcreferences)



def networksystem_vdcreferences(args):

    obj = Networksystem(args.ip, args.port)
    try:
        result = obj.networksystem_vdcreferences(args.initiator, args.target)
	uris = result['fc_vdc_reference']
	

        output = []
        outlst = []
        for uri in uris:

	    from exportgroup import ExportGroup
	    obj = ExportGroup(self.__ipAddr, self.__port)
	    groupdtls = obj.export_group_show(uri['groupUri'])

	    if(groupdtls):
		groupname = groupdtls['name']
		uri['group_name'] = groupname

	    from volume import Volume
	    obj = Volume(self.__ipAddr, self.__port)
	    volumedtls = obj.volume_show(uri['volumeUri'])
	
	    if(volumedtls):
		volumename = volumedtls['name']
		uri['volume_name'] = volumename

	    output.append(uri)


        if(len(output) > 0):
            if(args.verbose == True):
		return references
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'id', 'vdcName','group_name','volume_name','inactive']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'vdcName','group_name','volume_name']).printTable()

    except SOSError as e:
        raise e


def listconnections_parser(subcommand_parsers, common_parser):
    # show command parser
    listconnections_parser = subcommand_parsers.add_parser('list-connections',
                                description='ViPR Networksystem List connections CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='List connections of  a Networksystem')

    mandatory_args = listconnections_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Networksystem',
                                dest='name',
                                metavar='networksystemname',
                                required=True)

    listconnections_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List Networksystems with details',
                             dest='verbose')

    listconnections_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List Networksystems with more details in tabular form',
                             dest='long')

    listconnections_parser.set_defaults(func=networksystem_listconnections)

def networksystem_listconnections(args):

    obj = Networksystem(args.ip, args.port)
    try:
        result = obj.networksystem_listconnections(args.name)
	output = result['fc_endpoint']
	
        if(len(output) > 0):
            if(args.verbose == True):
		return output
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'fabric_id', 'remote_port_name','remote_node_name','switch_interface','switch_name','fabric_wwn']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'fabric_id','remote_port_name','remote_node_name']).printTable()

    except SOSError as e:
        raise e
# NEIGHBORHOOD List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='ViPR Networksystem List CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List of networksystems')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List Networksystems with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List Networksystems with more details in tabular form',
                             dest='long')

    list_parser.set_defaults(func=networksystem_list)

def networksystem_list(args):
    obj = Networksystem(args.ip, args.port)
    try:
        uris = obj.networksystem_list()
        output = []
        outlst = []
        for uri in uris:
	    temp = obj.networksystem_show(uri['id'])
	    if(temp):
                output.append(temp)

        if(len(output) > 0):
            if(args.verbose == True):
		return common.format_json_object(output)
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'name', 'system_type','ip_address']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'name']).printTable()

    except SOSError as e:
        raise e


#
# Networksystem Main parser routine
#

def networksystem_parser(parent_subparser, common_parser):
    # main networksystem parser
    parser = parent_subparser.add_parser('networksystem',
                                        description='ViPR Networksystem CLI usage',
                                        parents=[common_parser],
                                        conflict_handler='resolve',
                                        help='Operations on Networksystem')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # discover command parser
    discover_parser(subcommand_parsers, common_parser)

    # discover command parser
    #vdcreferences_parser(subcommand_parsers, common_parser)

    # discover command parser
    listconnections_parser(subcommand_parsers, common_parser)

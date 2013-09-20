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
from virtualarray import VirtualArray

class Network(object):
    '''
    The class definition for operations on 'Network'. 
    '''
    #Commonly used URIs for the 'Network' module
    URI_NETWORKS = '/vdc/networks'
    URI_NETWORK = URI_NETWORKS + '/{0}'
    URI_NETWORK_ENDPOINTS = URI_NETWORK + '/endpoints'
    URI_NETWORK_ENDPOINT = URI_NETWORK_ENDPOINTS + '/{1}'
    URI_VIRTUALARRAY_NETWORK = '/vdc/varrays/{0}/networks'
    URI_NETWORK_DEACTIVATE = '/vdc/networks/{0}/deactivate'
    URI_NETWORK_REGISTER = '/vdc/networks/{0}/register'
    URI_NETWORK_DEREGISTER = '/vdc/networks/{0}/deregister'


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    #Lists networks
    def list_networks(self, varray):
        '''
        Makes REST API call to list networks in a varray
        Parameters:
            varray: name of varray
        Returns:
            List of network uuids in JSON response payload
        '''
	varray_uri = None

	if(varray):
            from virtualarray import VirtualArray

            varray_obj = VirtualArray(self.__ipAddr, self.__port)
            varray_uri = varray_obj.varray_query(varray)
        
        return self.list_by_uri(varray_uri)
         

    #Get the list of network given a varray uri    
    def list_by_uri(self, varray_uri):
        '''
        Makes REST API call and retrieves networks based on varray UUID
        Parameters:
            project_uri: UUID of varray
        Returns:
            List of network UUIDs in JSON response payload
        '''
      
	if(varray_uri):
	    uri = Network.URI_VIRTUALARRAY_NETWORK.format(varray_uri)
	else:
	    uri = Network.URI_NETWORKS

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
					     uri,
                                             None)
        o = common.json_decode(s)
	return o['network']
        #if(o!=None):
         #   o = common.get_object_id(o)
        
	#return o
    def list_by_hrefs(self, hrefs):
        return common.list_by_hrefs(self.__ipAddr, self.__port, hrefs)
		
    # Shows network information given its name
    def show(self, name, varray, xml=False):
        '''
        Retrieves network details based on network name
        Parameters:
            name: name of the network. 
        Returns:
            Network details in JSON response payload
        '''
        
        turi = self.network_query(name, varray)
                      
        
        tz = self.show_by_uri(turi)
        if ( (tz is not None and tz['name'] == name) or (tz is not None and tz['id'] == name) ):
            tz = self.show_by_uri(turi, xml)
            return tz

        raise SOSError(SOSError.NOT_FOUND_ERR, "Network " + 
                        str(name) + ": not found")
    
    def assign(self, name, varray):
        '''
        Retrieves network details based on network name
        Parameters:
            name: name of the network. 
	    varray: varray to be assigned
        Returns:
            Network details in JSON response payload
        '''
        
        turi = self.network_query(name, None)

	nuri = None
	nlst = []

	if(varray):
            from virtualarray import VirtualArray
            varray_obj = VirtualArray(self.__ipAddr, self.__port)

	    for iter in varray:
	
                nuri = varray_obj.varray_query(iter)
		nlst.append(nuri)

	if( len(nlst) > 0 ):
	    parms =  {
                'varrays' : nlst
            }
	else:
	    parms =  {
                'varrays' : []
            }


	body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Network.URI_NETWORK.format(turi), 
                                             body)
                      

        
    # Shows network information given its uri
    def show_by_uri(self, uri, xml=False):
        '''
        Makes REST API call and retrieves network details based on UUID
        Parameters:
            uri: UUID of network
        Returns:
            Network details in JSON response payload
        '''
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Network.URI_NETWORK.format(uri),
                                             None)
        o = common.json_decode(s)
        if('inactive' in o):
            if(o['inactive'] == True):
                return None
        
        if(xml):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Network.URI_NETWORK.format(uri), None,None,xml)
            return s

        return o
    
    # Creates a network given varray, name and type
    def create(self, varray, name, type):
        '''
        Makes REST API call to create network in a varray
        Parameters:
            varray: name of varray
            name: name of network
            type: type of transport protocol. FC, IP or Ethernet
        Returns:
            Created task details in JSON response payload
        '''
                
        network_exists = True

        try:
            self.show(name, varray)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                network_exists = False
            else:
                raise e

        if(network_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Network with name: " +
                           name + " already exists")
       
        from virtualarray import VirtualArray

        varray_obj = VirtualArray(self.__ipAddr, self.__port)
        varray_uri = varray_obj.varray_query(varray)

        # As per the ViPR Source Code 5th July
        body = json.dumps({'name' : name, 'transport_type' : type})

        # As per the wiki apec
        '''
        body = json.dumps({'network':
        {
         'name' : name,
         '' :
               [
                  { "name" : endpoint }
               ]
        }
        })
        '''

 
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "POST",
                                             Network.URI_VIRTUALARRAY_NETWORK.format(varray_uri), 
                                             body)
        o = common.json_decode(s)
        return o
    
    # Update a network and varray info
    def update(self, name, newtzonename, varrayname, newvarray):
        '''
        Makes REST API call to update network information
        Parameters:
            name: name of the network to be updated
            varray: current varray name
            newvarraylist: updated varray list 

        Returns
            Created task details in JSON response payload
        '''

        turi = self.network_query(name, varrayname)
        
        nhurilist = []
        # update the new varray     
        if(newvarray):
            nhuri = VirtualArray(self.__ipAddr, self.__port).varray_query(newvarray)
            nhurilist.append(nhuri)
        else:#add a varray, That already exist with that zone
            if(varrayname != None):
                nhuri = VirtualArray(self.__ipAddr, self.__port).varray_query(varrayname)
                nhurilist.append(nhuri);
       
        parms =  {
            'name' : newtzonename,
            'varrays' : nhurilist
        }
        

        body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Network.URI_NETWORK.format(turi), body)
        o = common.json_decode(s)
        return o

    # adds an endpoint to a network
    def add_endpoint(self, varray, name, endpoint):
        '''
        Adds endpoint to a network
        Parameters:
            varray: name of the varray
            name: name of network
            endpoint: endpoint
        '''
        
        endpoint_exists = True

        try:
            tz = self.show(name, varray)
            if ("endpoints" in tz):
	        endpoints = tz['endpoints']
                if(endpoint in endpoints):
                    endpoint_exists = True
                else:
                    endpoint_exists = False
            else:
                endpoint_exists = False
        except SOSError as e:
            raise e

        if(endpoint_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Endpoint: " +
                           endpoint + " already added to " + name + " network.")

        network_uri = self.network_query(name, varray)
        
        body = json.dumps({'endpoints':[endpoint], 
                           'op' : 'add'})
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Network.URI_NETWORK_ENDPOINTS.format(network_uri), 
                                             body)
        o = common.json_decode(s)
        return o

     # removes an endpoint from a network
    def remove_endpoint(self, varray, name, endpoint):
        '''
        Removes endpoint to a transport zone
        Parameters:
            varray: name of the varray
            name: name of network
            endpoint: endpoint
        '''

        network_uri = self.network_query(name, varray)

        body = json.dumps({'endpoints': [endpoint], 
                           'op' : 'remove'})

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "PUT",
                                             Network.URI_NETWORK_ENDPOINTS.format(network_uri),
                                             body)
        o = common.json_decode(s)
        return o

   
    # As per the ViPR Wiki REST Spec 
    # Removes an endpoint from a network
    def remove_endpoint2(self, varray, name, endpoint):
        '''
        Removes endpoint from a network
        Parameters:
            varray: name of the varray
            name: name of network
            endpoint: endpoint
        '''
        
        network_uri = self.network_query(name, varray)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "DELETE",
                                             Network.URI_NETWORK_ENDPOINT.format(network_uri, endpoint), 
                                             None)
        o = common.json_decode(s)
        return o
       
 
    # Deletes a network given a network name
    def delete(self, name, varray):
        '''
        Deletes a network based on network name
        Parameters:
            name: name of network
        '''

        network_uri = self.network_query(name, varray)
        return self.delete_by_uri(network_uri)
    
    # Deletes a network given a network uri
    def delete_by_uri(self, uri):
        '''
        Deletes a network based on network uri
        Parameters:
            uri: uri of network
        '''

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Network.URI_NETWORK_DEACTIVATE.format(uri), 
                                             None)
        return

		
    # Queries a network given its name
    def network_query(self, name, varray):
        '''
        Makes REST API call to query the network by name
        Parameters:
            name: name of network
        Returns:
            Network details in JSON response payload
        '''
        if (common.is_uri(name)):
            return name

        networks = self.list_networks(varray)
	for zone in networks:
            tzone = common.show_by_href(self.__ipAddr, self.__port, zone)
	    if(tzone):
		if( ((varray) and (tzone.has_key('varray'))) or ((varray is None) and ( tzone.has_key('varray') == False)) ):
                    if (tzone['name'] == name):
                        return tzone['id']  

        raise SOSError(SOSError.NOT_FOUND_ERR, "Network " + 
                        name + ": not found")


    def register(self, varray, name):
        '''
        register a network
        Parameters:
            varray: name of the varray
            name: name of network
        '''

        network_uri = self.network_query(name, varray)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Network.URI_NETWORK_REGISTER.format(network_uri),
                                             None)
        o = common.json_decode(s)
        return o


    def deregister(self, varray, name):
        '''
        register a network 
        Parameters:
            varray: name of the varray
            name: name of network
        '''

        network_uri = self.network_query(name, varray)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Network.URI_NETWORK_DEREGISTER.format(network_uri),
                                             None)



# Network Create routines

def create_parser(subcommand_parsers, common_parser):
    create_parser = subcommand_parsers.add_parser('create',
                                description='ViPR Transport-zone Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a network')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-varray','-va', 
                                help='Name of varray',
                                metavar='<varray>',
                                dest='varray',
                                required=True)
    mandatory_args.add_argument('-transport_type', '-t',
                                help='Type of transport protocol',
                                choices=["FC", "IP", "Ethernet"],
                                dest='transport_type',
                                required=True)
    
    create_parser.set_defaults(func=network_create)

def network_create(args):
    obj = Network(args.ip, args.port)
    try:
        
        res = obj.create(args.varray, args.name, args.transport_type)
    except SOSError as e:
        if(e.err_code in [SOSError.SOS_FAILURE_ERR,SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Network " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e

# Network Update routines

def update_parser(subcommand_parsers, common_parser):
    update_parser = subcommand_parsers.add_parser('update',
                                description='ViPR Network Update CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Update a network')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
   
    update_parser.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of  current varray',
                                required=False)
    
    update_parser.add_argument('-label','-l', 
                                help='New name of network',
                                metavar='<label>',
                                dest='label',
                                required=False)
    
    update_parser.add_argument('-newvarray', '-nnh',
                                metavar='<newvarray>',
                                dest='newvarray',
                                help='Name of new varray  to be updated',

                                required=False)
    
    update_parser.set_defaults(func=network_update)
    

def network_update(args):
    obj = Network(args.ip, args.port)
    try:
       
        obj.update(args.name, args.label, args.varray, args.newvarray)
    except SOSError as e:
        if(e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Network " + 
                           args.name + ": Update failed\n" + e.err_text)
        else:
            raise e


# Network Delete routines
 
def delete_parser(subcommand_parsers, common_parser):
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='ViPR Network Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a network')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-varray','-va',
                                help='Name of varray',
                                metavar='<varray>',
                                dest='varray',
                                required=True)
    delete_parser.set_defaults(func=network_delete)

def network_delete(args):
    obj = Network(args.ip, args.port)
    try:
        obj.delete(args.name, args.varray)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Network " + 
                           args.name + ": Delete failed\n" + e.err_text)
        else:
            raise e


# Network Show routines
 
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='ViPR Network Show CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show details of network')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
    show_parser.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray')
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    show_parser.set_defaults(func=network_show)

def network_show(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.show(args.name, args.varray, args.xml)
        if(res):
            if (args.xml==True):
                return common.format_xml(res)
            return common.format_json_object(res)
    except SOSError as e:
        raise e

def assign_parser(subcommand_parsers, common_parser):
    assign_parser = subcommand_parsers.add_parser('assign',
                                description='ViPR Network Assign CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Assign varray to network')
    mandatory_args = assign_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)

    assign_parser.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray',
				nargs='*')
    assign_parser.set_defaults(func=network_assign)

def network_assign(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.assign(args.name, args.varray)
        #return common.format_json_object(res)
    except SOSError as e:
        raise e

# Network List routines

def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='ViPR Network List CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists networks in a varray')
    mandatory_args = list_parser.add_argument_group('mandatory arguments')
    list_parser.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray')
    list_parser.add_argument('-verbose', '-v',
                                dest='verbose',
                                help='List networks with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                                dest='long',
                                help='List network in table',
                                action='store_true')

    list_parser.set_defaults(func=network_list)

def network_list(args):
    obj = Network(args.ip, args.port)
    try:
        uris = obj.list_networks(args.varray)
        if(len(uris) > 0):
            output = []
            #for uri in uris:
            #    output.append(obj.show_by_uri(uri))
			#if(len(uris) > 0):
            for item in obj.list_by_hrefs(uris):
                output.append(item); 
             #show a short table
            if(args.verbose == False and args.long == False):
                from common import TableGenerator
                TableGenerator(output, ['module/name', 'endpoints']).printTable()
            #show a long table
            if(args.verbose == False and args.long == True):
                from common import TableGenerator
                TableGenerator(output, ['module/name', 'transport_type', 'endpoints']).printTable()
            #show all items in json format
            if(args.verbose == True):
                return common.format_json_object(output)
 
        else:
            return
    except SOSError as e:
        raise e


# Network add/remove endpoint routines
 
def endpoint_parser(subcommand_parsers, common_parser):
    endpoint_parser = subcommand_parsers.add_parser('endpoint',
                                description='ViPR Network endpoint CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='add/remove endpoints')
    subcommand_parsers = endpoint_parser.add_subparsers(help='Use one of the commands')

    add_parser=subcommand_parsers.add_parser('add',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Add endpoint')
    mandatory_args = add_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray',
                                required=True)
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-endpoint', '-e',
                                help='endpoint',
                                metavar='<endpoint>',
                                dest='endpoint',
                                required=True)
    add_parser.set_defaults(func=add_endpoint)

    remove_parser=subcommand_parsers.add_parser('remove',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Remove endpoint')
    mandatory_args = remove_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray',
                                required=True)
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-endpoint', '-e',
                                help='endpoint',
                                metavar='<endpoint>',
                                dest='endpoint',
                                required=True)
    remove_parser.set_defaults(func=remove_endpoint)
    
def add_endpoint(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.add_endpoint(args.varray, args.name, args.endpoint)
    except SOSError as e:
        raise e

def remove_endpoint(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.remove_endpoint(args.varray, args.name, args.endpoint)
    except SOSError as e:
        raise e

def register_parser(subcommand_parsers, common_parser):
    register_parser = subcommand_parsers.add_parser('register',
                                description='ViPR Network Register CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='register a network')
    mandatory_args = register_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)

    mandatory_args.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray',
                                required=True)
    register_parser.set_defaults(func=network_register)

def network_register(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.register(args.varray, args.name)
    except SOSError as e:
        common.format_err_msg_and_raise("register", "network", e.err_text, e.err_code)



def deregister_parser(subcommand_parsers, common_parser):
    deregister_parser = subcommand_parsers.add_parser('deregister',
                                description='ViPR Network Deregister CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Deregister a network')
    mandatory_args = deregister_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of network',
                                metavar='<network>',
                                dest='name',
                                required=True)

    mandatory_args.add_argument('-varray', '-va',
                                metavar='<varray>',
                                dest='varray',
                                help='Name of varray',
                                required=True)
    deregister_parser.set_defaults(func=network_deregister)


def network_deregister(args):
    obj = Network(args.ip, args.port)
    try:
        res = obj.deregister(args.varray, args.name)
    except SOSError as e:
        common.format_err_msg_and_raise("deregister", "network", e.err_text, e.err_code)



#
# Network Main parser routine
#
def network_parser(parent_subparser, common_parser):
    # main project parser

    parser = parent_subparser.add_parser('network',
                                description='ViPR Network CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Network')
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

    # varray assign command parser
    assign_parser(subcommand_parsers, common_parser)

    # register network command parser
    register_parser(subcommand_parsers, common_parser)

    # deregister command parser
    deregister_parser(subcommand_parsers, common_parser)

    # endpoint add/remove command parser
    endpoint_parser(subcommand_parsers, common_parser)


#!/usr/bin/python

# Copyright (c) 2012 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


import common
import json
from common import SOSError


class Transportzone(object):
    '''
    The class definition for operations on 'Transportzone'. 
    '''
    #Commonly used URIs for the 'Transportzone' module
    URI_TRANSPORTZONES = '/zone/transport-zones'
    URI_TRANSPORTZONE = URI_TRANSPORTZONES + '/{0}'
    URI_TRANSPORTZONE_ENDPOINTS = URI_TRANSPORTZONE + '/endpoints'
    URI_TRANSPORTZONE_ENDPOINT = URI_TRANSPORTZONE_ENDPOINTS + '/{1}'
    URI_NEIGHBORHOOD_TRANSPORTZONE = '/zone/neighborhoods/{0}/transport-zones'
    URI_TRANSPORTZONE_DEACTIVATE = '/zone/transport-zones/{0}/deactivate'
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    #Lists transportzones
    def list_transportzones(self, neighborhood):
        '''
        Makes REST API call to list transportzones in a neighborhood
        Parameters:
            neighborhood: name of neighborhood
        Returns:
            List of transportzone uuids in JSON response payload
        '''
	neighborhood_uri = None

	if(neighborhood):
            from neighborhood import Neighborhood

            neighborhood_obj = Neighborhood(self.__ipAddr, self.__port)
            neighborhood_uri = neighborhood_obj.neighborhood_query(neighborhood)
        
        return self.list_by_uri(neighborhood_uri)
         

    #Get the list of transportzone given a neighborhood uri    
    def list_by_uri(self, neighborhood_uri):
        '''
        Makes REST API call and retrieves transportzones based on neighborhood UUID
        Parameters:
            project_uri: UUID of neighborhood
        Returns:
            List of transportzone UUIDs in JSON response payload
        '''
      
	if(neighborhood_uri):
	    uri = Transportzone.URI_NEIGHBORHOOD_TRANSPORTZONE.format(neighborhood_uri)
	else:
	    uri = Transportzone.URI_TRANSPORTZONES

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
					     uri,
                                             None)
        o = common.json_decode(s)
	return o['transport_zone']
        #if(o!=None):
         #   o = common.get_object_id(o)
        
	#return o
    def list_by_hrefs(self, hrefs):
        return common.list_by_hrefs(self.__ipAddr, self.__port, hrefs)
		
    # Shows transportzone information given its name
    def show(self, name, neighborhood, xml=False):
        '''
        Retrieves transportzone details based on transportzone name
        Parameters:
            name: name of the transportzone. 
        Returns:
            Transportzone details in JSON response payload
        '''
        
        turi = self.transportzone_query(name, neighborhood)
                      
        
        tz = self.show_by_uri(turi)
        if (tz is not None and tz['name'] == name):
            tz = self.show_by_uri(turi, xml)
            return tz
        raise SOSError(SOSError.NOT_FOUND_ERR, "Transportzone " + 
                        str(name) + ": not found")
    
    def assign(self, name, neighborhood):
        '''
        Retrieves transportzone details based on transportzone name
        Parameters:
            name: name of the transportzone. 
	    neighborhood: neighborhood to be assigned
        Returns:
            Transportzone details in JSON response payload
        '''
        
        turi = self.transportzone_query(name, None)

	nuri = None
	nlst = []

	if(neighborhood):
            from neighborhood import Neighborhood
            neighborhood_obj = Neighborhood(self.__ipAddr, self.__port)

	    for iter in neighborhood:
	
                nuri = neighborhood_obj.neighborhood_query(iter)
		nlst.append(nuri)

	if( len(nlst) > 0 ):
	    parms =  {
                'neighborhoods' : nlst
            }
	else:
	    parms =  {
                'neighborhoods' : []
            }


	body = json.dumps(parms)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Transportzone.URI_TRANSPORTZONE.format(turi), 
                                             body)
                      

        
    def show(self, name, neighborhood, xml=False):
        '''
        Retrieves transportzone details based on transportzone name
        Parameters:
            name: name of the transportzone. 
        Returns:
            Transportzone details in JSON response payload
        '''
        
        turi = self.transportzone_query(name, neighborhood)
                      
        
        tz = self.show_by_uri(turi)
        if (tz is not None and tz['name'] == name):
            tz = self.show_by_uri(turi, xml)
            return tz
        raise SOSError(SOSError.NOT_FOUND_ERR, "Transportzone " + 
                        str(name) + ": not found")
        tz = self.show_by_uri(turi)
        if (tz is not None and tz['name'] == name):
            tz = self.show_by_uri(turi, xml)
            return tz
        raise SOSError(SOSError.NOT_FOUND_ERR, "Transportzone " + 
                        str(name) + ": not found")


    # Shows transportzone information given its uri
    def show_by_uri(self, uri, xml=False):
        '''
        Makes REST API call and retrieves transportzone details based on UUID
        Parameters:
            uri: UUID of transportzone
        Returns:
            Transportzone details in JSON response payload
        '''
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Transportzone.URI_TRANSPORTZONE.format(uri),
                                             None)
        o = common.json_decode(s)
        if('inactive' in o):
            if(o['inactive'] == True):
                return None
        
        if(xml):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Transportzone.URI_TRANSPORTZONE.format(uri), None,None,xml)
            return s

        return o
    
    # Creates a transportzone given neighborhood, name and type
    def create(self, neighborhood, name, type):
        '''
        Makes REST API call to create transportzone in a neighborhood
        Parameters:
            neighborhood: name of neighborhood
            name: name of transportzone
            type: type of transport protocol. FC, IP or Ethernet
        Returns:
            Created task details in JSON response payload
        '''
                
        transportzone_exists = True

        try:
            self.show(name, neighborhood)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                transportzone_exists = False
            else:
                raise e

        if(transportzone_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Transportzone with name: " +
                           name + " already exists")
       
        from neighborhood import Neighborhood

        neighborhood_obj = Neighborhood(self.__ipAddr, self.__port)
        neighborhood_uri = neighborhood_obj.neighborhood_query(neighborhood)

        # As per the StorageOS Source Code 5th July
        body = json.dumps({'name' : name, 'transport_type' : type})

        # As per the wiki apec
        '''
        body = json.dumps({'transport-zone':
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
                                             Transportzone.URI_NEIGHBORHOOD_TRANSPORTZONE.format(neighborhood_uri), 
                                             body)
        o = common.json_decode(s)
        return o
    
    # Update a transportzone information
    def update(self, name, label, neighborhood, endpoint):
        '''
        Makes REST API call to update transportzone information
        Parameters:
            name: name of the transportzone to be updated
            label: new name of the transportzone
            neighborhood: name of neighborhood
            endpoint: endpoint
        Returns
            Created task details in JSON response payload
        '''
        
       
        turi = self.transportzone_query(name, neighborhood)

        from neighborhood import Neighborhood

        neighborhood_obj = Neighborhood(self.__ipAddr, self.__port)
        neighborhood_uri = neighborhood_obj.neighborhood_query(neighborhood)


        body = json.dumps({'transport-zone':
        {
         'name' : label,
         'neighborhood' : neighborhood_uri,
         'endpoints' : [ endpoint ]
        }
        })
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Transportzone.URI_TRANSPORTZONE.format(turi), 
                                             body)
        o = common.json_decode(s)
        return o

    # adds an endpoint to a transportzone
    def add_endpoint(self, neighborhood, name, endpoint):
        '''
        Adds endpoint to a transport zone
        Parameters:
            neighborhood: name of the neighborhood
            name: name of transportzone
            endpoint: endpoint
        '''
        
        endpoint_exists = True

        try:
            tz = self.show(name, neighborhood)
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
                           endpoint + " already added to " + name + " transportzone.")

        transportzone_uri = self.transportzone_query(name, neighborhood)
        
        body = json.dumps({'endpoints':[endpoint], 
                           'op' : 'add'})
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "POST",
                                             Transportzone.URI_TRANSPORTZONE_ENDPOINTS.format(transportzone_uri), 
                                             body)
        o = common.json_decode(s)
        return o

     # removes an endpoint from a transportzone
    def remove_endpoint(self, neighborhood, name, endpoint):
        '''
        Adds endpoint to a transport zone
        Parameters:
            neighborhood: name of the neighborhood
            name: name of transportzone
            endpoint: endpoint
        '''

        transportzone_uri = self.transportzone_query(name, neighborhood)

        body = json.dumps({'endpoints': [endpoint], 
                           'op' : 'remove'})

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Transportzone.URI_TRANSPORTZONE_ENDPOINTS.format(transportzone_uri),
                                             body)
        o = common.json_decode(s)
        return o

   
    # As per the StorageOS Wiki REST Spec 
    # Removes an endpoint from a transportzone
    def remove_endpoint2(self, neighborhood, name, endpoint):
        '''
        Removes endpoint from a transport zone
        Parameters:
            neighborhood: name of the neighborhood
            name: name of transportzone
            endpoint: endpoint
        '''
        
        transportzone_uri = self.transportzone_query(name, neighborhood)
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "DELETE",
                                             Transportzone.URI_TRANSPORTZONE_ENDPOINT.format(transportzone_uri, endpoint), 
                                             None)
        o = common.json_decode(s)
        return o
       
 
    # Deletes a transportzone given a transportzone name
    def delete(self, name, neighborhood):
        '''
        Deletes a transportzone based on transportzone name
        Parameters:
            name: name of transportzone
        '''

        transportzone_uri = self.transportzone_query(name, neighborhood)
        return self.delete_by_uri(transportzone_uri)
    
    # Deletes a transportzone given a transportzone uri
    def delete_by_uri(self, uri):
        '''
        Deletes a transportzone based on transportzone uri
        Parameters:
            uri: uri of transportzone
        '''

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Transportzone.URI_TRANSPORTZONE_DEACTIVATE.format(uri), 
                                             None)
        return

		
    # Queries a transportzone given its name
    def transportzone_query(self, name, neighborhood):
        '''
        Makes REST API call to query the transportzone by name
        Parameters:
            name: name of transportzone
        Returns:
            Transportzone details in JSON response payload
        '''
        transport_zones = self.list_transportzones(neighborhood)
	for zone in transport_zones:
            tzone = common.show_by_href(self.__ipAddr, self.__port, zone)
	    if(tzone):
                if (tzone['name'] == name):
                    return tzone['id']  
        raise SOSError(SOSError.NOT_FOUND_ERR, "Transport-zone " + 
                        name + ": not found")



# Transportzone Create routines

def create_parser(subcommand_parsers, common_parser):
    create_parser = subcommand_parsers.add_parser('create',
                                description='StorageOS Transport-zone Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a transportzone')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-neighborhood','-nh', 
                                help='Name of neighborhood',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                required=True)
    mandatory_args.add_argument('-transport_type', '-t',
                                help='Type of transport protocol',
                                choices=["FC", "IP", "Ethernet"],
                                dest='transport_type',
                                required=True)
    
    create_parser.set_defaults(func=transportzone_create)

def transportzone_create(args):
    obj = Transportzone(args.ip, args.port)
    try:
        
        res = obj.create(args.neighborhood, args.name, args.transport_type)
    except SOSError as e:
        if(e.err_code in [SOSError.SOS_FAILURE_ERR,SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Transportzone " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e

# Transportzone Update routines

def update_parser(subcommand_parsers, common_parser):
    update_parser = subcommand_parsers.add_parser('update',
                                description='StorageOS Transportzone Update CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Update a transportzone')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-label','-l', 
                                help='New name of transportzone',
                                metavar='<label>',
                                dest='label',
                                required=True)
    mandatory_args.add_argument('-neighborhood','-nh', 
                                help='Name of neighborhood',
                                metavar='<neighborhood>',
                                dest='neighborhood',
				required=True)
    mandatory_args.add_argument('-endpoint', '-e',
                                help='endpoint',
                                metavar='<endpoint>',
                                dest='endpoint',
                                required=True)
    
    update_parser.set_defaults(func=transportzone_update)
    

def transportzone_update(args):
    obj = Transportzone(args.ip, args.port)
    try:
        
        res = obj.update(args.name, args.label, args.neighborhood, args.endpoint)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Transportzone " + 
                           args.name + ": Update failed\n" + e.err_text)
        else:
            raise e


# Transportzone Delete routines
 
def delete_parser(subcommand_parsers, common_parser):
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='StorageOS Transportzone Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a transportzone')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-neighborhood','-nh',
                                help='Name of neighborhood',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                required=True)
    delete_parser.set_defaults(func=transportzone_delete)

def transportzone_delete(args):
    obj = Transportzone(args.ip, args.port)
    try:
        obj.delete(args.name, args.neighborhood)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Transportzone " + 
                           args.name + ": Delete failed\n" + e.err_text)
        else:
            raise e


# Transportzone Show routines
 
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='StorageOS Transportzone Show CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show details of transportzone')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-neighborhood', '-nh',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                help='Name of neighborhood',
                                required=True)
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    show_parser.set_defaults(func=transportzone_show)

def transportzone_show(args):
    obj = Transportzone(args.ip, args.port)
    try:
        res = obj.show(args.name, args.neighborhood, args.xml)
        if(res):
            if (args.xml==True):
                return common.format_xml(res)
            return common.format_json_object(res)
    except SOSError as e:
        raise e

def assign_parser(subcommand_parsers, common_parser):
    assign_parser = subcommand_parsers.add_parser('assign',
                                description='StorageOS Transportzone Assign CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Assign neighborhood to transportzone')
    mandatory_args = assign_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)

    assign_parser.add_argument('-neighborhood', '-nh',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                help='Name of neighborhood',
				nargs='*')
    assign_parser.set_defaults(func=transportzone_assign)

def transportzone_assign(args):
    obj = Transportzone(args.ip, args.port)
    try:
        res = obj.assign(args.name, args.neighborhood)
        #return common.format_json_object(res)
    except SOSError as e:
        raise e

# Transportzone List routines

def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='StorageOS Transportzone List CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists transportzones in a neighborhood')
    mandatory_args = list_parser.add_argument_group('mandatory arguments')
    list_parser.add_argument('-neighborhood', '-nh',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                help='Name of neighborhood')
    list_parser.add_argument('-verbose', '-v',
                                dest='verbose',
                                help='List transportzones with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                                dest='long',
                                help='List transportzone in table',
                                action='store_true')

    list_parser.set_defaults(func=transportzone_list)

def transportzone_list(args):
    obj = Transportzone(args.ip, args.port)
    try:
        uris = obj.list_transportzones(args.neighborhood)
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
                TableGenerator(output, ['name', 'endpoints']).printTable()
            #show a long table
            if(args.verbose == False and args.long == True):
                from common import TableGenerator
                TableGenerator(output, ['name', 'transport_type', 'endpoints']).printTable()
            #show all items in json format
            if(args.verbose == True):
                return common.format_json_object(output)
 
        else:
            return
    except SOSError as e:
        raise e


# Transportzone add/remove endpoint routines
 
def endpoint_parser(subcommand_parsers, common_parser):
    endpoint_parser = subcommand_parsers.add_parser('endpoint',
                                description='StorageOS Transportzone endpoint CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='add/remove endpoints')
    subcommand_parsers = endpoint_parser.add_subparsers(help='Use one of the commands')


    common_args = common_parser.add_argument_group('mandatory arguments')
    common_args.add_argument('-neighborhood', '-nh',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                help='Name of neighborhood',
                                required=True)
    common_args.add_argument('-name', '-n',
                                help='Name of transportzone',
                                metavar='<transportzone>',
                                dest='name',
                                required=True)
    common_args.add_argument('-endpoint', '-e',
                                help='endpoint',
                                metavar='<endpoint>',
                                dest='endpoint',
                                required=True)

    add_parser=subcommand_parsers.add_parser('add',
			        parents=[common_parser],
                                conflict_handler='resolve',
                                help='Add endpoint')
    remove_parser=subcommand_parsers.add_parser('remove',
			        parents=[common_parser],
                                conflict_handler='resolve',
                                help='Remove endpoint')


    add_parser.set_defaults(func=add_endpoint)

    remove_parser.set_defaults(func=remove_endpoint)
    
def add_endpoint(args):
    obj = Transportzone(args.ip, args.port)
    try:
        res = obj.add_endpoint(args.neighborhood, args.name, args.endpoint)
    except SOSError as e:
        raise e

def remove_endpoint(args):
    obj = Transportzone(args.ip, args.port)
    try:
        res = obj.remove_endpoint(args.neighborhood, args.name, args.endpoint)
    except SOSError as e:
        raise e

#
# Transportzone Main parser routine
#
def transportzone_parser(parent_subparser, common_parser):
    # main project parser

    parser = parent_subparser.add_parser('transportzone',
                                description='StorageOS Transportzone CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Transportzone')
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

    # neighborhood assign command parser
    assign_parser(subcommand_parsers, common_parser)

    # endpoint add/remove command parser
    endpoint_parser(subcommand_parsers, common_parser)


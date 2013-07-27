#!/usr/bin/pytho

# Copyright (c) 2012 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


import json
import common
import argparse
import textwrap
from common import SOSError
from transportzone import Transportzone
from storagesystem import StorageSystem

class Storageport(object):
    '''
    Class definition for operations on 'Storage port'
    '''
    URI_STORAGEPORT_LIST = '/zone/storage-systems/{0}/storage-ports'
    URI_STORAGEPORT_DETAILS = '/zone/storage-systems/{0}/storage-ports/{1}'
    URI_STORAGEPORT_SHOW = '/zone/storage-ports/{0}'
    URI_STORAGEPORT_REGISTER = '/zone/storage-systems/{0}/storage-ports/{1}/register'
    URI_STORAGEPORT_DEREGISTER = '/zone/storage-ports/{0}/deregister'
    URI_STORAGEPORT_DELETE = '/zone/storage-ports/{0}'
    URI_STORAGEPORT_UPDATE = '/zone/storage-ports/{0}'
    URI_STORAGEPORT        = '/zone/storage-ports/{0}'
    URI_RESOURCE_DEACTIVATE = '{0}/deactivate'
    
    TZONE_TYPE = ['IP', 'Ethernet', 'FC']
    TZ_TYPE_INFO = 'type of transport zone: FC | IP | Ethernet'

    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
    
        '''
        creates a storage port
        Parameters:
            urideviceid   : uri of storage device
            label         : label of storage port
            portname      : name of a port
            portid        : id of a port
            transportType : transport type
            portspeed     : speed of a port
            portgroup     : group of port it belong
            transportZone : transportZone name 
        Returns:
            JSON response payload
        '''   
    def storageport_add(self, storagedeviceName, serialNumber, storagedeviceType, label, portname, portid, transportType, portspeed, portgroup, transportZoneId):
       
        storagesystemObj = StorageSystem(self.__ipAddr, self.__port) 
        urideviceid = None
        
        if(serialNumber):
            urideviceid = storagesystemObj.query_storagesystem_by_serial_number(serialNumber)

        elif(storagedeviceName):
            urideviceidTemp = storagesystemObj.show(name=storagedeviceName, type=storagedeviceType)
            urideviceid = urideviceidTemp['id']
        else:
            raise SOSError(SOSError.CMD_LINE_ERR,
                           "error: For device type " + storagedeviceType + "  -storagesystem name or serialnumber are required")

           
        #check snapshot is already exist
        is_storageport_exist = True
        try:
            self.storageport_query(storagedeviceName, serialNumber, storagedeviceType, portname)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                is_storageport_exist = False
            else:
                raise e

        if(is_storageport_exist):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "storageport with name " + portname + 
                           " already exists under device under type" + storagedeviceType)
        
        body = json.dumps({
                        'label' : label,
                        'portName' : portname,
                        'portId' : portid,
                        'transportType' : transportType,
                        'portSpeed' : portspeed,
                        'portGroup' : portgroup,
                        'transportZone':transportZoneId
                    }) 

        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Storageport.URI_STORAGEPORT_LIST.format(urideviceid), body)
        return common.json_decode(s)

    def storageport_register_uri(self, sspuri, spuri):
        
       
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Storageport.URI_STORAGEPORT_REGISTER.format(sspuri, spuri), None) 
        return common.json_decode(s)
    
    def storageport_update_uri(self, spuri, tzuri):
        
        parms = {}
        if (tzuri):
            parms['transport_zone'] = tzuri
        else:
            parms['auto_transport_zone'] = 'true'
        
        body = json.dumps(parms)
        
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "PUT", Storageport.URI_STORAGEPORT_UPDATE.format(spuri), body) 
        return common.json_decode(s)
    
    """
        Retrieve a list of storage port URI's associated with the given storage port
        Parameters:
            duri : URi of storage device
        Returns:
            JSON response payload contain list of storageports details
    """
    def storageport_list_uri(self, duri):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Storageport.URI_STORAGEPORT_LIST.format(duri), None)
        
        o = common.json_decode(s)
        
        return_list = o['storage_port']
        
        if(len(return_list) > 0):
            return return_list
        else:
            return [];
    
    '''
        Returns details of a storage port
        
         based on its name or UUID
        Parameters:
            uriport    :{UUID of storage port} 
        Returns:
            a JSON payload of port details
        Throws:
            SOSError - if id or name not found 
    '''
    def storageport_show_uri(self, ssuri, spuri, xml=False):
        '''
        Makes a REST API call to retrieve details of a storage port based on its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Storageport.URI_STORAGEPORT_DETAILS.format(ssuri, spuri), None)
        if(xml == False):
            o = common.json_decode(s)
            inactive = common.get_node_value(o, 'inactive')
            if(inactive):
                return None
            else:
                return o
        return s
    
    '''
        Deletes a storage device by name
    '''
    def storageport_delete_uri(self, uriport):
        '''
        Makes a REST API call to delete a storage port by its UUID
        '''
        common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Storageport.URI_RESOURCE_DEACTIVATE.format(Storageport.URI_STORAGEPORT.format(uriport)), None, None)
        return 0
    
    def storageport_deregister_uri(self, spuri):
       (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                            Storageport.URI_STORAGEPORT_DEREGISTER.format(spuri), None) 
       
    def storageport_update(self, serialNumber, storagedeviceName, storagedeviceType, transportType, tzone, neighborhood, portname):
        #process         
        tzuri = None
        ssuri = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType)

        if(tzone != None and neighborhood != None):
                tzuri = Transportzone(self.__ipAddr, self.__port).transportzone_query(tzone, neighborhood)
        
        if(ssuri != None ):
            porturis = self.storageport_list_uri(ssuri)
            if(portname != None ):
                for porturi in porturis:
                    sport = self.storageport_show_id(ssuri, porturi['id'])
                    if(sport['port_name'] == portname and sport['transport_type'] == transportType):
                        return self.storageport_update_uri(sport['id'], tzuri)
                # if port name is not found storage system, then raise not found exception
                raise SOSError(SOSError.NOT_FOUND_ERR, "Storage port : " + portname + " is not found")
                        
            else:
                for porturi in porturis:
                    sport = self.storageport_show_id(ssuri, porturi['id'])
                    if (sport['transport_type'] == transportType):
                            self.storageport_update_uri(sport['id'], tzuri)
        None
    
    def storageport_register(self, serialNumber, storagedeviceName, storagedeviceType, transportType, portname):
        #process         

        ssuri = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType)
                
        if(ssuri != None ):
            porturis = self.storageport_list_uri(ssuri)
            if(portname != None ):
                for porturi in porturis:
                    sport = self.storageport_show_id(ssuri, porturi['id'])
                    if(sport['port_name'] == portname and sport['transport_type'] == transportType):
                        return self.storageport_register_uri(ssuri, porturi['id'])
                raise SOSError(SOSError.NOT_FOUND_ERR, "Storage port : " + portname + " is not found")        
                    
            else:
                for porturi in porturis:
                    sport = self.storageport_show_id(ssuri, porturi['id'])
                    if (sport['transport_type'] == transportType and sport['registration_status'] == "UNREGISTERED"): # check if unregister, then only register.
                        self.storageport_register_uri(ssuri, porturi['id'])
        None
        
    def storageport_deregister(self, storagedeviceName, serialNumber, storagedeviceType, portName):
        ssuri = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType);
        spuri = self.storageport_query(ssuri, portName);
        return self.storageport_deregister_uri(spuri)
       
    def storagesystem_query(self, storagedeviceName, serialNumber, storagedeviceType):
        urideviceid = None
        storagesystemObj = StorageSystem(self.__ipAddr, self.__port)
        if(serialNumber):
            urideviceid = storagesystemObj.query_by_serial_number(serialNumber, storagedeviceType)

        elif(storagedeviceName):
            urideviceidTemp = storagesystemObj.show(name=storagedeviceName, type=storagedeviceType)
            urideviceid = urideviceidTemp['id']
        else:
            return
        
        return urideviceid

    def storageport_list(self, storagedeviceName, serialNumber, storagedeviceType):
        urideviceid = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType)
        if(urideviceid):
            return self.storageport_list_uri(urideviceid)
    
    def storageport_show_id(self, ssuri, spuri, xml=False):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                                             "GET", Storageport.URI_STORAGEPORT_DETAILS.format(ssuri, spuri), None, None, xml)
        if(xml==False):
            return common.json_decode(s)
        else:
            return s
        
    def storageport_show(self, storagedeviceName, serialNumber, storagedeviceType, portname, xml):
        ssuri = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType);
        spuri = self.storageport_query(ssuri, portname);
        return self.storageport_show_id(ssuri, spuri, xml);

    def storageport_remove(self, storagedeviceName, serialNumber, storagedeviceType, portname):
        ssuri = self.storagesystem_query(storagedeviceName, serialNumber, storagedeviceType);
        spuri = self.storageport_query(ssuri, portname);

        return self.storageport_delete_uri(spuri)
    
    def storageport_query(self, ssuri, portname):
        if(ssuri != None ):
            porturis = self.storageport_list_uri(ssuri)
            if(portname != None ):
                for porturi in porturis:
                    sport = self.storageport_show_id(ssuri, porturi['id'])
                    if(sport['port_name'] == portname ):
                        return porturi['id']
                    
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "Storage port with name: " + portname + " not found")
        
    def command_validation(self, devicetype, tzonetype):
        if(devicetype == 'vnxfile' or devicetype == 'isilon'):
            if(tzonetype != 'IP'):
                raise SOSError(SOSError.CMD_LINE_ERR, devicetype  + " transport type should be of  IP type"); 
        elif(devicetype == 'vnxblock' or devicetype == 'vmax'):
            if(tzonetype == 'Ethernet'):
                raise SOSError(SOSError.CMD_LINE_ERR, devicetype  + " transport type should be of  FC or IP type"); 
        return
def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('add',
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=textwrap.dedent('''\
                SOS Storageport Add cli usage:
                
                - storagesystem (name of storagesystem to which port should be added) 
                -type (storage system type )
                - filename(.cfg file should contain following attributes):
                      --------------------------------------------------------
                      portId           - it is a target port id.(either IP Address or IQN  or WWPN )
                      portGroup        - portgroupname to which storageport belongs.
                      portName         - portGroupname + integer value. (ex: SA_B:1, ipgroup1 etc..)
                      label            - label of a storageport.
                      transportType    - transport type.(either "FC" or  "IP" or "Ethernet")
                      portSpeed        - port speed.(default val - portSpeed = 0)  
                      transportZone    - transportzone name to which the storageport to be added.
                      neighborhoodName - Neighborhood name.(above provided trasportzone should be part of neighborhood)'''),
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add a Storageport to storagesystem')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-filename', '-fn',
                                help='Full path of a configuration filename',
                                metavar='<configfilename>',
                                dest='filename',
                                required=True)
    create_parser.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>')
                                
    create_parser.add_argument('-serialnumber', '-sn',
                             metavar="serialno",
                             help='Serial Number of the storage system',
                             dest='serialnumber')
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system',
                               required=True)
    
    create_parser.set_defaults(func=storageport_create)

def storageport_create(args):
    
    try:
        Storageport(args.ip, args.port)
        return 
    except SOSError as e:
        if e.err_code == SOSError.NOT_FOUND_ERR:
            raise SOSError(SOSError.NOT_FOUND_ERR, "Storageport Add failed: " + e.err_text)
        else:
            raise e

def resgister_parser(subcommand_parsers, common_parser):
    # show command parser
    register_parser = subcommand_parsers.add_parser('register',
                                                description='StorageOS Storageport register CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Storageport registration or \n register the discovered storage port with the passed id, on the \
     registered storage system with the passed id.')
    mandatory_args = register_parser.add_argument_group('mandatory arguments')
    
    arggroup = register_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem or Storage system where this port belongs',
                                dest='storagesystem',
                                metavar='<storagesystemname>')
    arggroup.add_argument('-serialnumber', '-sn',
                               metavar="<serialnumber>",
                               help='Serial Number of the storage system',
                               dest='serialnumber')
    
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               metavar="<storagesystem type>",
                               help='Type of storage system',
                               required=True)
    
    mandatory_args.add_argument('-transporttype', '-tt',
                                help=Storageport.TZ_TYPE_INFO,
                                metavar='<transporttype>',
                                choices=Storageport.TZONE_TYPE,
                                dest='transporttype',
                                required=True)

    register_parser.add_argument('-name', '-n',
                                help='Port name to be registered',
                                metavar='<storageportname>',
                                dest='name')
    
    register_parser.set_defaults(func=storageport_register)

def storageport_register(args):
    #get uri of a storage device by name
    obj = Storageport(args.ip, args.port)
    try:
        obj.command_validation(args.type, args.transporttype);
        obj.storageport_register(args.serialnumber, args.storagesystem, args.type, args.transporttype, args.name)
        
    except SOSError as e:
        raise e

def update_parser(subcommand_parsers, common_parser):
    # show command parser
    update_parser = subcommand_parsers.add_parser('update',
                                                description='StorageOS Storageport update CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Updates transport zone for the registered storage port')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    arggroup = update_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')
 
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>')
    
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system',
                               required=True)
   
    mandatory_args.add_argument('-tzone', '-tz',
                                help='Transport zone to which this port is physically connected',
                                metavar='<transportzone>',
                                dest='tzone',
                                required=True)
    mandatory_args.add_argument('-neighborhood', '-nh',
                                help='Name of Neighborhood',
                                metavar='<neighborhood>',
                                dest='neighborhood',
                                required=True)
    
    mandatory_args.add_argument('-transporttype', '-tt',
                                help=Storageport.TZ_TYPE_INFO,
                                metavar='<transporttype>',
                                choices=Storageport.TZONE_TYPE,
                                dest='transporttype',
                                required=True)
    
    update_parser.add_argument('-portName', '-pn',
                                help='portName or label that belong to storagesystem ',
                                metavar='<storageportname>',
                                dest='portName') 
    
    
    update_parser.set_defaults(func=storageport_update)

def storageport_update(args):
    #get uri of a storage device by name
    obj = Storageport(args.ip, args.port)
    try:
        obj.command_validation(args.type, args.transporttype);
        obj.storageport_update(args.serialnumber, args.storagesystem, args.type, args.transporttype, args.tzone, 
                                                                                                     args.neighborhood, 
                                                                                                     args.portName)
    except SOSError as e:
        raise e
                    
def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                                description='StorageOS Storageport List CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='List storageport for a storagesystem')
    mandatory_args = list_parser.add_argument_group('mandatory arguments')
    arggroup = list_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>',
                                )
    arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')

    mandatory_args.add_argument('-t', '-type',
                                choices=StorageSystem.SYSTEM_TYPE_LIST,
                                dest='type',
                                help='Type of storage system',
                                metavar="<storagesystemtype>",
                                required=True)
   
    list_parser.add_argument('-v', '-verbose',
                                dest='verbose',
                                help='List Storageport with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                                dest='long',
                                help='List Storageport in table with details',
                                action='store_true')

    list_parser.set_defaults(func=storageport_list)

def storageport_list(args):
    
    #get uri of a storage device by name
    obj = Storageport(args.ip, args.port)
    try:
        uris = obj.storageport_list(args.storagesystem, args.serialnumber, args.type)
        
        if(len(uris) > 0):
            output = []
            ssuri = obj.storagesystem_query(args.storagesystem, args.serialnumber, args.type)
            tz_name = []
            for port in uris:
                is_active_obj = obj.storageport_show_id(ssuri, port['id'])
                #transportzone name is display in long list
                if('transport_zone' in is_active_obj):
                    if('id' in is_active_obj['transport_zone']):
                        #using tranportzone uri, get zone details
                        tzob = Transportzone(args.ip, args.port).show_by_uri(is_active_obj['transport_zone']['id'], False)
                        if(tzob):
                            #append zone name into 'tz_name' varible( or directory) 
                            tz_name.append(tzob['name'])
                            #then added tranportzone name attribute into port object
                            is_active_obj['transport_zone_name'] = tz_name
                            output.append(is_active_obj)
                            tz_name = []
                else:
                    if(is_active_obj is not None):
                        output.append(is_active_obj)
            if(args.verbose == True):
                return common.format_json_object(output)
            else:
                from common import TableGenerator
                if(args.long == True):
                    TableGenerator(output, ['port_name', 'transport_type', 'transport_zone_name', 'port_network_id',
                                                                                                    'port_speed',
                                                                                                    'port_group', 
                                                                                                    'registration_status']).printTable()
                else:
                    TableGenerator(output, ['port_name', 'transport_type', 'transport_zone_name','port_network_id', 'registration_status']).printTable()
 
    except SOSError as e:
            raise e


def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                                description='StorageOS Storageport Show CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Show details of a Storageport')
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                help='name of storageport',
                                dest='name',
                                metavar='<storageportname>',
                                required=True)
    arggroup = show_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>',
                                )
    arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')

    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               metavar="<storagesystemtype>",
                               help='Type of storage system',
                               required=True)
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    show_parser.set_defaults(func=storageport_show)

def storageport_show(args):
    
    port_obj = Storageport(args.ip, args.port)
    try:
        # get uri's of device and port
        res = port_obj.storageport_show(args.storagesystem, args.serialnumber, args.type, args.name, args.xml)
        if(res):
            return common.format_json_object(res)
        else:
            SOSError(SOSError.NOT_FOUND_ERR, "storageport name : " + args.name + "Not Found")
    except SOSError as e:
        raise e

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                                description='StorageOS Storageport Remove CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Remove a registered storage port, so that it is no longer present in the system')
    
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    arggroup = delete_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>')
    arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')
    mandatory_args.add_argument('-t', '-type',
                                choices=StorageSystem.SYSTEM_TYPE_LIST,
                                dest='type',
                                metavar="<storagesystemtype>",
                                help='Type of storage system',
                                required=True)
    mandatory_args.add_argument('-name', '-n',
                                help='Name of Storageport',
                                metavar='<storageportname>',
                                dest='name',
                                required=True)
    delete_parser.set_defaults(func=storageport_delete)

def storageport_delete(args):
    obj = Storageport(args.ip, args.port)
    try:
        obj.storageport_remove(args.storagesystem, args.serialnumber, args.type, args.name)
        return 
    except SOSError as e:
        if (e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Storage port " + args.name + " : Remove failed\n" + e.err_text)
        else:
            raise e

def deregister_parser(subcommand_parsers, common_parser):
    # delete command parser
    deregister_parser = subcommand_parsers.add_parser('deregister',
                                                description='StorageOS Storageport deregister CLI usage',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help='Allows the user to deregister a registered storage port so that it is no longer used by the system.\
                                                \n sets the registration_status of the storage port to UNREGISTERED')
    
    mandatory_args = deregister_parser.add_argument_group('mandatory arguments')
    arggroup = deregister_parser.add_mutually_exclusive_group(required=True)
    mandatory_args.add_argument('-name', '-n',
                                help='Name of Storageport',
                                metavar='<storageportname>',
                                dest='name',
                                required=True)
    arggroup.add_argument('-storagesystem', '-ss',
                                help='Name of Storagesystem',
                                dest='storagesystem',
                                metavar='<storagesystemname>')
    arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')
    mandatory_args.add_argument('-t', '-type',
                                choices=StorageSystem.SYSTEM_TYPE_LIST,
                                dest='type',
                                metavar="<storagesystemtype>",
                                help='Type of storage system',
                                required=True)
    
    deregister_parser.set_defaults(func=storageport_deregister)

def storageport_deregister(args):
    obj = Storageport(args.ip, args.port)
    try:
        obj.storageport_deregister(args.storagesystem, args.serialnumber, args.type, args.name)
        
        return 
    except SOSError as e:
        if (e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Storage port " + args.name + " : Remove failed\n" + e.err_text)
        else:
            raise e

#
# Storage device Main parser routine
#
def storageport_parser(parent_subparser, common_parser):
    # main storage device parser

    parser = parent_subparser.add_parser('storageport',
                                description='StorageOS Storage port CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on storage port')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')
    
    #register command parser
    resgister_parser(subcommand_parsers, common_parser)
 
    #deregister command parser
    deregister_parser(subcommand_parsers, common_parser)

    # deactivate command parser
    #delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)
    
    # update command parser
    update_parser(subcommand_parsers, common_parser)    

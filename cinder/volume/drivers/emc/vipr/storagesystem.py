#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import common
import json
from argparse import ArgumentParser
from common import SOSError
import getpass
import sys

class StorageSystem(object):
    '''
    The class definition for operations on 'Storage system'.
    '''
    #Commonly used URIs for the 'StorageSystem' module
    URI_STORAGESYSTEM_LIST = '/vdc/storage-systems'
    URI_STORAGESYSTEM_DETAILS = '/vdc/storage-systems/{0}'
    URI_STORAGESYSTEM_INVENTORY = '/vdc/storage-systems/{0}/physical-inventory'
    
    URI_STORAGESYSTEM_REGISTER = '/vdc/smis-providers/{0}/storage-systems/{1}/register'
    URI_STORAGESYSTEM_UNREGISTER = '/vdc/storage-systems/{0}/deregister'
    URI_STORAGESYSTEM_DELETE = '/vdc/storage-systems/{0}/deactivate'
    URI_STORAGESYSTEM_DISCOVER_BY_ID = '/vdc/storage-systems/{0}/discover'
    URI_STORAGESYSTEM_DISCOVER_ALL = '/vdc/storage-systems/discover'
    
    URI_SMISPROVIDER_LIST = '/vdc/smis-providers'
    URI_SMISPROVIDER_DETAILS = '/vdc/smis-providers/{0}'
    URI_STORAGESYSTEM_CONNECTIVITY = '/vdc/storage-systems/{0}/connectivity'

    SYSTEM_TYPE_LIST = ['isilon', 'vnxblock', 'vnxfile', 'vmax', 'netapp', 'vplex']
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    def smis_device_create(self, name, ip_address, port, user_name, passwd, use_ssl):
        
        
        body = json.dumps(
        {
            'name' : name,
            'ip_address' : ip_address,
            'port_number' : port,
            'user_name' : user_name,
            'password' : passwd,
            'use_ssl' : use_ssl
            }
        )
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                              StorageSystem.URI_SMISPROVIDER_LIST,
                                              body)
        
        o = common.json_decode(s)
        return o
    
    def smis_device_show_by_uri(self, uri, xml=False):
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                           'GET', StorageSystem.URI_SMISPROVIDER_DETAILS.format(uri), None, None)
        o = common.json_decode(s)
        
        if(o["inactive"] == False):
            if(xml == True):
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, 'GET',
                                            StorageSystem.URI_SMISPROVIDER_DETAILS.format(uri), None, None, xml)
                return s
            else:
                return o
        return None
    
    def smis_device_show(self, name, xml=False):
        device_uri = self.smis_device_query(name)
        return self.smis_device_show_by_uri(device_uri, xml)
                        
    def smis_device_delete_by_uri(self, uri):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                           'DELETE', StorageSystem.URI_SMISPROVIDER_DETAILS.format(uri), None)
        
    def smis_device_delete(self, name):
        device_uri = self.smis_device_query(name)
        return self.smis_device_delete_by_uri(device_uri)

    def smis_device_query(self, name):
        if (common.is_uri(name)):
            return name

        providers = self.smis_device_list()
        for provider in providers:
            smisprovider = self.smis_device_show_by_uri(provider['id'])
            if (smisprovider is not None and smisprovider['name'] == name):
                return smisprovider['id']
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "Storage system with name: " + name + " not found")
    
    def smis_device_query_by_serial_number(self, serial_number):
        
        providers = self.smis_device_list()
        for provider in providers:
            smisprovider = self.smis_device_show_by_uri(provider['id'])
            if (serial_number == smisprovider["storage_systems"][0]):
                return smisprovider['id']
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "SMIS provider with serial number: " + serial_number + " not found")

        
    def smis_device_list(self):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 'GET',
                                        StorageSystem.URI_SMISPROVIDER_LIST, None)
        o = common.json_decode(s)
        if (not o or "smis_provider" not in o):
            return [];
        else:
            return_list = o['smis_provider']
            if(return_list and len(return_list) > 0):
                return return_list
            else:
                return [];
        
    def create(self, system_name, device_type, ip_address, port, user_name,
               passwd, serial_num, smis_ip, smis_port, use_ssl, smis_user,
               smis_passwd):
        '''
        Takes care of creating a storage system.
        Parameters:
            system_name: label for the storage system
            device_type: the type of storage system
            ip_address: the IP address of storage system
            port: the port number of storage system
            user_name: the username of storage system
            passwd: the password
            serial_num: serial number
            smis_ip: SMIS IP addrress
            smis_port: SMIS port number
            use_ssl: One of {True, False}
            smis_user: SMIS username
            smis_passwd : SMIS password
        Reurns:
            Response payload
        '''
        
        storage_system_exists = True
        
        try:
            if(device_type in ["vmax", "vnxblock"]):
                self.smis_device_query(system_name)
            else:
                self.show(name=system_name, type=device_type)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                storage_system_exists = False
            elif(e.err_code == SOSError.ENTRY_ALREADY_EXISTS_ERR):
                storage_system_exists = True
            else:
                raise e
                
        if(storage_system_exists):
            common.print_err_msg_and_exit("create", "storagesystem", 
                                          "Storage system with name: " +system_name + " already exists", 
                                          SOSError.ENTRY_ALREADY_EXISTS_ERR)
            
        if(device_type in ["vmax", "vnxblock"]):
            return self.smis_device_create(system_name, smis_ip, smis_port, smis_user, smis_passwd, use_ssl)
        else:
            request = {
                'name' : system_name,
                'system_type' : device_type,
                'ip_address' : ip_address,
                'port_number' : port,
                'user_name' : user_name,
                'password' : passwd
            }      
            
            if(serial_num):
                request['serial_number'] = serial_num
            if(smis_ip):
                request['smis_provider_ip'] = smis_ip
            if(smis_port):
                request['smis_port_number'] = smis_port
            if(use_ssl):
                request['smis_use_ssl'] = use_ssl
            if(smis_user):
                request['smis_user_name'] = smis_user
            if(smis_passwd):
                request['smis_password'] = smis_passwd
                        
            body = json.dumps(request)
            
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                                  StorageSystem.URI_STORAGESYSTEM_LIST,
                                                  body)
        
        o = common.json_decode(s)
        return o
    
    def register_smis_provider(self, name):
        smis_provider = None
        providers = self.smis_device_list()
        for provider in providers:
            smisprovider = self.smis_device_show_by_uri(provider['id'])
            if (smisprovider['name'] == name):
                smis_provider = smisprovider
                break
        
        if(smis_provider and "storage_systems" in smis_provider 
           and len(smis_provider['storage_systems']) > 0):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                                 StorageSystem.URI_STORAGESYSTEM_REGISTER.format(smis_provider['id'],
                                                 smis_provider['storage_systems'][0]), None, None)
        else:
            raise SOSError(SOSError.NOT_FOUND_ERR, "Storage system: " + name + 
                           " is not discovered.")
        o = common.json_decode(s)
        return o
    
    def unregister_storagesystem(self, serial_number):
        
        system_id = self.query_by_serial_number(serial_number)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                                  StorageSystem.URI_STORAGESYSTEM_UNREGISTER.format(system_id),
                                                  None, None)
        if(s):
            o = common.json_decode(s)
            return o
        return
    
    def query_by_serial_number_and_type(self, serial_number, system_type):
        serial_num_length = len(serial_number)
        
        if(serial_num_length < 3):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                       'The serial number: ' + serial_number + ' is invalid')
        systems = self.list_systems()
        for system in systems:
            storage_system = self.show_by_uri(system['id'])
            if ("serial_number" in storage_system and "system_type" in storage_system
                and system_type == storage_system["system_type"] and
                storage_system['serial_number'].endswith(serial_number)):
                return system['id']
           
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       'Storage system not found with serial number: ' + serial_number + ' and type : '+system_type)
    
    def query_by_name_and_type(self, name, system_type):
        
        systems = self.list_systems()
        for system in systems:
            storage_system = self.show_by_uri(system['id'])
            if ("name" in storage_system and "system_type" in storage_system
                and system_type == storage_system["system_type"] and
                name == storage_system['name']):
                return system['id']
            
            if ("name" not in storage_system and "native_guid" in storage_system and "system_type" in storage_system
                and system_type == storage_system["system_type"] and
                name == storage_system['native_guid']):
                return system['id']
           
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       'Storage system not found with name: ' + name + ' and type : '+system_type)
    
    def query_by_serial_number(self, serial_number):
        serial_num_length = len(serial_number)
        
        if(serial_num_length < 3):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                       'The serial number: ' + serial_number + ' is invalid')
        systems = self.list_systems()
        for system in systems:
            storage_system = self.show_by_uri(system['id'])
            if ("serial_number" in storage_system 
                and
                storage_system['serial_number'].endswith(serial_number)):
                return system['id']
           
        raise SOSError(SOSError.NOT_FOUND_ERR,
                       'Storage system not found with serial number: ' + serial_number)    
    
    
    def list_systems(self):
        '''
        Makes a REST API call to retrieve list of all storage systems
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             StorageSystem.URI_STORAGESYSTEM_LIST,
                                             None)
        o = common.json_decode(s)
        
        if(not o or "storage_system" not in o):
            return []
        
        return common.get_node_value(o, 'storage_system')
       
    def list_systems_by_query(self, **attribval):
        '''
        Returns all storage systems
        Parameters:
            type={device type}: returns list of systems based on given type
            None: returns list of all systems
        Returns:
            Response payload of storage system list
        '''
        output = []
        systems = self.list_systems()
        for item in systems:
            system = self.show_by_uri(item['id'])
            if(system and system["inactive"] == False): 
                if(len(attribval) == 0):
                    output.append(system)
                elif("type" in attribval):
                    if(attribval["type"] == system["system_type"]):
                        output.append(system)
                elif("serialnum" in attribval and "serial_number" in system):
                    if(attribval["serialnum"] == system["serial_number"]):
                        output.append(system)
                elif("name" in attribval and "name" in system):
                    if(attribval["name"] == system["name"]):
                        output.append(system)
                #Adding native_guid comparison for name check as CLI populates the native_guid as the name of
                #the array if there is no 'name' attribute for the array system from API.
                elif("name" in attribval and "name" not in system and "native_guid" in system):
                    if(attribval["name"] == system["native_guid"]):
                        output.append(system)
        return output
    
    def ps_connectivity_show(self, type, serialnum):
        '''
        Makes a REST API call to retrieve details of a storage system based on its UUID
        '''
        
        storage_system_id = self.query_by_serial_number_and_type(serialnum, type)
         
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             StorageSystem.URI_STORAGESYSTEM_CONNECTIVITY.format(storage_system_id),
                                             None, None)
        return  common.json_decode(s)
      


 
    def show_by_uri(self, uri, xml=False):
        '''
        Makes a REST API call to retrieve details of a storage system based on its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             StorageSystem.URI_STORAGESYSTEM_DETAILS.format(uri),
                                             None, None)        
        o = common.json_decode(s)
        inactive = common.get_node_value(o, 'inactive')
        
        if(inactive == True):
            return None
        if(xml == True):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             StorageSystem.URI_STORAGESYSTEM_DETAILS.format(uri),
                                             None, None, xml)
            return s
        else:
            return o
        
    
    
    def show(self, xml=False, **attribval):
        
        '''
        Returns details of a storage system based on its name or UUID
        Parameters:
            name: name of storage system
            serialnum : serial number of storage system
            type: type of storage system
        Returns:
            a Response payload of system details
        Throws:
            SOSError - if id or name not found
        '''

        if("serialnum" in attribval and "type" in attribval):
            storage_system_id = self.query_by_serial_number_and_type(attribval["serialnum"], attribval["type"])
            return self.show_by_uri(storage_system_id, xml)
        
        elif("name" in attribval and "type" in attribval):
            storage_systems = self.list_systems_by_query(type=attribval["type"])
            if(len(storage_systems) > 0):
                for system in storage_systems:
                    if( ( ("name" in system and system["name"] == attribval["name"])
                        or("name" not in system and "native_guid" in system and system["native_guid"] == attribval["name"]) )
                        and 
                       (system["system_type"] == attribval["type"])):
                        return self.show_by_uri(system['id'], xml)
                
                smis_providers = self.smis_device_list()
                for item in smis_providers:
                    provider = self.smis_device_show_by_uri(item['id'])
                    if(provider["name"] == attribval["name"]):
                        if("storage_systems"in provider and provider["storage_systems"]):
                            return self.show_by_uri(provider["storage_systems"][0], xml)
                            
            raise SOSError(SOSError.NOT_FOUND_ERR,
                            "Storage system with name: " + 
                            attribval["name"] + " of type: " + 
                            attribval["type"] + " not found")
        
    def show_by_name(self, name):
        '''
        Returns details of a storage system based on its name or UUID
        Parameters:
            name: name of storage system
        Returns:
            a Response payload of system details
        Throws:
            SOSError - if id or name not found
        '''
        
        storage_systems = self.list_systems_by_query()
        if(len(storage_systems) > 0):
            for system in storage_systems:
                if(("name" in system and system["name"] == name)
                   #Adding native_guid comparison for name check as CLI populates the native_guid as the name of
                   #the array if there is no 'name' attribute for the array.
                   or ("name" not in system and "native_guid" in system and system["native_guid"] == name)):
                    return system
            
            smis_providers = self.smis_device_list()
            
            for item in smis_providers:
                provider = self.smis_device_show_by_uri(item['id'])
                if(provider["name"] == name):
                    systems = self.list_systems_by_query(serialnum=provider["storage_systems"][0])
                    if(len(systems) > 0):
                        return systems[0]
                            
            raise SOSError(SOSError.NOT_FOUND_ERR,
                                "Storage system with name: " + 
                                name + " not found")
            
    def delete_storagesystem(self, device_name, device_type):
        '''
        Marks storage system for deletion
        '''
        device_detail = self.show(name=device_name, type=device_type)
        self.delete_by_uri(device_detail['id'])
                    
    def delete_by_uri(self, uri):
        '''
        Makes a REST API call to delete a storage system by its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                             StorageSystem.URI_STORAGESYSTEM_DELETE.format(uri),
                                              None)
        return
    
    def discover_storagesystem(self, device_name=None, serialno = None, device_type=None):
        if(device_name is None or device_type is None or serialno is None):
            self.discover_storagesystem_by_uri()
            return
        
        urideviceid = None
        if(serialno):
            urideviceid = self.query_by_serial_number_and_type(serialno, device_type)
        elif(device_name):
            urideviceidTemp = self.show(name=device_name, type=device_type)
            urideviceid = urideviceidTemp['id']    
        
        self.discover_storagesystem_by_uri(urideviceid)
        return
    
    def discover_storagesystem_by_uri(self, uri=None):
        '''
        Makes a REST API call to discover storage system
        '''
        request_uri = None
        if(uri):
            request_uri = StorageSystem.URI_STORAGESYSTEM_DISCOVER_BY_ID.format(uri)
        else:
            request_uri = StorageSystem.URI_STORAGESYSTEM_DISCOVER_ALL
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST",
                                            request_uri, None)
        return
    
    def update(self, deviceId, body):
        # Do the actual update
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             StorageSystem.URI_STORAGESYSTEM_DETAILS.format(deviceId), body)
        return
    
    #Extracted password reading as a method
    def get_password(self, componentName):
        if sys.stdin.isatty():
            passwd = getpass.getpass(prompt="Enter password of the "+componentName+": ")
        else:
            passwd = sys.stdin.readline().rstrip()
                
        if (len(passwd) > 0):
            if sys.stdin.isatty():
                confirm_passwd = getpass.getpass(prompt="Retype password: ")
            else:
                confirm_passwd = sys.stdin.readline().rstrip()
            if (confirm_passwd != passwd):
                raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                        " " + sys.argv[2] + ": error: Passwords mismatch")
        else:
            raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                           " " + sys.argv[2] + ": error: Invalid password")
        
        return passwd

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='StorageOS Storage system create CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Creates a storage system')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                help='Name of storage system',
                                metavar='<name>',
                                dest='name',
                                required=True)
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system',
                               required=True)
    create_parser.add_argument('-dip', '-deviceip',
                                help='IP address of storage system',
                                dest='deviceip',
                                metavar='<deviceip>')
    create_parser.add_argument('-dp', '-deviceport',
                                type=int,
                                dest='deviceport',
                                metavar='<deviceport>',
                                help='Port number of storage system')
    create_parser.add_argument('-u', '-user',
                                dest='user',
                                metavar='<username>',
                                help='Username of storage system')
    create_parser.add_argument('-sn', '-serialnumber',
                               dest='serialnum',
                               metavar='<serialnumber>',
                               help='Serial number of the storage system')
    create_parser.add_argument('-smisip',
                               dest='smisip',
                               metavar='<smisip>',
                               help='IP address of SMIS provider')
    create_parser.add_argument('-sp', '-smisport',
                               dest='smisport',
                               metavar='<smisport>',
                               type=int,
                               help='Port number of SMIS provider')
    create_parser.add_argument('-su', '-smisuser',
                               dest='smisuser',
                               metavar='<smisuser>',
                               help='Username of SMIS provider')
    create_parser.add_argument('-ssl', '-usessl',
                               dest='usessl',
                               action='store_true',
                               help='Use SSL or not')
    create_parser.set_defaults(func=storagesystem_create)
    

'''
Function to pre-process all the checks necessary for create storage system 
and invoke the create call after pre-propcessing is passed
'''
def storagesystem_create(args):
    
    #VNXBlock and VMAX are SMIS managed devices. To get the manageability of such devices requires 
    #Registering/creating SMI-S server which manages the underneath arrays.
    if (args.type in ['vnxblock', 'vmax']):
        validate_smis_props(args)
    #VNXFile requires both 1) Device props and 2) SMI-S Props
    #SMI-S provider is used to generate indications
    elif (args.type == 'vnxfile'):
        validate_device_props(args)
        validate_smis_props(args)        
    else:
        validate_device_props(args)
            
    obj = StorageSystem(args.ip, args.port)
    passwd = None
    if (args.user and len(args.user) > 0):
        passwd = obj.get_password("storage system")
            
    smis_passwd = None
    if (args.smisuser and len(args.smisuser) > 0):
        smis_passwd = obj.get_password("SMI-S provider")        
    
    try:
        if (not args.usessl):
            args.usessl = False
            
        res = obj.create(args.name, args.type,
                         args.deviceip, args.deviceport,
                         args.user, passwd,
                         args.serialnum, args.smisip,
                         args.smisport, args.usessl,
                         args.smisuser, smis_passwd)
    except SOSError as e:
        common.print_err_msg_and_exit("create", "storagesystem", e.err_text, e.err_code)
        
'''
This method checks if SMI-S provider properties are supplied or not
'''
def validate_smis_props(arguments):
    if(arguments.smisip is None or arguments.smisport is None or arguments.smisuser is None):
        errorMessage = "For device type "+arguments.type+" -smisuser, -smisip and -smisport are required"
        common.print_err_msg_and_exit("create", "storagesystem", errorMessage, SOSError.CMD_LINE_ERR)
    
    #Here means, SMI-S props are supplied
    #check if the SMI-S port is valid one
    if(not common.validate_port_number(arguments.smisport)):
        errorMessage = "-smisport " +  str(arguments.smisport) + " is not a valid port number"
        common.print_err_msg_and_exit("create", "storagesystem", errorMessage, SOSError.CMD_LINE_ERR)

'''
This method validates the properties required for the storage system not managed by SMI-S provider
'''
def validate_device_props(arguments):
    if(arguments.deviceip is None or arguments.deviceport is None or arguments.user is None):
        errorMessage = "For device type "+arguments.type+" -user, -deviceip, and -deviceport are required"
        common.print_err_msg_and_exit("create", "storagesystem", errorMessage, SOSError.CMD_LINE_ERR)
    
    #Here means, device props are supplied
    #check if the device port is valid one
    if(not common.validate_port_number(arguments.deviceport)):
        errorMessage = "-deviceport " +  str(arguments.deviceport) + " is not a valid port number"
        common.print_err_msg_and_exit("create", "storagesystem", errorMessage, SOSError.CMD_LINE_ERR)
        


        
def delete_parser(subcommand_parsers, common_parser):
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='StorageOS Storage system delete CLI usage ',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Deletes a storage system')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-n', '-name',
                             metavar='<name>',
                             dest='name',
                             help='Name of storage system',
                             required=True)
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system',
                               required=True)
    delete_parser.set_defaults(func=storagesystem_delete)

def storagesystem_delete(args):
    obj = StorageSystem(args.ip, args.port)
    try:
        obj.delete_storagesystem(args.name, args.type)
    except SOSError as e:
        raise e
    

def discover_parser(subcommand_parsers, common_parser):
    discover_parser = subcommand_parsers.add_parser('discover',
                                description='StorageOS Storage system discover CLI usage ',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Manually discover storage system')
    dis_arggroup = discover_parser.add_mutually_exclusive_group(required=False)
    dis_arggroup.add_argument('-n', '-name',
                             metavar='<name>',
                             dest='name',
                             help='Name of storage system')
    dis_arggroup.add_argument('-serialnumber', '-sn',
                                metavar="<serialnumber>",
                                help='Serial Number of the storage system',
                                dest='serialnumber')
    
    discover_parser.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system')
    discover_parser.add_argument('-a', '-all',
                               dest='all',
                               action='store_true',
                               help='Discover all registered storage systems')
    discover_parser.set_defaults(func=storagesystem_discover)

def storagesystem_discover(args):
    obj = StorageSystem(args.ip, args.port)
    # discover storage all 
    if(args.all):
        obj.discover_storagesystem()
        return
    # discover specific storage system by type
    if( (args.type != None and args.name != None) or 
        (args.type != None and args.serialnumber != None)  ):
        return obj.discover_storagesystem(args.name, args.serialnumber, args.type)
    else:
        raise SOSError(SOSError.CMD_LINE_ERR, "error: both (-n/-name or -sn/-serialnumber) and -t/-type are required")
        
    

def register_parser(subcommand_parsers, common_parser):
    # register command parser
    register_parser = subcommand_parsers.add_parser('register',
                                description='StorageOS Storage system registration CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Register a storage system')
    mandatory_args = register_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                               dest='name',
                               metavar='<name>',
                               help='name of the storage system',
                               required=True)
    register_parser.set_defaults(func=storagesystem_register)

def storagesystem_register(args):
    obj = StorageSystem(args.ip, args.port)
    try:
        obj.register_smis_provider(args.name)
    except SOSError as e:
        raise e
    

def unregister_parser(subcommand_parsers, common_parser):
    # unregister command parser
    unregister_parser = subcommand_parsers.add_parser('deregister',
                                description='StorageOS Storage system de-registration CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Unregister a storage system')
    mandatory_args = unregister_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-sn', '-serialnumber',
                               dest='serialnum',
                               metavar='<serialnumber>',
                               help='Serial number of the storage system',
                               required=True)
    unregister_parser.set_defaults(func=storagesystem_unregister)

def storagesystem_unregister(args):
    obj = StorageSystem(args.ip, args.port)
    try:
        obj.unregister_storagesystem(args.serialnum)
        
    except SOSError as e:
        if (e.err_code == SOSError.NOT_FOUND_ERR):
            common.print_err_msg_and_exit("deregister", "storagesystem", e.err_text, e.err_code)
        else:
            raise e

# show command parser
def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                description='StorageOS Storage system Show CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show storage system details')
    show_parser.add_argument('-xml',
                               dest='xml',
                               action='store_true',
                               help='XML response')
    mutex_group = show_parser.add_mutually_exclusive_group(required=True)
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-t', '-type',
                             dest='type',
                             help='Type of storage system',
                             choices=StorageSystem.SYSTEM_TYPE_LIST,
                             required=True)
    mutex_group.add_argument('-n', '-name',
                             metavar='<name>',
                             dest='name',
                             help='Name of storage system')
    mutex_group.add_argument('-sn', '-serialnumber',
                               dest='serialnum',
                               metavar='<serialnumber>',
                               help='Serial number of the storage system')
    

    show_parser.set_defaults(func=storagesystem_show)

def storagesystem_show(args):
    obj = StorageSystem(args.ip, args.port)
    try:
        if(args.serialnum):
            res = obj.show(args.xml, serialnum=args.serialnum, type=args.type)
        else:
            res = obj.show(args.xml, name=args.name, type=args.type)
            
        if(args.xml):
            return common.format_xml(res)
        return common.format_json_object(res)
    except SOSError as e:
        raise e
    
# connectivity command parser
def ps_con_parser(subcommand_parsers, common_parser):
    ps_con_parser = subcommand_parsers.add_parser('connectivity',
                                description='StorageOS Storage system connectivity with protection system CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show protection system connectivity details')
    mandatory_args = ps_con_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-t', '-type',
                             dest='type',
                             help='Type of storage system',
                             choices=StorageSystem.SYSTEM_TYPE_LIST,
                             required=True)
    mandatory_args.add_argument('-sn', '-serialnumber',
                               dest='serialnum',
                               metavar='<serialnumber>',
                               help='Serial number of the storage system',
                               required=True)


    ps_con_parser.set_defaults(func=ps_connectivity_show)

def ps_connectivity_show(args):
    obj = StorageSystem(args.ip, args.port)
    try:
        res = obj.ps_connectivity_show(args.type, args.serialnum)
        return common.format_json_object(res)
    except SOSError as e:
        raise e


# list command parser
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                description='StorageOS Storage system List CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Lists storage systems')
    list_parser.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system')
    list_parser.add_argument('-v', '-verbose',
                             dest='verbose',
                             action='store_true',
                             help='Lists storage systems with details')
    list_parser.add_argument('-l', '-long',
                             dest='largetable',
                             action='store_true',
                             help='Lists storage systems in a large table')
    list_parser.set_defaults(func=storagesystem_list)

def storagesystem_list(args):
    from common import TableGenerator
    obj = StorageSystem(args.ip, args.port)
    try:
        smis_provider_id_list = obj.smis_device_list()
        smis_provider_list = []
        for item in smis_provider_id_list:
            smis_provider_list.append(obj.smis_device_show_by_uri(item['id']))
        if(args.type is None):
            storage_system_list = obj.list_systems_by_query()
            output = populate_name_from_native_guid(storage_system_list)
            output = remove_duplicates_by_id(smis_provider_list, output)
        else:
            storage_system_list = obj.list_systems_by_query(type=args.type)
            result = populate_name_from_native_guid(storage_system_list)
            result = remove_duplicates_by_id(smis_provider_list, result)
            output = []
            for record in result:
                if("system_type" in record and record["system_type"]):
                    output.append(record)

        if(len(output) > 0):
            if(args.verbose == True):
                return common.format_json_object(output)
            else:
                for record in output:
                    if("export_masks" in record):
                        record["export_masks"] = None
                    if("ip_address" not in record or record["ip_address"] is None):
                        if("smis_ip_address" in record and record["smis_ip_address"]):
                            record["ip_Address"] = record["smis_ip_address"]
                    if("port_number" not in record or record["port_number"] is None):
                        if("smis_port_number" in record and record["smis_port_number"]):
                            record["port_number"] = record["smis_port_number"]
                if(args.largetable == True):
                    TableGenerator(output, ['name', 'provider_name','system_type', 'serial_number',
                                            'ip_address', 'port_number', 'registration_status',
                                            'smis_use_ssl', 'job_discovery_status']).printTable()
                else:
                    TableGenerator(output, ['name', 'provider_name', 'system_type', 'serial_number']).printTable()
        else:
            return 
    except SOSError as e:
        raise e
    
def populate_name_from_native_guid(storage_system_list):
    output = []
    for system in storage_system_list:
        output.append(system);
        
        if("name" not in system and "native_guid" in system):
            system["name"] = system["native_guid"]        
    
    return output

def remove_duplicates_by_id(smis_provider_list, storage_system_list):
    
    output = []
    for system in storage_system_list:
        output.append(system);
#        if("name" not in system):
        if("active_provider_uri" in system and 
           system["active_provider_uri"]):
            for provider in smis_provider_list:
                provider_uri = system["active_provider_uri"]
                if(provider != None):
                    if(provider["id"] == provider_uri["id"]):
                        system["provider_name"] = provider["name"]
                    # smis_provider_list.remove(provider)
                    
    for provider in smis_provider_list:
        if(provider != None):
            if(provider["inactive"] == False and provider["job_scan_status"] != "COMPLETE"):
                provider["provider_name"] = provider["name"]
                del provider["name"]
                output.append(provider)
        
    return output

# update command parser
def update_parser(subcommand_parsers, common_parser):
    update_parser = subcommand_parsers.add_parser('update',
                                description='StorageOS Storage system Update CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Updates a storage system')
    mandatory_args = update_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-n', '-name',
                                metavar='<name>',
                                dest='name',
                                help='Name of existing storage system to be updated',
                                required=True)
    mandatory_args.add_argument('-t', '-type',
                               choices=StorageSystem.SYSTEM_TYPE_LIST,
                               dest='type',
                               help='Type of storage system',
                               required=True)
    
    update_parser.add_argument('-mr','-maxresources',
                                metavar='<maxresources>',
                                dest='maxresources',
                                help='Maximum number of resources')
    update_parser.add_argument('-nn', '-newname',
                                metavar='<newname>',
                                dest='newname',
                                help='New name of storage system')
    update_parser.add_argument('-ndip', '-newipaddress',
                                metavar='<newipaddress>',
                                dest='newipaddress',
                                help='New IP address of storage system')
    update_parser.add_argument('-ndp', '-newport',
                                metavar='<newport>',
                                dest='newport',
                                help='New port for storage system')
    update_parser.add_argument('-nun', '-newusername',
                                metavar='<newusername>',
                                dest='newusername',
                                help='New user name for storage system')
    '''
    Adding these options and commenting for now.
    The current implementation of API for SMI-S update does not validate 
    the connection after its details are updated.
    
    update_parser.add_argument('-nsip', '-newsmisproviderip',
                                metavar='<newsmisproviderip>',
                                dest='newsmisproviderip',
                                help='New smis provider IP address for storage system')
    update_parser.add_argument('-nsp', '-newsmisport',
                                metavar='<newsmisport>',
                                dest='newsmisport',
                                help='New smis port for storage system')
    update_parser.add_argument('-nsun', '-newsmisusername',
                                metavar='<newsmisusername>',
                                dest='newsmisusername',
                                help='New smis user name for storage system')
    update_parser.add_argument('-nspw', '-newsmispassword',
                                metavar='<newsmispassword>',
                                dest='newsmispassword',
                                help='New smis password for storage system')
    update_parser.add_argument('-nssl', '-newsmisusessl',
                                metavar='<newsmisusessl>',
                                dest='newsmisusessl',
                                help='New smis use ssl for storage system')
    '''
    update_parser.set_defaults(func=update_storagesystem)
    
#Update is added only for storage systems as the API does connectivity check during update invoke
#TODO : Need to enhance it for SMI-S provider once API team implements the connectivity check during the update
def update_storagesystem(args):
    
    #Validations
    if(args.newname is None and args.newipaddress is None 
       and args.newport is None and args.newusername is None and args.maxresources is None):
        raise SOSError(SOSError.CMD_LINE_ERR, sys.argv[0] + " " + sys.argv[1] + 
                           " " + sys.argv[2] + ": error:"+ "At least one of the arguments :" 
                                                                                "-newname -newport "
                                                                                "-newipaddress -newusername -maxresources"
                                                                                " should be provided to update the storage system")
    obj = StorageSystem(args.ip, args.port)    
    if(args.newusername and len(args.newusername)>0):
        devicePassword = obj.get_password("storage system")
    
    # Capture the input details of array to be updated.        
    arrayName = args.name
    arrayType = args.type
        
    
    
    #Get the storage systems matching the type and the name
    deviceId = obj.query_by_name_and_type(arrayName, arrayType)
    
    if(deviceId):
        # Found the device. 
        # Create new empty request. 
        request = dict();
        #Add all modifiable attributes to the request
        if(args.newname is not None):
            request["name"] = args.newname
        if(args.newipaddress is not None):
            request["ip_address"] = args.newipaddress
        if(args.newport is not None):
            request["port_number"] = args.newport
        if(args.newusername is not None):
            request["user_name"] = args.newusername
            request["password"] = devicePassword
        if(args.maxresources is not None):
            request["max_resources"] = args.maxresources
            
        '''
        Adding this code for future
        Uncomment once the SMI-S update API validates the connectivity.
        
        if (args.type in ['vnxblock', 'vmax']):
            #Read the SMIS provider info for vnxblock and vmax type arrays
            if(args.newsmisproviderip is not None):
                request["smis_provider_ip"] = args.newsmisproviderip
            if(args.newsmisport is not None):
                request["smis_port_number"] = args.newsmisport
            if(args.newsmisusername is not None):
                request["smis_user_name"] = args.newsmisusername
            if(args.newsmispassword is not None):
                request["smis_password"] = args.newsmispassword
            if(args.newsmisusessl is not None):
                request["smis_use_ssl"] = args.newsmisusessl
        '''
        
        # Convert the request into json format
        body = json.dumps(request)
        
        #Call the update API
        obj.update(deviceId, body)
    
    return
    
#
# Storage device Main parser routine
#
def storagesystem_parser(parent_subparser, common_parser):
    # main storage system parser

    parser = parent_subparser.add_parser('storagesystem',
                                description='StorageOS Storage system CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on storage system')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)
    
    # delete command parser
    delete_parser(subcommand_parsers, common_parser)
    
    # register command parser
    # register_parser(subcommand_parsers, common_parser)
    
    # discover command parser
    discover_parser(subcommand_parsers, common_parser)

    # unregister command parser
    unregister_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # ps_connectivity parser
    ps_con_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)
    
    # update storage system command parser
    update_parser(subcommand_parsers, common_parser)
    



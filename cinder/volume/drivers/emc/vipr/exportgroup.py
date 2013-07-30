#!/usr/bin/python

# Copyright (c) 2012 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


#import python system modules

import common
import argparse
import sys
import os
import volume
from volume import Volume
from snapshot import Snapshot
from common import SOSError
from project import Project
from virtualarray import VirtualArray
import uuid
import json

class ExportGroup(object):
    '''
    The class definition for operations on 'Export group Service'. 
    '''
    URI_EXPORT_GROUP = "/block/exports"
    URI_EXPORT_GROUPS = URI_EXPORT_GROUP + "/?project={0}"
    URI_EXPORT_GROUPS_SHOW = URI_EXPORT_GROUP + "/{0}"
    URI_EXPORT_GROUPS_INITIATOR = URI_EXPORT_GROUP + "/{0}/initiators"
    URI_EXPORT_GROUPS_INITIATOR_INSTANCE = URI_EXPORT_GROUP + "/{0}/initiators/{1}"
    URI_EXPORT_GROUPS_INITIATOR_INSTANCE_DELETE = URI_EXPORT_GROUP + "/{0}/initiators/{1},{2}"
    URI_EXPORT_GROUPS_VOLUME = URI_EXPORT_GROUP + "/{0}/volumes"
    URI_EXPORT_GROUPS_VOLUME_INSTANCE = URI_EXPORT_GROUP + "/{0}/volumes/{1}"
    URI_EXPORT_GROUPS_STORAGEPORTS = URI_EXPORT_GROUP + "/{0}/storage-ports"  
    URI_EXPORT_GROUP_LIST = '/projects/{0}/resources'
    URI_EXPORT_GROUP_SEARCH = '/block/exports/search'
    URI_EXPORT_GROUP_DEACTIVATE = URI_EXPORT_GROUPS_SHOW +  '/deactivate' 
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    def exportgroup_list(self, project, tenant):
        '''
        This function will give us the list of export group uris
        separated by comma.
        prameters:
            project: Name of the project path.
        return
            returns with list of export group ids separated by comma. 
        '''
        if(tenant == None):
            tenant = ""
        projobj = Project(self.__ipAddr, self.__port)
        fullproj = tenant+"/"+project
        projuri = projobj.project_query(fullproj)
        
        uri = self.URI_EXPORT_GROUP_SEARCH
        
        if ('?' in uri):
            uri += '&project=' + projuri 
        else:
            uri += '?project=' + projuri

        # import pdb; pdb.set_trace()
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             uri, None)
        o = common.json_decode(s)
        if not o:
            return []
        
        exportgroups=[]
        resources = common.get_node_value(o, "resource")
        for resource in resources:
            exportgroups.append(resource["id"])
       
        return exportgroups

                     
    def exportgroup_show(self, name, project, tenant, xml = False):
        '''
        This function will take export group name and project name as input and
        It will display the Export group with details.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            returns with Details of export group. 
        '''
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_EXPORT_GROUPS_SHOW.format(uri), None)
        o = common.json_decode(s)
        if( o['inactive']):
           return None

        if(xml == False):
            return o

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             self.URI_EXPORT_GROUPS_SHOW.format(uri), None, None, xml) 

        return s     
    
    def exportgroup_storageports(self, name, project, tenant):
        '''
        This function will take export group name and project name as input and
        It will get the target storage port for  Export group.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            returns storage ports for export group.
        '''
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             self.URI_EXPORT_GROUPS_STORAGEPORTS.format(uri), None)
        return common.json_decode(s)  
    
    def exportgroup_create(self, name, project, tenant, varray):
        '''
        This function will take export group name and project name  as input and
        It will create the Export group with given name.
        parameters:
           name : Name of the export group.
           project: Name of the project path.
           tenant: Container tenant name.
        return
            returns with status of creation. 
        '''
        # check for existance of export group.
        try:
            status = self.exportgroup_show(name, project, tenant)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                if(tenant == None):
                    tenant = ""
                fullproj = tenant + "/" + project
	        projobj = Project(self.__ipAddr, self.__port)
                projuri = projobj.project_query(fullproj) 
				
		nh_obj = VirtualArray(self.__ipAddr, self.__port)
		nhuri = nh_obj.varray_query(varray)
				
		parms = {
			'name' : name,
			'project' : projuri,
			'varray' : nhuri,
			}
                body = json.dumps(parms)
                   
                (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             self.URI_EXPORT_GROUP, body)
                o = common.json_decode(s)
                return o
            else:
                raise e
        if(status):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Export group with name " + name + " already exists")

   
    def exportgroup_delete(self, name, project, tenant):
        '''
        This function will take export group name and project name as input and 
        marks the particular export group as delete.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            return with status of the delete operation.
            false incase it fails to do delete.
        '''
        token = "cli_export_group_delete:" + str(uuid.uuid4())
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                        "POST", 
                        self.URI_EXPORT_GROUP_DEACTIVATE.format(uri), 
                        None, token)
        return
    

    def exportgroup_query(self, name, project, tenant):
        '''
        This function will take export group name/id and project name  as input and 
        returns export group id.
        parameters:
           name : Name/id of the export group.
        return
            return with id of the export group.
         '''
        if (common.is_uri(name)):
            return name

        uris = self.exportgroup_list(project, tenant)
        for uri in uris:
            exportgroup = self.exportgroup_show(uri, project, tenant)
            if(exportgroup):
                if (exportgroup['name'] == name ):
                    return exportgroup['id']    
        raise SOSError(SOSError.NOT_FOUND_ERR, "Export Group " + name + ": not found")
    
    
    def exportgroup_add_initiator(self, name, project, tenant, protocol, initiatorNode, initiatorPort, hostname):
        #construct the body 
        
        token = "cli_export_group_add_initiator:" + str(uuid.uuid4())
       
        initParam = dict()
        initParam['protocol'] = protocol
        initParam['initiator_node'] = initiatorNode  
        initParam['initiator_port'] = initiatorPort 
        initParam['hostname'] = hostname

	parms = {
           'initiator' : [ initParam ]
        }
		
        body = json.dumps(parms)
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                        "POST", self.URI_EXPORT_GROUPS_INITIATOR.format(uri), 
                        body, token)
        o = common.json_decode(s)
        return o

    def exportgroup_remove_initiators(self, name, project, tenant, protocol, initiator):
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                 "DELETE", self.URI_EXPORT_GROUPS_INITIATOR_INSTANCE_DELETE.format(uri, protocol, initiator), 
                 None)
        o = common.json_decode(s)
        return o
                    
    def exportgroup_add_volumes(self, name, project, tenant, volume, lun, snapshot):
        if(tenant == None):
            tenant = ""
	fullvolname = tenant+"/"+project+"/"+volume
        volobj =  Volume(self.__ipAddr, self.__port)
        volumeURI = volobj.volume_query(fullvolname)

        if(snapshot):
            snapshotobj = Snapshot(self.__ipAddr, self.__port)
            snapuri =   snapshotobj.snapshot_query('block', 'volumes', volumeURI, snapshot)
            volumeURI = snapuri

        #construct the body
        volparms = dict()
        volparms['id'] = volumeURI
        if(lun != None):
            volparms['lun'] = lun
  
        parms = {
            'volume' : [volparms]
        }
			        
        token = "cli_export_group_add_volume:" + fullvolname
        body = json.dumps(parms)
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                        "POST", self.URI_EXPORT_GROUPS_VOLUME.format(uri), 
                        body, token)
        o = common.json_decode(s)
        return o
              
    def exportgroup_remove_volumes(self, name, project, tenant, volume, snapshot):
        if(tenant == None):
            tenant = ""
        volobj =  Volume(self.__ipAddr, self.__port)
        fullvolname = tenant+"/"+project+"/"+volume
        volumeURI = volobj.volume_query(fullvolname)

        if(snapshot):
            snapshotobj = Snapshot(self.__ipAddr, self.__port)
            snapuri =   snapshotobj.snapshot_query('block', 'volumes', volumeURI, snapshot)
            volumeURI = snapuri 
        
        token = "cli_export_group_remove_volume:" + fullvolname
        uri = self.exportgroup_query(name, project, tenant)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, 
                 "DELETE", self.URI_EXPORT_GROUPS_VOLUME_INSTANCE.format(uri, volumeURI), 
                 None, token)
        o = common.json_decode(s)
        return o
              

    
# Export Group Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                description='StorageOS Export Group Create cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Create an Export group')
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group ',
                required=True)  
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='container project name',
                required=True)
    create_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    mandatory_args.add_argument('-varray', '-va',
                metavar='<varray>',
                dest='varray',
                help='varray for export',
                required=True)
    create_parser.set_defaults(func=exportgroup_create)

def exportgroup_create(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        res = obj.exportgroup_create(args.name, args.project, args.tenant, args.varray)
    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR, "Export Group " + args.name + ": Create failed:\n" + e.err_text)
        

# Export group Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                description='StorageOS Export group Delete CLI usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Delete an Export group')
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group ',
                required=True) 
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    delete_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name') 
    delete_parser.set_defaults(func=exportgroup_delete)

def exportgroup_delete(args):
    obj = ExportGroup(args.ip, args.port)
    try:
        res = obj.exportgroup_delete(args.name, args.project, args.tenant)
        return res
    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR, "Export Group " + args.name + ": Delete failed:\n" + e.err_text)
        

# Export group Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                description='StorageOS Export group Show CLI usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Show full details of an Export group' )
    mandatory_args = show_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)  
    show_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    show_parser.add_argument('-xml',
                dest='xml',
                action='store_true',
                help='XML response')


    show_parser.set_defaults(func=exportgroup_show)

def exportgroup_show(args):
    
    obj = ExportGroup(args.ip, args.port)
    try:
        res = obj.exportgroup_show(args.name, args.project, args.tenant, args.xml)
        if(args.xml):
            return common.format_xml(res)

        return common.format_json_object(res)
    except SOSError as e:
        raise e

# Export Group List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                description='StorageOS Export group List CLI usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='List all Export groups'  )
    mandatory_args = list_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    list_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    list_parser.add_argument('-verbose', '-v',
                                dest='verbose',
                                help='Export group list with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List Export groups with details in table format',
                             dest='long')
    list_parser.set_defaults(func=exportgroup_list)

def exportgroup_list(args):
    obj = ExportGroup(args.ip, args.port)
    try:
        uris = obj.exportgroup_list(args.project, args.tenant)
        output = []
        if(len(uris) > 0):
            for uri in uris:
                eg = obj.exportgroup_show(uri, args.project, args.tenant)
                # The following code is to get volume/snapshot name part of export group list.
                if(eg):
                    if("project" in eg and "name" in eg["project"]):
                        del eg["project"]["name"]
                    volumeuris = common.get_node_value(eg, "volumes")
                    volobj = Volume(args.ip, args.port)
                    snapobj = Snapshot(args.ip, args.port)
                    volnames = []
                    strvol = ""
                    for volumeuri in volumeuris:
                        strvol = str(volumeuri['id'])
                        if(strvol.find('urn:storageos:Volume') >= 0):
                            vol = volobj.show_by_uri(strvol)
                            if(vol):
                                volnames.append(vol['name'])
                        elif(strvol.find('urn:storageos:BlockSnapshot')>= 0):
                            snapshot = snapobj.snapshot_show_uri('block', strvol)
                            if(snapshot):
                                volnames.append(snapshot['name'])
                    eg['volumes_snapshots']=volnames
                    output.append(eg)
            
	    if(args.verbose == True):
                return common.format_json_object(output)
            if(len(output) > 0):
                if(args.long == True):
                    from common import TableGenerator
                    TableGenerator(output, ['name', 'volumes_snapshots','initiator_node', 'initiator_port']).printTable()

                else:
                    from common import TableGenerator
                    TableGenerator(output, ['name']).printTable()

    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR, "Export group list failed:\n" + e.err_text)


# Export Group Add Volume routines

def add_volumes_parser(subcommand_parsers, common_parser):
    # add command parser
    add_volumes_parser = subcommand_parsers.add_parser('add_vol',
                description='StorageOS Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add a volume to an Export group')
    mandatory_args = add_volumes_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-volume', '-v',
                metavar='<Volume>',
                dest='volume',
                help='Volume name',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    add_volumes_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    add_volumes_parser.add_argument('-lun', '-l',
                metavar='<Logicalunitnumber>',
                dest='lun',
                help='Logical Unit Number')
    add_volumes_parser.add_argument('-snapshot', '-sh',
                metavar='<Snapshot for volume>',
                dest='snapshot',
                help='Snap shot for a volume')
    add_volumes_parser.set_defaults(func=exportgroup_add_volumes)

def exportgroup_add_volumes(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        res = obj.exportgroup_add_volumes(args.name, args.project, args.tenant, args.volume, args.lun, args.snapshot)
    except SOSError as e:
        if(args.snapshot):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Add Volume Snapshot  " + args.snapshot + ": failed:\n" + e.err_text)
        else:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Add Volume  " + args.volume + ": failed:\n" + e.err_text)
        
# Export Group Remove Volume routines

def remove_volumes_parser(subcommand_parsers, common_parser):
    # remove command parser
    remove_volumes_parser = subcommand_parsers.add_parser('remove_vol',
                description='StorageOS Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove a volume from Export group')
    mandatory_args = remove_volumes_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group ',
                required=True)  
    mandatory_args.add_argument('-volume', '-v',
                metavar='<Volume>',
                dest='volume',
                help='Volume name ',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    remove_volumes_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    remove_volumes_parser.add_argument('-snapshot', '-sh',
                metavar='<Snapshot for volume>',
                dest='snapshot',
                help='Snap shot for a volume')
    remove_volumes_parser.set_defaults(func=exportgroup_remove_volumes)

def exportgroup_remove_volumes(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        res = obj.exportgroup_remove_volumes(args.name, args.project, args.tenant, args.volume, args.snapshot)
    except SOSError as e:
        if(args.snapshot):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Remove Volume Snapshot " + args.snapshot + ": failed:\n" + e.err_text)
        else:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Remove Volume " + args.volume + ": failed:\n" + e.err_text) 
        

# Export Group Add Initiator routines

def add_initiators_parser(subcommand_parsers, common_parser):
    # add initiator command parser
    add_initiators_parser = subcommand_parsers.add_parser('add_initiator',
                description='StorageOS Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add an initiator to  Export group')
    mandatory_args = add_initiators_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-protocol', '-pl',
                metavar='<Protocol>',
                dest='protocol',
                help='Protocol',
                required=True)
    add_initiators_parser.add_argument('-initiatorNode', '-inn',
                metavar='<InitiatorNode>',
                dest='initiatorNode',
                help='Initiator Node')
    mandatory_args.add_argument('-initiatorPort', '-inp',
                metavar='<InitiatorPort>',
                dest='initiatorPort',
                help='Initiator Port',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    add_initiators_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    mandatory_args.add_argument('-hostid', '-hid',
                metavar='<HostName>',
                dest='hostname',
                help='Name of the host',
                required=True)
    add_initiators_parser.set_defaults(func=exportgroup_add_Initiators)

def exportgroup_add_Initiators(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        if(args.protocol == "FC" and args.initiatorNode == None):
            return SOSError(SOSError.SOS_FAILURE_ERR, "argument -initiatorNode/-inn is required for " + args.protocol + " protocol")

        res = obj.exportgroup_add_initiator(args.name,
                                       args.project,  
                                       args.tenant,    
                                       args.protocol, 
                                       args.initiatorNode, 
                                       args.initiatorPort,
				       args.hostname)
    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR, "Add initiator " + str(args.initiatorPort) + ": failed:\n" + e.err_text)
        
# Export Group Remove Initiators routines

def remove_initiators_parser(subcommand_parsers, common_parser):
    # create command parser
    remove_initiators_parser = subcommand_parsers.add_parser('remove_initiator',
                description='StorageOS Export group Remove initiator cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove an initiator from Export group')
    mandatory_args = remove_initiators_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-initiator', '-in',
                metavar='<InitiatorSpec>',
                dest='initiator',
                help='Initiator port specification',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    remove_initiators_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    mandatory_args.add_argument('-protocol', '-pl',
                metavar='<protocol>',
                dest='protocol',
                help='Protocol ',
                required=True)
    remove_initiators_parser.set_defaults(func=exportgroup_remove_initiators)

def exportgroup_remove_initiators(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        res = obj.exportgroup_remove_initiators(args.name, args.project, args.tenant, args.protocol, args.initiator)
    except SOSError as e:
        raise SOSError(SOSError.SOS_FAILURE_ERR,"Remove initiator " + args.initiator + ": failed:\n" + e.err_text) 
        
# Export group get storage-ports routines

def storageports_parser(subcommand_parsers, common_parser):
    # storageports  command parser
    storageports_parser = subcommand_parsers.add_parser('get_ports',
                description='StorageOS Export group get storage ports CLI usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Get the target storage ports for Export group' )
    mandatory_args = storageports_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    storageports_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    storageports_parser.set_defaults(func=exportgroup_storageports)

def exportgroup_storageports(args):

    obj = ExportGroup(args.ip, args.port)
    try:
        res = obj.exportgroup_storageports(args.name, args.project, args.tenant)
        return common.format_json_object(res)
    except SOSError as e:
        raise e



      
#
# ExportGroup Main parser routine
#

def exportgroup_parser(parent_subparser, common_parser):

    # main export group parser
    parser = parent_subparser.add_parser('exportgroup',
                description='StorageOS Export Group cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Operations on Export group')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # add volumes to host command parser
    add_volumes_parser(subcommand_parsers, common_parser)
    
    # remove volumes from host command parser
    remove_volumes_parser(subcommand_parsers, common_parser)

    # add initiators to host command parser
    add_initiators_parser(subcommand_parsers, common_parser)

    # remove initiators to host command parser
    remove_initiators_parser(subcommand_parsers, common_parser)

    # get target storage ports command parser
    #storageports_parser(subcommand_parsers, common_parser)


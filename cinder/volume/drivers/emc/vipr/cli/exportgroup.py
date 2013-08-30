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
from volume import Volume
from snapshot import Snapshot
from common import SOSError
from project import Project
from cluster import Cluster
from hostinitiators import HostInitiator
from host import Host
from virtualarray import VirtualArray
import uuid
import json

class ExportGroup(object):
    '''
    The class definition for operations on 'Export group Service'. 
    '''
    URI_EXPORT_GROUP = "/block/exports"
    URI_EXPORT_GROUPS_SHOW = URI_EXPORT_GROUP + "/{0}"
    URI_EXPORT_GROUP_LIST = '/projects/{0}/resources'
    URI_EXPORT_GROUP_SEARCH = '/block/exports/search'
    URI_EXPORT_GROUP_DEACTIVATE = URI_EXPORT_GROUPS_SHOW +  '/deactivate'
    URI_EXPORT_GROUP_UPDATE = '/block/exports/{0}'
    EXPORTGROUP_TYPE = ['Exclusive', 'Host', 'Cluster']
                         
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. These are
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
    
    
    def exportgroup_create(self, name, project, tenant, varray, exportgrouptype, export_destination=None):
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
                projuri = Project(self.__ipAddr, self.__port).project_query(fullproj) 
                nhuri = VirtualArray(self.__ipAddr, self.__port).varray_query(varray)
                
                parms = {
                'name' : name,
                'project' : projuri,
                'varray' : nhuri,
                'type' :exportgrouptype
                }
                if(exportgrouptype and export_destination):
                    if (exportgrouptype == 'Cluster'):
                        cluster_obj = Cluster(self.__ipAddr, self.__port)
                        try:
                            cluster_uri = cluster_obj.cluster_query(export_destination, fullproj)
                        except SOSError as e:
                            raise e
                        parms['clusters'] = [cluster_uri]
                    elif (exportgrouptype == 'Host'):
                        host_obj = Host(self.__ipAddr, self.__port)
                        try:
                            host_uri = host_obj.query_by_name(export_destination)
                        except SOSError as e:
                            raise e
                        parms['hosts'] = [host_uri]
                    # else:   # exportgrouptype == Exclusive
                        # TODO: add code for initiator                 
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
    

        
    
        '''
        add volume to export group
        parameters:
           exportgroupname : Name/id of the export group.
           tenantname      : tenant name
           projectname         : name of project
           volumename      : name of volume that need to be added to exportgroup
           lunid           : lun id
        return
            return action result
         '''        
    def exportgroup_add_volumes(self, exportgroupname, tenantname, projectname, volumename, snapshot = None, lunid = None, cg=None):
        
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        
        #get volume uri
        if(tenantname == None):
            tenantname = "" 
        fullvolname = tenantname+"/"+projectname+"/"+volumename
        vol_uri =  Volume(self.__ipAddr, self.__port).volume_query(fullvolname)
        
        #if snapshot given then snapshot added to exportgroup
        if(snapshot):
            if(cg):
                blockTypeName = 'consistency-groups'
                from consistencygroup import ConsistencyGroup
                resuri = ConsistencyGroup(self.__ipAddr, self.__port).consistencygroup_query(cg, projectname, tenantname) 
            else:
                blockTypeName = 'volumes'    
                resuri = vol_uri
                
            snapshot_uri = Snapshot(self.__ipAddr, self.__port).snapshot_query('block', blockTypeName, resuri, snapshot)
            #snapshot is exported or snapshot is added export group
            vol_uri =   snapshot_uri

        parms = {}
        #construct the body

        volparms = dict()
        volparms['id'] = vol_uri
        if(lunid != None):
            volparms['lun'] = lunid

        volumeEntries = []
        volumeEntries.append(volparms)
        
        volChanges = {}
        volChanges['add'] = volumeEntries
        parms['volume_changes'] = volChanges
        return self.send_json_request(exportgroup_uri, parms)
        
    def exportgroup_remove_volumes(self, exportgroupname, tenantname, projectname, volumename, snapshot=None, cg=None):
        
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)

        #get volume uri
        if(tenantname == None):
            tenantname = ""
        fullvolname = tenantname+"/"+projectname+"/"+volumename
        vol_uri =  Volume(self.__ipAddr, self.__port).volume_query(fullvolname)
                  
         #if snapshot given then snapshot added to exportgroup
        if(snapshot):
            if(cg):
                blockTypeName = 'consistency-groups'
                from consistencygroup import ConsistencyGroup
                resuri = ConsistencyGroup(self.__ipAddr, self.__port).consistencygroup_query(cg, projectname, tenantname) 
            else:
                blockTypeName = 'volumes'    
                resuri = vol_uri
                
            snapshot_uri = Snapshot(self.__ipAddr, self.__port).snapshot_query('block', blockTypeName, resuri, snapshot)
            #snapshot is exported or snapshot is added export group
            vol_uri =   snapshot_uri

        parms = {}

        parms['volume_changes'] = self._remove_list(vol_uri)
        
        return self.send_json_request(exportgroup_uri, parms)
    
    # initator
        '''
        add initiator to export group
        parameters:
           exportgroupname     : Name/id of the export group.
           tenantname          : tenant name
           projectname         : name of project
           initator            : name of initiator
           hostlabel           : name of host or host label
        return
            return action result
         '''
    def exportgroup_add_initiator(self, exportgroupname, tenantname, projectname, initator, hostlabel):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        initiator_uri = HostInitiator(self.__ipAddr, self.__port).query_by_portwwn(initator, hostlabel)
        parms = {}
        #initiator_changes
        parms['initiator_changes'] = self._add_list(initiator_uri)
        
        return self.send_json_request(exportgroup_uri, parms)        

    def exportgroup_remove_initiator(self, exportgroupname, tenantname, projectname, initator, hostlabel):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        initiator_uri = HostInitiator(self.__ipAddr, self.__port).query_by_portwwn(initator, hostlabel)
        parms = {}
        #initiator_changes
        parms['initiator_changes'] = self._remove_list(initiator_uri)
        return self.send_json_request(exportgroup_uri, parms)    


    #cluster
        '''
        add cluster to export group
        parameters:
           exportgroupname : Name/id of the export group.
           tenantname      : tenant name
           projectname     : name of project
           clustername     : name of cluster
        return
            return action result
         '''
    def exportgroup_add_cluster(self, exportgroupname, tenantname, projectname, clustername):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        cluster_uri = Cluster(self.__ipAddr, self.__port).cluster_query(clustername, projectname, tenantname)
        parms = {}
        parms['cluster_changes'] = self._add_list(cluster_uri)
        return self.send_json_request(exportgroup_uri, parms)
    
    
    def exportgroup_remove_cluster(self, exportgroupname, tenantname, projectname, clustername):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        cluster_uri = Cluster(self.__ipAddr, self.__port).cluster_query(clustername, projectname, tenantname)
        parms = {}
        parms['cluster_changes'] = self._remove_list(cluster_uri)
        return self.send_json_request(exportgroup_uri, parms)
    
    #host
        '''
        add host to export group
        parameters:
           exportgroupname     : Name/id of the export group.
           tenantname          : tenant name
           projectname         : name of project
           hostlabel           : name of host
        return
            return action result
         '''
    def exportgroup_add_host(self, exportgroupname, tenantname, projectname, hostlabel):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)

        host_uri = Host(self.__ipAddr, self.__port).query_by_name(hostlabel, tenantname)

        parms = {}
        parms['host_changes'] = self._add_list(host_uri)
        return self.send_json_request(exportgroup_uri, parms)
    
    def exportgroup_remove_host(self, exportgroupname, tenantname, projectname, hostlabel):
        exportgroup_uri = self.exportgroup_query(exportgroupname, projectname, tenantname)
        host_uri = Host(self.__ipAddr, self.__port).query_by_name(hostlabel, tenantname)
        parms = {}
        parms['host_changes'] = self._remove_list(host_uri)
        return self.send_json_request(exportgroup_uri, parms)
    
    #helper function
    def _add_list(self, uri):

        resEntries = []
        resEntries.append(uri)
        resChanges = {}
        resChanges['add'] = resEntries
        return resChanges

    def _remove_list(self, uri):
        resChanges = {}
        resEntries = []
        resEntries.append(uri)
        resChanges['remove'] = resEntries
        return resChanges

    def send_json_request(self, exportgroup_uri, param):
        body = json.dumps(param)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                            "PUT", self.URI_EXPORT_GROUP_UPDATE.format(exportgroup_uri), body)
        return common.json_decode(s)

    
# Export Group Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                description='ViPR Export Group Create cli usage.',
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
    mandatory_args.add_argument('-varray', '-va',
                metavar='<varray>',
                dest='varray',
                help='varray for export',
                required=True)
    create_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    create_parser.add_argument( '-type', '-t',
                help='Type of the ExportGroup type=Exclusive|Host|Cluster.(default:Exclusive)',
                default='Exclusive',
                dest='type',
                metavar='<exportgrouptype>',
                choices=ExportGroup.EXPORTGROUP_TYPE)
    create_parser.add_argument('-exportdestination', '-ed',
                metavar='<exportdestination>',
                dest='export_destination',
                help='name of initiator, host or cluster')
    create_parser.set_defaults(func=exportgroup_create)

def exportgroup_create(args):
    try:
        obj = ExportGroup(args.ip, args.port)
        obj.exportgroup_create(args.name, args.project, args.tenant, args.varray, args.type, args.export_destination)
    except SOSError as e:
        raise common.format_err_msg_and_raise("create", "exportgroup", e.err_text, e.err_code)


# Export group Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                description='ViPR Export group Delete CLI usage.',
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
        obj.exportgroup_delete(args.name, args.project, args.tenant)
    except SOSError as e:
        raise common.format_err_msg_and_raise("delete", "exportgroup", e.err_text, e.err_code)

# Export group Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                description='ViPR Export group Show CLI usage.',
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
        raise common.format_err_msg_and_raise("show", "exportgroup", e.err_text, e.err_code)

# Export Group List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                description='ViPR Export group List CLI usage.',
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
        raise common.format_err_msg_and_raise("list", "exportgroup", e.err_text, e.err_code)


# Export Group Add Volume routines

def add_volume_parser(subcommand_parsers, common_parser):
    # add command parser
    add_volume_parser = subcommand_parsers.add_parser('add_vol',
                description='ViPR Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add a volume to an Export group')
    mandatory_args = add_volume_parser.add_argument_group('mandatory arguments')
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
    add_volume_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    add_volume_parser.add_argument('-snapshot', '-sh',
                metavar='<Snapshot for volume>',
                dest='snapshot',
                help='name of snapshot of volume to export', 
                default = None)
    add_volume_parser.add_argument('-consistencygroup', '-cg',
                metavar='<consistencygroup>',
                dest='consistencygroup',
                help='name of consistencygroup', 
                default = None)

    add_volume_parser.add_argument('-lun', '-l',
                metavar='<Logicalunitnumber>',
                dest='lun',
                help='Logical Unit Number')

    add_volume_parser.set_defaults(func=exportgroup_add_volumes)

def exportgroup_add_volumes(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_add_volumes(args.name, args.tenant, args.project, args.volume, args.snapshot, args.lun, args.consistencygroup)            
    except SOSError as e:
        raise common.format_err_msg_and_raise("add_vol", "exportgroup", e.err_text, e.err_code)
        
# Export Group Remove Volume routines

def remove_volume_parser(subcommand_parsers, common_parser):
    # remove command parser
    remove_volume_parser = subcommand_parsers.add_parser('remove_vol',
                description='ViPR Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove a volume from Export group')
    mandatory_args = remove_volume_parser.add_argument_group('mandatory arguments')
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
    remove_volume_parser.add_argument('-snapshot', '-sh',
                metavar='<Snapshot for volume>',
                dest='snapshot',
                help='name of snapshot of volume to export', 
                default = None)
    remove_volume_parser.add_argument('-consistencygroup', '-cg',
                metavar='<consistencygroup>',
                dest='consistencygroup',
                help='name of consistencygroup', 
                default = None)

    remove_volume_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    remove_volume_parser.set_defaults(func=exportgroup_remove_volumes)

def exportgroup_remove_volumes(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)

        objExGroup.exportgroup_remove_volumes(args.name, args.tenant, args.project, args.volume, args.snapshot, args.consistencygroup)        

    except SOSError as e:
        raise common.format_err_msg_and_raise("remove_vol", "exportgroup", e.err_text, e.err_code)
        

# Export Group Add Initiator routines

def add_initiator_parser(subcommand_parsers, common_parser):
    # add initiator command parser
    add_initiator_parser = subcommand_parsers.add_parser('add_initiator',
                description='ViPR Export group Add volumes cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add an initiator to  Export group')
    mandatory_args = add_initiator_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-initiator', '-in',
                metavar='<initiator>',
                dest='initiator',
                help='name of initiator',
                required=True)
    mandatory_args.add_argument('-hl', '-hostlabel',
                dest='hostlabel',
                metavar='<hostlabel>',
                help='Host for which initiators to be searched',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    add_initiator_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    add_initiator_parser.set_defaults(func=exportgroup_add_initiators)

def exportgroup_add_initiators(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_add_initiator(args.name, args.tenant, args.project, args.initiator, args.hostlabel)
    except SOSError as e:
        raise common.format_err_msg_and_raise("add_initiator", "exportgroup", e.err_text, e.err_code)
        
# Export Group Remove Initiators routines

def remove_initiator_parser(subcommand_parsers, common_parser):
    # create command parser
    remove_initiator_parser = subcommand_parsers.add_parser('remove_initiator',
                description='ViPR Export group Remove initiator port cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove an initiator port from Export group')
    mandatory_args = remove_initiator_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-initiator', '-in',
                metavar='<initiator>',
                dest='initiator',
                help='name of initiator',
                required=True)
    mandatory_args.add_argument('-hl', '-hostlabel',
                dest='hostlabel',
                metavar='<hostlabel>',
                help='Host for which initiators to be searched',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    remove_initiator_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    remove_initiator_parser.set_defaults(func=exportgroup_remove_initiators)

def exportgroup_remove_initiators(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_remove_initiator(args.name, args.tenant, args.project, args.initiator, args.hostlabel)
    except SOSError as e:
        raise common.format_err_msg_and_raise("remove_initiator", "exportgroup", e.err_text, e.err_code)

# Export Group Add Volume routines

def add_cluster_parser(subcommand_parsers, common_parser):
    # add command parser
    add_cluster_parser = subcommand_parsers.add_parser('add_cluster',
                description='ViPR Export group Add Cluster cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add a Cluster to an Export group')
    
    mandatory_args = add_cluster_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-cluster','-cl', 
                help='Name of the cluster',
                dest='cluster',
                metavar='<cluster>',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    add_cluster_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    
    add_cluster_parser.set_defaults(func=exportgroup_add_cluster)

def exportgroup_add_cluster(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_add_cluster(args.name, args.tenant, args.project, args.cluster)
    except SOSError as e:
        raise common.format_err_msg_and_raise("add_cluster", "exportgroup", e.err_text, e.err_code)

        
# Export Group Remove Volume routines

def remove_cluster_parser(subcommand_parsers, common_parser):
    # remove command parser
    remove_cluster_parser = subcommand_parsers.add_parser('remove_cluster',
                description='ViPR Export group Remove cluster cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove a cluster from Export group')
    mandatory_args = remove_cluster_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument( '-cluster', '-cl',
                help='Name of the cluster',
                dest='cluster',
                metavar='<cluster>',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    remove_cluster_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    
    remove_cluster_parser.set_defaults(func=exportgroup_remove_cluster)

def exportgroup_remove_cluster(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_remove_cluster(args.name, args.tenant, args.project, args.cluster)
    except SOSError as e:
        raise common.format_err_msg_and_raise("remove_cluster", "exportgroup", e.err_text, e.err_code)
        
def add_host_parser(subcommand_parsers, common_parser):
    # add command parser
    add_host_parser = subcommand_parsers.add_parser('add_host',
                description='ViPR Export group Add Host cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Add a Host to an Export group')
    mandatory_args = add_host_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group',
                required=True)  
    mandatory_args.add_argument('-hl', '-hostlabel',
                dest='hostlabel',
                metavar='<hostlabel>',
                help='Host for which initiators to be searched',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project ',
                required=True)
    add_host_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')

    add_host_parser.set_defaults(func=exportgroup_add_host)

def exportgroup_add_host(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_add_host(args.name, args.tenant, args.project, args.hostlabel)
    except SOSError as e:
        raise common.format_err_msg_and_raise("add_host", "exportgroup", e.err_text, e.err_code)
        
# Export Group Remove Volume routines

def remove_host_parser(subcommand_parsers, common_parser):
    # remove command parser
    remove_host_parser = subcommand_parsers.add_parser('remove_host',
                description='ViPR Export group Add Host cli usage.',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Remove a Host from Export group')
    mandatory_args = remove_host_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                metavar='<exportgroupname>',
                dest='name',
                help='name of Export Group ',
                required=True)
    mandatory_args.add_argument('-hl', '-hostlabel',
                dest='hostlabel',
                metavar='<hostlabel>',
                help='Name of Host',
                required=True)
    mandatory_args.add_argument('-project', '-pr',
                metavar='<projectname>',
                dest='project',
                help='name of Project',
                required=True)
    remove_host_parser.add_argument('-tenant', '-tn',
                metavar='<tenantname>',
                dest='tenant',
                help='container tenant name')
    remove_host_parser.set_defaults(func=exportgroup_remove_host)

def exportgroup_remove_host(args):
    try:
        objExGroup = ExportGroup(args.ip, args.port)
        objExGroup.exportgroup_remove_host(args.name, args.tenant, args.project, args.hostlabel)
    except SOSError as e:
        raise common.format_err_msg_and_raise("remove_host", "exportgroup", e.err_text, e.err_code)

#
# ExportGroup Main parser routine
#

def exportgroup_parser(parent_subparser, common_parser):

    # main export group parser
    parser = parent_subparser.add_parser('exportgroup',
                description='ViPR Export Group cli usage.',
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

    # add volume to host command parser
    add_volume_parser(subcommand_parsers, common_parser)
    
    # remove volume from host command parser
    remove_volume_parser(subcommand_parsers, common_parser)

    # add initiator to host command parser
    add_initiator_parser(subcommand_parsers, common_parser)

    # remove initiator command parser
    remove_initiator_parser(subcommand_parsers, common_parser)
    
    # add cluster   command parser
    add_cluster_parser(subcommand_parsers, common_parser)
    
    #remove cluster command parser
    remove_cluster_parser(subcommand_parsers, common_parser)
     
    # add cluster   command parser
    add_host_parser(subcommand_parsers, common_parser)
    
    #remove cluster command parser
    remove_host_parser(subcommand_parsers, common_parser)
   


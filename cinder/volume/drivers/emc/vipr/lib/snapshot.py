# Copyright (c)2012 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import common
import fileshare
import volume
import json
import time
from threading import Timer
from common import SOSError

class Snapshot(object):
    
    #The class definition for operations on 'Snapshot'. 

    #Commonly used URIs for the 'Snapshot' module
    URI_SNAPSHOTS                = '/{0}/snapshots/{1}'
    URI_BLOCK_SNAPSHOTS          = '/block/snapshots/{0}'
    URI_FILE_SNAPSHOTS           = '/file/snapshots/{0}'
    URI_SNAPSHOT_LIST            = '/{0}/{1}/{2}/snapshots'        
    URI_SNAPSHOT_EXPORTS         = '/{0}/snapshots/{1}/exports'
    URI_SNAPSHOT_UNEXPORTS_FILE  = URI_SNAPSHOT_EXPORTS + '/{2},{3},{4},{5}'
    URI_SNAPSHOT_VOLUME_EXPORT   = '/{0}/snapshots/{1}/exports'
    URI_SNAPSHOT_UNEXPORTS_VOL   = URI_SNAPSHOT_EXPORTS + '/{2},{3},{4}'
    URI_FILE_SNAPSHOT_SHARES     = '/file/snapshots/{0}/shares'
    URI_FILE_SNAPSHOT_UNSHARE    = URI_FILE_SNAPSHOT_SHARES  + '/{1}'
    URI_SNAPSHOT_RESTORE         = '/{0}/snapshots/{1}/restore'
    URI_BLOCK_SNAPSHOTS_ACTIVATE = '/{0}/snapshots/{1}/activate'
    
    URI_FILE_SNAPSHOT_TASKS      = '/{0}/snapshots/{1}/tasks'
    URI_SNAPSHOT_TASKS_BY_OPID   = '/{0}/snapshots/{1}/tasks/{2}'
    
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'
    
    
    SHARES  = 'filesystems'
    VOLUMES = 'volumes'
    OBJECTS  = 'objects'
    
    FILE    = 'file'
    BLOCK   = 'block'
    OBJECT  = 'object'
 
    isTimeout = False 
    timeout = 300
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def snapshot_create(self, otype, typename, ouri, snaplabel, activate, rptype, sync):
        '''new snapshot is created, for a given shares or volumes
            parameters:
                otype      : either file or block or object type should be provided
                typename   : either filesystem or volume should be provided
                ouri       : uri of filesystems or volume 
                snaplabel  : name of the snapshot
        '''
        #check snapshot is already exist
        is_snapshot_exist = True
        try:
            self.snapshot_query(otype, typename, ouri, snaplabel)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                is_snapshot_exist = False
            else:
                raise e

        if(is_snapshot_exist):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "Snapshot with name " + snaplabel + 
                           " already exists under " + typename)
        
        body = None
        if(otype == Snapshot.BLOCK):
            parms = {
                'name'  : snaplabel,
                'create_inactive' : activate
            }
            body = json.dumps( parms ) 
            
        else:
            parms = {
                'name'  : snaplabel
            }
            body = json.dumps( parms ) 
        
        # REST api call    
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_LIST.format(otype, typename, ouri), body)
        o = common.json_decode(s)
        
        task = None
        if(otype == Snapshot.BLOCK):
            task = o["task"][0]
        else:
            task = o
       
        if(sync):
            return self.block_until_complete(otype, task['resource']['id'], task["op_id"])
        else:
            return o
    
    def snapshot_show_task_opid(self, otype, snap, taskid):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                                 "GET",
                                                 Snapshot.URI_SNAPSHOT_TASKS_BY_OPID.format(otype, snap, taskid),
                                                 None)
        if (not s):
            return None
        o = common.json_decode(s)
        return o
    
    def snapshot_show_task(self, otype, suri):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                                "GET",
                                                Snapshot.URI_FILE_SNAPSHOT_TASKS.format(otype, suri),
                                                None)
        if (not s):
            return []
        o = common.json_decode(s)
        return o["task"]
    
    def snapshot_list_uri(self, otype, otypename, ouri):
        '''
        Makes REST API call to list snapshot under a shares or volumes
         parameters:
            otype     : either file or block or object type should be provided
            otypename : either filesystem or volumes should be provided
            ouri      : uri of filesystem or volumes 
            
        Returns:
            return list of snapshots
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Snapshot.URI_SNAPSHOT_LIST.format(otype, otypename, ouri), None)
        o = common.json_decode(s)
        return o['snapshot']
                
    def snapshot_list(self, otype, otypename, filesharename, volumename, project, tenant):
        resourceUri = self.storageResource_query(otype, filesharename, volumename, project, tenant)
        if(resourceUri is not None):
            return self.snapshot_list_uri(otype, otypename, resourceUri)
        return None
    
    def snapshot_show_uri(self, otype, suri, xml=False):
        ''' 
        Retrieves snapshot details based on snapshot Name or Label
        Parameters:
            otype : either file or block
            suri : uri of the Snapshot.
        Returns:
            Snapshot details in JSON response payload 
        '''
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Snapshot.URI_SNAPSHOTS.format(otype, suri), None, None, xml)
        
        if(xml==False):
            return common.json_decode(s)
        return s
    
    def snapshot_show(self, storageresType, storageresTypename, resourceUri, name, xml ):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_show_uri(storageresType, snapshotUri, xml)
        
    '''Delete a snapshot by uri
        parameters:
            otype : either file or block
            suri : Uri of the Snapshot.
    '''
    def snapshot_delete_uri(self, otype, suri, sync):
        s = None
        if(otype == Snapshot.FILE):
            #print Snapshot.URI_RESOURCE_DEACTIVATE.format(Snapshot.URI_FILE_SNAPSHOTS.format(suri))
           (s, h)  = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_RESOURCE_DEACTIVATE.format(Snapshot.URI_FILE_SNAPSHOTS.format(suri)), None)
        else:
            #print Snapshot.URI_RESOURCE_DEACTIVATE.format(Snapshot.URI_BLOCK_SNAPSHOTS.format(suri))
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_RESOURCE_DEACTIVATE.format(Snapshot.URI_BLOCK_SNAPSHOTS.format(suri)), None)
        o = common.json_decode(s)
        if(sync):
            return self.block_until_complete(otype, o["resource"]["id"], o["op_id"])
        
        return o
    def snapshot_delete(self, storageresType, storageresTypename, resourceUri, name, sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        self.snapshot_delete_uri(storageresType, snapshotUri, sync)

    def snapshot_restore(self, storageresType, storageresTypename, resourceUri, name, sync):    
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_restore_uri(storageresType, storageresTypename, snapshotUri, sync)

    def snapshot_restore_uri(self, otype, typename, suri, sync):
        ''' Makes REST API call to restore Snapshot under a shares or volumes
            parameters:
                otype    : either file or block or object type should be provided
                typename : either filesystem or volumes should be provided
                suri     : uri of a snapshot

            returns:
                restore the snapshot
        '''
        #print Snapshot.URI_SNAPSHOT_RESTORE.format(otype, suri)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_RESTORE.format(otype, suri), None)
        o = common.json_decode(s)
        #print o
        if(sync):
            return self.block_until_complete(otype, suri, o["op_id"])
        else:
            return o
    def snapshot_activate_uri(self, otype, typename, suri, sync):
        
        #print Snapshot.URI_BLOCK_SNAPSHOTS_ACTIVATE.format(otype, suri)
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_BLOCK_SNAPSHOTS_ACTIVATE.format(otype, suri), None)
        o = common.json_decode(s)
        if(sync):
            return self.block_until_complete(otype, suri, o["op_id"])
        else:
            return o
    
    def snapshot_activate(self, storageresType, storageresTypename, resourceUri, name, sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        snapshotUri = snapshotUri.strip()
        return self.snapshot_activate_uri(storageresType, storageresTypename, snapshotUri, sync)

      
    def snapshot_export_file_uri(self, otype, suri, permissions, securityType, protocol, rootUserMapping, endpoints, 
                                                                                                        sharename, 
                                                                                                        description, 
                                                                                                        sync):
        
        o = None
        if(protocol == "NFS"):
            
            parms = {       'type'        : securityType,
                            'permissions' : permissions,
                            'root_user'   : rootUserMapping,
                            'endpoints'   : endpoints,
                            'protocol'    : protocol
                            } 
            
            body = json.dumps( parms ) 
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_EXPORTS.format(otype, suri), 
                                             body)
            o = common.json_decode(s)
            #print o
        else:
            parms = {
                     'name'        : sharename,
                     'description' : description
                }
            body = json.dumps(parms);
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_FILE_SNAPSHOT_SHARES.format(suri), body)
            o = common.json_decode(s)
            
        if(sync):
            return self.block_until_complete(otype, suri, o["op_id"])
        else:
            return o
    
   
    def snapshot_export_file(self, storageresType, storageresTypename, resourceUri, name, 
                                                                                    permissions, 
                                                                                    securityType, 
                                                                                    protocol, 
                                                                                    rootUserMapping, 
                                                                                    endpoints, 
                                                                                    sharename, 
                                                                                    description,
                                                                                    sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_export_file_uri(storageresType, snapshotUri, 
                                             permissions, 
                                             securityType, 
                                             protocol, 
                                             rootUserMapping, 
                                             endpoints, 
                                             sharename, description, sync)
        
    ''' export a snapshot of a volume to given host.
        parameters:
            otype            : Either file or block
            suri            : URI of snapshot
            protocol        : FC or iSCSI
            host_id         : Physical address of the host
            initiator       : Port of host (combination of WWNN and WWPN for FC and IQN for ISCSI)
            hlu             : HLU
            sync            : syncronize of a task  
    '''
    def snapshot_export_volume_uri(self, otype, suri, host_id, protocol, initiatorPort, initiatorNode, hlu, sync):
         body = json.dumps( {
                             'host_id'        : host_id,
                             'initiator_port' : initiatorPort,
                             'initiator_node' : initiatorNode,
                             'lun'            :  hlu,
                             'protocol'       : protocol
                             } )
         (s, h) = common.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_EXPORTS.format(otype, suri), body)
         o = common.json_decode(s)
        
         if(sync):
             return self.block_until_complete(otype, suri, o["op_id"])
         else:
             return o
         
    def snapshot_export_volume(self, storageresType, storageresTypename, resourceUri, name, 
                                                                                    host_id, 
                                                                                    protocol, 
                                                                                    initiatorPort,
                                                                                    initiatorNode, 
                                                                                    hlu,
                                                                                    sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_export_volume_uri(storageresType, snapshotUri, host_id, 
                                                                            protocol, 
                                                                            initiatorPort,
                                                                            initiatorNode, 
                                                                            hlu,
                                                                            sync)
    ''' Unexport a snapshot of a filesystem 
        parameters:
            otype         : either file or block
            suri          : uri of snapshot
            perm          : Permission (root, rw, ro, etc..)
            securityType  : Security(sys, krb5, etc..)
            protocol      : protocol to be used (NFS, CIFS)
            root_user     : user name
            sync          : synchronous task 
    '''
    def snapshot_unexport_file_uri(self, otype, suri, perm, securityType, protocol, root_user, sharename, sync):
        
        o = None
        if(protocol == "NFS"):
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Snapshot.URI_SNAPSHOT_UNEXPORTS_FILE.format(otype, 
                                                                                    suri,
                                                                                    protocol, 
                                                                                    securityType, 
                                                                                    perm, 
                                                                                    root_user), None)
            o = common.json_decode(s)
        else:
             
            (s, h) = common.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Snapshot.URI_FILE_SNAPSHOT_UNSHARE.format(suri, sharename), None)
            o = common.json_decode(s)
        
        if(sync):
            return self.block_until_complete(otype, suri, o["op_id"])
        else:
            return o

    
    def snapshot_unexport_file(self, storageresType, storageresTypename, resourceUri, name,
                                                                                      perm, 
                                                                                      securityType, 
                                                                                      protocol, 
                                                                                      root_user,
                                                                                      sharename,
                                                                                      sync):
        
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_unexport_file_uri(storageresType, snapshotUri, perm, 
                                                                            securityType, 
                                                                            protocol, 
                                                                            root_user, sharename, sync)
    
    '''
        Unexport a snapshot of a volume.
        parameters:
            otype        : either file or block
            suri         : uri of snapshot
            protocol     : protocol type
            initiator    : port of host (combination of WWNN and WWPN for FC and IQN for ISCSI)
            hlu          : logical unit number'
            sync         : synchronous task 
        '''
    def snapshot_unexport_volume_uri(self, otype, suri, protocol, initiator, hlu, sync):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Snapshot.URI_SNAPSHOT_UNEXPORTS_VOL.format(otype, 
                                                                                    suri,
                                                                                    protocol, initiator, hlu), None)
        o = common.json_decode(s)
        if(sync):
            return self.block_until_complete(otype, suri, o["op_id"])
        else:
            return o
        
    
    def snapshot_unexport_volume(self, storageresType, storageresTypename, resourceUri, name,
                                                                                        protocol, 
                                                                                        initiator_port, 
                                                                                        hlu, sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_unexport_volume_uri(storageresType, snapshotUri, protocol, initiator_port, hlu, sync)
       
             
    def snapshot_query(self, storageresType, storageresTypename, resuri, snapshotName):
        if(resuri is not None):
            uris = self.snapshot_list_uri(storageresType, storageresTypename, resuri)
            for uri in uris:
                snapshot = self.snapshot_show_uri(storageresType, uri['id'])
                if(False == (common.get_node_value(snapshot, 'inactive')) ):
                    if (snapshot['name'] == snapshotName):
                        return snapshot['id']
                
        raise SOSError(SOSError.SOS_FAILURE_ERR, "snapshot with the name:" + snapshotName + " Not Found")
  
    def storageResource_query(self, storageresType, fileshareName, volumeName, project, tenant):
        resourcepath = "/" + project + "/"
        if(tenant != None):
            resourcepath = tenant + resourcepath
        
        resUri      = None
        resourceObj = None
        if(Snapshot.FILE == storageresType):
            resourceObj = fileshare.Fileshare(self.__ipAddr, self.__port)
            resUri = resourceObj.fileshare_query(resourcepath+fileshareName)
        elif(Snapshot.BLOCK == storageresType):
            resourceObj = volume.Volume(self.__ipAddr, self.__port)
            resUri = resourceObj.volume_query(resourcepath +volumeName)
        else:
            resourceObj = None
            
        return resUri
         
    def get_storageAttributes(self, fileshareName, volumeName):
        storageresType     = None
        storageresTypeName = None
        if(fileshareName is not None):
            storageresType = Snapshot.FILE
            storageresTypeName = Snapshot.SHARES
        elif(volumeName is not None):
            storageresType = Snapshot.BLOCK
            storageresTypeName = Snapshot.VOLUMES
        else:
            storageresType = None
            storageresTypeName = None
        return (storageresType, storageresTypeName)
    
    # Timeout handler for synchronous operations
    def timeout_handler(self):
        self.isTimeout = True


    # Blocks the opertaion until the task is complete/error out/timeout
    def block_until_complete(self, storageresType, resuri, op_id):
        t = Timer(self.timeout, self.timeout_handler)
        t.start()
        while(True):
            #out = self.show_by_uri(id)
            out = self.snapshot_show_task_opid(storageresType, resuri, op_id)
            
            if(out):
                if(out["state"] == "ready"):
                    # cancel the timer and return
                    t.cancel()
                    break
                # if the status of the task is 'error' then cancel the timer and raise exception
                if(out["state"] == "error"):
                    # cancel the timer
                    t.cancel()
                    raise SOSError(SOSError.VALUE_ERR, 
                                   "Task: ["+ op_id +"], "+ out["message"] )

            if(self.isTimeout):
                print "Operation timed out"
                self.isTimeout=False
                break
        return


# Snapshot Create routines
    
def create_parser(subcommand_parsers, common_parser):
    create_parser = subcommand_parsers.add_parser('create',
                                                description='StorageOS Snapshot Create CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help = 'create a snapshot')
    
    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    create_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    
    create_parser.add_argument('-inactive', '-ci',
                                dest='inactive',
                                help='This option allows the snapshot to be create by without activating the synchronization',
                                action='store_true')
    create_parser.add_argument('-type', '-t', 
                               help = 'This option creates a bookmark of a specific type, such as rp',
                               dest='type',
                               metavar='<type>')
    
    create_parser.add_argument('-synchronous', '-sync',
                                dest='synchronous',
                                help='Synchronous snapshot export',
                                action='store_true')

    group = create_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    group.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    
    create_parser.set_defaults(func=snapshot_create)
 
def snapshot_create(args):

    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        if(storageresType == Snapshot.FILE and args.inactive == True):
            print "-inactive option is used for block type only"
            return 
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, args.volume, args.project, args.tenant)
        obj.snapshot_create(storageresType, storageresTypename, resourceUri, args.name, args.inactive, args.type, args.synchronous)
        return 
        
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot: " + args.name + ", Create Failed\n" + e.err_text)
        else:
            raise e
        
# Snapshot List routines
        
def list_parser(subcommand_parsers, common_parser):
    list_parser = subcommand_parsers.add_parser('list',
                                            description='StorageOS Snapshot List CLI usage.',
                                            parents=[common_parser],
                                            conflict_handler='resolve',
                                            help ='list a snapshots')
 
    mandatory_args = list_parser.add_argument_group('mandatory arguments')
    list_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    arggroup = list_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    arggroup.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    list_parser.add_argument('-verbose', '-v',
                                dest='verbose',
                                help='List snapshots with details',
                                action='store_true')
    list_parser.add_argument('-long', '-l',
                                dest='long',
                                help='List Storageport in table with details',
                                action='store_true')

    list_parser.set_defaults(func=snapshot_list)

def snapshot_list(args):

    obj = Snapshot(args.ip, args.port)
    try:
        resourcepath = "/" + args.project + "/"
        if(args.tenant != None):
            resourcepath = args.tenant + resourcepath
        
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        uris = obj.snapshot_list(storageresType, storageresTypename, args.filesystem, args.volume, args.project, args.tenant)
        
        records = []
        for uri in uris:
            snapshot_obj = obj.snapshot_show_uri(storageresType, uri['id']);
            if(False == (common.get_node_value(snapshot_obj, 'inactive')) ):
                records.append(snapshot_obj)
                
        if(len(records) > 0):
            if(args.verbose == True ):
                if(len(records) > 0):
                    return common.format_json_object(records)
                else:
                    return                 
            else:
                #name is displayed twice, so delete 'name' in other sections of attribute
                for record in records:
                    if("fs_exports" in record):
                        del record["fs_exports"]
                        
                from common import TableGenerator
                if(args.long == True):
                    if(storageresType == Snapshot.FILE):
                        TableGenerator(records, ['name', 'mount_path']).printTable()
                    else:#table should updated
                        TableGenerator(records, ['name', 'is_sync_active', 'wwn']).printTable()
             
                else:
                    if(storageresType == Snapshot.FILE):
                        TableGenerator(records, ['name']).printTable()
                    else:
                        TableGenerator(records, ['name', 'is_sync_active']).printTable()
        else:
            return
        
    except SOSError as e:
        raise e

# Snapshot Show routines

def show_parser(subcommand_parsers, common_parser):
    show_parser = subcommand_parsers.add_parser('show',
                                            description='StorageOS Snapshot Show CLI usage.',
                                            parents=[common_parser],
                                            conflict_handler='resolve',
                                            help = 'show a snapshot details')
    
    group = show_parser.add_argument_group('mandatory arguments')
    group.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    show_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    group.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    
    show_parser.add_argument('-xml',
                            dest='xml',
                            action='store_true',
                            help='XML response')
     
    mutex_group = show_parser.add_mutually_exclusive_group(required=True)
    
    mutex_group.add_argument('-volume', '-vol', 
                             metavar='<volumename>',
                             dest = 'volume',
                             help='Name of a volume')
    mutex_group.add_argument('-filesystem', '-fs',  
                             metavar = '<filesystemname>', 
                             dest = 'filesystem', 
                             help='Name a filesystem')
  
    show_parser.set_defaults(func=snapshot_show)

def snapshot_show(args):
    obj = Snapshot(args.ip, args.port)
    try:
        #get URI name
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, args.volume, args.project, args.tenant)
        respContent = obj.snapshot_show(storageresType, storageresTypename, resourceUri, args.name, args.xml)
        
        if(args.xml):
            return common.format_xml(respContent)
        else:
            return common.format_json_object(respContent)
        
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "snapshot " + args.name + ": Not Found")
        else:
            raise e

# Snapshot Delete routines

def delete_parser(subcommand_parsers, common_parser):
    delete_parser = subcommand_parsers.add_parser('delete',
                                                description='StorageOS Snapshot Delete CLI usage.',
                                                parents=[common_parser],
                                                conflict_handler='resolve',
                                                help ='delete a snapshot')
    
    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    
    delete_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)

    group = delete_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemsname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    group.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    
    delete_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot export',
                                action='store_true')
  
    delete_parser.set_defaults(func=snapshot_delete)

def snapshot_delete(args):
    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, args.volume, args.project, args.tenant)
        obj.snapshot_delete(storageresType, storageresTypename, resourceUri, args.name, args.sync)
        return 
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + args.name + 
                           ": Delete Failed\n" + e.err_text)
        else:
            raise e

# Snapshot Export file routines

def export_file_parser(subcommand_parsers, common_parser):
    export_parser = subcommand_parsers.add_parser('export-file',
                                description='StorageOS Snapshot Export CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='export a snapshot of filesystem')
    
    mandatory_args = export_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of snapshot for export/share',
                                required=True)
    mandatory_args.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem',
                                required=True)
    export_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    mandatory_args.add_argument('-protocol', '-pl',
                                help='access protocol for this export ( NFS | CIFS )',
                                choices=["NFS", "CIFS"],
                                dest='protocol',
                                required=True)
    
    export_parser.add_argument('-security', '-sec',
                                metavar='<securitytype>',
                                dest='security',
                                help='security type (sys | krb5 | krb5i | krb5p)',
                                required=False)
    export_parser.add_argument('-permission', '-pe',
                                metavar='<permission>',
                                dest='permission',
                                help='file share access permission',
                                required=False)
    export_parser.add_argument('-rootuser', '-ru',
                                metavar='<root_user>',
                                dest='rootuser',
                                help='root user mapping for anonymous accesses',
                                required=False)
    export_parser.add_argument('-endpoints', '-ep',
                                metavar='<endpoint>',
                                dest='endpoints',
                                help='list of client endpoints (ip|net|netgroup)',
                                nargs='+',
                                required=False)
    export_parser.add_argument('-share', '-sh',
                                help='Share Name(should be used for CIFS protocol only)',
                                metavar='<sharename>',
                                dest='share',
                                required=False)
    export_parser.add_argument('-description', '-desc',
                                help='Description of the share(should be used for CIFS protocol only))',
                                metavar='<description>',
                                dest='description',
                                required=False)
    export_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot export',
                                action='store_true')
        
    mandatory_args.set_defaults(func=snapshot_export_file)
    
def snapshot_export_file(args):

    obj = Snapshot(args.ip, args.port)
    try:
       
        if(args.protocol == "CIFS"):
            if(args.share == None and args.description == None):
                print '-share, -description are required for CIFS protocol (smb share)'
                return
        else:
            if( args.permission == None or args.security == None or args.rootuser == None or args.endpoints == None):
                print '-endpoints, -permission, -security and -rootuser are required for NFS protocol'
                return
            
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, None)
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, None, args.project, args.tenant)
        res = obj.snapshot_export_file(storageresType, storageresTypename, resourceUri, args.name,
                                                                                        args.permission, 
                                                                                        args.security, 
                                                                                        args.protocol, 
                                                                                        args.rootuser, 
                                                                                        args.endpoints,
                                                                                        args.share,
                                                                                        args.description, 
                                                                                        args.sync)
        if(args.sync == False):
            return
            #return common.format_json_object(res)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot: " + args.name +", Export failed\n" + e.err_text)
        else:
            raise e
        
# Snapshot volume file routines
        
def export_volume_parser(subcommand_parsers, common_parser):
    export_parser = subcommand_parsers.add_parser('export-volume',
                                description='StorageOS Snapshot Export volume CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='export a snapshot of volume')
    
    mandatory_args = export_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    export_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)

    mandatory_args.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume',
                                required=True)
    mandatory_args.add_argument('-protocol', '-pl',
                                help='access protocol for this export (FC | iSCSI)',
                                choices=["FC", "iSCSI"],
                                dest='protocol',
                                required=True)
    mandatory_args.add_argument('-initiator_port', '-inp',
                                metavar='<initiator_port>',
                                dest='initiator_port',
                                help='Initiator port name  (WWPN for FC and IQN for ISCSI)',
                                required=True)
    mandatory_args.add_argument('-initiator_node', '-inn',
                                metavar='<initiator_node>',
                                dest='initiator_node',
                                help='Initiator node name (WWNN)',
                                required=True)
    mandatory_args.add_argument('-hlu', '-hl',
                                metavar='<lun>',
                                dest='hlu',
                                help='host logical unit number -- should be unused on the host',
                                required=False)
    mandatory_args.add_argument('-hostid', '-ho',
                                metavar='<hostid>',
                                dest='hostid',
                                help='Physical address of the host',
                                required=True)
    
    export_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot export',
                                action='store_true')
 
    mandatory_args.set_defaults(func=snapshot_export_volume)

def snapshot_export_volume(args):

    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(None, args.volume)
        resourceUri = obj.storageResource_query(storageresType, None, args.volume, args.project, args.tenant)
        res = obj.snapshot_export_volume(storageresType, storageresTypename, resourceUri, args.name,
                                                                                          args.hostid, 
                                                                                          args.protocol, 
                                                                                          args.initiator_port,
                                                                                          args.initiator_node,
                                                                                          args.hlu,
                                                                                          args.sync)
        if(args.sync == False):
            return common.format_json_object(res)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot: " + args.name +", Export failed\n" + e.err_text)
        else:
            raise e
        
# Snapshot Unexport routines

def unexport_file_parser(subcommand_parsers, common_parser):
    unexport_parser = subcommand_parsers.add_parser('unexport-file',
                                description='StorageOS Snapshot Unexport file CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='unexport a snapshot of filesystem')
    
    mandatory_args = unexport_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of snapshot for unshare/unexport',
                                required=True)
    mandatory_args.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem',
                                required=True)
    unexport_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    mandatory_args.add_argument('-protocol', '-pl',
                                help='access protocol for this export (NFS | CIFS) ',
                                choices=["NFS", "CIFS"],
                                dest='protocol',
                                required=True)
    
    unexport_parser.add_argument('-security', '-sec',
                                metavar='<securitytype>',
                                dest='security',
                                help='Security type',
                                required=False)
    
    unexport_parser.add_argument('-permission', '-pe',
                                metavar='<permission>',
                                dest='permission',
                                help='file share access permission',
                                required=False)
    
    unexport_parser.add_argument('-rootuser', '-ru',
                                metavar='<root_user>',
                                dest='rootuser',
                                help='root user mapping for anonymous accesses',
                                required=False)

    unexport_parser.add_argument('-share', '-sh',
                                help='Sharename to unshare',
                                metavar='<sharename>',
                                dest='share',
                                required=False)
    
    unexport_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot unexport',
                                action='store_true')
        
    unexport_parser.set_defaults(func=snapshot_unexport_file)
    
def snapshot_unexport_file(args):

    obj = Snapshot(args.ip, args.port)
    try:
        if(args.protocol == "CIFS"):
            if(args.share == None):
                print '-share name is required for CIFS protocol.'
                return
        else:
            if(args.permission == None or args.security == None or args.rootuser == None):
                print '-permission, -security, -rootuser and -protocol are required for NFS protocol'
                return
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, None)
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, None, args.project, args.tenant)
        
        res = obj.snapshot_unexport_file(storageresType, storageresTypename, resourceUri, args.name,
                                                                                    args.permission, 
                                                                                    args.security, 
                                                                                    args.protocol, 
                                                                                    args.rootuser,
                                                                                    args.share,
                                                                                    args.sync)
        if(args.sync == False):
            return
            #return common.format_json_object(res)
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + args.name  
                           + ", Unexport for file is failed\n" + e.err_text)
        else:
            raise e
        
def unexport_volume_parser(subcommand_parsers, common_parser):
    unexport_parser = subcommand_parsers.add_parser('unexport-volume',
                                description='StorageOS Snapshot Unexport volume CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='unexport a snapshot of volume')
    
    mandatory_args = unexport_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    mandatory_args.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    mandatory_args.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume',
                                required=True)
    
    mandatory_args.add_argument('-initiatorPort', '-inp',
                                metavar='<initiatorPort>',
                                dest='initiatorPort',
                                help='Port of host (combination of WWNN and ' + 
                                    'WWPN for FC and IQN for ISCSI)',
                                required=True)
    mandatory_args.add_argument('-hlu', '-hl',
                                metavar='<hlu>',
                                dest='hlu',
                                help='Host Logical Unit',
                                required=True)
    mandatory_args.add_argument('-protocol', '-pl',
                                help='block protocols (FC | iSCSI)',
                                choices=["FC", "iSCSI"],
                                dest='protocol',
                                required=True)
    
    unexport_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot unexport',
                                action='store_true')
    
    unexport_parser.set_defaults(func=snapshot_unexport_volume)
    
def snapshot_unexport_volume(args):

    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(None, args.volume)
        resourceUri = obj.storageResource_query(storageresType, None, args.volume, args.project, args.tenant)
        res = obj.snapshot_unexport_volume(storageresType, storageresTypename, resourceUri, args.name,
                                                                                            args.protocol, 
                                                                                            args.initiatorPort, 
                                                                                            args.hlu,
                                                                                            args.sync)
        if(args.sync == False):
            return common.format_json_object(res)
        
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + args.name  
                           + ", Unexport for volume  is failed\n" + e.err_text)
        else:
            raise e
        
def activate_parser(subcommand_parsers, common_parser):
    activate_parser = subcommand_parsers.add_parser('activate',
                                description='StorageOS Snapshot activate CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='active a snapshot')
    
    mandatory_args = activate_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    activate_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    mandatory_args.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume',
                                required=True)

    '''
    group = activate_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    group.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    '''
    
    activate_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot activate',
                                action='store_true')
    
    mandatory_args.set_defaults(func=snapshot_activate)
def snapshot_activate(args):
    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(None, args.volume)
        resourceUri = obj.storageResource_query(storageresType, None, args.volume, args.project, args.tenant)
        snapshotUri = obj.snapshot_query(storageresType, storageresTypename, resourceUri, args.name)
        snapshotUri = snapshotUri.strip()
        start = time.time()
        res = obj.snapshot_activate_uri(storageresType, storageresTypename, snapshotUri, args.sync)
        total = time.time() - start
        #print res
        #print "Activate snapshot completed in", "{0:.2f}".format(total), "seconds, status is " + s + "\n" + m
    
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + args.name + ": activate Failed\n" + e.err_text)
        else:
            raise e
# Snapshot restore routines,

def restore_parser(subcommand_parsers, common_parser):
    restore_parser = subcommand_parsers.add_parser('restore',
                                description='StorageOS Snapshot restore CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help ='restore a snapshot')
    
    mandatory_args = restore_parser.add_argument_group('mandatory arguments')
    
    mandatory_args.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of Snapshot',
                                required=True)
    mandatory_args.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    group = restore_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    group.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    
    restore_parser.add_argument('-synchronous', '-sync',
                                dest='sync',
                                help='Synchronous snapshot unexport',
                                action='store_true')
    
    mandatory_args.set_defaults(func=snapshot_restore)
   
def snapshot_restore(args):
    obj = Snapshot(args.ip, args.port)
    try:
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        resourceUri = obj.storageResource_query(storageresType, args.filesystem, args.volume, args.project, args.tenant)
        obj.snapshot_restore(storageresType, storageresTypename, resourceUri, args.name, args.sync)
    
    except SOSError as e:
        if (e.err_code == SOSError.SOS_FAILURE_ERR):
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + args.name + ": Restore Failed\n" + e.err_text)
        else:
            raise e
        
# Snapshot tasks routines
def tasks_parser(subcommand_parsers, common_parser):
    tasks_parser = subcommand_parsers.add_parser('tasks',
                                            description='StorageOS Snapshot tasks CLI usage.',
                                            parents=[common_parser],
                                            conflict_handler='resolve',
                                            help ='tasks of a snapshot')
 
    mandatory_args = tasks_parser.add_argument_group('mandatory arguments')
    tasks_parser.add_argument('-tenant', '-tn',
                                metavar='<tenantname>',
                                dest='tenant',
                                help='Name of tenant',
                                required=False)
    mandatory_args.add_argument('-project', '-pr',
                                metavar='<projectname>',
                                dest='project',
                                help='Name of project',
                                required=True)
    arggroup = tasks_parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument('-filesystem', '-fs', 
                                metavar='<filesystemname>',
                                dest = 'filesystem', 
                                help = 'Name of filesystem')
    arggroup.add_argument('-volume', '-vol', 
                                metavar = '<volumename>', 
                                dest = 'volume', 
                                help = 'Name of a volume')
    
    tasks_parser.add_argument('-name', '-n',
                                metavar='<snapshotname>',
                                dest='name',
                                help='Name of snapshot',
                                required=False)
    
    tasks_parser.add_argument('-id', 
                                dest='id',
                                metavar='<opid>',
                                help='Operation ID')
    tasks_parser.add_argument('-v', '-verbose',
                              dest='verbose',
                              action="store_true",
                              help='List all tasks')



    tasks_parser.set_defaults(func=snapshot_tasks)
    
def snapshot_tasks(args):

    obj = Snapshot(args.ip, args.port)
    try:
        if(args.id != None):
            if(args.name == None):
                print '-name <snapshotname> is required for opids'
           
        resourcepath = "/" + args.project + "/"
        if(args.tenant != None):
            resourcepath = args.tenant + resourcepath
          
        (storageresType, storageresTypename) = obj.get_storageAttributes(args.filesystem, args.volume)
        uris = obj.snapshot_list(storageresType, storageresTypename, args.filesystem, args.volume, args.project, args.tenant)
        #for a given snapshot, get all actions
        
        all_tasks = []
        #get all snapshot opids(actions) under a volume or filesystem
        if( args.name == None and args.id == None):
            for suri in uris:
                taskslist = obj.snapshot_show_task(storageresType, suri['id'])
                if(taskslist and len(taskslist) > 0):
                    all_tasks+=taskslist
        else:# get all snapshot opids for a given snapshot name
            snapshot_ob = None
            for suri in uris:
                snapshot_ob = obj.snapshot_show_uri(storageresType, suri['id'])
                if(snapshot_ob['name'] == args.name):
                    break
                else:
                    snapshot_ob = None
            
            if(snapshot_ob != None):#if snapshot object in found, then call for tasks    
                
                if(args.id != None):# get opids details, for a specific operation id
                    #return task object in json format
                    return common.format_json_object( obj.snapshot_show_task_opid(storageresType, suri['id'], args.id) )
                else:# get all opids for given snapshot name  
                    taskslist = obj.snapshot_show_task(storageresType, suri['id'])
                    if(taskslist and len(taskslist) > 0):
                        all_tasks+=taskslist
            else:
                return
        
        if(args.verbose): 
            return common.format_json_object(all_tasks)
        else:#display in table format (all task for given file share/volume or snapshot name)
            if(all_tasks and len(all_tasks) > 0): 
                from common import TableGenerator      
                TableGenerator(all_tasks, ["op_id", "name", "state"]).printTable()
                
    except SOSError as e:
        raise e
#
# Snapshot Main parser routine
#
def snapshot_parser(parent_subparser, common_parser):
    # main project parser

    parser = parent_subparser.add_parser('snapshot',
                                description='StorageOS Snapshot CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on Snapshot')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # export-file command parser
    export_file_parser(subcommand_parsers, common_parser)

    # export-volume command parser
    #export_volume_parser(subcommand_parsers, common_parser)


    # unexport-file command parser
    unexport_file_parser(subcommand_parsers, common_parser)
    
    # unexport-volume command parser
    #unexport_volume_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)
    
    #activate command parser
    activate_parser(subcommand_parsers, common_parser)
    
    #restore command parser
    restore_parser(subcommand_parsers, common_parser)
    
    #tasks command parser    
    tasks_parser(subcommand_parsers, common_parser)


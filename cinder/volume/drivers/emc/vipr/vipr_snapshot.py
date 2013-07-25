#!/usr/bin/python
# Copyright (c)2013 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import vipr_utils
import vipr_volume
import json
from threading import Timer



from vipr_utils import SOSError

class Snapshot(object):
    '''
    The class definition for operations on 'Snapshot'. 
    '''

    #Commonly used URIs for the 'Snapshot' module
     
    URI_SNAPSHOTS                = '/{0}/snapshots/{1}'        
    URI_SNAPSHOT_EXPORTS         = '/{0}/snapshots/{1}/exports'
    URI_SNAPSHOT_DEACTIVATE      = '/{0}/snapshots/{1}/deactivate'
    URI_SNAPSHOT_VOLUME_EXPORT   = '/{0}/snapshots//{1}/exports'
    URI_SNAPSHOT_UNEXPORTS_FILE  =  URI_SNAPSHOT_EXPORTS + '/{2},{3},{4},{5}'
    URI_SNAPSHOT_UNEXPORTS_VOL   =  URI_SNAPSHOT_EXPORTS + '/{2},{3},{4}'
    URI_SNAPSHOT_LIST            = '/{0}/{1}/{2}/snapshots'
    URI_SNAPSHOT_RESTORE         = '/{0}/{1}/{2}/restore'
    
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
        
    
    def snapshot_create(self, otype, typename, ouri, snaplabel):
        '''
        new snapshot is created, for a given shares or volumes
        parameters:
            otype     : either file or block or object type should be provided
            typename : either shares or volumes should be provided
            ouri     : uri of shares or volumes 
            snaplabel: name of the snapshot
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
        
        body = vipr_utils.json_encode('name', snaplabel)
                
        # REST api call    
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_LIST.format(otype, typename, ouri), body)
        return vipr_utils.json_decode(s)
   
    
    def snapshot_list_uri(self, otype, otypename, ouri):
        '''
        Makes REST API call to list snapshot under a shares or volumes
         parameters:
            otype     : either file or block or object type should be provided
            otypename : either shares or volumes should be provided
            ouri     : uri of shares or volumes 
            snaplabel: name of the snapshot
        Returns:
            List of filesystem's uuids in JSON response payload
        '''

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Snapshot.URI_SNAPSHOT_LIST.format(otype, otypename, ouri), None)
        o = vipr_utils.json_decode(s)
        return o['snapshot']
                
    def snapshot_list(self, otype, otypename, filesharename, volumename, resourcepath):
        resourceUri = self.storageResource_query(otype, filesharename, volumename, resourcepath)
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
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Snapshot.URI_SNAPSHOTS.format(otype, suri), None, None, xml)
        
        if(xml==False):
            o = vipr_utils.json_decode(s)
            inactive = vipr_utils.get_node_value(o, 'inactive')
            if(inactive):
                return None
            else:
                return o
        
        return s
    
    def snapshot_show(self, storageresType, storageresTypename, resourceUri, name, xml ):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        
        return self.snapshot_show_uri(storageresType, snapshotUri, xml)
        
    
    def snapshot_delete_uri(self, otype, suri):
        '''
        Delete a snapshot by uri
        parameters:
            otype : either file or block
            suri : Uri of the Snapshot.
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Snapshot.URI_SNAPSHOT_DEACTIVATE.format(otype, suri), None)
        
        return 
    
    def snapshot_delete(self, storageresType, storageresTypename, resourceUri, name):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        self.snapshot_delete_uri(storageresType, snapshotUri)
        return

    def snapshot_restore(self, storageresType, storageresTypename, resourceUri, name):    
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        self.snapshot_restore_uri(storageresType, storageresTypename, snapshotUri)

    def snapshot_restore_uri(self, otype, typename, suri):
        '''
        Makes REST API call to restore Snapshot under a shares or volumes
         parameters:
            otype     : either file or block or object type should be provided
            typename : either shares or volumes should be provided
            ouri     : Uri of Shares or Volumes 
            puri     : Uri of project
            snaplabel: name of the Snapshot
        Returns:
            restore the snapshot
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_RESTORE.format(otype, typename, suri), None)
        o = vipr_utils.json_decode(s)
        return o
      
    def snapshot_export_file_uri(self, otype, suri, permissions, securityType, protocol, rootUserMapping, endpoint, sync):
        '''
        export a snapshot of a filesystem.
        parameters:
            type            : Either file or block
            suri            : URI of snapshot
            permissions     : Permission (root, rw, ro, etc)
            securityType    : Security(sys, krb5, etc..)
            protocol        : FC, NFS, iSCSI
            rootUserMapping : user name
            endpoint        : host names, IP addresses, or netgroups
        '''
        body = json.dumps({
                        'type'   : securityType,
                        'perm'   : permissions,
                        'root-user' : rootUserMapping,
                        'endpoint' : 
                        [
                            { "name" : endpoint }
                        ],
                        'protocol' : protocol
                    }) 
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_EXPORTS.format(otype, suri), 
                                             body)
        o = vipr_utils.json_decode(s)
        if(sync):
            return self.block_until_complete(otype, o["id"], o["task"])
        else:
            return o
    
    def snapshot_export_file(self, storageresType, storageresTypename, resourceUri, 
                                                                         name, 
                                                                         permissions, 
                                                                         securityType, 
                                                                         protocol, 
                                                                         rootUserMapping, 
                                                                         endpoint, sync):
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_export_file_uri(storageresType, snapshotUri, 
                                             permissions, 
                                             securityType, 
                                             protocol, 
                                             rootUserMapping, 
                                             endpoint, sync)
        
    
    '''
        export a snapshot of a volume to given host.
        parameters:
            type            : Either file or block
            suri            : URI of snapshot
            host_id         : Physical address of the host
            initiator       : Port of host (combination of WWNN and WWPN for FC and IQN for ISCSI)
            hlu             : HLU
        '''
    def snapshot_export_volume_uri(self, otype, suri, host_id, protocol, initiatorPort, initiatorNode, hlu, sync):
         body = json.dumps( {
                             'host_id' : host_id,
                             'initiator_port' : initiatorPort,
                             'initiator_node' : initiatorNode,
                             'lun' :  hlu,
                             'protocol': protocol
                }   )
         (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             Snapshot.URI_SNAPSHOT_EXPORTS.format(otype, suri), 
                                             body)
         o = vipr_utils.json_decode(s)
        
         if(sync):
             return o
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
 
        return self.snapshot_export_volume_uri(storageresType, snapshotUri, 
                                                                        host_id, 
                                                                        protocol, 
                                                                        initiatorPort,
                                                                        initiatorNode, 
                                                                        hlu,
                                                                        sync)
    '''
        Unexport a snapshot of a filesystem 
        parameters:
            type         : Either file or block
            suri         : URI of snapshot
            perm         : Permission (root, rw, ro, etc..)
            securityType : Security(sys, krb5, etc..)
            protocol     : protocol to be used (FC, NFS, iSCSI)
            root_user    : user name
      '''
    def snapshot_unexport_file_uri(self, otype, suri, perm, securityType, protocol, root_user, sync):
        
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Snapshot.URI_SNAPSHOT_UNEXPORTS_FILE.format(otype, 
                                                                                    suri,
                                                                                    protocol, 
                                                                                    securityType, 
                                                                                    perm, 
                                                                                    root_user),
                                             None)
        o = vipr_utils.json_decode(s)
        
        if(sync):
            return self.block_until_complete(otype, o["id"], o["task"])
        else:
            return o

    
    def snapshot_unexport_file(self, storageresType, storageresTypename, resourceUri, name,
                                                                                      perm, 
                                                                                      securityType, 
                                                                                      protocol, 
                                                                                      root_user,
                                                                                      sync):
        
        snapshotUri = self.snapshot_query(storageresType, storageresTypename, resourceUri, name)
        return self.snapshot_unexport_file_uri(storageresType, snapshotUri, perm, 
                                                                            securityType, 
                                                                            protocol, 
                                                                            root_user, sync)
    
    '''
        Unexport a snapshot of a volume.
        parameters:
            type         : Either file or block
            suri         : URI of snapshot
            initiator    : Port of host (combination of WWNN and WWPN for FC and IQN for ISCSI)
            
        '''
    def snapshot_unexport_volume_uri(self, otype, suri, protocol, initiator, hlu, sync):
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Snapshot.URI_SNAPSHOT_UNEXPORTS_VOL.format(otype, 
                                                                                    suri,
                                                                                    protocol, initiator, hlu), None)
        o = vipr_utils.json_decode(s)
        if(sync):
            return self.block_until_complete(otype, o["id"], o["task"])
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
                if(snapshot is not None):
                    if (snapshot['name'] == snapshotName):
                        return snapshot['id']
                
        raise SOSError(SOSError.SOS_FAILURE_ERR, "snapshot " + snapshotName + ": Not Found")
  
    def storageResource_query(self, storageresType, fileshareName, volumeName, resourcepath):
        resUri      = None
        resourceObj = None
        
        if(Snapshot.FILE == storageresType):
            resourceObj = fileshare.Fileshare(self.__ipAddr, self.__port)
            resUri = resourceObj.fileshare_query(resourcepath+fileshareName)
        elif(Snapshot.BLOCK == storageresType):
            resourceObj = vipr_volume.Volume(self.__ipAddr, self.__port)
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
    def block_until_complete(self, storageresType, id, task):
        t = Timer(self.timeout, self.timeout_handler)
        t.start()
        while(True):
            out = self.snapshot_show_uri(storageresType, id)
            
            if(out):
                if(out["operationStatus"][task]["status"] == "ready"):
                    # cancel the timer and return
                    t.cancel()
                    break

                # if the status of the task is 'error' then cancel the timer and raise exception
                if(out["operationStatus"][task]["status"] == "error"):
                    # cancel the timer
                    t.cancel()
                    raise SOSError(SOSError.NOT_FOUND_ERR, "")

            if(self.isTimeout):
                print "Operation timed out."
                self.isTimeout=False
                break
        return

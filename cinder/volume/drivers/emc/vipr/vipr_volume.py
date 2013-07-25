#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import json 
from oslo.config import cfg
import time 
from xml.dom.minidom import parseString

from cinder import context
from cinder import exception
from cinder.openstack.common import log as logging
from cinder.volume import volume_types

import vipr_utils
from vipr_utils import SOSError
from threading import Timer
from vipr_project import Project
from vipr_neighborhood import Neighborhood
from vipr_vpool import VPool
from vipr_auth import Authentication

LOG = logging.getLogger(__name__)


class Volume(object):
    '''
    The class definition for operations on 'Volume'. 
    '''
    #Commonly used URIs for the 'Volume' module
    URI_SEARCH_VOLUMES = '/search?resource_type=volume&project={0}'
    URI_VOLUMES = '/block/volumes'
    URI_VOLUME = URI_VOLUMES + '/{0}'
    URI_VOLUME_CREATE = URI_VOLUMES + '?project={0}'
    URI_VOLUME_DEACTIVATE = URI_VOLUME + '/deactivate'
    URI_VOLUME_SNAPSHOTS = URI_VOLUME + '/snapshots'
    URI_VOLUME_RESTORE = URI_VOLUME + '/restore'
    URI_VOLUME_EXPORTS = URI_VOLUME + '/exports'
    URI_VOLUME_UNEXPORTS = URI_VOLUME_EXPORTS + '/{1},{2},{3}'
    URI_VOLUME_CONSISTENCYGROUP = URI_VOLUME + '/consistency-group'
    URI_PROJECT_RESOURCES = '/projects/{0}/resources'
    URI_BULK_DELETE = URI_VOLUMES + '/deactivate'
    URI_EXPAND = URI_VOLUME + '/expand'
    URI_TASK_LIST = URI_VOLUME + '/tasks'
    URI_TASK = URI_TASK_LIST + '/{1}'
   
    isTimeout = False
    timeout = 300

    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    #Lists volumes in a project
    def list_volumes(self, project):
        '''
        Makes REST API call to list volumes under a project
        Parameters:
            project: name of project
        Returns:
            List of volumes uuids in JSON response payload
        '''

        proj = Project(self.__ipAddr, self.__port)
        project_uri = proj.project_query(project)
        
        return self.list_by_uri(project_uri)

    def search_volumes(self, project_uri):

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                              "GET",
                                              Volume.URI_SEARCH_VOLUMES.format(project_uri),
                                              None)
        o = vipr_utils.json_decode(s)
        if not o:
            return []

        volume_uris=[]
        resources = vipr_utils.get_node_value(o, "resource")
        for resource in resources:
            volume_uris.append(resource["id"])
        return volume_uris

    #Get the list of volumes given a project uri    
    def list_by_uri(self, project_uri):
        '''
        Makes REST API call and retrieves volumes based on project UUID
        Parameters:
            project_uri: UUID of project
        Returns:
            List of volumes UUIDs in JSON response payload
        '''
      
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Volume.URI_PROJECT_RESOURCES.format(project_uri),
                                             None)
        o = vipr_utils.json_decode(s)
        if not o:
            return []

        volumes=[]
        resources = vipr_utils.get_node_value(o, "project_resource")
        for resource in resources:
            if(resource["resource_type"].lower()=="volume"):
                item = self.show_by_uri(resource["id"])
                if(item):
                    volumes.append(item["id"])
        
        return volumes

    def show(self, name, show_inactive=False, xml=False):
        '''
        Retrieves volume details based on volume name
        Parameters:
            name: name of the volume. If the volume is under a project,
            then full XPath needs to be specified.
            Example: If VOL1 is a volume under project PROJ1, then the name
            of volume is PROJ1/VOL1
        Returns:
            Volume details in JSON response payload
        '''

        if (vipr_utils.is_uri(name)):
            return name
        (pname, label) = vipr_utils.get_parent_child_from_xpath(name)
        if (pname is None):
            raise SOSError(SOSError.NOT_FOUND_ERR, "Volume " +
                str(name) + ": not found")

        proj = Project(self.__ipAddr, self.__port)
        puri = proj.project_query(pname)
        puri = puri.strip()

        uris = self.search_volumes(puri)

        for uri in uris:
            volume = self.show_by_uri(uri, show_inactive)
            if (volume and volume['name'] == label):
                if(not xml):
                    return volume
                else:
                    return self.show_by_uri(volume['id'],
                                            show_inactive, xml)
        raise SOSError(SOSError.NOT_FOUND_ERR, "Volume " +
                        str(label) + ": not found")

    # Shows volume information given its uri
    def show_by_uri(self, uri, show_inactive=False, xml=False):
        '''
        Makes REST API call and retrieves volume details based on UUID
        Parameters:
            uri: UUID of volume
        Returns:
            Volume details in JSON response payload
        '''
        if(xml):
            (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Volume.URI_VOLUME.format(uri),
                                             None, None, xml)
            return s

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Volume.URI_VOLUME.format(uri),
                                             None)
        o = vipr_utils.json_decode(s)
        if(show_inactive):
            return o
        inactive = vipr_utils.get_node_value(o,'inactive')
        if(inactive == True):
            return None
        return o

    # Shows volume information given its uri
    def show_volume_exports_by_uri(self, uri):
        '''
        Makes REST API call and retrieves volume details based on UUID
        Parameters:
            uri: UUID of volume
        Returns:
            Volume details in JSON response payload
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             Volume.URI_VOLUME_EXPORTS.format(uri),
                                             None)
        o = vipr_utils.json_decode(s)
        #inactive = vipr_utils.get_node_value(o,'inactive')
        #if(inactive == True):
        #    return None
        return o

    # Creates a volume given label, project, vpool and size
    def create(self, project, label, size, neighborhood, vpool,
               protocol, sync, number_of_volumes):
        '''
        Makes REST API call to create volume under a project
        Parameters:
            project: name of the project under which the volume will be created
            label: name of volume
            size: size of volume
            neighborhood: name of neighborhood
            vpool: name of vpool
            protocol: protocol used for the volume (FC or iSCSI)
        Returns:
            Created task details in JSON response payload
        '''
        name = project + '/' + label

        proj_obj = Project(self.__ipAddr, self.__port)
        project_uri  = proj_obj.project_query(project)

        if(number_of_volumes and number_of_volumes > 1):
            for vol_id in self.get_volume_ids(project_uri, label, number_of_volumes):
                volume = self.show_by_uri(vol_id, True)
                if(volume):
                    if(volume["inactive"]):
                        pass
                    elif(volume["inactive"] == False):
                        raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                               "Volume with name: " + volume["name"] +
                               " already exists")
                    else:
                        tasks = self.show_task_by_uri(vol_id)
                        for task in tasks:
                            if(task['state'] in ["pending", "ready"]):
                                raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                                               "Volume with name: " + task["resource"]["name"] +
                                               " already exists. Associated task[" + task["op_id"]
                                               + "] is in " + task['state'] +" state")

        else:
            try:
                volume = self.show(name, True)
                if(volume):
                    if(volume["inactive"]):
                        pass
                    elif(volume["inactive"] == False):
                        raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                               "Volume with name: " + volume["name"] +
                               " already exists")
                    else:
                        tasks = self.show_task_by_uri(volume["id"])
                        for task in tasks:
                            if(task['state'] in ["pending", "ready"]):
                                raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                                       "Volume with name: " + task["resource"]["name"] +
                                       " already exists. Associated task[" + task["op_id"]
                                       + "] is in " + task['state'] +" state")
            except SOSError as e:
                if(e.err_code==SOSError.NOT_FOUND_ERR):
                    pass
                else:
                    raise e


        vpool_obj = VPool(self.__ipAddr, self.__port)
        vpool_uri = vpool_obj.vpool_query(vpool, "block")

        neighborhood_obj = Neighborhood(self.__ipAddr, self.__port)
        neighborhood_uri = neighborhood_obj.neighborhood_query(neighborhood)

        request = {
             'name' : label,
             'size' : size,
             'neighborhood' : neighborhood_uri,
             'project' : project_uri,
             'cos' : {'id' : vpool_uri}
            }

        if(number_of_volumes and number_of_volumes > 1):
            request["count"] = number_of_volumes
        body = json.dumps(request)

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Volume.URI_VOLUMES,
                                             body)
        o = vipr_utils.json_decode(s)
        if(sync):
            if(number_of_volumes < 2):
                task = o["task"][0]
                return self.block_until_complete(task["resource"]["id"],
                                             task["op_id"])
        else:
            return o

    # Update a volume information
    def update(self, name, label, vpool):
        '''
        Makes REST API call to update a volume information
        Parameters:
            name: name of the volume to be updated
            label: new name of the volume
            vpool: name of vpool
        Returns
            Created task details in JSON response payload
        '''
        volume_uri = self.volume_query(name)
        
        vpool_obj = VPool(self.__ipAddr, self.__port)
        vpool_uri = vpool_obj.vpool_query(vpool, "block")
        
        body = json.dumps({'volume':
        {
         'name' : label,
         'cos' : { "id" : vpool_uri }
        }
        })
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                                             "PUT",
                                             Volume.URI_VOLUME.format(volume_uri), 
                                             body)
        o = vipr_utils.json_decode(s)
        return o

    # Exports a volume to a host given a volume name, initiator and hlu
    def export(self, name, protocol, initiator_port, initiator_node, hlu, host_id, sync):
        '''
        Makes REST API call to export volume to a host
        Parameters:
            name: Name of the volume
            protocol: Protocol used for export
            initiator_port: Port of host (WWPN for FC and IQN for ISCSI)
            initiator_node: Node of the host(WWNN for FC and IQN for ISCSI)
            hlu: host logical unit number -- should be unused on the host
            host_id: Physical address of the host
        Returns:
            Created Operation ID details in JSON response payload
        '''
        volume_uri = self.volume_query(name)
        return self.export_by_uri(volume_uri, protocol, initiator_port, initiator_node, hlu, host_id, sync)

    # Exports a volume to a host given a volume uri, initiator and hlu
    def export_by_uri(self, uri, protocol, initiator_port, initiator_node, hlu, host_id, sync):
        '''
        Makes REST API call to export volume to a host
        Parameters:
            uri: Uri of the volume
            protocol: Protocol used for export
            initiator_port: Port of host (WWPN for FC and IQN for ISCSI)
            initiator_node: Node of the host(WWNN for FC and IQN for ISCSI)
            hlu: host logical unit number -- should be unused on the host
            host_id: Physical address of the host
        Returns:
            Created Operation ID details in JSON response payload
        '''

        body = json.dumps(
        {
         'protocol' : protocol,
         'initiator_port' : initiator_port,
         'initiator_node' : initiator_node, 
         'lun' :  hlu,
         'host_id' : host_id
        }
        )
       
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "POST", 
                                             Volume.URI_VOLUME_EXPORTS.format(uri),
                                             body)
        o = vipr_utils.json_decode(s)
        if(sync):
            return self.block_until_complete(o["id"], o["task"])
        else:
            return o
    
    # Unexports a volume from a host given a volume name and the host name
    def unexport(self, name, initiator, protocol, hlu, sync):
        '''
        Makes REST API call to unexport volume from host
        Parameters:
            name: Name of the volume
            initiator: Port of host (combination of WWNN and WWPN for FC and IQN for iSCSI)
            protocol: Protocol used for export
            hlu: host logical unit number -- should be unused on the host
        Returns:
            Created Operation ID details in JSON response payload
        '''
        volume_uri = self.volume_query(name)
        return self.unexport_by_uri(volume_uri, initiator, protocol, hlu, sync)
    
    # Unexports a volume from a host given a volume uri and the host name
    def unexport_by_uri(self, uri, initiator, protocol, hlu, sync):
        '''
        Makes REST API call to unexport volume from a host
        Parameters:
            uri: Uri of the volume
            initiator: Port of host (combination of WWNN and WWPN for FC and IQN for iSCSI)
            protocol: Protocol used for export
            hlu: host logical unit number -- should be unused on the host
        Returns:
            Created Operation ID details in JSON response payload
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                            "DELETE", 
                                            Volume.URI_VOLUME_UNEXPORTS.format(uri, protocol, initiator, hlu), 
                                            None)
        o = vipr_utils.json_decode(s)
        
        if(sync):
            return self.block_until_complete(o["id"], o["task"])
        else:
            return o

    # Deletes a volume given a volume name
    def delete(self, name):
        '''
        Deletes a volume based on volume name
        Parameters:
            name: name of volume
        '''

        volume_uri = self.volume_query(name)
        return self.delete_by_uri(volume_uri)
    
    # Deletes a volume given a volume uri
    def delete_by_uri(self, uri):
        '''
        Deletes a volume based on volume uri
        Parameters:
            uri: uri of volume
        '''

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             Volume.URI_VOLUME_DEACTIVATE.format(uri),
                                             None)
        return
 
    # Queries a volume given its name
    def volume_query(self, name):
        '''
        Makes REST API call to query the volume by name
        Parameters:
            name: name of volume
        Returns:
            Volume details in JSON response payload
        '''

        if (vipr_utils.is_uri(name)):
            return name

        (pname, label) = vipr_utils.get_parent_child_from_xpath(name)
        if(not pname):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Project name  not specified") 
        proj = Project(self.__ipAddr, self.__port)
        puri = proj.project_query(pname)
        puri = puri.strip()
        uris = self.list_volumes(puri)
        for uri in uris:
            volume = self.show_by_uri(uri)
            if (volume['name'] == label):
                return volume['id']
        raise SOSError(SOSError.NOT_FOUND_ERR, "Volume " +
                            name + ": not found")

    # Timeout handler for synchronous operations
    def timeout_handler(self):
        self.isTimeout = True

    # Blocks the opertaion until the task is complete/error out/timeout
    def block_until_complete(self, volume_uri, task_id):
        self.isTimeout = False
        t = Timer(self.timeout, self.timeout_handler)
        t.start()
        while(True):
            out = self.show_task_by_uri(volume_uri, task_id)

            if(out):
                if(out["state"] == "ready"):
                    # cancel the timer and return
                    t.cancel()
                    break

                # if the status of the task is 'error' then cancel the timer and raise exception
                if(out["state"] == "error"):
                    # cancel the timer
                    t.cancel()
                    raise SOSError(SOSError.VALUE_ERR, "Task: "+ task_id + " is in ERROR state")

            if(self.isTimeout):
                print "Operation timed out."
                self.isTimeout=False
                break
        return

    def show_task_by_uri(self, volume_uri, task_id=None):

        if(not task_id):
            (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                                "GET",
                                                Volume.URI_TASK_LIST.format(volume_uri),
                                                None)
            if (not s):
                return []
            o = vipr_utils.json_decode(s)
            res = o["task"]
            return res
        else:
            (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                                 "GET",
                                                 Volume.URI_TASK.format(volume_uri, task_id),
                                                 None)
            if (not s):
                return None
            o = vipr_utils.json_decode(s)
            return o

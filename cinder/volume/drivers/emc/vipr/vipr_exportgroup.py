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
from vipr_auth import Authentication
from vipr_volume import Volume

LOG = logging.getLogger(__name__)


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
    URI_EXPORT_GROUP_SEARCH = '/search?resource_type={0}' 
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    def exportgroup_list(self, project):
        '''
        This function will give us the list of export group uris
        separated by comma.
        prameters:
            project: Name of the project path.
        return
            returns with list of export group ids separated by comma. 
        '''
        projobj = Project(self.__ipAddr, self.__port)
        projuri = projobj.project_query(project)
        
        uri = self.URI_EXPORT_GROUP_SEARCH.format('block_export')
        
        if ('?' in uri):
            uri += '&project=' + projuri 
        else:
            uri += '?project=' + projuri

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             uri, None)
        o = vipr_utils.json_decode(s)
        if not o:
            return []

        exportgroups=[]
        resources = vipr_utils.get_node_value(o, "resource")
        for resource in resources:
            if(resource["resource_type"].lower()=="block_export"):
                exportgroups.append(resource["id"])
       
        return exportgroups
                     
    def exportgroup_show(self, name, project):
        '''
        This function will take export group name and project name as input and
        It will display the Export group with details.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            returns with Details of export group. 
        '''
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             self.URI_EXPORT_GROUPS_SHOW.format(uri), None)
        return vipr_utils.json_decode(s)
   
    def exportgroup_show_uri(self, uri):
        '''
        This function will take export group name and project name as input and
        It will display the Export group with details.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            returns with Details of export group.
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             self.URI_EXPORT_GROUPS_SHOW.format(uri), None)
        return vipr_utils.json_decode(s)
 
    def exportgroup_storageports(self, name, project):
        '''
        This function will take export group name and project name as input and
        It will get the target storage port for  Export group.
        parameters:
           name : Name of the export group.
           project: Name of the project.
        return
            returns storage ports for export group.
        '''
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             self.URI_EXPORT_GROUPS_STORAGEPORTS.format(uri), None)
        return vipr_utils.json_decode(s)

    def exportgroup_create(self, name, project, neighborhood, 
                            protocol, initiatorNode, initiatorPort, hostname, 
                            volume, lun=None):
        '''
        This function will take export group name and project name  as input and
        It will create the Export group with given name.
        parameters:
           name : Name of the export group.
           project: Name of the project path.
        return
            returns with status of creation.
        '''
        # check for existance of export group.
        try:
            status = self.exportgroup_show(name, project)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                projobj = Project(self.__ipAddr, self.__port)
                projuri = projobj.project_query(project)

                nh_obj = Neighborhood(self.__ipAddr, self.__port)
                nhuri = nh_obj.neighborhood_query(neighborhood)

                initParam = dict()
                initParam['protocol'] = protocol
                initParam['initiator_node'] = initiatorNode
                initParam['initiator_port'] = initiatorPort
                initParam['hostname'] = hostname

                fullvolname = project+"/"+volume
                volobj =  Volume(self.__ipAddr, self.__port)
                volumeURI = volobj.volume_query(fullvolname)
                #construct the body
                volParam = dict()
                volParam['id'] = volumeURI
                if (lun != None):
                    volParam['lun'] = lun

                parms = {
                        'name' : name,
                        'project' : projuri,
                        'neighborhood' : nhuri,
                        'initiators': [initParam],
                        'volumes': [volParam]
                        }
                body = json.dumps(parms)

                (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST",
                                             self.URI_EXPORT_GROUP, body)
                o = vipr_utils.json_decode(s)
                return o
            else:
                raise e
        if(status):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Export group with name " + name + " already exists")
   
    def exportgroup_delete(self, name, project):
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
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                        "DELETE", 
                        self.URI_EXPORT_GROUPS_SHOW.format(uri), 
                        None, token)
        return str(s) + " ++ " + str(h)
    

    def exportgroup_query(self, name, project):
        '''
        This function will take export group name/id and project name  as input and 
        returns export group id.
        parameters:
           name : Name/id of the export group.
        return
            return with id of the export group.
         '''
        if (vipr_utils.is_uri(name)):
            return name

        uris = self.exportgroup_list(project)
        for uri in uris:
            exportgroup = self.exportgroup_show(uri, project)
            if (exportgroup['name'] == name ):
                return exportgroup['id']    
        raise SOSError(SOSError.NOT_FOUND_ERR, "Export Group " + name + ": not found")
    
    
    def exportgroup_add_initiator(self, name, project, protocol, initiatorNode, initiatorPort, hostname):
        #construct the body 
        
        token = "cli_export_group_add_initiator:" + str(uuid.uuid4())
       
        initParam = dict()
        initParam['protocol'] = protocol
        initParam['initiator_node'] = initiatorNode  
        initParam['initiator_port'] = initiatorPort 
        initParam['hostname'] = hostname

	parms = {
           'initiator' : initParam
        }
		
        body = json.dumps(parms)
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                        "POST", self.URI_EXPORT_GROUPS_INITIATOR.format(uri), 
                        body, token)
        o = vipr_utils.json_decode(s)
        return o

    def exportgroup_remove_initiators(self, name, project, protocol, initiator):
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                 "DELETE", self.URI_EXPORT_GROUPS_INITIATOR_INSTANCE_DELETE.format(uri, protocol, initiator), 
                 None)
        o = vipr_utils.json_decode(s)
        return o
                    
    def exportgroup_add_volumes(self, name, project, volume, lun):
	fullvolname = project+"/"+volume
        volobj =  Volume(self.__ipAddr, self.__port)
        volumeURI = volobj.volume_query(fullvolname)
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
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                        "POST", self.URI_EXPORT_GROUPS_VOLUME.format(uri), 
                        body, token)
        o = vipr_utils.json_decode(s)
        return o
              
    def exportgroup_remove_volumes(self, name, project, volume):
        volobj =  Volume(self.__ipAddr, self.__port)
        fullvolname = project+"/"+volume
        volumeURI = volobj.volume_query(fullvolname)
        
        token = "cli_export_group_remove_volume:" + fullvolname
        uri = self.exportgroup_query(name, project)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                 "DELETE", self.URI_EXPORT_GROUPS_VOLUME_INSTANCE.format(uri, volumeURI), 
                 None, token)
        o = vipr_utils.json_decode(s)
        return o

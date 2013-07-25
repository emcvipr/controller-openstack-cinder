#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import vipr_utils
import argparse
import sys
import os
from vipr_utils import SOSError
from vipr_neighborhood import Neighborhood
import json
from vipr_tenant import Tenant

class VPool(object):
    '''
    The class definition for operations on 'Class of Service'. 
    '''
    
    URI_VPOOL             = "/{0}/cos"
    URI_VPOOL_SHOW        = URI_VPOOL + "/{1}"
    URI_VPOOL_STORAGEPOOL = URI_VPOOL_SHOW + "/storage-pools"
    URI_VPOOL_ACL         = URI_VPOOL_SHOW + "/acl"
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    def vpool_list_uris(self, type):
        '''
        This function will give us the list of VPOOL uris
        separated by comma.
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                                             "GET", self.URI_VPOOL.format(type), None)
        
        o = vipr_utils.json_decode(s)
        return o['cos']

    def vpool_list(self, type):
        '''
        this function is wrapper to the vpool_list_uris
        to give the list of vpool uris.
        '''
        uris = self.vpool_list_uris(type)
        return uris
        
    def vpool_show_uri(self, type, uri, xml=False):
        '''
        This function will take uri as input and returns with 
        all parameters of VPOOL like lable, urn and type.
        parameters
            uri : unique resource identifier.
        return
            returns with object contain all details of VPOOL.
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                                             "GET", 
                                             self.URI_VPOOL_SHOW.format(type, uri), None, None)
        
        o = vipr_utils.json_decode(s)
        if( o['inactive']):
            return None
        
        if(xml == False):
            return o
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET",
                                             self.URI_VPOOL_SHOW.format(type, uri), None, None, xml)
        return s
     
    def vpool_show(self, name, type, xml=False):
        '''
        This function is wrapper to  with vpool_show_uri. 
        It will take vpool name as input and do query for uri,
        and displays the details of given vpool name.
        parameters
            name : Name of the VPOOL.
            type : Type of the VPOOL { 'file', 'block' or 'object'}
        return
            returns with object contain all details of VPOOL.
        '''
        uri = self.vpool_query(name, type)
        vpool = self.vpool_show_uri(type, uri, xml)
        return vpool
  
    def vpool_list_by_hrefs(self, hrefs):
        return vipr_utils.list_by_hrefs(self.__ipAddr, self.__port, hrefs)     

    def vpool_allow_tenant(self, name, type, tenant):
        '''
        This function is allow given vpool to use by given tenant.
        It will take vpool name, tenant  as inputs and do query for uris.
        parameters
            name : Name of the VPOOL.
            type : Type of the VPOOL { 'file' or 'block' }
            tenant : Name of the tenant
        '''
        uri = self.vpool_query(name, type)
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)

        parms = {
            'add':[{
                'privilege': ['USE'],
                'tenant': tenanturi, 
                }]
            }

        body = json.dumps(parms)
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "POST",
                                             self.URI_VPOOL_ACL.format(type, uri), body)
        return s
    

    def vpool_create(self, name, description,  type, protocols, resiliencyMin, resiliencyMax, performance,
                   consistency, multipaths, snapshots, neighborhoods):
        '''
        This is the function will create the VPOOL with given name and type.
        It will send REST API request to StorageOS instance.
        parameters:
            name : Name of the VPOOL.
            type : Type of the VPOOL { 'file', 'block' or 'object'}
        return
            returns with VPOOL object with all details.
        '''
        # check for existance of vpool.
        try:
            status = self.vpool_show(name, type)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                parms = dict()
                if (name):
                    parms['name'] = name
                if (description):
                    parms['description'] = description
                if (protocols):
                    parms['protocols'] = protocols
                if(performance != None):
                    parms['performance'] = performance
                parms['resiliency_min'] = resiliencyMin 
                parms['resiliency_max'] = resiliencyMax
                if(consistency != None):
                    parms['multi_volume_consistency']= consistency
                if (multipaths):
                    parms['num_paths'] = multipaths
                if (snapshots):
                    parms['max_snapshots'] = snapshots
                if(neighborhoods):
                    urilist = []
                    nh_obj = Neighborhood(self.__ipAddr, self.__port)
                    for neighborhood in neighborhoods:
                        nhuri = nh_obj.neighborhood_query(neighborhood)
                        urilist.append(nhuri)
                    parms['neighborhoods'] = urilist
                
                body = json.dumps(parms)
                (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "POST", self.URI_VPOOL.format(type), body)
                o = vipr_utils.json_decode(s)
                return o
            else:
                raise e
        if(status):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "VPOOL with name " + name + " ("+ type + ") " + "already exists")

    
    def vpool_delete_uri(self, type, uri):
        '''
        This function will take uri as input and deletes that particular VPOOL
        from StorageOS database.
        parameters:
            uri : unique resource identifier for given VPOOL name.
        return
            return with status of the delete operation.
            false incase it fails to do delete.
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, 
                                             "DELETE", 
                                             self.URI_VPOOL_SHOW.format(type, uri), 
                                             None)
        return str(s) + " ++ " + str(h)
    
    def vpool_delete(self, name, type):
        uri = self.vpool_query(name, type)
        res = self.vpool_delete_uri(type, uri)
        return res  
   
  
    def vpool_query(self, name, type):
        '''
        This function will take the VPOOL name and type of VPOOL 
        as input and get uri of the first occurance of given VPOOL.
        paramters:
             name : Name of the VPOOL.
             type : Type of the VPOOL { 'file', 'block' or 'object'}
        return
            return with uri of the given vpool.
        '''
        if (vipr_utils.is_uri(name)):
            return name

        uris = self.vpool_list_uris(type)
        for uri in uris:
            vpool = vipr_utils.show_by_href(self.__ipAddr, self.__port, uri)
	    if(vpool):
                if (vpool['name'] == name):
                    return vpool['id']    
        raise SOSError(SOSError.SOS_FAILURE_ERR, "VPOOL " + name + 
		      " ("+ type + ") " + ": not found")

#!/usr/bin/python
# Copyright (c)2013 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import json
import vipr_utils

from vipr_utils import SOSError
from vipr_tenant import Tenant

class Neighborhood(object):
    '''
    The class definition for operations on 'Neighborhood'. 
    '''

    #Commonly used URIs for the 'Neighborhoods' module
    URI_NEIGHBORHOOD = '/zone/neighborhoods'
    URI_NEIGHBORHOOD_URI = '/zone/neighborhoods/{0}'
    URI_NEIGHBORHOOD_ACLS = URI_NEIGHBORHOOD_URI + '/acl'


    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
       
        
    def neighborhood_query(self, name):
        '''
        Returns the UID of the neighborhood specified by the name
        '''
        if (vipr_utils.is_uri(name)):
            return name

        uris = self.neighborhood_list()

        for uri in uris:
            neighborhood = self.neighborhood_show(uri, False) 
	    if(neighborhood):
                if(neighborhood['name'] == name):
                    return neighborhood['id']
    
        raise SOSError(SOSError.NOT_FOUND_ERR, 
                       "Neighborhood " + name + ": not found")

        

    def neighborhood_list(self):
        '''
        Returns all the neighborhoods in a zone
        Parameters:           
        Returns:
                JSON payload of neighborhood list
        '''
            
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Neighborhood.URI_NEIGHBORHOOD, None)

        o = vipr_utils.json_decode(s)
	
	returnlst = []
	for iter in o['neighborhood']:
	    returnlst.append(iter['id'])

        return returnlst


    def neighborhood_show(self, label, xml=False):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(label)

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET", 
                                             Neighborhood.URI_NEIGHBORHOOD_URI.format(uri),
                                             None, None, xml)

	if(xml==False):
            o = vipr_utils.json_decode(s)
        
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s
    
        return o


    def neighborhood_allow_tenant(self, neighborhood, tenant):
        '''
        Makes a REST API call to retrieve details of a neighborhood  based on its UUID
        '''
        uri = self.neighborhood_query(neighborhood)

	tenant_obj = Tenant(self.__ipAddr, self.__port)
        tenanturi =  tenant_obj.tenant_query(tenant)

	parms = {
            'add':[{
                'privilege': ['USE'],
                'tenant': tenanturi, 
                }]
            }

        body = json.dumps(parms)

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                             self.URI_NEIGHBORHOOD_ACLS.format(uri),
                                             body)
	
	return s


    def neighborhood_create(self, label):
        '''
        creates a neighborhood
        parameters:    
            label:  label of the neighborhood
        Returns:
            JSON payload response
        '''
        try:     
            check = self.neighborhood_show(label)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                var = dict()
                params = dict()
                params['name'] = label
                body = json.dumps(params)
                (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST", 
                                                     Neighborhood.URI_NEIGHBORHOOD , body)
                o = vipr_utils.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, 
                           "Neighborhood with name " + label + " already exists")
        
            
    def neighborhood_delete(self, label):
        '''
        Makes a REST API call to delete a neighborhood by its UUID
        '''
        uri = self.neighborhood_query(label)

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "DELETE", 
                                             Neighborhood.URI_NEIGHBORHOOD_URI.format(uri),
                                             None)
        return str(s) + " ++ " + str(h)

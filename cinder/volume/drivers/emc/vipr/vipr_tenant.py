#!/usr/bin/python
# Copyright (c) 2013 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import argparse
import vipr_utils
import os
import sys
import json
import base64
from vipr_utils import SOSError

class Tenant(object):
    '''
    The class definition for operations on 'Project'. 
    '''

    URI_SERVICES_BASE = '' 
    URI_TENANT = URI_SERVICES_BASE + '/tenant'
    URI_TENANTS	 = URI_SERVICES_BASE + '/tenants/{0}'
    URI_TENANTS_SUBTENANT = URI_TENANTS	 + '/subtenants'
    URI_TENANT_CONTENT = URI_TENANT
    URI_TENANT_ROLES = URI_TENANTS + '/role-assignments'
    URI_SUBTENANT = URI_TENANT + '/subtenants'
    URI_SUBTENANT_INFO = URI_SUBTENANT + '/{0}'
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port


    def tenant_assign_role(self, tenant_name, roles, subject_id, group):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

        parms = {
            'role_assignments': [{
                        'role' : roles,
                        'subject_id' : subject_id,
                        'group' : group 
                        }]
                    }
        body = json.dumps(parms)
    
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             body)
    
    def tenant_get_role(self, tenant_name, subject_id, group):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

    
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             None)

 	o = vipr_utils.json_decode(s)

        if (not o):
            return {}

	return o


    def get_tenant_by_name(self, tenant):
        uri = None
        if (not tenant):
            uri = self.tenant_getid()
        else:
            if not vipr_utils.is_uri(tenant):
                uri = self.tenant_query(tenant)
            else:
                uri = tenant
            if (not uri):
                raise SOSError(SOSError.NOT_FOUND_ERR,
                               'Tenant ' + tenant + ': not found')
        return uri	
    

    def tenant_query(self, label):
        '''
        Returns the UID of the tenant specified by the hierarchial name 
        (ex tenant`1/tenant2/tenant3)
        '''

        if (vipr_utils.is_uri(label)):
            return label

        id = self.tenant_getid()
        subtenants = self.tenant_list(id)
        subtenants.append(self.tenant_show(None))

        for tenant in subtenants:
            if (tenant['name'] == label):
                rslt = self.tenant_show_by_uri(tenant['id'])
                if(rslt):
                    return tenant['id']

        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "Tenant " + label + ": not found")

    def tenant_list(self, uri=None):
        '''
        Returns all the tenants under a parent tenant
        Parameters:
            parent: The parent tenant name
        Returns:
                JSON payload of tenant list
        '''

        if (not uri):
            uri = self.tenant_getid()

        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                    "GET", self.URI_TENANTS_SUBTENANT.format(uri),
                     None)

        o = vipr_utils.json_decode(s)

        if (not o):
            return {}

        return o['subtenant']



    def tenant_show(self, label, xml=False):
        '''
        Returns the details of the tenant based on its name
        '''
        if label:
            id = self.tenant_query(label)
        else:
            id = self.tenant_getid()

        return self.tenant_show_by_uri(id, xml)



    def tenant_show_by_uri(self, uri,xml=False):
        '''
        Makes a REST API call to retrieve details of a tenant  based on its UUID
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Tenant.URI_TENANTS.format(uri),
                         		             None, None, xml)

	if(xml==False):
            o = vipr_utils.json_decode(s)
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s

        return o


    def tenant_getid(self):
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Tenant.URI_TENANT, None)

        o = vipr_utils.json_decode(s)
        return o['id']


    def tenant_create(self, label, description, suffix):
        '''
        creates a tenant
        parameters:    
            label:  label of the tenant
            parent: parent tenant of the tenant
        Returns:
            JSON payload response
        '''
            
        try:
            check = self.tenant_show(label)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                parms = dict()
                parms['name'] = label
                parms['description'] = description
                parms['enterprise_suffix'] = [suffix]

        
                body = json.dumps(parms)
                uri = self.tenant_getid()
                

                (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                     "POST", self.URI_TENANTS_SUBTENANT.format(uri), body)

                o = vipr_utils.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                            "Tenant create failed: subtenant with same" + 
                            "name already exists")
        

    def tenant_delete_by_uri(self, uri):
        '''
        Makes a REST API call to delete a tenant by its UUID
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                         "DELETE", Tenant.URI_TENANTS.format(uri),
                         		         None)
        return 
    
    def tenant_delete(self, label):
        '''
        deletes a tenant by name
        '''
        uri = self.tenant_query(label)
        return self.tenant_delete_by_uri(uri)

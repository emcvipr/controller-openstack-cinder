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
from vipr_utils import SOSError
import json
from vipr_tenant import Tenant

class Project(object):
    '''
    The class definition for operations on 'Project'. 
    '''

    #Commonly used URIs for the 'Project' module
    URI_PROJECT_LIST = '/tenants/{0}/projects'
    URI_PROJECT = '/projects/{0}'
    URI_PROJECT_RESOURCES = '/projects/{0}/resources'
    URI_PROJECT_ACL = '/projects/{0}/acl'
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the StorageOS instance. These are
        needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def project_create(self, name, tenant_name):
        '''
        Makes REST API call to create project under a tenant
        Parameters:
            name: name of project
            tenant_name: name of the tenant under which project 
                         is to be created
        Returns:
            Created project details in JSON response payload
        '''
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e
        
        project_already_exists = True

        try:
            self.project_query(tenant_name + "/" + name)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                project_already_exists = False
            else:
                raise e

        if(project_already_exists):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                           "Project with name: " + name + 
                           " already exists")
            
        body = vipr_utils.json_encode('name', name)
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Project.URI_PROJECT_LIST.format(tenant_uri), body)
        o = vipr_utils.json_decode(s)
        return o
    
    def project_list(self, tenant_name):
        '''
        Makes REST API call and retrieves projects based on tenant UUID
        Parameters: None
        Returns:
            List of project UUIDs in JSON response payload 
        '''
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
        except SOSError as e:
            raise e
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Project.URI_PROJECT_LIST.format(tenant_uri), None)
        o = vipr_utils.json_decode(s)
        
        if("project" in o):        
            return vipr_utils.get_list(o, 'project')
        return []
        

        
    def project_show_by_uri(self, uri, xml=False):
        '''
        Makes REST API call and retrieves project derails based on UUID
        Parameters:
            uri: UUID of project
        Returns:
            Project details in JSON response payload
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Project.URI_PROJECT.format(uri), None)
        o = vipr_utils.json_decode(s)
        inactive = vipr_utils.get_node_value(o, 'inactive')
        if(inactive == True):
            return None
        
        if(xml):
            (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Project.URI_PROJECT.format(uri), None, None, xml)
            return s
            
        return o
        
    def project_show(self, name, xml=False):
        '''
        Retrieves project derails based on project name
        Parameters:
            name: name of the project
        Returns:
            Project details in JSON response payload
        '''
        project_uri = self.project_query(name)
        project_detail = self.project_show_by_uri(project_uri, xml)
        return project_detail
    


    def project_query(self, name):
        '''
        Retrieves UUID of project based on its name
        Parameters:
            name: name of project
        Returns: UUID of project
        Throws:
            SOSError - when project name is not found 
        '''
        if (vipr_utils.is_uri(name)):
            return name
        (tenant_name, project_name) = vipr_utils.get_parent_child_from_xpath(name)
        if(not tenant_name):
            raise SOSError(SOSError.NOT_FOUND_ERR, 'Tenant name is not specified')
        tenant_obj = Tenant(self.__ipAddr, self.__port)
        
        try:
            tenant_uri = tenant_obj.tenant_query(tenant_name)
            projects = self.project_list(tenant_uri)
            if(projects and len(projects) > 0):
                for project in projects:
                    if (project):
                        project_detail = self.project_show_by_uri(project['id'])
                        if(project_detail and project_detail['name'] == project_name):
                            return project_detail['id']
            raise SOSError(SOSError.NOT_FOUND_ERR, 'Project: ' + 
                           project_name + ' not found under tenant: ' + tenant_name)
        except SOSError as e:
            raise e
        
    
    def project_delete_by_uri(self, uri):
        '''
        Deletes a project based on project UUID
        Parameters:
            uri: UUID of project
        '''
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port,
                                             "DELETE", Project.URI_PROJECT.format(uri), None)
        return
    
    def project_delete(self, name):
        '''
        Deletes a project based on project name
        Parameters:
            name: name of project
        '''
        project_uri = self.project_query(name)
        return self.project_delete_by_uri(project_uri)
    
    def update(self, project_name, new_name, new_owner):
        '''
        Makes REST API call and updates project name and owner
        Parameters:
            project_name: name of project
            new_name: new name of the project
            
        Returns:
            List of project resources in response payload 
        '''
        project_uri = self.project_query(project_name);
        
        request = dict()
        if(new_name and len(new_name) > 0):
            request["name"] = new_name
        if(new_owner and len(new_owner) > 0):
            request["owner"] = new_owner
        
        body = json.dumps(request)
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Project.URI_PROJECT.format(project_uri), body)
    
    def get_acl(self, project_name):
        
        project_uri = self.project_query(project_name)
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Project.URI_PROJECT_ACL.format(project_uri), None)
        o = vipr_utils.json_decode(s)
        return o
    
    def full_update_acl(self, project_name):
        project_uri = self.project_query(project_name)
        
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Project.URI_PROJECT_ACL.format(project_uri), None)
        o = vipr_utils.json_decode(s)
        return o
    
    def add_remove_acl(self, project_name, operation, privilege, subject_id):
        project_uri = self.project_query(project_name)
        
        if("add"==operation):
            request= {
                    'add':[{
                        'privilege': [privilege],
                        'subject_id': subject_id,
                        }]
                      }
        else:
            request= {
                    'remove':[{
                        'privilege': [privilege],
                        'subject_id': subject_id,
                        }]
                      }
        body = json.dumps(request);
                    
        (s, h) = vipr_utils.service_json_request(self.__ipAddr, self.__port, "POST",
                                             Project.URI_PROJECT_ACL.format(project_uri), body)

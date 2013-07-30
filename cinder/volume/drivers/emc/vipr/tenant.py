#!/usr/bin/python
# Copyright (c) 2012 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import argparse
import common
import os
import sys
import json
import base64
from common import SOSError

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
    URI_RESOURCE_DEACTIVATE      = '{0}/deactivate'

    URI_NAMESPACE_COMMON            = URI_SERVICES_BASE + '/object/namespaces'
    URI_NAMESPACE_BASE              = URI_NAMESPACE_COMMON + '/namespace'
    URI_NAMESPACE_INSTANCE          = URI_NAMESPACE_BASE + '/{0}'
    URI_NAMESPACE_TENANT_BASE       = URI_NAMESPACE_COMMON + '/tenant'
    URI_NAMESPACE_TENANT_INSTANCE   = URI_NAMESPACE_TENANT_BASE + '/{0}'
    
    PROVIDER_TENANT = "Provider Tenant"

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
    

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             body)
    

    def tenant_update_role(self, tenant_name, role, subject_id, group):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

	if(subject_id):
	    objecttype = 'subject_id'
	    objectname = subject_id
	else:
	    objecttype = 'group'
	    objectname = group

 	parms = {
                 "add" : [ { "role" : [role], objecttype : objectname }]
                 }

        body = json.dumps(parms)
    
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             body)


    def tenant_delete_role(self, tenant_name, role, subject_id, group):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

	if(subject_id):
	    objecttype = 'subject_id'
	    objectname = subject_id
	else:
	    objecttype = 'group'
	    objectname = group

 	parms = {
                 "remove" : [ { "role" : [role], objecttype : objectname }]
                 }

        body = json.dumps(parms)
    
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "PUT",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             body)



    def tenant_get_namespace(self, tenant_name):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

    
        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             Tenant.URI_NAMESPACE_TENANT_INSTANCE.format(tenant_uri),
                                             None)

 	o = common.json_decode(s)

        if (not o):
            return {}

	return o


    def namespace_query(self, label):
        '''
        Returns the UID of the tenant specified by the hierarchial name 
        (ex tenant`1/tenant2/tenant3)
        '''

        namespaces = self.list_namespaces()

        for namespace in namespaces:
            if (namespace == label):
		return label

        raise SOSError(SOSError.NOT_FOUND_ERR,
                       "Namespace " + label + ": not found")



    def show_namespace(self, namespace):
        '''
        Makes a REST API call to assign admin role
         '''
    
        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             Tenant.URI_NAMESPACE_INSTANCE.format(namespace),
                                             None)

 	o = common.json_decode(s)

        if (not o):
            return {}

	return o


    def tenant_delete_namespace(self, namespace):
        '''
        Makes a REST API call to assign admin role
         '''
    
        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "POST",
                                             Tenant.URI_RESOURCE_DEACTIVATE.format(Tenant.URI_NAMESPACE_INSTANCE.format(namespace)),
                                             None)



    def list_namespaces(self):
        '''
        Makes a REST API call to assign admin role
         '''
    
        (s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT, "GET",
                                             Tenant.URI_NAMESPACE_COMMON,
                                             None)

 	o = common.json_decode(s)

        if (not o):
            return {}

	namespaces = o['namespace']
	
        ids = []
        if (type(namespaces) != list):
            namespaces = [namespaces]
        for namespace in namespaces:
            ids.append(namespace.get('id'))
        return ids



    def tenant_create_namespace(self, tenant_name, namespace, project, cos):
        '''
        Makes a REST API call to assign admin role
         '''
	try:
	    ret = self.namespace_query(namespace)
	    if(ret):
            	raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                            "Namespace create failed: namespace with same name already exists")
		
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
		tenant_uri = self.get_tenant_by_name(tenant_name)

		cos_uri = None
		project_uri = None

		if( cos ):
            	    from objectcos import Objectcos
            	    obj = Objectcos(self.__ipAddr, self.__port)
            	    cos_uri = obj.objectcos_query( cos)

        	if( project ):
            	    from project import Project
            	    obj = Project(self.__ipAddr, self.__port)

		    qualifiedname = project
		    if(tenant_name):
			qualifiedname = tenant_name + "/"+project
            	    project_uri = obj.project_query( qualifiedname )


		parms = {
                	'namespace' : namespace,
                	'zones' : [
                    		{
                        	'tenant' : tenant_uri,
                    		}
                	]
        	}

		if ( project_uri != None ):
            	    parms['zones'][0]['default_object_project'] = project_uri

		if ( cos_uri != None ):
            	    parms['zones'][0]['default_object_store'] = cos_uri



        	body = json.dumps(parms)

        	(s, h) = common.service_json_request(self.__ipAddr, common.OBJCTRL_PORT , "POST", self.URI_NAMESPACE_BASE,
                                             body, None)

            else:
		raise e
	


    def tenant_get_role(self, tenant_name, subject_id, group , xml=False):
        '''
        Makes a REST API call to assign admin role
         '''
        tenant_uri = self.get_tenant_by_name(tenant_name)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             None, None, False)


        o = common.json_decode(s)
        if('inactive' in o):
            if(o['inactive'] == True):
                return None


	if(xml == False):
	    return o


        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Tenant.URI_TENANT_ROLES.format(tenant_uri),
                                             None, None, xml)

	return s



    def get_tenant_by_name(self, tenant):
        uri = None
        if (not tenant):
            uri = self.tenant_getid()
        else:
            if not common.is_uri(tenant):
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

        if (common.is_uri(label)):
            return label

        # import pdb; pdb.set_trace()
        id = self.tenant_getid()

	if not label:
            return id

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

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                    "GET", self.URI_TENANTS_SUBTENANT.format(uri),
                     None)

        o = common.json_decode(s)

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
        (s, h) = common.service_json_request(self.__ipAddr, self.__port, "GET",
                                             Tenant.URI_TENANTS.format(uri),
                         		             None, None, xml)

	if(xml==False):
            o = common.json_decode(s)
            if('inactive' in o):
                if(o['inactive'] == True):
                    return None
	else:
	    return s

        return o


    def tenant_getid(self):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                             "GET", Tenant.URI_TENANT, None)

        o = common.json_decode(s)
        return o['id']


    def tenant_create(self, name, key, value, domain):
        '''
        creates a tenant
        parameters:    
            label:  label of the tenant
            parent: parent tenant of the tenant
        Returns:
            JSON payload response
        '''
            
        try:
            check = self.tenant_show(name)
        except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                parms = dict()
		parms = {
                'name': name
        	}
		keyval = dict()

		if(key):
		    keyval['key']=key
		if(value):
		    vallst = []
		    vallst.append(value)
		    keyval['value']=vallst

		usermappinglst = []
		attrlst = []

		if( (keyval.has_key('key')) or (keyval.has_key('value')) ):
		    attrlst.append(keyval)

		usermapping = dict()
		usermapping['attributes']=attrlst
		usermapping['domain'] = domain
		usermappinglst.append(usermapping)

		parms['user_mappings']=usermappinglst

                body = json.dumps(parms)
                uri = self.tenant_getid()
                
                (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                     "POST", self.URI_TENANTS_SUBTENANT.format(uri), body)

                o = common.json_decode(s)
                return o
            else:
                raise e

        if(check):
            raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR,
                            "Tenant create failed: subtenant with same" + 
                            "name already exists")
        

    def tenant_add_attribute(self, label, key, value, domain):
        '''
        creates a tenant
        parameters:    
            label:  label of the tenant
            parent: parent tenant of the tenant
        Returns:
            JSON payload response
        '''
            
        try:
            tenant = self.tenant_show(label)
	    
	    user_mappings = tenant['user_mappings']

	    for user_mapping in user_mappings:
                if(domain == user_mapping['domain']):
                    for attribute in user_mapping['attributes']:
                        if (key == attribute['key'] and value in attribute['value']):
	    		    if(label):
				tenname = label
	    		    else:
				tenname = self.PROVIDER_TENANT

            		    raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, "Tenant " + 
                           	          tenname + ": already has the key="+key+" and value="+value+" combination" )

            parms = dict()

	    keyval = dict()

	    if(key):
	        keyval['key']=key
	    if(value):
	        vallst = []
	        vallst.append(value)
	        keyval['value']=vallst

	    usermappinglst = []
	    attrlst = []

	    if( (keyval.has_key('key')) or (keyval.has_key('value')) ):
	        attrlst.append(keyval)

	    usermapping = dict()
	    usermapping['attributes']=attrlst
	    usermapping['domain'] = domain
	    usermappinglst.append(usermapping)
	    
	    adddict = dict()
	    adddict['add'] = usermappinglst

	    parms['user_mapping_changes'] = adddict

            body = json.dumps(parms)

            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                 "PUT", self.URI_TENANTS.format(tenant['id']), body)
	
	
        except SOSError as e:
            raise e


    def tenant_remove_attribute(self, label, key, value, domain):
        '''
        creates a tenant
        parameters:    
            label:  label of the tenant
            parent: parent tenant of the tenant
        Returns:
            JSON payload response
        '''
            
        try:
            tenant = self.tenant_show(label)
	    
	    user_mappings = tenant['user_mappings']

            parms = dict()
	    parms = {
                 'user_mapping_changes': {
                     'remove': [{
                        'domain': domain,
                        'attributes':[{
                            'key':key,
                            'value':[value]
                         }],
                     }]}
                 }

            body = json.dumps(parms)

            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                 "PUT", self.URI_TENANTS.format(tenant['id']), body)
	
        except SOSError as e:
            raise e


    def tenant_add_group(self, label, ingroup, domain):
        '''
        creates a tenant
        parameters:    
            label:  label of the tenant
            parent: parent tenant of the tenant
        Returns:
            JSON payload response
        '''
            
        try:
            tenant = self.tenant_show(label)
	    
	    user_mappings = tenant['user_mappings']

	    for user_mapping in user_mappings:
                if(domain == user_mapping['domain']):
                    for group in user_mapping['groups']:
			if (group == ingroup):
	    		    if(label):
				tenname = label
	    		    else:
				tenname = self.PROVIDER_TENANT

            		    raise SOSError(SOSError.ENTRY_ALREADY_EXISTS_ERR, "Tenant " + 
                           	           tenname + ": already contains group mapping " + group +" already"  )

            parms = dict()
	    parms = {
                 'user_mapping_changes': {
                     'add': [{
                        'domain': domain,
                        'groups': [ingroup],
                     }]}
                 }


            body = json.dumps(parms)

            (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                 "PUT", self.URI_TENANTS.format(tenant['id']), body)
	
        except SOSError as e:
            raise e



    def tenant_delete_by_uri(self, uri):
        '''
        Makes a REST API call to delete a tenant by its UUID
        '''
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                         "POST", self.URI_RESOURCE_DEACTIVATE.format(self.URI_TENANTS.format(uri)),
                         		         None)
        return 
    
    def tenant_delete(self, label):
        '''
        deletes a tenant by name
        '''
        uri = self.tenant_query(label)
        return self.tenant_delete_by_uri(uri)
    
# TENANT Create routines

def create_parser(subcommand_parsers, common_parser):
    # create command parser
    create_parser = subcommand_parsers.add_parser('create',
                                description='StorageOS Tenant Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a Tenant')

    mandatory_args = create_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='Name of Tenant',
                                metavar='<tenantname>',
                                dest='name',
                                required=True)

    create_parser.add_argument('-key',
                               help='key of AD attribute to map to tenant',
                               dest='key', metavar='<key>')

    create_parser.add_argument('-value',
                               help='value of AD attribute to map to tenant',
                               dest='value', metavar='<value>')

    mandatory_args.add_argument('-domain',
                               help='domain',
                               dest='domain', metavar='<domain>', required=True)

    create_parser.set_defaults(func=tenant_create)

def tenant_create(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_create(args.name, args.key , args.value, args.domain)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR,
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Tenant " + 
                           args.name + ": Create failed\n" + e.err_text)
        else:
            raise e



# TENANT add attribute routines

def add_attribute_parser(subcommand_parsers, common_parser):
    # create command parser
    add_attribute_parser = subcommand_parsers.add_parser('add-attribute',
                                description='StorageOS Tenant Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a Tenant')

    mandatory_args = add_attribute_parser.add_argument_group('mandatory arguments')
    add_attribute_parser.add_argument('-name', '-n',
                                help='Name of Tenant',
                                metavar='<tenantname>',
                                dest='name')

    add_attribute_parser.add_argument('-key',
                               help='key of AD attribute to map to tenant',
                               dest='key', metavar='<key>')

    add_attribute_parser.add_argument('-value',
                               help='value of AD attribute to map to tenant',
                               dest='value', metavar='<value>')

    mandatory_args.add_argument('-domain',
                               help='domain',
                               dest='domain', metavar='<domain>',
			       required=True)


    add_attribute_parser.set_defaults(func=tenant_add_attribute)


def tenant_add_attribute(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_add_attribute(args.name, args.key , args.value, args.domain)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR,
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
	    if(args.name):
		tenname = args.name
	    else:
		tenname = Tenant.PROVIDER_TENANT

            raise SOSError(e.err_code, "Tenant " + 
                           tenname + ": Add attribute failed\n" + e.err_text)
        else:
            raise e


def remove_attribute_parser(subcommand_parsers, common_parser):
    # create command parser
    remove_attribute_parser = subcommand_parsers.add_parser('remove-attribute',
                                description='StorageOS Tenant remove attribute CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Remove attribute of a Tenant')

    mandatory_args = remove_attribute_parser.add_argument_group('mandatory arguments')
    remove_attribute_parser.add_argument('-name', '-n',
                                help='Name of Tenant',
                                metavar='tenantname',
                                dest='name')

    mandatory_args.add_argument('-key',
                               help='key of AD attribute to map to tenant',
                               dest='key', metavar='key')

    mandatory_args.add_argument('-value',
                               help='value of AD attribute to map to tenant',
                               dest='value', metavar='value')

    mandatory_args.add_argument('-domain',
                               help='domain',
                               dest='domain', metavar='<domain>')

    remove_attribute_parser.set_defaults(func=tenant_remove_attribute)


def tenant_remove_attribute(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_remove_attribute(args.name, args.key , args.value, args.domain)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR,
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
            raise SOSError(e.err_code, "Tenant " + 
                           args.name + ": Remove attribute failed\n" + e.err_text)
        else:
            raise e

def add_group_parser(subcommand_parsers, common_parser):
    # create command parser
    add_group_parser = subcommand_parsers.add_parser('add-group',
                                description='StorageOS Tenant Create CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Create a Tenant')

    mandatory_args = add_group_parser.add_argument_group('mandatory arguments')
    add_group_parser.add_argument('-name', '-n',
                                help='Name of Tenant',
                                metavar='tenantname',
                                dest='name')

    mandatory_args.add_argument('-group',
                               help='group',
                               dest='group', metavar='<group>')

    mandatory_args.add_argument('-domain',
                               help='domain',
                               dest='domain', metavar='<domain>')

    add_group_parser.set_defaults(func=tenant_add_group)


def tenant_add_group(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_add_group(args.name, args.group , args.domain)
    except SOSError as e:
        if (e.err_code in [SOSError.NOT_FOUND_ERR,
                           SOSError.ENTRY_ALREADY_EXISTS_ERR]):
	
	    if(args.name):
		tenname = args.name
	    else:
		tenname = Tenant.PROVIDER_TENANT
            raise SOSError(e.err_code, "Tenant " + 
                           tenname + ": Add group failed\n" + e.err_text)
        else:
            raise e
# TENANT Delete routines

def delete_parser(subcommand_parsers, common_parser):
    # delete command parser
    delete_parser = subcommand_parsers.add_parser('delete',
                                description='StorageOS Tenant Delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete a Tenant')

    mandatory_args = delete_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)

    delete_parser.set_defaults(func=tenant_delete)

def tenant_delete(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_delete(args.name)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Tenant delete failed: " + e.err_text)
        else:
            raise e

# TENANT Show routines

def show_parser(subcommand_parsers, common_parser):
    # show command parser
    show_parser = subcommand_parsers.add_parser('show',
                                description='StorageOS Tenant Show CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Show a Tenant')

    show_parser.add_argument('-name', '-n',
                help='name of Tenant',
                dest='name',
                metavar='tenantname',
                required=False)

    show_parser.add_argument('-xml',
                            dest='xml',
                            action='store_true',
                            help='XML response')


    show_parser.set_defaults(func=tenant_show)

def tenant_show(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_show(args.name, args.xml)

	if(args.xml):
            return common.format_xml(str(res))

        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR,
                           "Tenant show failed: " + e.err_text)
        else:
            raise e

# TENANT Query routines

def query_parser(subcommand_parsers, common_parser):
    # query command parser
    query_parser = subcommand_parsers.add_parser('query',
                                description='StorageOS Tenant Query CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Query a Tenant')

    mandatory_args = query_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)

    query_parser.set_defaults(func=tenant_query)



def tenant_query(args):
    obj = Tenant(args.ip, args.port)
    try:
        res = obj.tenant_query(args.name)
        return common.format_json_object(res)
    except SOSError as e:
        if(e.err_code == SOSError.NOT_FOUND_ERR):
            raise SOSError(SOSError.NOT_FOUND_ERR, "Tenant query failed: " + 
                  e.err_text)
        else:
            raise e

# TENANT List routines

def list_parser(subcommand_parsers, common_parser):
    # list command parser
    list_parser = subcommand_parsers.add_parser('list',
                                description='StorageOS Tenant List CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='List subtenants of a Tenant')
 
    list_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List tenants with details',
                             dest='verbose')

    list_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List tenants with more details in tabular format',
                             dest='long')
    list_parser.set_defaults(func=tenant_list)

def tenant_list(args):
    obj = Tenant(args.ip, args.port)
    try:
        uris = obj.tenant_list()

        output = []

        myid = obj.tenant_getid()
        output.append(obj.tenant_show(myid))

        for uri in uris:
            if(obj.tenant_show(uri['id'])):
                output.append(obj.tenant_show(uri['id']))
        if(len(output) > 0):
            if(args.verbose == True):
		return common.format_json_object(output)
	    elif(args.long == True):
		from common import TableGenerator
                TableGenerator(output, [ 'module/name', 'description']).printTable()
            else:
		from common import TableGenerator
                TableGenerator(output, [ 'module/name']).printTable()
    except SOSError as e:
            if(e.err_code == SOSError.NOT_FOUND_ERR):
                raise SOSError(SOSError.NOT_FOUND_ERR,
                      "Tenant list failed: " + e.err_text)
            else:
                raise e

# TENANT Role addition

def assign_tenant_role_parser(subcommand_parsers, common_parser):
    # role  command parser
    role_parser = subcommand_parsers.add_parser('assign-role',
                                description='StorageOS Tenant role assignment CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Assign role to a tenant')
    mandatory_args = role_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)
    
    mandatory_args.add_argument('-role', '-r',
                                nargs='+',
                                help='Role of Tenant',
                                dest='roles',
                                choices=["TENANT_ADMIN","PROJECT_ADMIN"],
                                required=True)
    
    arggroup =  role_parser.add_mutually_exclusive_group(required=True)

    arggroup.add_argument('-subject-id', '-sb',
                                help='Subject ID',
                                dest='subjectid',
                                metavar='subjectid')

    arggroup.add_argument('-group', '-g',
                             help='Group',
                             dest='group',
                             metavar='group')

    role_parser.set_defaults(func=assign_role)

def assign_role(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_assign_role(args.name, args.roles, args.subjectid, args.group)
    except SOSError as e:
        raise e


def add_tenant_role_parser(subcommand_parsers, common_parser):
    # role  command parser
    add_role_parser = subcommand_parsers.add_parser('add-role',
                                description='StorageOS Tenant role update CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Update role to a tenant')
    mandatory_args = add_role_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)
    
    mandatory_args.add_argument('-role', '-r',
                                #nargs='+',
                                help='Role of Tenant',
                                dest='roles',
                                choices=["TENANT_ADMIN", "PROJECT_ADMIN"],
                                required=True)
    
    arggroup =  add_role_parser.add_mutually_exclusive_group(required=True)

    arggroup.add_argument('-subject-id', '-sb',
                                help='Subject ID',
                                dest='subjectid',
                                metavar='subjectid')

    arggroup.add_argument('-group', '-g',
                             help='Group',
                             dest='group',
                             metavar='group')
 
    add_role_parser.set_defaults(func=update_role)


def update_role(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_update_role(args.name, args.roles, args.subjectid, args.group)
    except SOSError as e:
        raise e



def delete_tenant_role_parser(subcommand_parsers, common_parser):
    # role  command parser
    delete_role_parser = subcommand_parsers.add_parser('delete-role',
                                description='StorageOS Tenant role delete CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Delete role to a tenant')
    mandatory_args = delete_role_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)
    
    mandatory_args.add_argument('-role', '-r',
                                help='Role of Tenant',
                                dest='roles',
                                choices=["TENANT_ADMIN", "PROJECT_ADMIN"],
                                required=True)
    
    arggroup =  delete_role_parser.add_mutually_exclusive_group(required=True)

    arggroup.add_argument('-subject-id', '-sb',
                                help='Subject ID',
                                dest='subjectid',
                                metavar='subjectid')

    arggroup.add_argument('-group', '-g',
                             help='Group',
                             dest='group',
                             metavar='group')
 
    delete_role_parser.set_defaults(func=delete_role)



def delete_role(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_delete_role(args.name, args.roles, args.subjectid, args.group)
    except SOSError as e:
        raise e


def get_tenant_role_parser(subcommand_parsers, common_parser):
    # role  command parser
    get_role_parser = subcommand_parsers.add_parser('get-role',
                                description='StorageOS Tenant role display CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Get roles of a tenant')
    mandatory_args = get_role_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-name', '-n',
                                help='name of Tenant',
                                dest='name',
                                metavar='tenantname',
                                required=True)
    
    get_role_parser.add_argument('-xml',
                            dest='xml',
                            action='store_true',
                            help='XML response')
 
    get_role_parser.set_defaults(func=get_role)



def get_role(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_get_role(args.name, None , None, args.xml)
	if(args.xml):
            return common.format_xml(str(res))

	return common.format_json_object(res)

    except SOSError as e:
        raise e




def create_namespace_parser(subcommand_parsers, common_parser):
    # role  command parser
    create_namespace_parser = subcommand_parsers.add_parser('create',
                                description='StorageOS Tenant Create Namespace CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='create a namespace')
    mandatory_args = create_namespace_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-namespace', '-ns',
                                help='name of Namespace',
                                dest='namespace',
                                metavar='namespace',
                                required=True)
    
 
    create_namespace_parser.add_argument('-tenant', 
                                help='name of Tenant',
                                dest='tenant',
                                metavar='tenant')

    create_namespace_parser.add_argument('-project',
                                 help='name of Project',
                                 dest='project',
                                 metavar='<project>')

    create_namespace_parser.add_argument('-cos',
                                 help='name of Object COS',
                                 dest='cos',
                                 metavar='<cos>')

    create_namespace_parser.set_defaults(func=tenant_create_namespace)



def tenant_create_namespace(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        obj.tenant_create_namespace(args.tenant, args.namespace, args.project, args.cos)
    except SOSError as e:
        raise e




def get_namespace_parser(subcommand_parsers, common_parser):
    # role  command parser
    get_namespace_parser = subcommand_parsers.add_parser('get-namespace',
                                description='StorageOS Get Tenant Namespace CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='get namespace')
 
    get_namespace_parser.add_argument('-tenant', 
                                help='name of Tenant',
                                dest='tenant',
                                metavar='tenant')

    get_namespace_parser.set_defaults(func=tenant_get_namespace)



def tenant_get_namespace(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_get_namespace(args.tenant)
        return common.format_json_object(res)
    except SOSError as e:
        raise e


def show_namespace_parser(subcommand_parsers, common_parser):
    # role  command parser
    show_namespace_parser = subcommand_parsers.add_parser('show',
                                description='StorageOS Show Namespace CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='show namespace')
 
    mandatory_args = show_namespace_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-namespace','-ns',
                                help='name of Namespace',
                                dest='namespace',
                                metavar='<namespace>', 
                                required=True)

    show_namespace_parser.set_defaults(func=show_namespace)



def show_namespace(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.show_namespace(args.namespace)
        return common.format_json_object(res)
    except SOSError as e:
        raise e


def delete_namespace_parser(subcommand_parsers, common_parser):
    # role  command parser
    delete_namespace_parser = subcommand_parsers.add_parser('delete',
                                description='StorageOS Show Namespace CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='delete namespace')
 
    mandatory_args = delete_namespace_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-namespace', '-ns',
                                help='name of Namespace',
                                dest='namespace',
                                metavar='<namespace>', 
                                required=True)

    delete_namespace_parser.set_defaults(func=delete_namespace)



def delete_namespace(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        res = obj.tenant_delete_namespace(args.namespace)
	return res
    except SOSError as e:
        raise e


def list_namespaces_parser(subcommand_parsers, common_parser):
    # role  command parser
    list_namespaces_parser = subcommand_parsers.add_parser('list',
                                description='StorageOS List Namespaces CLI usage.',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='list namespace')
 
    
    list_namespaces_parser.add_argument('-verbose', '-v',
                             action='store_true',
                             help='List tenants with details',
                             dest='verbose')


    list_namespaces_parser.add_argument('-long', '-l',
                             action='store_true',
                             help='List tenants with more details in tabular format',
                             dest='long')

    list_namespaces_parser.set_defaults(func=list_namespaces)



def list_namespaces(args):
    obj = Tenant(args.ip, args.port)
    
    try:
        uris = obj.list_namespaces()

        output = []

	for uri in uris:
            if(obj.show_namespace(uri)):
		tmp = obj.show_namespace(uri)
		
    		objTenant = Tenant(args.ip, args.port)
		tenantval = objTenant.tenant_show_by_uri(tmp['zones']['ZONE0']['tenant'])
		tmp['tenantname'] = tenantval['name']
                output.append(tmp)

        if(len(output) > 0):
            if(args.verbose == True):
                return common.format_json_object(output)
            elif(args.long == True):
                from common import TableGenerator
                TableGenerator(output, [ 'id', 'tenantname']).printTable()
            else:
                from common import TableGenerator
                TableGenerator(output, [ 'id']).printTable()

    except SOSError as e:
        raise e
#
# Tenant Main parser routine
#

def tenant_parser(parent_subparser, common_parser):
    # main tenant parser
    parser = parent_subparser.add_parser('tenant',
                description='StorageOS Tenant CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Operations on Tenant')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create command parser
    create_parser(subcommand_parsers, common_parser)

    # delete command parser
    delete_parser(subcommand_parsers, common_parser)

    # show command parser
    show_parser(subcommand_parsers, common_parser)

    # query command parser
    #query_parser(subcommand_parsers, common_parser)

    # list command parser
    list_parser(subcommand_parsers, common_parser)

    # role command parser
    #assign_tenant_role_parser(subcommand_parsers, common_parser)

    # role command parser
    get_tenant_role_parser(subcommand_parsers, common_parser)

    # add attribute command parser
    add_attribute_parser(subcommand_parsers, common_parser)

    # aupdate role parser
    add_tenant_role_parser(subcommand_parsers, common_parser)

    # delete role parser
    delete_tenant_role_parser(subcommand_parsers, common_parser)

    # add group parser
    add_group_parser(subcommand_parsers, common_parser)

    # remove attribute parser
    remove_attribute_parser(subcommand_parsers, common_parser)

    # remove group parser
    #remove_group_parser(subcommand_parsers, common_parser)



def namespace_parser(parent_subparser, common_parser):
    # main tenant parser
    parser = parent_subparser.add_parser('namespace',
                description='StorageOS namespace CLI usage',
                parents=[common_parser],
                conflict_handler='resolve',
                help='Operations on Namespace')
    subcommand_parsers = parser.add_subparsers(help='Use One Of Commands')

    # create namespace parser
    create_namespace_parser(subcommand_parsers, common_parser)

    # get namespace parser
    get_namespace_parser(subcommand_parsers, common_parser)

    # show namespace parser
    show_namespace_parser(subcommand_parsers, common_parser)

    # list namespace parser
    list_namespaces_parser(subcommand_parsers, common_parser)

    # delete namespace parser
    delete_namespace_parser(subcommand_parsers, common_parser)


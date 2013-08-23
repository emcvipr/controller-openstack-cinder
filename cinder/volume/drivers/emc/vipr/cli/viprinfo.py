#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import xml.dom.minidom

'''
    Get EMC ViPR configuration parameters
'''
def _get_vipr_info(filename):
    if filename == None:
        return

    configfile = open(filename, 'r')
    if (configfile):
        line = configfile.readline()
        while line :
            if (line[0] == '#'):
                line = configfile.readline()
                continue
            if line.startswith('vipr_hostname'):
                (word,fqdn) = line.rsplit('=',1)
                fqdn = fqdn.rstrip()
                fqdn = fqdn.lstrip()
            if line.startswith('vipr_port'):
                (word,port) = line.rsplit('=',1)
                port = port.rstrip()
                port = port.lstrip()
            if line.startswith('vipr_tenant'):
                (word,tenant) = line.rsplit('=',1)
                tenant = tenant.rstrip()
                tenant = tenant.lstrip()                
            if line.startswith('vipr_project'):
                (word,project) = line.rsplit('=',1)
                project = project.rstrip()
                project = project.lstrip()
            if line.startswith('vipr_varray'):
                (word,varray) = line.rsplit('=',1)
                varray = varray.rstrip()
                varray = varray.lstrip()
                
            if line.startswith('vipr_username'):
                (word,username) = line.rsplit('=',1)
                username = username.rstrip()
                username = username.lstrip()                 
            if line.startswith('vipr_password'):
                (word,password) = line.rsplit('=',1)
                password = password.rstrip()
                password = password.lstrip()                       
                
                             
            line = configfile.readline()   




    viprinfo = {'FQDN': str(fqdn),
                'port': str(port),
                'username': str(user),
                'password': str(password),
                'tenant': str(tenant),
                'project': str(project),
                'varray': str(varray)}

    return viprinfo
    
#viprinfo = _get_vipr_info( '/etc/cinder/cinder_emc_config.xml')
#print(viprinfo) 

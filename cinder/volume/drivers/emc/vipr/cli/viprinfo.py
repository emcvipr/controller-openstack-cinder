

#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import ConfigParser

'''
    Get EMC ViPR configuration parameters
'''
def _get_vipr_info(filename):
    if filename == None:
        return

    config = ConfigParser.SafeConfigParser({'vipr_hostname' : 'localhost',
                                            'vipr_port' : '4443'})
    config.read(filename)

    # username
    username = config.get('DEFAULT', 'vipr_username')
    # password
    password = config.get('DEFAULT', 'vipr_password')
    # hostname
    fqdn = config.get('DEFAULT', 'vipr_hostname')
    # port
    port = config.get('DEFAULT', 'vipr_port')
    # tenant
    tenant = config.get('DEFAULT', 'vipr_tenant')
    # project
    project = config.get('DEFAULT', 'vipr_project')
    # varray
    varray = config.get('DEFAULT', 'vipr_varray')

    viprinfo = {'FQDN': str(fqdn),
                'port': str(port),
                'username': str(username),
                'password': str(password),
                'tenant': str(tenant),
                'project': str(project),
                'varray': str(varray)}

    return viprinfo
    
# viprinfo = _get_vipr_info( '/etc/cinder/cinder.conf')
# print(viprinfo) 

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
    
    vipr_file = open(filename, 'r')
    data = vipr_file.read()
    vipr_file.close()
    dom = xml.dom.minidom.parseString(data)
    fqdns = dom.getElementsByTagName('ViPRFQDN')
    if fqdns is not None and len(fqdns) > 0:
        fqdn = fqdns[0].toxml().replace('<ViPRFQDN>', '')
        fqdn = fqdn.replace('</ViPRFQDN>', '')
        
    ports = dom.getElementsByTagName('ViPRPort')
    if ports is not None and len(ports) > 0:
        port = ports[0].toxml().replace('<ViPRPort>', '')
        port = port.replace('</ViPRPort>', '')

    users = dom.getElementsByTagName('ViPRUserName')
    if users is not None and len(users) > 0:
        user = users[0].toxml().replace('<ViPRUserName>', '')
        user = user.replace('</ViPRUserName>', '')

    passwords = dom.getElementsByTagName('ViPRPassword')
    if passwords is not None and len(passwords) > 0:
        password = passwords[0].toxml().replace('<ViPRPassword>', '')
        password = password.replace('</ViPRPassword>', '')

    tenants = dom.getElementsByTagName('ViPRTenant')
    if tenants is not None and len(tenants) > 0:
        tenant = tenants[0].toxml().replace('<ViPRTenant>', '')
        tenant = tenant.replace('</ViPRTenant>', '')

    projects = dom.getElementsByTagName('ViPRProject')
    if projects is not None and len(projects) > 0:
        project = projects[0].toxml().replace('<ViPRProject>', '')
        project = project.replace('</ViPRProject>', '')

    varrays = dom.getElementsByTagName('ViPRVirtualArray')
    if varrays is not None and len(varrays) > 0:
        varray = varrays[0].toxml().replace('<ViPRVirtualArray>', '')
        varray = varray.replace('</ViPRVirtualArray>', '')
 
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

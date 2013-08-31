

#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import ConfigParser
import os

from common import SOSError
from authentication import Authentication

AUTHENTICATED = False

class ViPRInfo(object):
    '''
        Get EMC ViPR configuration parameters
    '''
    
    def __init__(self, filename):
        self._vipr_info = self._get_vipr_info_from_config(filename)
    
    def get_vipr_info(self):
        return self._vipr_info
    
    def _get_vipr_info_from_config(self, filename):
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

        viprinfo = {'hostname': str(fqdn),
                    'port': str(port),
                    'username': str(username),
                    'password': str(password),
                    'tenant': str(tenant),
                    'project': str(project),
                    'varray': str(varray)}

        return viprinfo
    
    def authenticate_user(self):       
        global AUTHENTICATED
        
        # we should check to see if we are already authenticated before blindly doing it again
        if (AUTHENTICATED == False ):
            obj = Authentication(self._vipr_info['hostname'], int(self._vipr_info['port']))
            cookiedir = '/tmp/vipr_cookie_dir'
            cookiefile = 'cookie-' + self._vipr_info['username'] + '-' + str(os.getpid())
            obj.authenticate_user(self._vipr_info['username'], self._vipr_info['password'], cookiedir, cookiefile)
            AUTHENTICATED = True
            
def retry_wrapper(func):
    def try_and_retry(*args, **kwargs):
        global AUTHENTICATED
        retry = False
        try:
            return func(*args, **kwargs)
        except SOSError as e:
            # if we got an http error and
            # the string contains 401 or if the string contains the word cookie
            if (e.err_code == SOSError.HTTP_ERR and
                (e.err_text.find('401') != -1 or e.err_text.lower().find('cookie') != -1)):
                retry=True
                AUTHENTICATED=False
        except Exception as e:
            raise e
 
        print("retry =" + str(retry))   
        if (retry):        
            return func(*args, **kwargs)
    
    return try_and_retry            
        
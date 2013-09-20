#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

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
        
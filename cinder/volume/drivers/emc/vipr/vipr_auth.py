#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import os
import sys
import requests
import cookielib
import vipr_utils
import getpass
from vipr_utils import SOSError
from requests.exceptions import SSLError
from requests.exceptions import ConnectionError
import socket

class Authentication(object):
    '''
    The class definition for authenticating the specified user 
    '''

    #Commonly used URIs for the 'Authentication' module
    URI_AUTHENTICATION = '/login?using-cookies'
    HEADERS = {'Content-Type': 'application/json', 'ACCEPT': 'application/json', 'X-EMC-REST-CLIENT': 'TRUE'}
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. 
        These are needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def authenticate_user(self, username, password, cookiedir, cookiefile):
        '''
        Makes REST API call to generate the cookiefile for the 
        specified user after validation.
        Returns:
            SUCCESS OR FAILURE
        '''
        cookiejar=cookielib.LWPCookieJar()

        url = 'https://'+str(self.__ipAddr)+self.URI_AUTHENTICATION
        try:
            login_response = requests.get(url, headers=self.HEADERS, verify=False,
                                          auth=(username,password), cookies=cookiejar)
        except (SSLError, socket.error, ConnectionError) as e:
            raise SOSError(SOSError.HTTP_ERR, str(e))
        if (login_response.status_code != requests.codes['ok']):
            error_msg=None
            if(login_response.status_code == 401):
                error_msg = "Access forbidden: Authentication required"
            elif(login_response.status_code == 403):
                error_msg = "Access forbidden: You don't have sufficient \
                    privileges to perform this operation"
            elif(login_response.status_code == 500):
                error_msg="ViPR internal server error"
            elif(login_response.status_code == 404):
                error_msg="Requested resource is currently unavailable"
            elif(login_response.status_code == 405):
                error_msg = "GET method is not supported by resource: " + url
            elif(login_response.status_code == 503):
                error_msg = "Service temporarily unavailable: The server is temporarily \
                 unable to service your request due to maintenance downtime or capacity problems"
            else:
                error_msg=login_response.text
                if isinstance(error_msg, unicode):
                    error_msg = error_msg.encode('utf-8')
            raise SOSError(SOSError.HTTP_ERR, "HTTP code: " +
                str(login_response.status_code) +
                ", Response: " + login_response.reason +
                " [" + error_msg + "]")

        form_cookiefile= None
        parentshellpid = None
        installdir_cookie = None
        if sys.platform.startswith('linux'):
            parentshellpid = os.getppid()
            if(cookiefile is None):
                if (parentshellpid is not None):
                    cookiefile=str(username)+'cookie'+str(parentshellpid)
                else:
                    cookiefile=str(username)+'cookie'
            form_cookiefile = cookiedir+'/'+cookiefile
            if (parentshellpid is not None):
                installdir_cookie = '/cookie/'+str(parentshellpid)
            else:
                installdir_cookie = '/cookie/cookiefile' 
        elif sys.platform.startswith('win'):
            if (cookiefile is None):
                cookiefile=str(username)+'cookie'
            form_cookiefile = cookiedir+'\\'+cookiefile
            installdir_cookie = '\\cookie\\cookiefile'
        else:
            if (cookiefile is None):
                cookiefile=str(username)+'cookie'
            form_cookiefile = cookiedir+'/'+cookiefile
            installdir_cookie = '/cookie/cookiefile'

        if (vipr_utils.create_file(form_cookiefile)):
            cookiejar.save(form_cookiefile, ignore_discard=True, ignore_expires=True);
            sos_cli_install_dir = os.getcwd()
            if (sos_cli_install_dir):
                if (not os.path.isdir(sos_cli_install_dir)):  
                    raise SOSError(SOSError.NOT_FOUND_ERR,
                     sos_cli_install_dir+" : Not a directory")    
                config_file = sos_cli_install_dir+installdir_cookie
                if (vipr_utils.create_file(config_file)):
                    fd = open(config_file,'w+')
                    if (fd):
                        fd_content=os.path.abspath(form_cookiefile)+'\n'
                        fd.write(fd_content)
                        fd.close()
                        ret_val=username+' : Authenticated Successfully\n'+ \
                        form_cookiefile+' : Cookie saved successfully'
                    else:
                        raise SOSError(SOSError.NOT_FOUND_ERR,
                            config_file+" : Failed to save the cookie file path " 
                            + form_cookiefile)
                else:
                    raise SOSError(SOSError.NOT_FOUND_ERR,
                        config_file+" : Failed to create file")
            
            else:
                raise SOSError(SOSError.NOT_FOUND_ERR,
                    "SOS_CLI_INSTALL_DIR is not set. Please check soscli.profile")
        return ret_val

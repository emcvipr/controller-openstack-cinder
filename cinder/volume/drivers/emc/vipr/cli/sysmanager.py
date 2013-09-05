#!/usr/bin/python

# Copyright (c) 2012 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

import common
import urllib
import datetime
import time
import json
import os
import re
import sysmgrcontrolsvc
from common import SOSError
from xml.etree import ElementTree


class Upgrade(object):
    '''
    The class definition for authenticating the specified user 
    '''
    #Commonly used URIs for Upgrade service 
    URI_CLUSTER_STATE = '/upgrade/cluster-state'
    URI_TARGET_VERSION = '/upgrade/target-version'
    URI_IMAGE_INSTALL = '/upgrade/image/install'
    URI_IMAGE_REMOVE = '/upgrade/image/remove'
    URI_INTERNAL_IMAGE = '/upgrade/internal/image?version={0}'
    URI_INTERNAL_WAKEUP = '/upgrade/internal/wakeup'
    URI_IMAGE_UPLOAD='/upgrade/image/upload'
    
    DEFAULT_PORT="9993"
    DEFAULT_SYSMGR_PORT = "4443"
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. 
        These are needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def get_cluster_state(self, force=False):
        
        request = ""
        if(force):
            request += "?force=1"
        else:
            request += "?force=0"
            
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Upgrade.URI_CLUSTER_STATE + request,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
    
    def update_cluster_version(self, target_version, force=False):
        
        request = ""
        if(force):
            request += "?force=1"
        else:
            request += "?force=0"
        
        request += "&version=" + target_version
                
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "PUT", Upgrade.URI_TARGET_VERSION + request,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
    
    def get_target_version(self):
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Upgrade.URI_TARGET_VERSION,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
    
    def install_image(self, target_version, force=False):
        
        request = ""
        if(force):
            request += "?force=1"
        else:
            request += "?force=0"
            
        request += "&version=" + target_version
                   
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Upgrade.URI_IMAGE_INSTALL + request,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
    
    def remove_image(self, target_version, force=False):
        
        request = ""
        if(force):
            request += "?force=1"
        else:
            request += "?force=0"
            
        request += "&version=" + target_version
        
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Upgrade.URI_IMAGE_REMOVE+request,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
  

class Logging(object):
    '''
    The class definition for Logging
    '''

    #Commonly used URIs for Logging service
    URI_LOGS = "/logs"
    URI_LOG_LEVELS = URI_LOGS + "/log-levels"

    DEFAULT_PORT="9993"
    DEFAULT_SYSMGR_PORT = "4443"

    URI_SEND_ALERT = "/callhome/alert/"
    URI_SEND_HEARTBEAT = "/callhome/heartbeat/"
    URI_SEND_REGISTRATION = "/callhome/registration/"
    URI_GET_ESRSCONFIG = "/callhome/esrs-device/"
    URI_CONFIGURE_CONNECTEMC_SMTP = "/config/connectemc/email/"
    URI_CONFIGURE_CONNECTEMC_FTPS = "/config/connectemc/ftps/"
    URI_GET_LICENSE = "/license/"

    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance. 
        These are needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port


    def direct_print_log_unit(self, unit, accept = 'json',filehandle=None):
	
    	if unit is None:
            print_str = ''
	    if(filehandle):
		try:
		    filehandle.write(print_str)
	    	except IOError:
    	            pass
	    else:
		print print_str

            return
      
    	if accept == 'json':
    	    print_str = "{\n" + "\tnode:\t\t" + unit.get('node') + "\n" \
            	        + "\tseverity:\t" + unit.get('severity') + "\n" \
                        + "\tthread:\t\t" + unit.get('thread') + "\n" \
                        + "\tmessage:\t" + unit.get('message').replace('\n', '\n\t\t\t') + "\n" \
                        + "\tservice:\t" + unit.get('service') + "\n" \
                        + "\ttime:\t\t" + unit.get('time') + "\n" \
                        + "\tline:\t\t" + str(unit.get('line')) + "\n" \
                        + "\tclass:\t\t" + unit.get('class') + "\n" \
                        + "}" + "\n"
	    if(filehandle):
	        try:
	            filehandle.write(print_str)
                except IOError:
    	            pass
	    
    	elif accept == 'xml':
            print_str = "<log>" + "\n" \
            + "\t<node>\t\t" + (unit.get('node') if unit.get('node') is not None else "") + "</node>" + "\n" \
            + "\t<severity>\t" + (unit.get('severity') if unit.get('severity') is not None else "") + "</severity>" + "\n" \
            + "\t<thread>\t" + (unit.get('thread') if unit.get('thread') is not None else "") + "</thread>" + "\n" \
            + "\t<message>\t" + (unit.get('message').replace('\n', '\n\t\t\t') if unit.get('message') is not None else "") + "</message>" + "\n" \
            + "\t<service>\t" + (unit.get('service') if unit.get('service') is not None else "") + "</service>" + "\n" \
            + "\t<time>\t\t" + (unit.get('time') if unit.get('time') is not None else "") + "</time>" + "\n" \
            + "\t<line>\t\t" + (str(unit.get('line')) if unit.get('line') is not None else "") + "</line>" + "\n" \
            + "\t<class>\t\t" + (unit.get('class') if unit.get('class') is not None else "") + "</class>" + "\n" \
            + "</log>" + "\n" 
	
	    if(filehandle):
                try:
	            filehandle.write(print_str)
	    	except IOError:
    	            pass

	   #padded with fillers	
        elif accept == 'padded':
            #general logs
            if unit.get('class'):    
                utcTime=datetime.datetime.utcfromtimestamp(unit.get('time_ms')/1000.0).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                print_str = utcTime + ' ' + unit.get('node') + ' ' + unit.get('service') + ' [' + unit.get('thread') + '] ' + \
                unit.get('severity') + ' ' + unit.get('class') + ' (line ' + unit.get('line') + ') ' + unit.get('message') 
            # system logs
            else:
                print_str = unit.get('time') + ',000 ' + unit.get('node') + ' ' + unit.get('service') + ' [-] ' + unit.get('severity') + \
                ' - ' + '(line -) ' + unit.get('message')
            
	    if(filehandle):
                try:
	            filehandle.write(print_str)
	        except IOError:
    	            pass
       #native text
        else: 
            #general logs
            if unit.get('class'):    
                utcTime=datetime.datetime.utcfromtimestamp(unit.get('time_ms')/1000.0).strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
                print_str = utcTime + ' ' + unit.get('node') + ' ' + unit.get('service') + ' [' + unit.get('thread') + '] ' + \
                unit.get('severity') + ' ' + unit.get('class') + ' (line ' + unit.get('line') + ') ' + unit.get('message') 
            # system logs
            else:
                print_str = unit.get('time') + ',000 ' + unit.get('node') + ' ' + unit.get('service') + ' ' + unit.get('severity') + \
                ' ' + unit.get('message')
            
	    if(filehandle):
                try:
	            filehandle.write(print_str)
	        except IOError:
                    pass

    def get_logs(self, log, severity, start, end, node, regex, format, maxcount, filepath):

        params = ''
        if ( log != '' ):
            params += '&' if ('?' in params) else '?'
            params += "log_name=" + log
        if ( severity != '' ):
            params += '&' if ('?' in params) else '?'
            params += "severity=" + severity
        if ( start != '' ):
            params += '&' if ('?' in params) else '?'
            params += "start=" + start
        if ( end != '' ):
            params += '&' if ('?' in params) else '?'
            params += "end=" + end
        if ( node != '' ):
            params += '&' if ('?' in params) else '?'
            params += "node_id=" + node
        if ( regex != '' ):
            params += '&' if ('?' in params) else '?'
            params += "msg_regex=" + urllib.quote_plus(regex.encode("utf8"))
        if (maxcount != ''):
            params += '&' if ('?' in params) else '?'
            params += "maxcount=" + maxcount

	tmppath = filepath+".tmp"
        
        (res, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", self.URI_LOGS + params,
                                              None, None , False , None, tmppath)

	resp = None
        try:
	    if(os.path.getsize(tmppath) > 0):
                with open(tmppath) as infile:
                    resp = json.load(infile)
        except ValueError:
            raise SOSError(SOSError.VALUE_ERR,
                       "Failed to recognize JSON payload")
        except Exception as e:
            raise SOSError(e.errno, e.strerror)
	
	fp = None
	if(filepath):
	    try:
	        fp = open(filepath , 'w')
	    except IOError as e:
                raise SOSError(e.errno, e.strerror)

        if resp:
            if 'error' in resp:
                print resp.get('error')
            elif type(resp) is list:
                layer1_size = len(resp)
                i = 0
                while i < layer1_size:
	            self.direct_print_log_unit(resp[i], format, fp)  
                    i += 1
                    
	    try:
		os.remove(tmppath)	
	    except IOError:
    	        pass

        else:
            print "No log available."

        if(fp):
            fp.close()            

        if(not resp):
            return None
	

    def get_log_level(self, loglst, nodelst):
        request = ""
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Logging.URI_LOG_LEVELS + self.prepare_get_log_lvl_params(loglst, nodelst),
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
	



    def set_log_level(self, severity, logs, nodes):
        request = ""
        
	params = self.prepare_set_log_level_body(severity, logs, nodes)

	if (params):
            body = json.dumps(params)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Logging.URI_LOG_LEVELS ,
                                              body)
        if(not s):
            return None
        o = common.json_decode(s)
        return o


    def send_alert(self, args):

        logparams = self.prepare_params(args)

        uriparams = self.prepare_alert_params(logparams , args)

        params = self.prepare_body(args)

        if (params):
            body = json.dumps(params)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Logging.URI_SEND_ALERT + uriparams,
                                              body)

        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def send_heartbeat(self):

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Logging.URI_SEND_HEARTBEAT,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def send_registration(self):

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Logging.URI_SEND_REGISTRATION,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        return o



    def get_esrsconfig(self):

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Logging.URI_GET_ESRSCONFIG,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o


    def prepare_params(self, args):

        params = self.prepare_get_log_lvl_params(args.log, args.node)

        if ( args.severity != '' ):
            params += '&' if ('?' in params) else '?'
            params += "severity=" + args.severity
        if ( args.start != '' ):
            params += '&' if ('?' in params) else '?'
            params += "start=" + args.start
        if ( args.end != '' ):
            params += '&' if ('?' in params) else '?'
            params += "end=" + args.end
        if ( args.regular != '' ):
            params += '&' if ('?' in params) else '?'
            params += "msg_regex=" + urllib.quote_plus(args.regular.encode("utf8"))
        if ( args.maxcount != ''):
            params += '&' if ('?' in params) else '?'
            params += "maxcount=" + args.maxcount
        return params

    def prepare_get_log_lvl_params(self, loglst, nodelst):
        params = ''
        if(loglst):
            for log in loglst:
                params += '&' if ('?' in params) else '?'
                params += "log_name=" + log
        if(nodelst):
            for node in nodelst:
                params += '&' if ('?' in params) else '?'
                params += "node_id=" + node
        return params

    def prepare_alert_params(self, params, args):
        if ( args.source != ''):
            params += '&' if ('?' in params) else '?'
            params += "source=" + args.source
        if ( args.eventid != ''):
            params += '&' if ('?' in params) else '?'
            params += "event_id=" + args.eventid
        return params

    def prepare_body(self, args):
        params = { 'user_str' : args.message,
              'contact' : args.contact
             }
        return params


    def prepare_set_log_level_body(self , severity, logs, nodes):
        params = {'severity' : int(severity)}
        if ( logs ):
            params['log_name'] = logs
        if ( nodes  ):
            params['node_id'] = nodes

        return params


    def prepare_get_log_lvl_params(self, loglst, nodelst):
        params = ''
	if(loglst):
            for log in loglst:
                params += '&' if ('?' in params) else '?'
                params += "log_name=" + log
	if(nodelst):
            for node in nodelst:
                params += '&' if ('?' in params) else '?'
                params += "node_id=" + node
        return params




    def prepare_license_body(self, args):
        text = ''
        if args.licensefile:
            try:
                with open(args.licensefile, 'r') as content_file:
                    text = content_file.read()
                text = text.rstrip('\n')
            except Exception as e:
                raise SOSError(e.errno, e.strerror)

        else:
            text = args.license_text
        params = {"license_text" : text}
        return params


    def get_license(self):

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Logging.URI_GET_LICENSE,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o

    def add_license(self, args):
	if(args.licensefile is ""):
            raise SOSError(SOSError.CMD_LINE_ERR,
                        "License file path can not be empty string")


        params =  self.prepare_license_body(args)

        if (params):
            body = json.dumps(params)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Logging.URI_GET_LICENSE,
                                              body)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


class Monitoring(object):
    '''
    The class definition for Monitoring
    '''

    URI_MONITOR_STATS = "/monitor/stats"
    URI_MONITOR_HEALTH = "/monitor/health"
    URI_MONITOR_DIAGNOSTICS = "/monitor/diagnostics"
    URI_MONITOR_STORAGE="/monitor/storage"

    DEFAULT_PORT="9993"
    DEFAULT_SYSMGR_PORT = "4443"

    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance.
        These are needed to make http requests for REST API
        '''
        self.__ipAddr = ipAddr
        self.__port = port


    def get_stats(self, nodeid):

	if(nodeid):
	    uri = Monitoring.URI_MONITOR_STATS + "?node_id="+nodeid
	else: 
	    uri = Monitoring.URI_MONITOR_STATS

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", uri,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o

    def get_health(self, nodeid):

	if(nodeid):
	    uri = Monitoring.URI_MONITOR_HEALTH + "?node_id="+nodeid
	else: 
	    uri = Monitoring.URI_MONITOR_HEALTH

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", uri,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o


    def get_diagnostics(self, nodeid, verbose):

	if(verbose):
	    uri = Monitoring.URI_MONITOR_DIAGNOSTICS+"?verbose=True"
	else:
	    uri = Monitoring.URI_MONITOR_DIAGNOSTICS+"?verbose=False"

	if(nodeid):
	    uri = uri +  "&node_id="+nodeid

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", uri,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o


    def get_storage(self):
	uri = Monitoring.URI_MONITOR_STORAGE
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", uri,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o



class Configuration(object):
    '''
    The class definition for Configuration
    '''

    DEFAULT_PORT="9993"
    DEFAULT_SYSMGR_PORT = "4443"

    URI_CONFIGURE_CONNECTEMC_SMTP = "/config/connectemc/email/"
    URI_CONFIGURE_CONNECTEMC_FTPS = "/config/connectemc/ftps/"
    URI_PROPS = "/config/properties/"
    URI_PROPS_METADATA = "/config/properties/metadata"
    URI_RESET_PROPS = "/config/properties/reset/"
    URI_DATANODE_CONFIG = "/config/datanode-config"
    URI_RESET_EXTRANODES_UPGRADELOCK = "/config/extranodes-upgradelock/reset"


    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the SOS instance.
        These are needed to make http requests for REST API
        '''
        self.__ipAddr = ipAddr
        self.__port = port

    def configure_connectemc_ftps(self, args):
        params = self.prepare_connectemc_ftps_body(args)

        if (params):
            body = json.dumps(params)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Configuration.URI_CONFIGURE_CONNECTEMC_FTPS,
                                              body)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def configure_connectemc_smtp(self, args):
        params = self.prepare_connectemc_smtp_body(args)

        if (params):
            body = json.dumps(params)

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Configuration.URI_CONFIGURE_CONNECTEMC_SMTP,
                                              body)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def prepare_connectemc_ftps_body(self, args):
        params = {'bsafe_encryption_ind' : 'no',
                'host_name' : args.ftpserver
                }
        return params


    def prepare_connectemc_smtp_body(self, args):
        params = {'bsafe_encryption_ind' : 'no',
              'email_server' : args.smtpserver,
              'primary_email_address' : args.primaryemail,
              'email_sender' : args.senderemail
             }
        return params


    def get_properties(self):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Configuration.URI_PROPS,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o


    def get_properties_metadata(self):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Configuration.URI_PROPS_METADATA,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)

        return o


    def reset_extranodes_upgrade_lock(self):

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Configuration.URI_RESET_EXTRANODES_UPGRADELOCK ,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def set_properties(self, propertiesfile):

       try:
           f  = open(propertiesfile, 'r')
	   props = []
           for line in f :
               props.append(line)

       except Exception as e:
           raise SOSError(e.errno, e.strerror)

       params = self.prepare_properties_body(props)

       if (params):
           body = json.dumps(params)

       (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "PUT", Configuration.URI_PROPS,
                                              body)
       if(not s):
           return None

       o = common.json_decode(s)
       return o

    def disable_update_check(self):
       params = self.prepare_properties_body(['system_update_repo='])
       body = json.dumps(params)
       (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "PUT", Configuration.URI_PROPS,
                                              body)
       if(not s):
           return None

       o = common.json_decode(s)
       return o

    def reset_properties(self, propertiesfile, force):

        try:
            f  = open(propertiesfile, 'r')
            props = ''
            for line in f :
                props += line + ','

        except Exception as e:
            raise SOSError(e.errno, e.strerror)

        params = self.prepare_reset_properties_body(props.split(','))

        if (params):
            body = json.dumps(params)

	if(force):
	    forcestr = "True"
	else:
	    forcestr = "False"

        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", Configuration.URI_RESET_PROPS + "?removeObsolete=" + forcestr,
                                              body)
        if(not s):
            return None

        o = common.json_decode(s)
        return o


    def prepare_reset_properties_body(self, keys):
        params = dict()
        params['property'] = []
        for k in keys:
            m = re.match("(.+)\n?", k)
            if m:
                key = m.groups()[0]
                params['property'].append(key)
        return params



    def prepare_properties_body(self, props):
        params = dict()
        properties = dict()
        params['properties'] = properties
        properties['entry'] = []
        for prop in props:
            matching = re.match("(.+?)=(.*)\n?", prop)
            if matching:
                key, value = matching.groups()
                entry = dict()
                entry['key'] = key
                entry['value'] = value
                properties['entry'].append(entry)
        return params

    def get_datanode_config(self):
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Configuration.URI_DATANODE_CONFIG,
                                              None)

        if(not s):
	    raise SOSError(SOSError.SOS_FAILURE_ERR, "Error getting datanode config.")
	else:
	    expected_iso_size = '131072'
    	    expected_iso_name = 'config.iso'
	    filename = self.get_download_filename(h['content-disposition'])
	    print "Written to "+filename

	    if (h['content-length'] == expected_iso_size and filename == expected_iso_name):
                self.write_to_file(expected_iso_name, 'wb', s)
            else:
                raise Exception("Received response ISO image's size and name [" + h['content-length'] + ", '" + filename + "'] are not equal to [" + expected_iso_size + ", '" + expected_iso_name + "']")

	return



    def get_download_filename(self, content_disposition):
	content_disposition = content_disposition.replace(" ", "")
    	matching = re.match("(.*)filename=(.+)", content_disposition)
    	if matching:
            filename = matching.group(2)
            return filename
        else:
            return ""




    def write_to_file(self, filename, mode, content):
        try:
            with open(filename, mode) as f:
                f.write(content.encode('utf-8'))
	except IOError as e:
                raise SOSError(e.errno, e.strerror)







def get_logs_parser(subcommand_parsers, common_parser):
    get_logs_parser = subcommand_parsers.add_parser('get-logs',
                                description='ViPR: CLI usage to get the logs',
                                conflict_handler='resolve',
                                help='Get logs')

    get_logs_parser.add_argument('-log', '-lg',
                                metavar='<logname>',
                                dest='log',
                                help='Log Name',
				default='')

    add_log_args(get_logs_parser)
    
    get_logs_parser.set_defaults(func=get_logs)
    
def get_alerts_parser(subcommand_parsers, common_parser):
    get_alerts_parser = subcommand_parsers.add_parser('get-alerts',
                                description='ViPR: CLI usage to get the alerts',
                                conflict_handler='resolve',
                                help='Get alerts')

    add_log_args(get_alerts_parser)
    
    get_alerts_parser.set_defaults(func=get_alerts)


def get_alerts(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    log = "systemevents"
    from common import TableGenerator
    try:
        res = obj.get_logs(log, args.severity,args.start, args.end, args.node, args.regular, args.format, args.maxcount, args.filepath)
    except SOSError as e:
        common.format_err_msg_and_raise("get", log, e.err_text, e.err_code)


def get_logs(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    from common import TableGenerator
    try:
        res = obj.get_logs(args.log, args.severity,args.start, args.end, args.node, args.regular, args.format, args.maxcount, args.filepath)
    except SOSError as e:
	common.format_err_msg_and_raise("get", "logs", e.err_text, e.err_code)


def get_log_level_parser(subcommand_parsers, common_parser):
    get_log_level_parser = subcommand_parsers.add_parser('get-log-level',
                                description='ViPR: CLI usage to get the logging level',
                                conflict_handler='resolve',
                                help='Get log level')

    get_log_level_parser.add_argument('-logs', '-lg',
                                metavar='<logs>',
                                dest='logs',
                                help='Logs Name',
				nargs="+")

    get_log_level_parser.add_argument('-nodes',
                                metavar='<nodes>',
                                dest='nodes',
                                help='Nodes',
                                nargs="+")

    get_log_level_parser.set_defaults(func=get_log_level)


def get_log_level(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    from common import TableGenerator
    try:
        res = obj.get_log_level(args.logs, args.nodes)
	return common.format_json_object(res)
    except SOSError as e:
	common.format_err_msg_and_raise("get", "log level", e.err_text, e.err_code)
        

def set_log_level_parser(subcommand_parsers, common_parser):
    set_log_level_parser = subcommand_parsers.add_parser('set-log-level',
                                description='ViPR: CLI usage to set the logging level',
                                conflict_handler='resolve',
                                help='Set logging level')

    set_log_level_parser.add_argument('-severity', '-sv',
                                metavar='<severity>',
                                dest='severity',
				help='Any value from 0,4,5,7,8,9(FATAL, ERROR, WARN, INFO, DEBUG, TRACE).',
				choices=['0','4', '5', '7','8','9'],
				default='7')

    set_log_level_parser.add_argument('-logs', '-lg',
                                metavar='<logs>',
                                dest='logs',
                                help='Logs Name',
				nargs="+")

    set_log_level_parser.add_argument('-nodes',
                                metavar='<nodes>',
                                dest='nodes',
                                help='Nodes',
                                nargs="+")

    '''set_log_level_parser.add_argument('-type',
                                metavar='<type>',
                                dest='type',
                                help='type')'''

    set_log_level_parser.set_defaults(func=set_log_level)


def set_log_level(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    from common import TableGenerator
    try:
        res = obj.set_log_level(args.severity, args.logs, args.nodes)
    except SOSError as e:
	    common.format_err_msg_and_raise("set", "log level", e.err_text, e.err_code)
    
   
        
def get_cluster_state_parser(subcommand_parsers, common_parser):

    get_cluster_state_parser = subcommand_parsers.add_parser('get-cluster-state',
                                description='ViPR: CLI usage to get the state of the cluster',
                                conflict_handler='resolve',
                                help='Gets cluster state')
    get_cluster_state_parser.add_argument('-f', '-force',
                                          action='store_true',
                                          dest='force',
                                          help='Show all removable versions even though the installed versions are less than MAX_SOFTWARE_VERSIONS')
    get_cluster_state_parser.set_defaults(func=get_cluster_state)
    
def get_cluster_state(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_SYSMGR_PORT)
    from common import TableGenerator
    try:
        res = obj.get_cluster_state(args.force)
        
        state = dict()
        node = dict()
        state["cluster_state"] = res["cluster_state"]
        
        if 'target_state' in res:
            targetState = res['target_state']
            state["current_version"] = targetState['current_version']
            state["available_versions"] = targetState['available_versions']['available_version']
                
        if 'nodes' in res:
            nodestatemap = res['nodes']
            nodestates = nodestatemap['entry']
            try:
                for entry in nodestates:
                    key = entry['key']
                    value = entry['value']
                    node["node_id"] = key
                    node["current_version"] = value['current_version']
                    node["available_versions"] = value['available_versions']['available_version']
                      
            except:
                key = nodestates['key']
                value = nodestates['value']
                node["node_id"] = key
                node["current_version"] = value['current_version']
                node["available_versions"] = value['available_versions']['available_version']

        if 'removable_versions' in res:
            state["removable_versions"]= res['removable_versions']
        
        
        if(len(node)>0):
            print "NODE_INFORMATION"
            node_list=[node]
            TableGenerator(node_list, ["node_id", "current_version", "available_versions"]).printTable()
        
        print "\nSTATE_INFORMATION"
        state_list=[state]
        TableGenerator(state_list, ["cluster_state", "current_version", 
                                    "available_versions", "removable_versions"]).printTable()
                                    
        if("new_versions" in res and res['new_versions'] and "new_version" in res['new_versions']):
            print "\nNEW_VERSIONS"
            for item in res['new_versions']['new_version']:
                print item
        
    except SOSError as e:
        raise e
    

def update_cluster_version_parser(subcommand_parsers, common_parser):

    update_cluster_version_parser = subcommand_parsers.add_parser('update-cluster',
                                description='ViPR: CLI usage to update the cluster',
                                conflict_handler='resolve',
                                help='Updates target version. Version can only be updated incrementally. Ex: storageos-1.0.0.2.xx can only be updated to sotrageos-1.0.0.3.xx and not to storageos-1.0.0.4.xx')
    update_cluster_version_parser.add_argument('-f', '-force',
                                          action='store_true',
                                          dest='force',
                                          help='Version numbers will not be verified. Can be updated from storageos-1.0.0.2.xx to storageos-1.0.0.4.xx')
    
    mandatory_args = update_cluster_version_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-v', '-version',
                                metavar='<target_version>',
                                dest='version',
                                help='The new version number',
                                required=True)
    
    update_cluster_version_parser.set_defaults(func=update_cluster_version)
    
def update_cluster_version(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_SYSMGR_PORT)
    try:
        obj.update_cluster_version(args.version, args.force)
    except SOSError as e:
        raise e
    
def get_target_version_parser(subcommand_parsers, common_parser):

    get_target_version_parser = subcommand_parsers.add_parser('get-target-version',
                                description='ViPR: CLI usage to get the target version',
                                conflict_handler='resolve',
                                help='Gets the target version')    
    get_target_version_parser.set_defaults(func=get_target_version)
    
def get_target_version(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_SYSMGR_PORT)
    from common import TableGenerator
    try:
        res = obj.get_target_version()
        output = [res]
        TableGenerator(output, ["target_version"]).printTable()
    except SOSError as e:
        raise e
    
def install_image_parser(subcommand_parsers, common_parser):

    install_image_parser = subcommand_parsers.add_parser('install-image',
                                description='ViPR: CLI usage to install image',
                                conflict_handler='resolve',
                                help='Install image. Image can be installed only if the number of installed images are less than MAX_SOFTWARE_VERSIONS')
    install_image_parser.add_argument('-f', '-force',
                                      action='store_true',
                                      dest='force',
                                      help='Image will be installed even if the maximum number of versions installed are more than MAX_SOFTWARE_VERSIONS')
    
    mandatory_args = install_image_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-v', '-version',
                                metavar='<target_version>',
                                dest='version',
                                help='Version to be installed',
                                required=True)
    
    install_image_parser.set_defaults(func=install_image)
    
def install_image(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_SYSMGR_PORT)
    try:
        obj.install_image(args.version, args.force)
    except SOSError as e:
        raise e
    
def remove_image_parser(subcommand_parsers, common_parser):

    remove_image_parser = subcommand_parsers.add_parser('remove-image',
                                description='ViPR: CLI usage to install image',
                                conflict_handler='resolve',
                                help='Remove image. Image can be removed only if the number of installed images are greater than MAX_SOFTWARE_VERSIONS')
    remove_image_parser.add_argument('-f', '-force',
                                     action='store_true',
                                     dest='force',
                                     help='Image will be removed even if the maximum number of versions installed are less than MAX_SOFTWARE_VERSIONS')
    
    mandatory_args = remove_image_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-v', '-version',
                                metavar='<target_version>',
                                dest='version',
                                help='Version to be removed',
                                required=True)
    
    remove_image_parser.set_defaults(func=remove_image)
    
def remove_image(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_SYSMGR_PORT)
    try:
        obj.remove_image(args.version, args.force)
    except SOSError as e:
        raise e
        
def add_log_args(parser, sendAlertFlag=False):
    
    parser.add_argument('-severity', '-sv',
                                 metavar='<severity>',
                                 dest='severity',
				 help='Any value from 0,4,5,7,8,9(FATAL, ERROR, WARN, INFO, DEBUG, TRACE).',
				 choices=['0','4', '5', '7','8','9'],
                                 default='7')

    parser.add_argument('-start',
                                metavar='<start>',
                                dest='start',
                                help='start date in yyyy-mm-dd_hh:mm:ss format or in milliseconds',
                                default='')

    parser.add_argument('-end',
                                metavar='end',
                                dest='end',
                                help='end date in yyyy-mm-dd_hh:mm:ss format or in milliseconds',
                                default='')

    parser.add_argument('-node',
                                metavar='<node_id>',
                                dest='node',
                                help='Node',
                                default='')


    parser.add_argument('-regular', '-regex',
                                metavar='<msg_regex>',
                                dest='regular',
                                help='Message Regex',
                                default='')

    parser.add_argument('-format',
                                dest='format',
                                help='Response: xml, json, native, padded',
                                choices=['xml','json','native','padded'],
                                default='native') 

    parser.add_argument('-maxcount',
                                metavar='maxcount',
                                dest='maxcount',
                                help='Maximum number of log messages to retrieve',
                                default='')

    mandatory_args = parser.add_argument_group('mandatory arguments')


    if(sendAlertFlag == False):
        mandatory_args.add_argument('-filepath', '-fp',
                                help='file path',
                                metavar='<filepath>',
                                dest='filepath',
				required=True)
    

def add_license_parser(subcommand_parsers, common_parser):

    add_license_parser = subcommand_parsers.add_parser('add-license',
                                description='ViPR: CLI usage to add license',
                                conflict_handler='resolve',
                                help='Add license')


    mandatory_args = add_license_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-licesnsefile', '-lf',
                                help='license file',
                                metavar='<licensefile>',
                                dest='licensefile',
                                required=True)

    add_license_parser.set_defaults(func=add_license)


def add_license(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        obj.add_license(args)
    except SOSError as e:
        common.format_err_msg_and_raise("add", "license", e.err_text, e.err_code)



def get_license_parser(subcommand_parsers, common_parser):

    get_license_parser = subcommand_parsers.add_parser('get-license',
                                description='ViPR: CLI usage to get license',
                                conflict_handler='resolve',
                                help='Get License.')

    get_license_parser.set_defaults(func=get_license)


def get_license(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        return obj.get_license()
    except SOSError as e:
        common.format_err_msg_and_raise("get", "license", e.err_text, e.err_code)


def get_esrsconfig_parser(subcommand_parsers, common_parser):

    get_esrsconfig_parser = subcommand_parsers.add_parser('get-esrsconfig',
                                description='ViPR: CLI usage to get esrs configuration',
                                conflict_handler='resolve',
                                help='Get Esrs config.')

    get_esrsconfig_parser.set_defaults(func=get_esrsconfig)


def get_esrsconfig(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_esrsconfig())
    except SOSError as e:
        common.format_err_msg_and_raise("get", "ESRS Config", e.err_text, e.err_code)


def send_heartbeat_parser(subcommand_parsers, common_parser):

    send_heartbeat_parser = subcommand_parsers.add_parser('send-heartbeat',
                                description='ViPR: CLI usage to send heartbeat',
                                conflict_handler='resolve',
                                help='Send heart beat.')

    send_heartbeat_parser.set_defaults(func=send_heartbeat)


def send_heartbeat(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        obj.send_heartbeat()
    except SOSError as e:
        common.format_err_msg_and_raise("send", "heartbeat", e.err_text, e.err_code)


def send_registration_parser(subcommand_parsers, common_parser):

    send_registration_parser = subcommand_parsers.add_parser('send-registration',
                                description='ViPR: CLI usage to send registration',
                                conflict_handler='resolve',
                                help='Send registration.')

    send_registration_parser.set_defaults(func=send_registration)


def send_registration(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        obj.send_registration()
    except SOSError as e:
        common.format_err_msg_and_raise("send", "registration", e.err_text, e.err_code)



def send_alert_parser(subcommand_parsers, common_parser):

    send_alert_parser = subcommand_parsers.add_parser('send-alert',
                                description='ViPR: CLI usage to send alert',
                                conflict_handler='resolve',
                                help='Send alert with logs. Event attachments size cannot exceed more than 16 MB compressed size. Please select time window for logs (with help of start, end parameters) during which issue might have occurred.')


    add_log_args(send_alert_parser, True)


    send_alert_parser.add_argument('-src', '-source',
                                     metavar='<target_version>',
                                     dest='source',
                                     help='Send Alert',
                                     default='')

    send_alert_parser.add_argument('-eventid', '-eid',
                                     metavar='<event_id>',
                                     dest='eventid',
                                     help='Event Id',
                                     default='')

    send_alert_parser.add_argument('-msg', '-message',
                                     metavar='<message>',
                                     dest='message',
                                     help='Message',
                                     default='')

    send_alert_parser.add_argument('-contact',
                                     metavar='<contact>',
                                     dest='contact',
                                     help='Contact',
                                     default='')

    send_alert_parser.add_argument('-log', '-lg',
                                metavar='<logname>',
                                dest='log',
                                help='Log Name',
				default='')

    send_alert_parser.set_defaults(func=send_alert)

def send_alert(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        return obj.send_alert(args)
    except SOSError as e:
        common.format_err_msg_and_raise("send", "alert", e.err_text, e.err_code)




def connectemc_ftps_parser(subcommand_parsers, common_parser):

    connectemc_ftps_parser = subcommand_parsers.add_parser('connectemc-ftps',
                                description='ViPR: CLI usage of connect EMC by ftps',
                                conflict_handler='resolve',
                                help='Connect EMC using ftps.')


    mandatory_args = connectemc_ftps_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-ftpserver', '-fsvr',
                                help='ftpserver',
                                metavar='<ftpserver>',
                                dest='ftpserver',
                                required=True)

    connectemc_ftps_parser.set_defaults(func=connectemc_ftps)


def connectemc_ftps(args):
    obj = Configuration(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        obj.configure_connectemc_ftps(args)
    except SOSError as e:
        common.format_err_msg_and_raise("connect", "ftps", e.err_text, e.err_code)


def connectemc_smtp_parser(subcommand_parsers, common_parser):

    connectemc_smtp_parser = subcommand_parsers.add_parser('connectemc-smtp',
                                description='ViPR: CLI usage of connect EMC by smtp',
                                conflict_handler='resolve',
                                help='Connect EMC using smtp.')

    mandatory_args = connectemc_smtp_parser.add_argument_group('mandatory arguments')

    mandatory_args.add_argument('-primaryemail', '-pm',
                                help='primaryemail',
                                metavar='<primaryemail>',
                                dest='primaryemail',
                                required=True)

    mandatory_args.add_argument('-smtpserver', '-sms',
                                help='smtpserver',
                                metavar='<smtpserver>',
                                dest='smtpserver',
                                required=True)

    mandatory_args.add_argument('-senderemail', '-se',
                                help='senderemail',
                                metavar='<senderemail>',
                                dest='senderemail',
                                required=True)

    connectemc_smtp_parser.set_defaults(func=connectemc_smtp)


def connectemc_smtp(args):
    obj = Configuration(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    try:
        obj.configure_connectemc_smtp(args)
    except SOSError as e:
        common.format_err_msg_and_raise("connect", "smtp", e.err_text, e.err_code)



def get_stats_parser(subcommand_parsers, common_parser):

    get_stats_parser = subcommand_parsers.add_parser('get-stats',
                                description='ViPR: CLI usage to get statistics',
                                conflict_handler='resolve',
                                help='Get Statistics.')


    get_stats_parser.add_argument('-node',
                                metavar='<node>',
                                dest='node',
                                help='Node',
				default='')

    get_stats_parser.set_defaults(func=get_stats)


def get_stats(args):
    obj = Monitoring(args.ip, Monitoring.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_stats(args.node))
    except SOSError as e:
        common.format_err_msg_and_raise("get", "statistics", e.err_text, e.err_code)



def get_health_parser(subcommand_parsers, common_parser):

    get_health_parser = subcommand_parsers.add_parser('get-health',
                                description='ViPR: CLI usage to get health',
                                conflict_handler='resolve',
                                help='Get health.')


    get_health_parser.add_argument('-node',
                                metavar='<node>',
                                dest='node',
                                help='Node',
				default='')

    get_health_parser.set_defaults(func=get_health)


def get_health(args):
    obj = Monitoring(args.ip, Monitoring.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_health(args.node))
    except SOSError as e:
        common.format_err_msg_and_raise("get", "health", e.err_text, e.err_code)


def get_diagnostics_parser(subcommand_parsers, common_parser):

    get_diagnostics_parser = subcommand_parsers.add_parser('get-diagnostics',
                                description='ViPR: CLI usage to get diagnostics',
                                conflict_handler='resolve',
                                help='Get Diagnostics.')


    get_diagnostics_parser.add_argument('-node',
                                metavar='<node>',
                                dest='node',
                                help='Node',
				default='')

    get_diagnostics_parser.add_argument('-verbose','-v',
                             action='store_true',
                             help='List diagnostics with details',
                             dest='verbose')

    get_diagnostics_parser.set_defaults(func=get_diagnostics)


def get_diagnostics(args):
    obj = Monitoring(args.ip, Monitoring.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_diagnostics(args.node, args.verbose))
    except SOSError as e:
        common.format_err_msg_and_raise("get", "diagnostics", e.err_text, e.err_code)



def get_storage_parser(subcommand_parsers, common_parser):

    get_storage_parser = subcommand_parsers.add_parser('get-storage',
                                description='ViPR: CLI usage to get storage',
                                conflict_handler='resolve',
                                help='Get Storage.')


    get_storage_parser.set_defaults(func=get_storage)


def get_storage(args):
    obj = Monitoring(args.ip, Monitoring.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_storage())
    except SOSError as e:
        common.format_err_msg_and_raise("get", "storage", e.err_text, e.err_code)



def get_properties_parser(subcommand_parsers, common_parser):

    get_properties_parser = subcommand_parsers.add_parser('get-properties',
                                description='ViPR: CLI usage to get properties',
                                conflict_handler='resolve',
                                help='Get Properties.')


    get_properties_parser.set_defaults(func=get_properties)


def get_properties(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_properties())
    except SOSError as e:
        common.format_err_msg_and_raise("get", "properties", e.err_text, e.err_code)
    

def get_properties_metadata_parser(subcommand_parsers, common_parser):

    get_properties_metadata_parser = subcommand_parsers.add_parser('get-properties-metadata',
                                description='ViPR: CLI usage to get properties metadata',
                                conflict_handler='resolve',
                                help='Get Properties Meta Data.')


    get_properties_metadata_parser.set_defaults(func=get_properties_metadata)


def get_properties_metadata(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.get_properties_metadata())
    except SOSError as e:
        common.format_err_msg_and_raise("get", "properties metadata", e.err_text, e.err_code)



def get_datanode_config_parser(subcommand_parsers, common_parser):

    get_datanode_config_parser = subcommand_parsers.add_parser('get-datanode-config',
                                description='ViPR: CLI usage to get datanode configuration',
                                conflict_handler='resolve',
                                help='Get Datanode Configuration.')

    get_datanode_config_parser.set_defaults(func=get_datanode_config)


def get_datanode_config(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        obj.get_datanode_config()
    except SOSError as e:
        common.format_err_msg_and_raise("get", "datanode config", e.err_text, e.err_code)



def set_properties_parser(subcommand_parsers, common_parser):

    set_properties_parser = subcommand_parsers.add_parser('set-properties',
                                description='ViPR: CLI usage to set properties',
                                conflict_handler='resolve',
                                help='Set Properties.')


    mandatory_args = set_properties_parser.add_argument_group('mandatory arguments')


    mandatory_args.add_argument('-propertyfile', '-pf',
                                help='property file',
                                metavar='<propertyfile>',
                                dest='propertyfile',
                                required=True)

    set_properties_parser.set_defaults(func=set_properties)


def set_properties(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        common.format_json_object(obj.set_properties(args.propertyfile))
    except SOSError as e:
        common.format_err_msg_and_raise("set", "properties", e.err_text, e.err_code)


def reset_properties_parser(subcommand_parsers, common_parser):

    reset_properties_parser = subcommand_parsers.add_parser('reset-properties',
                                description='ViPR: CLI usage to reset properties',
                                conflict_handler='resolve',
                                help='Reset Properties.')


    mandatory_args = reset_properties_parser.add_argument_group('mandatory arguments')


    mandatory_args.add_argument('-propertyfile', '-pf',
                                help='property file',
                                metavar='<propertyfile>',
                                dest='propertyfile',
                                required=True)

    reset_properties_parser.add_argument('-f', '-force',
                                          action='store_true',
                                          dest='force',
                                          help='Force option')

    reset_properties_parser.set_defaults(func=reset_properties)


def reset_properties(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        common.format_json_object(obj.reset_properties(args.propertyfile, args.force))
    except SOSError as e:
        common.format_err_msg_and_raise("reset", "properties", e.err_text, e.err_code)

def disable_update_check_parser(subcommand_parsers, common_parser):

    disable_update_check_parser = subcommand_parsers.add_parser('disable-update-check',
                                     description='StorageOS: CLI usage to disable check for updates',
                                     conflict_handler='resolve',
                                     help='Disable Update Check')

    disable_update_check_parser.set_defaults(func=disable_update_check)


def disable_update_check(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        return common.format_json_object(obj.disable_update_check())
    except SOSError as e:
        common.format_err_msg_and_raise("disable", "update check", e.err_text, e.err_code)



def reset_extranodes_upgrade_lock_parser(subcommand_parsers, common_parser):

    reset_extranodes_upgrade_lock_parser = subcommand_parsers.add_parser('reset-extranodes-upgrade-lock',
                                description='ViPR: CLI usage to reset extranodes upgrade lock',
                                conflict_handler='resolve',
                                help='reset extranodes upgrade lock')


    reset_extranodes_upgrade_lock_parser.set_defaults(func=reset_extranodes_upgrade_lock)


def reset_extranodes_upgrade_lock(args):
    obj = Configuration(args.ip, Configuration.DEFAULT_SYSMGR_PORT)
    try:
        common.format_json_object(obj.reset_extranodes_upgrade_lock())
    except SOSError as e:
        common.format_err_msg_and_raise("reset", "extra nodes lock", e.err_text, e.err_code)


def system_parser(parent_subparser, common_parser):

    parser = parent_subparser.add_parser('system',
                                description='ViPR system CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Operations on system')
    subcommand_parsers = parser.add_subparsers(help='use one of sub-commands')
    
    get_logs_parser(subcommand_parsers, common_parser)
    
    get_alerts_parser(subcommand_parsers, common_parser)

    get_cluster_state_parser(subcommand_parsers, common_parser)
    
    update_cluster_version_parser(subcommand_parsers, common_parser)
    
    get_target_version_parser(subcommand_parsers, common_parser)
    
    install_image_parser(subcommand_parsers, common_parser)

    remove_image_parser(subcommand_parsers, common_parser)
    
    get_log_level_parser(subcommand_parsers, common_parser)

    set_log_level_parser(subcommand_parsers, common_parser)

    add_license_parser(subcommand_parsers, common_parser)

    get_license_parser(subcommand_parsers, common_parser)

    connectemc_ftps_parser(subcommand_parsers, common_parser)

    connectemc_smtp_parser(subcommand_parsers, common_parser)

    send_registration_parser(subcommand_parsers, common_parser)

    send_heartbeat_parser(subcommand_parsers, common_parser)

    send_alert_parser(subcommand_parsers, common_parser)

    get_esrsconfig_parser(subcommand_parsers, common_parser)

    get_storage_parser(subcommand_parsers, common_parser)

    get_health_parser(subcommand_parsers, common_parser)

    get_diagnostics_parser(subcommand_parsers, common_parser)

    get_stats_parser(subcommand_parsers, common_parser)

    get_properties_parser(subcommand_parsers, common_parser)

    get_datanode_config_parser(subcommand_parsers, common_parser)

    reset_properties_parser(subcommand_parsers, common_parser)

    reset_extranodes_upgrade_lock_parser(subcommand_parsers, common_parser)

    set_properties_parser(subcommand_parsers, common_parser)

    get_properties_metadata_parser(subcommand_parsers, common_parser)

    disable_update_check_parser(subcommand_parsers, common_parser)
    
    sysmgrcontrolsvc.restart_service_parser(subcommand_parsers, common_parser)
    sysmgrcontrolsvc.reboot_node_parser(subcommand_parsers, common_parser)
    sysmgrcontrolsvc.cluster_poweroff_parser(subcommand_parsers, common_parser)

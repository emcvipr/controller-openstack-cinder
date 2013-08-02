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
    URI_NODES = '/nodes'
    URI_STATS = '/stats'
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
    
    def get_cluster_nodes(self):
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Upgrade.URI_NODES,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        
        ret_val = common.get_list(o, "node")
        return ret_val
        
    
    def get_system_status(self):
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Upgrade.URI_STATS,
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        ret_val=None
        if(o):
            ret_val = common.get_node_value(o, "svc")
        return ret_val
    
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
	            print print_str
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
                    print print_str
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
                    print print_str
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
                    print print_str
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

        try:
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
	    except IOError:
    	        pass

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


    def get_log_level(self, loglst, nodelst):
        request = ""
            
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "GET", Logging.URI_LOG_LEVELS + self.prepare_get_log_lvl_params(loglst, nodelst),
                                              None)
        if(not s):
            return None
        o = common.json_decode(s)
        return o
	
    def prepare_set_log_level_body(self , severity, logs, nodes):
        params = {'severity' : int(severity)}
        if ( logs ):
            params['log_name'] = logs
        if ( nodes  ):
            params['node_id'] = nodes

        return params


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


def get_logs_parser(subcommand_parsers, common_parser):
    get_logs_parser = subcommand_parsers.add_parser('get-logs',
                                description='StorageOS: CLI usage to get the logs',
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
                                description='StorageOS: CLI usage to get the alerts',
                                conflict_handler='resolve',
                                help='Get alerts')

    add_log_args(get_alerts_parser)
    
    get_alerts_parser.set_defaults(func=get_alerts)


def get_logs(args):
    obj = Logging(args.ip, Logging.DEFAULT_PORT)
    from common import TableGenerator
    try:
        res = obj.get_logs(args.log, args.severity,args.start, args.end, args.node, args.regex, args.format, args.maxcount, args.filepath)
    except SOSError as e:
	common.print_err_msg_and_exit("get", "logs", e.err_text, e.err_code)


def get_log_level_parser(subcommand_parsers, common_parser):
    get_log_level_parser = subcommand_parsers.add_parser('get-log-level',
                                description='StorageOS: CLI usage to get the logging level',
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
	common.print_err_msg_and_exit("get", "log level", e.err_text, e.err_code)
        

def set_log_level_parser(subcommand_parsers, common_parser):
    set_log_level_parser = subcommand_parsers.add_parser('set-log-level',
                                description='StorageOS: CLI usage to set the logging level',
                                conflict_handler='resolve',
                                help='Set logging level')

    set_log_level_parser.add_argument('-severity', '-sv',
                                metavar='<severity>',
                                dest='severity',
                                help='Severity',
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
	    common.print_err_msg_and_exit("set", "log level", e.err_text, e.err_code)
    
def get_alerts(args):
    obj = Logging(args.ip, Logging.DEFAULT_SYSMGR_PORT)
    log = "alerts"
    from common import TableGenerator
    try:
        res = obj.get_logs(log, args.severity,args.start, args.end, args.node, args.regex, args.format, args.maxcount, args.filepath)
    except SOSError as e:
        common.print_err_msg_and_exit("get", "alerts", e.err_text, e.err_code)
   
        
def get_cluster_state_parser(subcommand_parsers, common_parser):

    get_cluster_state_parser = subcommand_parsers.add_parser('get-cluster-state',
                                description='StorageOS: CLI usage to get the state of the cluster',
                                conflict_handler='resolve',
                                help='Gets cluster state')
    get_cluster_state_parser.add_argument('-f', '-force',
                                          action='store_true',
                                          dest='force',
                                          help='Show all removable versions even though the installed versions are less than MAX_SOFTWARE_VERSIONS')
    get_cluster_state_parser.set_defaults(func=get_cluster_state)
    
def get_cluster_state(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
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
                                description='StorageOS: CLI usage to update the cluster',
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
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    try:
        obj.update_cluster_version(args.version, args.force)
    except SOSError as e:
        raise e
    
def get_target_version_parser(subcommand_parsers, common_parser):

    get_target_version_parser = subcommand_parsers.add_parser('get-target-version',
                                description='StorageOS: CLI usage to get the target version',
                                conflict_handler='resolve',
                                help='Gets the target version')    
    get_target_version_parser.set_defaults(func=get_target_version)
    
def get_target_version(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    from common import TableGenerator
    try:
        res = obj.get_target_version()
        output = [res]
        TableGenerator(output, ["target_version"]).printTable()
    except SOSError as e:
        raise e
    
def cluster_list_parser(subcommand_parsers, common_parser):

    cluster_list_parser = subcommand_parsers.add_parser('list',
                                description='StorageOS: CLI usage for listing nodes of the cluster',
                                conflict_handler='resolve',
                                help='Retrieves node IDs and IPs for all nodes in the cluster')
    cluster_list_parser.set_defaults(func=get_cluster_list)
    
def get_cluster_list(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    try:
        res = obj.get_cluster_nodes()
        if(res and len(res) > 0):
            from common import TableGenerator
            TableGenerator(res, ["id","ip","hostname"]).printTable()
    except SOSError as e:
        raise e
    
def system_status_parser(subcommand_parsers, common_parser):

    system_status_parser = subcommand_parsers.add_parser('status',
                                description='StorageOS: CLI usage for getting the status of services',
                                conflict_handler='resolve',
                                help='Retrieves status for each service on this node')
    system_status_parser.set_defaults(func=get_system_status)
    
def get_system_status(args):
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    try:
        res = obj.get_system_status()
        if(res):
            from common import TableGenerator
            TableGenerator(res, ["name","status"]).printTable()
    except SOSError as e:
        raise e
    
def install_image_parser(subcommand_parsers, common_parser):

    install_image_parser = subcommand_parsers.add_parser('install-image',
                                description='StorageOS: CLI usage to install image',
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
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    try:
        obj.install_image(args.version, args.force)
    except SOSError as e:
        raise e
    
def remove_image_parser(subcommand_parsers, common_parser):

    remove_image_parser = subcommand_parsers.add_parser('remove-image',
                                description='StorageOS: CLI usage to install image',
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
    obj = Upgrade(args.ip, Upgrade.DEFAULT_PORT)
    try:
        obj.remove_image(args.version, args.force)
    except SOSError as e:
        raise e
        
def add_log_args(parser):
    
    parser.add_argument('-severity', '-sv',
                                 metavar='<severity>',
                                 dest='severity',
                                 help='Any value from 0 to 9(FATAL, EMERG, ALERT, CRIT, ERROR, WARN, NOTICE, INFO, DEBUG, TRACE).',
				 choices=['0','1','2','3','4', '5','6', '7','8','9'],
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
                                dest='regex',
                                help='Message Regex',
                                default='')

    parser.add_argument('-format',
                                metavar='format',
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


    mandatory_args.add_argument('-filepath', '-fp',
                                help='file path',
                                metavar='<filepath>',
                                dest='filepath',
				required=True)
    
    
def system_parser(parent_subparser, common_parser):

    parser = parent_subparser.add_parser('system',
                                description='StorageOS system CLI usage',
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
    
    cluster_list_parser(subcommand_parsers, common_parser)
    
    system_status_parser(subcommand_parsers, common_parser)

    get_log_level_parser(subcommand_parsers, common_parser)

    set_log_level_parser(subcommand_parsers, common_parser)

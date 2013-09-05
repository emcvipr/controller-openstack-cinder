# Copyright (c) 2013 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.
import common
from common import SOSError

class ControlService(object):
    
    #START - CLASS Indentation
    
    #URIs
    URI_CONTROL_CLUSTER_POWEROFF = '/control/cluster/poweroff'
    URI_CONTROL_NODE_REBOOT = '/control/node/reboot?node_id={0}'
    URI_CONTROL_SERVICE_RESTART = '/control/service/restart?node_id={0}&name={1}'
    
    def __init__(self, ipAddr, port):
        '''
        Constructor: takes IP address and port of the ViPR instance. 
        These are needed to make http requests for REST API   
        '''
        self.__ipAddr = ipAddr
        self.__port = port
        
    
    def rebootNode(self, nodeId):
        #START - rebootNode
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", 
                                              ControlService.URI_CONTROL_NODE_REBOOT.format(nodeId),
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        print("response : "+o)
        return o
        #END - rebootNode
        
    def clusterPoweroff(self):
        #START - clusterPoweroff
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", 
                                              ControlService.URI_CONTROL_CLUSTER_POWEROFF,
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        return o
        #END - clusterPoweroff
        
    def restartService(self, nodeId, serviceName):
        #START - restartService
        (s, h) = common.service_json_request(self.__ipAddr, self.__port,
                                              "POST", 
                                              ControlService.URI_CONTROL_SERVICE_RESTART.format(nodeId, serviceName),
                                              None)
        if(not s):
            return None

        o = common.json_decode(s)
        return o
        #END - restartService   
    
    #END - CLASS Indentation
    
    
#START Parser definitions

'''
Parser for the restart-service command
'''
def restart_service_parser(subcommand_parsers, common_parser):
    # restart-service command parser
    restart_service_parser = subcommand_parsers.add_parser('restart-service',
                                description='ViPR restart-service CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Restarts a service')
    
    mandatory_args = restart_service_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-id', '-nodeid',
                                help='Id of the node from which the service to be restarted',
                                metavar='<nodeid>',
                                dest='nodeid',
                                required=True)
    mandatory_args.add_argument('-svc', '-servicename ',
                               dest='servicename',
                               metavar='<servicename>',
                               help='Name of the service to be restarted',
                               required=True)
    
    restart_service_parser.set_defaults(func=restart_service)


def restart_service(args):
    nodeId = args.nodeid
    serviceName = args.servicename
    
    try:
        response = common.ask_continue("restart service:"+serviceName+" in node: "+nodeId)
        if(str(response)=="y"):
            contrlSvcObj = ControlService(args.ip, args.port)
            contrlSvcObj.restartService(nodeId, serviceName)
    except SOSError as e:
        common.format_err_msg_and_raise("restart-service", serviceName+" in node: "+nodeId, e.err_text, e.err_code)
        

'''
Parser for the reboot node
'''        
def reboot_node_parser(subcommand_parsers, common_parser):
    # create command parser
    reboot_node_parser = subcommand_parsers.add_parser('reboot-node',
                                description='ViPR reboot-node CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Reboots the node')
    
    mandatory_args = reboot_node_parser.add_argument_group('mandatory arguments')
    mandatory_args.add_argument('-id', '-nodeid',
                                help='Id of the node to be rebooted',
                                metavar='<nodeid>',
                                dest='nodeid',
                                required=True)
    
    reboot_node_parser.set_defaults(func=reboot_node)


def reboot_node(args):
    nodeId = args.nodeid
    
    try:
        response = common.ask_continue("reboot node:"+nodeId)
        if(str(response)=="y"):
            contrlSvcObj = ControlService(args.ip, args.port)
            contrlSvcObj.rebootNode(nodeId)
    except SOSError as e:
        common.format_err_msg_and_raise("reboot-node", nodeId, e.err_text, e.err_code)
        

'''
Parser for the cluster poweroff
'''        
def cluster_poweroff_parser(subcommand_parsers, common_parser):
    # create command parser
    cluster_poweroff_parser = subcommand_parsers.add_parser('cluster-poweroff',
                                description='ViPR cluster-poweroff CLI usage',
                                parents=[common_parser],
                                conflict_handler='resolve',
                                help='Power off the cluster')
    
    cluster_poweroff_parser.set_defaults(func=cluster_poweroff)


def cluster_poweroff(args):
        
    try:
        response = common.ask_continue("power-off the cluster")
        if(str(response)=="y"):
            contrlSvcObj = ControlService(args.ip, args.port)
            contrlSvcObj.clusterPoweroff()
    except SOSError as e:
        common.format_err_msg_and_raise("cluster-poweroff", "", e.err_text, e.err_code)
        
    
    
    
    
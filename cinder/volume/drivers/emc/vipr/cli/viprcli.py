#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved
#
# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


# importing python system modules

import argparse
import os
from common import SOSError
import sys

# importing ViPR modules

import authentication
import common
import virtualpool
import tenant
import project
import fileshare
import snapshot
import storagepool
import volume
import metering
import monitoring
import storagesystem
import virtualarray
import storageport
import exportgroup
import networksystem
import network
import sysmanager
#import objectpool
import vcenter
import vcenterdatacenter
import objectuser
import objectvpool
import secretkeyuser
import protectionsystem
import consistencygroup
import host
import hostinitiators
import hostipinterfaces
import cluster
import openstack

import warnings


warnings.filterwarnings(
    'ignore',
    message='BaseException.message has been deprecated as of Python 2.6',
    category=DeprecationWarning,
    module='argparse')

# Fetch ViPR environment variables defined (if any)

vipr_ip = common.getenv('VIPR_HOSTNAME')
vipr_port = common.getenv('VIPR_PORT')
vipr_cli_dir = common.getenv('VIPR_CLI_INSTALL_DIR')
# parser having common arguments across all modules

common_parser = argparse.ArgumentParser()
common_parser.add_argument('-hostname', '-hn',
               metavar='<hostname>',
               default=vipr_ip,
	       dest='ip',
               help='Hostname (fully qualifiled domain name) of ViPR')
common_parser.add_argument('-port', '-po',
               type=int,
               metavar='<port_number>',
               default=vipr_port,
	       dest='port',
               help='port number of ViPR')
common_parser.add_argument('-cf','-cookiefile',
	       help='Full name of cookiefile',
	       metavar='<cookiefile>',
	       dest='cookiefile')

# main commandline parser

main_parser = argparse.ArgumentParser(
            description='ViPR CLI usage',
            parents=[common_parser],
            conflict_handler='resolve')
main_parser.add_argument('-v', '--version','-version',
            action='version',
            version='%(prog)s 1.0',
            help='show version number of program and exit')

def display_version():
    try:
        filename = vipr_cli_dir + "/bin/ver.txt"
        verfile = open(filename,'r')
        line = verfile.readline()
        print line
    except IOError as e:
        raise SOSError(SOSError.NOT_FOUND_ERR, str(e))


# register module specific parsers with the common_parser
module_parsers = main_parser.add_subparsers(help='Use One Of Commands') 

authentication.authenticate_parser(module_parsers, vipr_ip, vipr_port)
authentication.logout_parser(module_parsers, vipr_ip, vipr_port)
authentication.authentication_parser(module_parsers, common_parser)
virtualpool.vpool_parser(module_parsers, common_parser)
tenant.tenant_parser(module_parsers, common_parser)
tenant.namespace_parser(module_parsers, common_parser)
project.project_parser(module_parsers, common_parser)
fileshare.fileshare_parser(module_parsers, common_parser)
snapshot.snapshot_parser(module_parsers, common_parser)
volume.volume_parser(module_parsers, common_parser)
consistencygroup.consistencygroup_parser(module_parsers, common_parser)
storagepool.storagepool_parser(module_parsers, common_parser)
metering.meter_parser(module_parsers, common_parser)
monitoring.monitor_parser(module_parsers, common_parser)
storagesystem.storagesystem_parser(module_parsers, common_parser)
host.host_parser(module_parsers, common_parser)
hostinitiators.initiator_parser(module_parsers, common_parser)
hostipinterfaces.ipinterface_parser(module_parsers, common_parser)
cluster.cluster_parser(module_parsers, common_parser)
virtualarray.varray_parser(module_parsers, common_parser)
storageport.storageport_parser(module_parsers, common_parser)
exportgroup.exportgroup_parser(module_parsers, common_parser)
sysmanager.system_parser(module_parsers, common_parser)
protectionsystem.protectionsystem_parser(module_parsers, common_parser)
#objectpool.objectpool_parser(module_parsers, common_parser)
vcenter.vcenter_parser(module_parsers, common_parser)
vcenterdatacenter.vcenterdatacenter_parser(module_parsers, common_parser)
objectuser.objectuser_parser(module_parsers, common_parser)
objectvpool.objectvpool_parser(module_parsers, common_parser)
secretkeyuser.secretkeyuser_parser(module_parsers, common_parser)
networksystem.networksystem_parser(module_parsers, common_parser)
network.network_parser(module_parsers, common_parser)
host.host_parser(module_parsers, common_parser)
cluster.cluster_parser(module_parsers, common_parser)
openstack.openstack_parser(module_parsers, common_parser)

# Parse Command line Arguments and execute the corresponding routines
try:
    if( len(sys.argv) > 1 and (sys.argv[1]=='-v' or sys.argv[1]=='-version' or sys.argv[1]=='--version') ):
        display_version()
    else:
        args = main_parser.parse_args()
        common.COOKIE=args.cookiefile
        result = args.func(args)
        if(result):
            if isinstance(result, list):
                for record in result:
                    print record
            else:
                print result
    
except SOSError as e:
    sys.stderr.write(e.err_text+"\n")
    sys.exit(e.err_code)
except (EOFError, KeyboardInterrupt):
    sys.stderr.write("\nUser terminated request\n")
    sys.exit(SOSError.CMD_LINE_ERR)
         
         

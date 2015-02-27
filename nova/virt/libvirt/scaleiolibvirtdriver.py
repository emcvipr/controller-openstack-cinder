
# Copyright (c) 2013 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


import glob
import hashlib
import os
import time
import urllib2
import urlparse
import requests
import json
import re
import sys
import urllib

from oslo.config import cfg

from nova import exception
from nova.openstack.common.gettextutils import _
from nova.openstack.common import log as logging
from nova.openstack.common import loopingcall
from nova.openstack.common import processutils
from nova import paths
from nova.storage import linuxscsi
from nova import utils
from nova.virt.libvirt import config as vconfig
from nova.virt.libvirt import utils as virtutils
from nova.virt.libvirt.volume import LibvirtBaseVolumeDriver

LOG = logging.getLogger(__name__)

volume_opts = [
    cfg.IntOpt('num_iscsi_scan_tries',
               default=3,
               help='number of times to rescan iSCSI target to find volume'),
    cfg.IntOpt('num_iser_scan_tries',
               default=3,
               help='number of times to rescan iSER target to find volume'),
    cfg.StrOpt('rbd_user',
               help='the RADOS client name for accessing rbd volumes'),
    cfg.StrOpt('rbd_secret_uuid',
               help='the libvirt uuid of the secret for the rbd_user'
                    'volumes'),
    cfg.StrOpt('nfs_mount_point_base',
               default=paths.state_path_def('mnt'),
               help='Dir where the nfs volume is mounted on the compute node'),
    cfg.StrOpt('nfs_mount_options',
               help='Mount options passed to the nfs client. See section '
                    'of the nfs man page for details'),
    cfg.IntOpt('num_aoe_discover_tries',
               default=3,
               help='number of times to rediscover AoE target to find volume'),
    cfg.StrOpt('glusterfs_mount_point_base',
                default=paths.state_path_def('mnt'),
                help='Dir where the glusterfs volume is mounted on the '
                      'compute node'),
    cfg.BoolOpt('libvirt_iscsi_use_multipath',
                default=False,
                help='use multipath connection of the iSCSI volume'),
    cfg.BoolOpt('libvirt_iser_use_multipath',
                default=False,
                help='use multipath connection of the iSER volume'),
    cfg.StrOpt('scality_sofs_config',
               help='Path or URL to Scality SOFS configuration file'),
    cfg.StrOpt('scality_sofs_mount_point',
               default='$state_path/scality',
               help='Base dir where Scality SOFS shall be mounted'),
    cfg.ListOpt('qemu_allowed_storage_drivers',
               default=[],
               help='Protocols listed here will be accessed directly '
                    'from QEMU. Currently supported protocols: [gluster]')
    ]

CONF = cfg.CONF
CONF.register_opts(volume_opts)

OK_STATUS_CODE=200
VOLUME_NOT_MAPPED_ERROR=84
VOLUME_ALREADY_MAPPED_ERROR=81

class LibvirtScaleIOVolumeDriver(LibvirtBaseVolumeDriver):
    """Class implements libvirt part of volume driver for ScaleIO cinder driver."""
    local_sdc_id = None
    mdm_id = None
    pattern3 = None

    def __init__(self, connection):
        """Create back-end to nfs."""
        LOG.warning("ScaleIO libvirt volume driver INIT")
        super(LibvirtScaleIOVolumeDriver,
              self).__init__(connection, is_block_dev=False)

    def find_volume_path(self, volume_id):
        
        LOG.info("looking for volume %s" % volume_id)
        #look for the volume in /dev/disk/by-id directory
        disk_filename = ""
        tries = 0
        while not disk_filename:
            if (tries > 15):
                raise exception.NovaException("scaleIO volume {0} not found at expected path ".format(volume_id))
            by_id_path = "/dev/disk/by-id"
            if not os.path.isdir(by_id_path):
                LOG.warn("scaleIO volume {0} not yet found (no directory /dev/disk/by-id yet). Try number: {1} ".format(volume_id, tries))
                tries = tries + 1
                time.sleep(1)
                continue
            filenames = os.listdir(by_id_path)
            LOG.warning("Files found in {0} path: {1} ".format(by_id_path, filenames))
            for filename in filenames:
                if (filename.startswith("emc-vol") and filename.endswith(volume_id)):
                    disk_filename = filename
            if not disk_filename:
                LOG.warn("scaleIO volume {0} not yet found. Try number: {1} ".format(volume_id, tries))
                tries = tries + 1
                time.sleep(1)

        if (tries != 0):
            LOG.warning("Found scaleIO device {0} after {1} retries ".format(disk_filename, tries))
        full_disk_name = by_id_path + "/" + disk_filename
        LOG.warning("Full disk name is " + full_disk_name)
        return full_disk_name
#         path = os.path.realpath(full_disk_name)
#         LOG.warning("Path is " + path)
#         return path
    
    def _get_client_id(self, server_ip, server_port, server_username, server_password, server_token, sdc_ip):
        request = "https://" + server_ip + ":" + server_port + "/api/types/Client/instances/getByIp::" + sdc_ip + "/"
        LOG.info("ScaleIO get client id by ip request: %s" % request)
        r = requests.get(request, auth=(server_username, server_token), verify=False)
        r = self._check_response(r, request, server_ip, server_port, server_username, server_password, server_token)
        
        sdc_id = r.json()
        if (sdc_id == '' or sdc_id is None):
            msg = ("Client with ip %s wasn't found " % (sdc_ip))
            LOG.error(msg)
            raise exception.NovaException(data=msg) 
        if (r.status_code != 200 and "errorCode" in sdc_id):
            msg = ("Error getting sdc id from ip %s: %s " % (sdc_ip, sdc_id['message']))
            LOG.error(msg)
            raise exception.NovaException(data=msg)  
        LOG.info("ScaleIO sdc id is %s" % sdc_id)
        return sdc_id
    
    def _get_volume_id(self, server_ip, server_port, server_username, server_password, server_token, volname):
        volname_encoded = urllib.quote(volname, '')
        volname_double_encoded = urllib.quote(volname_encoded, '') 
#         volname = volname.replace('/', '%252F')
        LOG.info("volume name after double encoding is %s " % volname_double_encoded)
        request = "https://" + server_ip + ":" + server_port + "/api/types/Volume/instances/getByName::" + volname_double_encoded
        LOG.info("ScaleIO get volume id by name request: %s" % request)
        r = requests.get(request, auth=(server_username, server_token), verify=False)
        r = self._check_response(r, request, server_ip, server_port, server_username, server_password, server_token)
                
        volume_id = r.json()
        if (volume_id == '' or volume_id is None):
            msg = ("Volume with name %s wasn't found " % (volname))
            LOG.error(msg)
            raise exception.NovaException(data=msg) 
        if (r.status_code != OK_STATUS_CODE and "errorCode" in volume_id):
            msg = ("Error getting volume id from name %s: %s " % (volname, volume_id['message']))
            LOG.error(msg)
            raise exception.NovaException(data=msg)  
        LOG.info("ScaleIO volume id is %s" % volume_id)
        return volume_id
    
    def _check_response(self, response, request, server_ip, server_port, server_username, server_password, server_token):
        if (response.status_code == 401 or response.status_code == 403):
            LOG.info("Token is invalid, going to re-login and get a new one")           
            login_request = "https://" + server_ip + ":" + server_port + "/api/login"    
            r = requests.get(login_request, auth=(server_username, server_password), verify=False) 
            token = r.json()
            #repeat request with valid token
            LOG.debug("going to perform request again {0} with valid token".format(request))
            res = requests.get(request, auth=(server_username, token), verify=False)
            return res
        return response
        

    def connect_volume(self, connection_info, disk_info):
        """Connect the volume. Returns xml for libvirt."""
        conf = super(LibvirtScaleIOVolumeDriver,
                     self).connect_volume(connection_info,
                                          disk_info)
        LOG.info("scaleIO connect volume in scaleio libvirt volume driver")
        data = connection_info
        LOG.info("scaleIO connect to stuff "+str(data))
        data = connection_info['data']
        LOG.info("scaleIO connect to joined "+str(data))
        LOG.info("scaleIO Dsk info "+str(disk_info))
        volname = connection_info['data']['scaleIO_volname']
        #sdc ip here is wrong, probably not retrieved properly in cinder driver. Currently not used.
        sdc_ip = connection_info['data']['hostIP']
        server_ip = connection_info['data']['serverIP']
        server_port = connection_info['data']['serverPort']
        server_username = connection_info['data']['serverUsername']
        server_password = connection_info['data']['serverPassword']
        server_token = connection_info['data']['serverToken']
        iops_limit = connection_info['data']['iopsLimit']
        bandwidth_limit = connection_info['data']['bandwidthLimit']
        LOG.debug("scaleIO Volume name: {0}, SDC IP: {1}, REST Server IP: {2}, REST Server username: {3}, REST Server password: {4}, iops limit: {5}, bandwidth limit: {6}".format(volname, sdc_ip, server_ip, server_username, server_password, iops_limit, bandwidth_limit))
        
        
        cmd = ['drv_cfg']
        cmd += ["--query_guid"]

        LOG.info("ScaleIO sdc query guid command: "+str(cmd))
        
        try:
            (out, err) = utils.execute(*cmd, run_as_root=True)
            LOG.info("map volume %s: stdout=%s stderr=%s" % (cmd, out, err))
        except processutils.ProcessExecutionError as e:
            msg = ("Error querying sdc guid: %s" % (e.stderr))
            LOG.error(msg)
            raise exception.NovaException(data=msg) 
        
        guid = out
        msg = ("Current sdc guid: %s" % (guid))
        LOG.info(msg)        

#         sdc_id = self._get_client_id(server_ip, server_port, server_username, server_password, server_token, sdc_ip)

#         params = {'sdcId' : sdc_id}

        params = {'guid' : guid, 'allowMultipleMappings' : 'TRUE'}
        
        volume_id = self._get_volume_id(server_ip, server_port, server_username, server_password, server_token, volname)
        headers = {'content-type': 'application/json'}
        request = "https://" + server_ip + ":" + server_port + "/api/instances/Volume::" + str(volume_id) + "/action/addMappedSdc"
        LOG.info("map volume request: %s" % request)
        r = requests.post(request, data=json.dumps(params), headers=headers, auth=(server_username, server_token), verify=False)
        r = self._check_response(r, request, server_ip, server_port, server_username, server_password, server_token)
#         LOG.info("map volume response: %s" % r.text)
        
        if (r.status_code != OK_STATUS_CODE):
            response = r.json()
            error_code = response['errorCode']
            if (error_code == VOLUME_ALREADY_MAPPED_ERROR):
                msg = ("Ignoring error mapping volume %s: volume already mapped" % (volname))
                LOG.warning(msg)  
            else: 
                msg = ("Error mapping volume %s: %s" % (volname, response['message']))
                LOG.error(msg)
                raise exception.NovaException(data=msg)     
        
#       convert id to hex  
#         val = int(volume_id)
#         id_in_hex = hex((val + (1 << 64)) % (1 << 64))
#         formated_id = id_in_hex.rstrip("L").lstrip("0x") or "0"
        formated_id = volume_id
            
        conf.source_path = self.find_volume_path(formated_id)
        conf.source_type = 'block'
        
#       set QoS settings after map was performed  
        if (iops_limit != None and bandwidth_limit != None):
            params = {'sdcId' : sdc_id, 'iopsLimit': iops_limit, 'bandwidthLimitInKbps': bandwidth_limit}
            request = "https://" + server_ip + ":" + server_port + "/api/instances/Volume::" + str(volume_id) + "/action/setMappedSdcLimits"
            LOG.info("set client limit request: %s" % request)
            r = requests.post(request, data=json.dumps(params), headers=headers, auth=(server_username, server_token), verify=False)
            r = self._check_response(r, request, server_ip, server_port, server_username, server_password, server_token)
            if (r.status_code != OK_STATUS_CODE):
                response = r.json()
                LOG.info("set client limit response: %s" % response)
                msg = ("Error setting client limits for volume %s: %s" % (volname, response['message']))
                LOG.error(msg)            
        
        return conf

    def disconnect_volume(self, connection_info, disk_info):
        conf = super(LibvirtScaleIOVolumeDriver,
                     self).disconnect_volume(connection_info,
                                          disk_info)
        '''LOG.info("scaleIO disconnect volume in scaleio libvirt volume driver")
        volname = connection_info['data']['scaleIO_volname']
        sdc_ip = connection_info['data']['hostIP']
        server_ip = connection_info['data']['serverIP']
        server_port = connection_info['data']['serverPort']
        server_username = connection_info['data']['serverUsername']
        server_password = connection_info['data']['serverPassword']
        server_token = connection_info['data']['serverToken']
        LOG.debug("scaleIO Volume name: {0}, SDC IP: {1}, REST Server IP: {2}".format(volname, sdc_ip, server_ip))

        cmd = ['drv_cfg']
        cmd += ["--query_guid"]

        LOG.info("ScaleIO sdc query guid command: "+str(cmd))
        
        try:
            (out, err) = utils.execute(*cmd, run_as_root=True)
            LOG.info("map volume %s: stdout=%s stderr=%s" % (cmd, out, err))
        except processutils.ProcessExecutionError as e:
            msg = ("Error querying sdc guid: %s" % (e.stderr))
            LOG.error(msg)
            raise exception.NovaException(data=msg) 
        
        guid = out
        msg = ("Current sdc guid: %s" % (guid))
        LOG.info(msg)        
        
        params = {'guid' : guid}
        
        headers = {'content-type': 'application/json'}

        volume_id = self._get_volume_id(server_ip, server_port, server_username, server_password, server_token, volname)
        request = "https://" + server_ip + ":" + server_port + "/api/instances/Volume::" + str(volume_id) + "/action/removeMappedSdc"
        LOG.info("unmap volume request: %s" % request)
        r = requests.post(request, data=json.dumps(params), headers=headers, auth=(server_username, server_token), verify=False)
        r = self._check_response(r, request, server_ip, server_port, server_username, server_password, server_token)
        
        if (r.status_code != OK_STATUS_CODE):
            response = r.json()
            error_code = response['errorCode']
            if (error_code == VOLUME_NOT_MAPPED_ERROR):
                msg = ("Ignoring error unmapping volume %s: volume not mapped" % (volname))
                LOG.warning(msg)  
            else: 
                msg = ("Error unmapping volume %s: %s" % (volname, response['message']))
                LOG.error(msg)
                raise exception.NovaException(data=msg) '''


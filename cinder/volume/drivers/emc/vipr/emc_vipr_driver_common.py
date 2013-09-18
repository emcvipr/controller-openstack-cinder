#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


import os
import platform
import random
import string
from oslo.config import cfg
from threading import Timer
import time 
from xml.dom.minidom import parseString

from cinder import context
from cinder import exception
from cinder.openstack.common import log as logging
from cinder.volume import volume_types

from cli.authentication import Authentication
import cli.common as vipr_utils
from cli.common import SOSError
from cli.exportgroup import ExportGroup
from cli.virtualarray import VirtualArray 
from cli.project import Project
from cli.snapshot import Snapshot
from cli.volume import Volume
from cli.host import Host
from cli.hostinitiators import HostInitiator
from cli.virtualarray import VirtualArray

# for the delegator
import sys,os,traceback

LOG = logging.getLogger(__name__)

volume_opts = [
    cfg.StrOpt('vipr_hostname',
               default=None,
               help='Hostname for the EMC ViPR Instance'),
    cfg.IntOpt('vipr_port',
               default=4443,
               help='Port for the EMC ViPR Instance'),
    cfg.StrOpt('vipr_username',
               default=None,
               help='Username for accessing the EMC ViPR Instance'),
    cfg.StrOpt('vipr_password',
               default=None,
               help='Password for accessing the EMC ViPR Instance'),
    cfg.StrOpt('vipr_tenant',
               default=None,
               help='Tenant to utilize within the EMC ViPR Instance'),   
    cfg.StrOpt('vipr_project',
               default=None,
               help='Project to utilize within the EMC ViPR Instance'),                 
    cfg.StrOpt('vipr_varray',
               default=None,
               help='Virtual Array to utilize within the EMC ViPR Instance')                  
    ]

CONF=cfg.CONF
CONF.register_opts(volume_opts)

URI_VPOOL_VARRAY_CAPACITY = '/block/vpools/{0}/varrays/{1}/capacity'


def retry_wrapper(func):
    def try_and_retry(*args, **kwargs):
        global AUTHENTICATED
        retry = False
        
        try:
            return func(*args, **kwargs)
        except SOSError as e:
            # if we got an http error and
            # the string contains 401 or if the string contains the word cookie
            if (e.err_code == SOSError.HTTP_ERR and (e.err_text.find('401') != -1 or e.err_text.lower().find('cookie') != -1)):
                retry=True
                AUTHENTICATED=False
            else:               
                exception_message = "\nViPR Exception: %s\nStack Trace:\n%s" % (e.err_text,traceback.format_exc())
                raise exception.VolumeBackendAPIException(data=exception_message)               
        except Exception as o:
            exception_message = "\nGeneral Exception: %s\nStack Trace:\n%s" % (sys.exc_info()[0],traceback.format_exc())
            raise exception.VolumeBackendAPIException(data=exception_message)   
    
        if (retry):        
            return func(*args, **kwargs)
    
    return try_and_retry


AUTHENTICATED = False

class EMCViPRDriverCommon():
    
    OPENSTACK_TAG = 'OpenStack'

    def __init__(self, prtcl, configuration=None):
        self.protocol = prtcl
        self.configuration = configuration
        self.configuration.append_config_values(volume_opts)
        vipr_utils.COOKIE = None
        
        # instantiate a few vipr cli objects for later use
        self.volume_obj = Volume(self.configuration.vipr_hostname, self.configuration.vipr_port)
        self.exportgroup_obj = ExportGroup(self.configuration.vipr_hostname, self.configuration.vipr_port)
        self.host_obj = Host(self.configuration.vipr_hostname, self.configuration.vipr_port)
        self.hostinitiator_obj = HostInitiator(self.configuration.vipr_hostname, self.configuration.vipr_port)
        self.varray_obj = VirtualArray(self.configuration.vipr_hostname, self.configuration.vipr_port)
        
        self.stats = {'driver_version': '1.0',
                 'free_capacity_gb': 'unknown',
                 'reserved_percentage': '0',
                 'storage_protocol': prtcl,
                 'total_capacity_gb': 'unknown',
                 'vendor_name': 'EMC'}

    def check_for_setup_error(self):
        # validate all of the vipr_* configuration values
        if (self.configuration.vipr_hostname is None):
            message="vipr_hostname is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)
        
        if (self.configuration.vipr_port is None):
            message="vipr_port is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)
                  
        if (self.configuration.vipr_username is None):
            message="vipr_username is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message) 
           
        if (self.configuration.vipr_password is None):
            message="vipr_password is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)  
           
        if (self.configuration.vipr_tenant is None):
            message="vipr_tenant is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)  
            
        if (self.configuration.vipr_project is None):
            message="vipr_project is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)  
            
        if (self.configuration.vipr_varray is None):
            message="vipr_varray is not set in cinder configuration"
            raise exception.VolumeBackendAPIException(data=message)
                                
        # check the rpc_response_timeout value, should be greater than 300 
        if (self.configuration.rpc_response_timeout is None or self.configuration.rpc_response_timeout<300):
            LOG.warn(_("rpc_response_time should be set to at least 300 seconds"))

    def authenticate_user(self):       
        global AUTHENTICATED
        
        # we should check to see if we are already authenticated before blindly doing it again
        if (AUTHENTICATED == False ):
            obj = Authentication(self.configuration.vipr_hostname, self.configuration.vipr_port)
            cookiedir = os.getcwd()
            obj.authenticate_user(self.configuration.vipr_username, self.configuration.vipr_password, cookiedir, None)
            AUTHENTICATED = True

    @retry_wrapper
    def create_volume(self, vol):
    
        self.authenticate_user()
        
        name = self._get_volume_name(vol)
            
        size = int(vol['size']) * 1073741824

        vpool = self._get_vpool(vol)
        self.vpool = vpool['ViPR:VPOOL']

        try:
            res = self.volume_obj.create(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project,
                             name,
                             size,
                             self.configuration.vipr_varray,
                             self.vpool,
                             protocol=None, # no longer specified in volume creation
                             sync=True,
                             number_of_volumes=1,
                             thin_provisioned=None, # no longer specified in volume creation
                             protection=None,
                             protection_varrays=None,
                             consistent_volume_label=None,
                             consistencygroup=None
                             )
        except SOSError as e:
            if(e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Volume " +
                               name + ": Tag failed\n" + e.err_text)
            else:
                raise e
                            
    @retry_wrapper
    def setTags(self, vol):
    
        self.authenticate_user()
        name = self._get_volume_name(vol)        
                
        # first, get the current tags that start with the OPENSTACK_TAG eyecatcher
        removeTags=[]
        currentTags = self.volume_obj.getTags(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project + "/" + name)
        for cTag in currentTags:
            if (cTag.startswith(self.OPENSTACK_TAG)):
                removeTags.append(cTag)

        try:
            if (len(removeTags)>0):
                self.volume_obj.modifyTags(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project + "/" + name, None, removeTags)
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                LOG.debug("SOSError adding the tag: " + e.err_text)
        
        
        # now add the tags for the volume
        addTags=[]
        # put all the openstack volume properties into the ViPR volume
        for prop, value in vars(vol).iteritems():
            try:
                # don't put the status in, it's always the status before the current transaction
                if (not prop.startswith("status")):
                    addTags.append(self.OPENSTACK_TAG+":"+prop+":"+value)
            except Exception:
                pass
        
        try:
            self.volume_obj.modifyTags(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project + "/" + name, addTags, None)
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                LOG.debug("SOSError adding the tag: " + e.err_text)
                
        return self.volume_obj.getTags(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project + "/" + name)    

    @retry_wrapper
    def create_cloned_volume(self, vol, src_vref):
        """Creates a clone of the specified volume."""        
        self.authenticate_user()
        name = self._get_volume_name(vol)
        srcname = self._get_volume_name(src_vref)
        
        try:
            res = self.volume_obj.clone(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project,
                             name,
                             number_of_volumes=1,
                             srcname=srcname,
                             sync=True
                             )
        except SOSError as e:
            if(e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Volume " +
                               name + ": clone failed\n" + e.err_text)
            else:
                raise e
                
    @retry_wrapper
    def delete_volume(self, vol):
        self.authenticate_user()
        name = self._get_volume_name(vol)
        try:
            self.volume_obj.delete(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project + "/" + name, volume_name_list=None, sync=True)
        except SOSError as e:
            if e.err_code == SOSError.NOT_FOUND_ERR:
                LOG.info("Volume " + name + " no longer exists; volume deletion is considered success.")
            elif e.err_code == SOSError.SOS_FAILURE_ERR:
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Volume " +
                               name + ": Delete failed\n" + e.err_text)
            else:
                raise e

    @retry_wrapper
    def list_volume(self):
        try:
            uris = self.volume_obj.list_volumes(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project)
            if(len(uris) > 0):
                output = []
                for uri in uris:
                    output.append(self.volume_obj.show_by_uri(uri))
                    
                return vipr_utils.format_json_object(output)
            else:
                return
        except SOSError as e:
            raise e

    @retry_wrapper
    def create_snapshot(self, snapshot):
        self.authenticate_user()
        obj = Snapshot(self.configuration.vipr_hostname, self.configuration.vipr_port)
        try:    
            snapshotname = snapshot['name']
            vol = snapshot['volume']
            volumename = self._get_volume_name(vol)
            projectname = self.configuration.vipr_project
            tenantname = self.configuration.vipr_tenant
            storageresType = 'block'
            storageresTypename = 'volumes'
            resourceUri = obj.storageResource_query(storageresType, fileshareName=None, volumeName=volumename, cgName=None, project=projectname, tenant=tenantname)
            inactive = False
            rptype = None
            sync = True
            obj.snapshot_create(storageresType, storageresTypename, resourceUri, snapshotname, inactive, rptype, sync)
            return

        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot: " + snapshotname + ", Create Failed\n" + e.err_text)
            else:
                raise e

    @retry_wrapper
    def delete_snapshot(self, snapshot):
        self.authenticate_user()
        obj = Snapshot(self.configuration.vipr_hostname, self.configuration.vipr_port)
        snapshotname = snapshot['name']
        try:
            vol = snapshot['volume']
            volumename = self._get_volume_name(vol)
            projectname = self.configuration.vipr_project
            tenantname = self.configuration.vipr_tenant
            storageresType = 'block'
            storageresTypename = 'volumes'
            resourceUri = obj.storageResource_query(storageresType, fileshareName=None, volumeName=volumename, cgName=None, project=projectname, tenant=tenantname)
            if resourceUri is None:
                LOG.info("Snapshot " + snapshotname + " is not found; snapshot deletion is considered successful.")
            else:
                obj.snapshot_delete(storageresType, storageresTypename, resourceUri, snapshotname, sync=True)
            return
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + snapshotname + ": Delete Failed\n")
            else:
                raise e
            
    @retry_wrapper
    def initialize_connection(self, volume, 
            protocol, initiatorNode, initiatorPort, hostname):
        try:
            self.authenticate_user()
            volumename = self._get_volume_name(volume)           
            foundgroupname = self._find_exportgroup(initiatorPort)
            if (foundgroupname is None):
                # check if this initiator is contained in any ViPR Host object
                foundhostname= self._find_host(initiatorPort)
                if (foundhostname is None):
                    if (not self._host_exists(hostname)):
                        # create a host so it can be added to the export group
                        self.host_obj.create(hostname, platform.system(), hostname, self.configuration.vipr_tenant, project=None, port=None, username=None, passwd=None, usessl=None, osversion=None, cluster=None, datacenter=None, vcenter=None)
                        LOG.info("Created host " + hostname)
                    # add the initiator to the host
                    self.hostinitiator_obj.create(hostname, protocol, initiatorNode, initiatorPort);
                    foundhostname = hostname
                    LOG.info("Initiator " + initiatorPort + " added to host " + hostname)
                else:
                    LOG.info("Found host " + foundhostname +
                            " containing initiator " + initiatorPort +
                            "; add this host to the export group.")

                # create an export group for this host
                foundgroupname = hostname + 'SG'
                # create a unique name
                foundgroupname = foundgroupname + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                res = self.exportgroup_obj.exportgroup_create(foundgroupname, self.configuration.vipr_project, self.configuration.vipr_tenant, self.configuration.vipr_varray, 'Host', foundhostname);

            res = self.exportgroup_obj.exportgroup_add_volumes(foundgroupname, self.configuration.vipr_tenant, self.configuration.vipr_project, volumename, None, None,None, True)
            return self._find_device_info(volume, initiatorPort)

        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Attach volume (" + self._get_volume_name(volume) + ") to host (" + hostname + ") initiator (" + initiatorPort + ") failed: " + e.err_text)

    @retry_wrapper
    def terminate_connection(self, volume, 
            protocol, initiatorNode, initiatorPort, hostname):
        try:
            self.authenticate_user()
            volumename = self._get_volume_name(volume)
            tenantproject = self.configuration.vipr_tenant+ '/' + self.configuration.vipr_project
            voldetails = self.volume_obj.show(tenantproject + '/' + volumename)
            volid = voldetails['id']

            foundgroupname = self._find_exportgroup(initiatorPort)
            if foundgroupname is not None:
                res = self.exportgroup_obj.exportgroup_remove_volumes(foundgroupname, self.configuration.vipr_tenant, self.configuration.vipr_project, volumename, snapshot=False)
            else:
                LOG.info("No export group found for this initiator: " + initiatorPort + "; this is considered already detached.")
                
        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Detaching volume " + volumename + " from host " + hostname + " failed: " + e.err_text)

    @retry_wrapper
    def _find_device_info(self, volume, initiator_port):
        '''
        Returns the device_info in a list of itls that have the matched initiator
        (there could be multiple targets, hence a list):
                [
                 {
                  "hlu":9,
                  "initiator":{...,"port":"20:00:00:25:B5:49:00:22"},
                  "export":{...},
                  "device":{...,"wwn":"600601602B802D00B62236585D0BE311"},
                  "target":{...,"port":"50:06:01:6A:46:E0:72:EF"},
                  "san_zone_name":"..."
                 },
                 {
                  "hlu":9,
                  "initiator":{...,"port":"20:00:00:25:B5:49:00:22"},
                  "export":{...},
                  "device":{...,"wwn":"600601602B802D00B62236585D0BE311"},
                  "target":{...,"port":"50:06:01:62:46:E0:72:EF"},
                  "san_zone_name":"..."
                 }
                ]
        '''
        volumename = self._get_volume_name(volume)
        fullname = self.configuration.vipr_project + '/' + volumename
        vol_uri = self.volume_obj.volume_query(fullname)
        
        '''
        The itl info shall be available at the first try since now export is a 
        synchronous call.  We are trying a few more times to accommodate any 
        delay on filling in the itl info after the export task is completed.
        '''
        itls = []
        for x in xrange(10):
            exports = self.volume_obj.get_exports_by_uri(vol_uri)
            LOG.debug(_("Volume exports: %s") % exports)
            for itl in exports['itl']:
                if (str(initiator_port) == itl['initiator']['port']):
                    found_device_number = itl['hlu']
                    if found_device_number is not None and found_device_number != '-1':
                        # 0 is a valid number for found_device_number.
                        # Only loop if it is None or -1
                        LOG.debug(_("Found Device Number: %(found_device_number)s") % (locals()))
                        itls.append(itl)
            
            if itls:
                break
            else:
                LOG.debug(_("Device Number not found yet. Retrying after 10 seconds..."))
                time.sleep(10)
            
        if itls is None:
            # No device number found after 10 tries; return an empty itl
            LOG.info(_("No device number has been found after 10 tries; this likely indicates an unsuccessful attach of volume %(volumename) to initiator %(initiatorPort).") % (locals()))
            
        return itls
    
    def _get_volume_name(self, vol):
        try:
            name = vol['display_name']
        except:
            name = None
             
        if (name is None or len(name) == 0):
            name = vol['name']
            
        return name
    
    def _get_vpool(self, volume):
        vpool = {}
        ctxt = context.get_admin_context()
        type_id = volume['volume_type_id']
        if type_id is not None:
            volume_type = volume_types.get_volume_type(ctxt, type_id)
            specs = volume_type.get('extra_specs')
            for key, value in specs.iteritems():
                vpool[key] = value

        return vpool

    @retry_wrapper
    def _find_exportgroup(self, initiator_port):
        '''
        Find the export group to which the given initiator port belong, if exists.
        '''
        foundgroupname = None
        grouplist = self.exportgroup_obj.exportgroup_list(self.configuration.vipr_project, self.configuration.vipr_tenant)
        for groupid in grouplist:
            groupdetails = self.exportgroup_obj.exportgroup_show(groupid, self.configuration.vipr_project, self.configuration.vipr_tenant)
            if groupdetails is not None:
                initiators = groupdetails['initiators']
                for initiator in initiators:
                    if (initiator['initiator_port'] == initiator_port):
                        foundgroupname = groupdetails['name']
                        break

                if foundgroupname is not None:
                    # Check the associated varray
                    if groupdetails['varray']:
                        varray_uri = groupdetails['varray']['id']
                        varray_details = self.varray_obj.varray_show(varray_uri)
                        if (varray_details['name'] == self.configuration.vipr_varray):
                            LOG.debug("Found exportgroup " + foundgroupname + " for initiator " + initiator_port)
                            break
                    
                    # Not the right varray
                    foundgroupname = None

        return foundgroupname

    @retry_wrapper
    def _find_host(self, initiator_port):
        ''' Find the host, if exists, to which the given initiator belong. '''
        foundhostname = None
        hosts = self.host_obj.list_by_tenant(self.configuration.vipr_tenant)
        hostsdetails = self.host_obj.show(hosts)
        for host in hostsdetails:
            initiators = self.host_obj.list_initiators(host['name'])
            for initiator in initiators:
                if (initiator_port == initiator['name']):
                    foundhostname = host['name']
                    break

            if foundhostname is not None:
                break

        return foundhostname

    @retry_wrapper
    def _host_exists(self, host_name):
        ''' Check if a Host object with the given hostname already exists in ViPR '''
        hosts = self.host_obj.list_by_tenant(self.configuration.vipr_tenant)
        hostsdetails = self.host_obj.show(hosts)
        for host in hostsdetails:
            if (host_name == host['name']):
                return True

        return False


    @retry_wrapper
    def update_volume_stats(self):
        """Retrieve stats info."""
        LOG.debug(_("Updating volume stats"))
        self.authenticate_user()
 
        try:
            vols = self.volume_obj.list_volumes(self.configuration.vipr_tenant + "/" + self.configuration.vipr_project)
            vpairs = set()            
            if (len(vols) > 0):
                for vol in vols:
                    if(vol):              
                        vpair = (vol["vpool"]["id"], vol["varray"]["id"])
                        if (vpair not in vpairs):
                            vpairs.add(vpair)

            if (len(vpairs) > 0):            
                free_gb = 0.0
                used_gb = 0.0
                provisioned_gb = 0.0
                precent_used = 0.0
                percent_provisioned = 0.0            
                for vpair in vpairs:            
                    if(vpair): 
                        (s, h) = vipr_utils.service_json_request(self.configuration.vipr_hostname, self.configuration.vipr_port,
                                      "GET",
                                      URI_VPOOL_VARRAY_CAPACITY.format(vpair[0], vpair[1]),
                                      body=None)
                        capacity = vipr_utils.json_decode(s)
                        
                        free_gb += float(capacity["free_gb"])
                        used_gb += float(capacity["used_gb"])
                        provisioned_gb += float(capacity["provisioned_gb"])
                        
                self.stats['free_capacity_gb'] = free_gb
                self.stats['total_capacity_gb'] = free_gb + used_gb
                self.stats['reserved_percentage'] = 100 * provisioned_gb/(free_gb + used_gb)

            return self.stats

        except SOSError as e:
            raise e


#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

"""
Driver for EMC ViPR iSCSI volumes.

"""

import os
import socket
import time
from oslo.config import cfg


from cinder import exception
# ERIC: we get an error imprting flags
# from cinder import flags
from cinder.openstack.common import log as logging
from cinder import utils
from cinder.volume import driver
from cinder.volume.drivers.emc.vipr.emc_vipr_driver_common import EMCViPRDriverCommon 

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

class EMCViPRISCSIDriver(driver.ISCSIDriver):
    """EMC ViPR iSCSI Driver"""
    
    def __init__(self, *args, **kwargs):
        super(EMCViPRISCSIDriver, self).__init__(*args, **kwargs)
        self.configuration.append_config_values(volume_opts)
        self.common = EMCViPRDriverCommon(
                        'iSCSI',
                        configuration=self.configuration)

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
        if (self.configuration.rpc_response_timeout<300):
            LOG.warn(_("cinder configuration should set rpc_response_time to at least 300 seconds"))
            
        pass

    def create_volume(self, volume):
        """Creates a EMC Volume. """
        self.common.create_volume(volume)
        self.common.setTags(volume)

    def create_cloned_volume(self, volume, src_vref):
        """Creates a cloned Volume."""
        self.common.create_cloned_volume(volume, src_vref)
        self.common.setTags(volume)                
        
    def create_volume_from_snapshot(self, volume, snapshot):
        """Creates a volume from a snapshot."""
        #self.common.create_volume_from_snapshot(volume, snapshot)
        snapshotname = snapshot['name']
        volumename = volume['name']
        exception_message = (_('Error Create Volume from Snapshot: '
                             'Volume: %(volumename)s  Snapshot: '
                             '%(snapshotname)s. Create Volume '
                             'from Snapshot is NOT supported on '
                             'EMCViPRISCSIDriver.')
                             % {'volumename': volumename,
                                'snapshotname': snapshotname})
        LOG.error(exception_message)
        raise exception.VolumeBackendAPIException(data=exception_message)

    def delete_volume(self, volume):
        """Deletes an EMC volume."""
        self.common.delete_volume(volume)

    def create_snapshot(self, snapshot):
        """Creates a snapshot."""
        self.common.create_snapshot(snapshot)

    def delete_snapshot(self, snapshot):
        """Deletes a snapshot."""
        self.common.delete_snapshot(snapshot)

    def _iscsi_location(ip, target, iqn, lun=None):
        return "%s:%s,%s %s %s" % (ip, self.configuration.iscsi_port, target, iqn, lun)

    def ensure_export(self, context, volume):
        """Driver entry point to get the export info for an existing volume."""
        pass

    def create_export(self, context, volume):
        """Driver entry point to get the export info for a new volume."""
        pass

    def remove_export(self, context, volume):
        """Driver exntry point to remove an export for a volume.
        """
        pass

    def check_for_export(self, context, volume_id):
        """Make sure volume is exported."""
        pass

    def initialize_connection(self, volume, connector):
        """Initializes the connection and returns connection info.

        the iscsi driver returns a driver_volume_type of 'iscsi'.
        the format of the driver data is defined in _get_iscsi_properties.
        Example return value::

            {
                'driver_volume_type': 'iscsi'
                'data': {
                    'target_discovered': True,
                    'target_iqn': 'iqn.2010-10.org.openstack:volume-00000001',
                    'target_portal': '127.0.0.0.1:3260',
                    'volume_id': 1,
                }
            }

        """
        initiatorNode = None
        initiatorPort = connector['initiator']
        protocol = 'iSCSI'
        hostname = connector['host'] # socket.gethostname()        
        self.common.initialize_connection(volume,
            protocol, initiatorNode, initiatorPort, hostname)

        iscsi_properties = self._get_iscsi_properties(volume)
        return {
            'driver_volume_type': 'iscsi',
            'data': iscsi_properties
        }

    def _do_iscsi_discovery(self, volume, ip_address=None):

        LOG.warn(_("ISCSI provider_location not stored, using discovery"))

        if ip_address is None:
            (out, _err) = self._execute('iscsiadm', '-m', 'discovery',
                                    '-t', 'sendtargets', '-p',
                                    self.configuration.iscsi_ip_address,
                                    run_as_root=True)
        else:
            (out, _err) = self._execute('iscsiadm', '-m', 'discovery',
                                    '-t', 'sendtargets', '-p',
                                    ip_address,
                                    run_as_root=True)

        targets = []
        for target in out.splitlines():
            targets.append(target)

        return targets 

    def _get_iscsi_properties(self, volume):
        """Gets iscsi configuration

        We ideally get saved information in the volume entity, but fall back
        to discovery if need be. Discovery may be completely removed in future
        The properties are:

        :target_discovered:    boolean indicating whether discovery was used

        :target_iqn:    the IQN of the iSCSI target

        :target_portal:    the portal of the iSCSI target

        :target_lun:    the lun of the iSCSI target

        :volume_id:    the id of the volume (currently used by xen)

        :auth_method:, :auth_username:, :auth_password:

            the authentication details. Right now, either auth_method is not
            present meaning no authentication, or auth_method == `CHAP`
            meaning use CHAP with the specified credentials.
        """

        properties = {}

        device_info = self.common.find_device_number(volume)
        if device_info is None:
            exception_message = (_("Cannot find device number for volume %s")
                                 % volume['name'])
            raise exception.VolumeBackendAPIException(data=exception_message)

        ip_address = device_info['ip_address']

        location = self._do_iscsi_discovery(volume, ip_address)
        if not location:
            raise exception.InvalidVolume(_("Could not find iSCSI export "
                                          " for volume %s") %
                                          (volume['name']))

        LOG.debug(_("ISCSI Discovery: Found %s") % (location))
        properties['target_discovered'] = True

        '''
        device_info = self.common.find_device_number(volume)
        if device_info is None or device_info['hostlunid'] is None:
            exception_message = (_("Cannot find device number for volume %s")
                                 % volume['name'])
            raise exception.VolumeBackendAPIException(data=exception_message)
        '''

        try:
            if device_info['hostlunid'] is None:
                exception_message = (_("Cannot find device number for volume %s")
                                 % volume['name'])
        except KeyError as e:
            raise exception.VolumeBackendAPIException(data=exception_message)

        device_number = device_info['hostlunid']
        endpoint = device_info['endpoint']

        foundEndpoint = False
        for loc in location:
            results = loc.split(" ")
            properties['target_portal'] = results[0].split(",")[0]
            properties['target_iqn'] = results[1]
            if properties['target_iqn'] == endpoint:
                LOG.debug(_("Found iSCSI endpoint: %s") % endpoint)
                foundEndpoint = True
                break

        if not foundEndpoint:
            LOG.warn(_("ISCSI endpoint not found for volume %(name)s.")
                     % {'name': volume['name']})

        properties['target_lun'] = device_number

        properties['volume_id'] = volume['id']

        auth = volume['provider_auth']
        if auth:
            (auth_method, auth_username, auth_secret) = auth.split()

            properties['auth_method'] = auth_method
            properties['auth_username'] = auth_username
            properties['auth_password'] = auth_secret

        LOG.debug(_("ISCSI properties: %s") % (properties))

        return properties

    def _run_iscsiadm(self, iscsi_properties, iscsi_command, **kwargs):
        check_exit_code = kwargs.pop('check_exit_code', 0)
        (out, err) = self._execute('iscsiadm', '-m', 'node', '-T',
                                   iscsi_properties['target_iqn'],
                                   '-p', iscsi_properties['target_portal'],
                                   *iscsi_command, run_as_root=True,
                                   check_exit_code=check_exit_code)
        LOG.debug("iscsiadm %s: stdout=%s stderr=%s" %
                  (iscsi_command, out, err))
        return (out, err)

    def terminate_connection(self, volume, connector, **kwargs):
        """Disallow connection from connector"""
        initiatorNode = connector['initiator']
        initiatorPort = connector['initiator']
        protocol = 'iSCSI'
        hostname = connector['host']
        self.common.terminate_connection(volume,
            protocol, initiatorNode, initiatorPort, hostname)

    def get_volume_stats(self, refresh=False):
        """Get volume status.

        If 'refresh' is True, run update the stats first.
        """
        if refresh:
            self.update_volume_stats()

        return self._stats

    def update_volume_stats(self):
        """Retrieve stats info from virtual pool/virtual array."""
        LOG.debug(_("Updating volume stats"))
        self._stats = self.common.update_volume_stats()


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

from oslo.config import cfg

from cinder import exception
# ERIC: we get an error importing flags
# from cinder import flags
from cinder.openstack.common import log as logging
from cinder.volume import driver
from cinder.volume.drivers.emc.vipr.emc_vipr_driver_common import EMCViPRDriverCommon 

LOG = logging.getLogger(__name__)


class EMCViPRISCSIDriver(driver.ISCSIDriver):
    """EMC ViPR iSCSI Driver"""
    
   
    def __init__(self, *args, **kwargs):
        super(EMCViPRISCSIDriver, self).__init__(*args, **kwargs)
        self.common = EMCViPRDriverCommon(
                        protocol='iSCSI',
                        default_backend_name=self.__class__.__name__,
                        configuration=self.configuration)

    def check_for_setup_error(self):
        self.common.check_for_setup_error()

    def create_volume(self, volume):
        """Creates a Volume. """
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

    def _iscsi_location(self, ip, target, iqn, lun=None):
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
        the format of the driver data is defined as:
    
            :target_discovered:    boolean indicating whether discovery was used
    
            :target_iqn:    the IQN of the iSCSI target
    
            :target_portal:    the portal of the iSCSI target
    
            :target_lun:    the lun of the iSCSI target
    
            :volume_id:    the id of the volume (currently used by xen)
    
            :auth_method:, :auth_username:, :auth_password:
    
                the authentication details. Right now, either auth_method is not
                present meaning no authentication, or auth_method == `CHAP`
                meaning use CHAP with the specified credentials.

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
        hostname = connector['host']
        itls = self.common.initialize_connection(volume,
            protocol, initiatorNode, initiatorPort, hostname)
        
        properties = {}
        properties['target_discovered'] = False
        properties['volume_id'] = volume['id']
        if itls:
            properties['target_iqn'] = itls[0]['target']['port']
            properties['target_portal'] = itls[0]['target']['ip_address'] + ':' + itls[0]['target']['tcp_port']
            properties['target_lun'] = itls[0]['hlu']
        
        auth = volume['provider_auth']
        if auth:
            (auth_method, auth_username, auth_secret) = auth.split()
            properties['auth_method'] = auth_method
            properties['auth_username'] = auth_username
            properties['auth_password'] = auth_secret

        LOG.debug(_("ISCSI properties: %s") % (properties))
        return {
            'driver_volume_type': 'iscsi',
            'data': properties
        }

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


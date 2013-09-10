#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.

"""
Driver for EMC ViPR FC volumes.

"""

import os
import socket
import time
from xml.dom.minidom import parseString

from cinder import exception
from cinder.openstack.common import log as logging
from cinder import utils
from cinder.volume import driver
from cinder.volume.drivers.emc.vipr.emc_vipr_driver_common import EMCViPRDriverCommon 

LOG = logging.getLogger(__name__)


class EMCViPRFCDriver(driver.FibreChannelDriver):
    """EMC ViPR FC Driver"""
    
    def __init__(self, *args, **kwargs):
        super(EMCViPRFCDriver, self).__init__(*args, **kwargs)
        self.common = EMCViPRDriverCommon(
                        'FC',
                        configuration=self.configuration)

    def check_for_setup_error(self):
        self.common.check_for_setup_error()

    def create_volume(self, volume):
        """Creates a EMC Volume. """
        self.common.create_volume(volume)
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
                             'EMCViPRFCDriver.')
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

    def ensure_export(self, context, volume):
        """Driver entry point to get the export info for an existing volume."""
        pass

    def create_export(self, context, volume):
        """Driver entry point to get the export info for a new volume."""
        pass

    def remove_export(self, context, volume):
        """Driver exntry point to remove an export for a volume."""
        pass

    def check_for_export(self, context, volume_id):
        """Make sure volume is exported."""
        pass

    def initialize_connection(self, volume, connector):
        """Initializes the connection and returns connection info.

        The  driver returns a driver_volume_type of 'fibre_channel'.
        The target_wwn can be a single entry or a list of wwns that
        correspond to the list of remote wwn(s) that will export the volume.
        Example return values:

            {
                'driver_volume_type': 'fibre_channel'
                'data': {
                    'target_discovered': True,
                    'target_lun': 1,
                    'target_wwn': '1234567890123',
                }
            }

            or

             {
                'driver_volume_type': 'fibre_channel'
                'data': {
                    'volume_id': 1,
                    'target_discovered': True,
                    'target_lun': 1,
                    'target_wwn': ['1234567890123', '0987654321321'],
                }
            }

        """
        initiatorNode = None
        initiatorPort = connector['initiator']
        protocol = 'FC'
        hostname = connector['host'] # socket.gethostname()        
        itls = self.common.initialize_connection(volume,
            protocol, initiatorNode, initiatorPort, hostname)

        properties = {}
        properties['volume_id'] = volume['id']
        properties['target_discovered'] = False
        if itls:
            properties['target_lun'] = itls[0]['hlu']
            properties['target_wwn'] = []
            for itl in itls:
                properties['target_wwn'].append(itl['target']['port'])
        
        auth = volume['provider_auth']
        if auth:
            (auth_method, auth_username, auth_secret) = auth.split()
            properties['auth_method'] = auth_method
            properties['auth_username'] = auth_username
            properties['auth_password'] = auth_secret

        LOG.debug(_("FC properties: %s") % (properties))
        return {
            'driver_volume_type': 'fibre_channel',
            'data': properties
        }

    def terminate_connection(self, volume, connector, **kwargs):
        """Driver entry point to detach a volume from an instance."""
        initiatorNode = connector['host']
        initiatorPort = connector['wwpns']
        protocol = 'FC'
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
        stats = self.common.update_volume_stats()
        stats['volume_backend_name'] = self.__class__.__name__
        self._stats = stats
        LOG.info(_("Volume stats updated: %s") % (stats))

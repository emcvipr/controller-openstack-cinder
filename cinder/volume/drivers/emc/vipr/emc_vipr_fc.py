#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Driver for EMC ViPR FC volumes.

"""

import os
import re
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
                        protocol='FC',
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
        properties = {}
        properties['volume_id'] = volume['id']
        properties['target_discovered'] = False
        properties['target_wwn'] = []

        protocol = 'FC'
        hostname = connector['host']
        initPorts = []
        initNodes = []
        for i in xrange(len(connector['wwpns'])):
            initiatorNode = ':'.join(re.findall('..', connector['wwnns'][i])).upper()   # Add ":" every two digits
            initiatorPort = ':'.join(re.findall('..', connector['wwpns'][i])).upper()   # Add ":" every two digits
            initPorts.append(initiatorPort)
            initNodes.append(initiatorNode)
        itls = self.common.initialize_connection(volume, protocol, initNodes, initPorts, hostname)
        if itls:
            properties['target_lun'] = itls[0]['hlu']
            for itl in itls:
                properties['target_wwn'].append(itl['target']['port'].replace(':','').lower())
        
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
        protocol = 'FC'
        hostname = connector['host']
        initPorts = []
        initNodes = []
        for i in xrange(len(connector['wwpns'])):
            initiatorNode = ':'.join(re.findall('..', connector['wwnns'][i])).upper()   # Add ":" every two digits
            initiatorPort = ':'.join(re.findall('..', connector['wwpns'][i])).upper()   # Add ":" every two digits
            initPorts.append(initiatorPort)
            initNodes.append(initiatorNode)
        self.common.terminate_connection(volume, protocol, initNodes, initPorts, hostname)

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

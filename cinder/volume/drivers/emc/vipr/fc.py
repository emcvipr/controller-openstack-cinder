# Copyright (c) 2014 EMC Corporation
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

import re

try:
    from oslo_log import log as logging
except ImportError:
    from cinder.openstack.common import log as logging

from cinder.volume import driver
from cinder.volume.drivers.emc.vipr import common as vipr_common

try:
    # new utilities introduced in Juno
    from cinder.zonemanager.utils import AddFCZone
    from cinder.zonemanager.utils import RemoveFCZone
except ImportError:
    # AddFCZone or RemoveFCZone are not ready
    # Define them for backward compatibility
    def AddFCZone(func):
        return func

    def RemoveFCZone(func):
        return func

LOG = logging.getLogger(__name__)


class EMCViPRFCDriver(driver.FibreChannelDriver):
    """EMC ViPR FC Driver"""

    def __init__(self, *args, **kwargs):
        super(EMCViPRFCDriver, self).__init__(*args, **kwargs)
        self.common = self._get_common_driver()

    def _get_common_driver(self):
        return vipr_common.EMCViPRDriverCommon(
            protocol='FC',
            default_backend_name=self.__class__.__name__,
            configuration=self.configuration)

    def check_for_setup_error(self):
        self.common.check_for_setup_error()

    def create_volume(self, volume):
        """Creates a Volume."""
        self.common.create_volume(volume, self)
        self.common.set_volume_tags(volume)

    def create_cloned_volume(self, volume, src_vref):
        """Creates a cloned Volume."""
        self.common.create_cloned_volume(volume, src_vref)
        self.common.set_volume_tags(volume)

    def create_volume_from_snapshot(self, volume, snapshot):
        """Creates a volume from a snapshot."""
        self.common.create_volume_from_snapshot(snapshot, volume, self.db)
        self.common.set_volume_tags(volume)

    def extend_volume(self, volume, new_size):
        """expands the size of the volume."""
        self.common.expand_volume(volume, new_size)

    def delete_volume(self, volume):
        """Deletes an EMC volume."""
        self.common.delete_volume(volume)

    def create_snapshot(self, snapshot):
        """Creates a snapshot."""
        self.common.create_snapshot(snapshot, self.db)

    def delete_snapshot(self, snapshot):
        """Deletes a snapshot."""
        self.common.delete_snapshot(snapshot)

    def ensure_export(self, context, volume):
        """Driver entry point to get the export info for an existing volume."""
        pass

    def create_export(self, context, volume, connector=None):
        """Driver entry point to get the export info for a new volume."""
        pass

    def remove_export(self, context, volume):
        """Driver exntry point to remove an export for a volume."""
        pass

    def create_consistencygroup(self, context, group):
        """Creates a consistencygroup."""        
        return self.common.create_consistencygroup(context, group)
    
    def update_consistencygroup(self, context, group, add_volumes, remove_volumes):
        """Updates volumes in consistency group."""
        return self.common.update_consistencygroup(self, context, group, add_volumes, remove_volumes)
        
    def delete_consistencygroup(self, context, group):
        """Deletes a consistency group."""
        return self.common.delete_consistencygroup(self, context, group)
        
    def create_cgsnapshot(self, context, cgsnapshot):
        """Creates a cgsnapshot."""
        return self.common.create_cgsnapshot(self, context, cgsnapshot)

    def delete_cgsnapshot(self, context, cgsnapshot):
        """Deletes a cgsnapshot."""
        return self.common.delete_cgsnapshot(self, context, cgsnapshot)

    def check_for_export(self, context, volume_id):
        """Make sure volume is exported."""
        pass

    @AddFCZone
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
        initPorts, initNodes = self._build_initport_initnode_list(connector)
        itls = self.common.initialize_connection(volume,
                                                 protocol,
                                                 initNodes,
                                                 initPorts,
                                                 hostname)
        if itls:
            properties['target_lun'] = itls[0]['hlu']
            target_wwns, initiator_target_map = \
                self._build_initiator_target_map(itls, connector)

        properties['target_wwn'] = target_wwns
        properties['initiator_target_map'] = initiator_target_map

        auth = volume['provider_auth']
        if auth:
            (auth_method, auth_username, auth_secret) = auth.split()
            properties['auth_method'] = auth_method
            properties['auth_username'] = auth_username
            properties['auth_password'] = auth_secret

        LOG.debug('FC properties: ')
        LOG.debug(properties)
        return {
            'driver_volume_type': 'fibre_channel',
            'data': properties
        }

    @RemoveFCZone
    def terminate_connection(self, volume, connector, **kwargs):
        """Driver entry point to detach a volume from an instance."""
        protocol = 'FC'
        hostname = connector['host']
        initPorts, initNodes = self._build_initport_initnode_list(connector)
        itls = self.common.terminate_connection(volume,
                                                protocol,
                                                initNodes,
                                                initPorts,
                                                hostname)

        volumes_count = self.common.get_exports_count_by_initiators(initPorts)
        if volumes_count > 0:
            #return empty data
            data = {'driver_volume_type': 'fibre_channel', 'data': {}}
        else:
            target_wwns, initiator_target_map = \
                self._build_initiator_target_map(itls, connector)
            data = {
                'driver_volume_type': 'fibre_channel',
                'data': {
                    'target_wwn': target_wwns,
                    'initiator_target_map': initiator_target_map}}

        LOG.debug('Return FC data: ')
        LOG.debug(data)
        return data

    def _build_initiator_target_map(self, itls, connector):

        target_wwns = []
        for itl in itls:
            target_wwns.append(itl['target']['port'].replace(':', '').lower())

        initiator_wwns = connector['wwpns']
        initiator_target_map = {}
        for initiator in initiator_wwns:
            initiator_target_map[initiator] = target_wwns

        return target_wwns, initiator_target_map

    def _build_initport_initnode_list(self, connector):
        initPorts = []
        initNodes = []
        for i in xrange(len(connector['wwpns'])):
            initiatorNode = ':'.join(re.findall(
                '..',
                connector['wwnns'][i])).upper()   # Add ":" every two digits
            initiatorPort = ':'.join(re.findall(
                '..',
                connector['wwpns'][i])).upper()   # Add ":" every two digits
            initPorts.append(initiatorPort)
            initNodes.append(initiatorNode)

        return initPorts, initNodes

    def get_volume_stats(self, refresh=False):
        """Get volume status.

        If 'refresh' is True, run update the stats first.
        """
        if refresh:
            self.update_volume_stats()

        return self._stats

    def update_volume_stats(self):
        """Retrieve stats info from virtual pool/virtual array."""
        LOG.debug("Updating volume stats")
        self._stats = self.common.update_volume_stats()


    def retype(self, ctxt, volume, new_type, diff, host):
        """Change the volume type"""
        return self.common.retype(ctxt, volume, new_type, diff, host)


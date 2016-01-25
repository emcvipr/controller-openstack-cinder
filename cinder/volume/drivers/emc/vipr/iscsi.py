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
Driver for EMC ViPR iSCSI volumes.

"""

try:
    from oslo_log import log as logging
except ImportError:
    from cinder.openstack.common import log as logging

from cinder.volume import driver
from cinder.volume.drivers.emc.vipr import common as vipr_common

LOG = logging.getLogger(__name__)


class EMCViPRISCSIDriver(driver.ISCSIDriver):
    """EMC ViPR iSCSI Driver"""

    def __init__(self, *args, **kwargs):
        super(EMCViPRISCSIDriver, self).__init__(*args, **kwargs)
        self.common = self._get_common_driver()

    def _get_common_driver(self):
        return vipr_common.EMCViPRDriverCommon(
            protocol='iSCSI',
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

    def _iscsi_location(self, ip, target, iqn, lun=None):
        return "%s:%s,%s %s %s" % (ip,
                                   self.configuration.iscsi_port,
                                   target,
                                   iqn,
                                   lun)

    def ensure_export(self, context, volume):
        """Driver entry point to get the export info for an existing volume."""
        pass

    def create_export(self, context, volume, connector=None):
        """Driver entry point to get the export info for a new volume."""
        pass

    def remove_export(self, context, volume):
        """Driver exntry point to remove an export for a volume.
        """
        pass

    def create_consistencygroup(self, context, group):
        """Creates a consistencygroup."""        
        return self.common.create_consistencygroup(context, group)

    def delete_consistencygroup(self, context, group):
        """Deletes a consistency group."""
        return self.common.delete_consistencygroup(self, context, group)
    
    
    def update_consistencygroup(self, context, group, add_volumes, remove_volumes):
        """Updates volumes in consistency group."""
        return self.common.update_consistencygroup(self, context, group, add_volumes, remove_volumes)
        
    def create_cgsnapshot(self, context, cgsnapshot):
        """Creates a cgsnapshot."""
        return self.common.create_cgsnapshot(self, context, cgsnapshot)

    def delete_cgsnapshot(self, context, cgsnapshot):
        """Deletes a cgsnapshot."""
        return self.common.delete_cgsnapshot(self, context, cgsnapshot)

    def check_for_export(self, context, volume_id):
        """Make sure volume is exported."""
        pass

    def initialize_connection(self, volume, connector):
        """Initializes the connection and returns connection info.

        the iscsi driver returns a driver_volume_type of 'iscsi'.
        the format of the driver data is defined as:
            :target_discovered:    boolean indicating
            whether discovery was used
            :target_iqn:    the IQN of the iSCSI target
            :target_portal:    the portal of the iSCSI target
            :target_lun:    the lun of the iSCSI target
            :volume_id:    the id of the volume (currently used by xen)
            :auth_method:, :auth_username:, :auth_password:
                the authentication details. Right now,
                either auth_method is not
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
        initiatorNodes = []
        initiatorNode = None
        initiatorNodes.append(initiatorNode)
        initiatorPorts = []
        initiatorPort = connector['initiator']
        initiatorPorts.append(initiatorPort)
        protocol = 'iSCSI'
        hostname = connector['host']
        itls = self.common.initialize_connection(volume,
                                                 protocol,
                                                 initiatorNodes,
                                                 initiatorPorts,
                                                 hostname)
        properties = {}
        properties['target_discovered'] = False
        properties['volume_id'] = volume['id']
        if itls:
            properties['target_iqn'] = itls[0]['target']['port']
            properties['target_portal'] = itls[0]['target']['ip_address'] + \
                ':' + itls[0]['target']['tcp_port']
            properties['target_lun'] = itls[0]['hlu']
        auth = volume['provider_auth']
        if auth:
            (auth_method, auth_username, auth_secret) = auth.split()
            properties['auth_method'] = auth_method
            properties['auth_username'] = auth_username
            properties['auth_password'] = auth_secret

        LOG.debug("ISCSI properties: ")
        LOG.debug(properties)
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
        initPorts = []
        initNodes = []
        initPorts.append(initiatorPort)
        initNodes.append(initiatorNode)
        self.common.terminate_connection(volume,
                                         protocol,
                                         initNodes,
                                         initPorts,
                                         hostname)

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


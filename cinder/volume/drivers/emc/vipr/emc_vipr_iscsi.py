# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 EMC Corporation, Inc.
# Copyright (c) 2013 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
"""
ViPR Drivers for EMC volumes.

"""

import os
import socket
import time
from xml.dom.minidom import parseString

from cinder import exception
# ERIC: we get an error imprting flags
# from cinder import flags
from cinder.openstack.common import log as logging
from cinder import utils
from cinder.volume import driver
from cinder.volume.drivers.emc.vipr.emc_vipr_driver_common import EMCViPRDriverCommon 

LOG = logging.getLogger(__name__)


class EMCViPRISCSIDriver(driver.ISCSIDriver):
    """EMC ViPR iSCSI Driver"""

    stats = {'driver_version': '1.0',
             'free_capacity_gb': 0,
             'reserved_percentage': 0,
             'storage_protocol': None,
             'total_capacity_gb': 0,
             'vendor_name': 'EMC',
             'volume_backend_name': None}

    def __init__(self, *args, **kwargs):

        super(EMCViPRISCSIDriver, self).__init__(*args, **kwargs)
        self.common = EMCViPRDriverCommon(
                        'iSCSI',
                        configuration=self.configuration)

    def check_for_setup_error(self):
        pass

    def create_volume(self, volume):
        """Creates a EMC Volume. """
        self.common.create_volume(volume)

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
        initiatorNode = connector['initiator']
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

    def _do_iscsi_discovery(self, volume):

        LOG.warn(_("ISCSI provider_location not stored, using discovery"))

        (out, _err) = self._execute('iscsiadm', '-m', 'discovery',
                                    '-t', 'sendtargets', '-p',
                                    self.configuration.iscsi_ip_address,
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

        location = self._do_iscsi_discovery(volume)
        if not location:
            raise exception.InvalidVolume(_("Could not find iSCSI export "
                                          " for volume %s") %
                                          (volume['name']))

        LOG.debug(_("ISCSI Discovery: Found %s") % (location))
        properties['target_discovered'] = True

        device_info = self.common.find_device_number(volume)
        if device_info is None or device_info['hostlunid'] is None:
            exception_message = (_("Cannot find device number for volume %s")
                                 % volume['name'])
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
            self.update_volume_status()

        return self._stats

    def update_volume_status(self):
        """Retrieve status info from volume group."""
        LOG.debug(_("Updating volume status"))
        self.stats['volume_backend_name'] = 'EMCViPRISCSIDriver'
        self.stats['storage_protocol'] = 'iSCSI'
        self.stats['total_capacity_gb'] = 'unknown' 
        self.stats['free_capacity_gb'] = 'unknown'
        self._stats = self.stats

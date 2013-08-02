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

import os
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

from lib.authentication import Authentication
import lib.common as vipr_utils
from lib.common import SOSError
from lib.exportgroup import ExportGroup
from lib.virtualarray import VirtualArray 
from lib.project import Project
from lib.snapshot import Snapshot
from lib.volume import Volume

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

CINDER_EMC_CONFIG_FILE = '/etc/cinder/cinder_emc_config.xml'


class EMCViPRDriverCommon():
    def __init__(self, prtcl, configuration=None):
        opt = cfg.StrOpt('cinder_emc_config_file',
                         default=CINDER_EMC_CONFIG_FILE,
                         help='use this file for cinder emc plugin '
                         'config data')
        CONF.register_opt(opt)
        self.protocol = prtcl
        self.configuration = configuration
        self.configuration.append_config_values([opt])

        self._get_vipr_info()
        vipr_utils.COOKIE = None

    def _get_vipr_info(self, filename=None):
        if filename == None:
            filename = filename = self.configuration.cinder_emc_config_file 

        file = open(filename, 'r')
        data = file.read()
        file.close()
        dom = parseString(data)
        fqdns = dom.getElementsByTagName('ViPRFQDN')
        if fqdns is not None and len(fqdns) > 0:
            fqdn = fqdns[0].toxml().replace('<ViPRFQDN>', '')
            fqdn = fqdn.replace('</ViPRFQDN>', '')
            self.fqdn = fqdn
            LOG.debug(_("ViPR FQDN: %(fqdn)s") % (locals()))
        ports = dom.getElementsByTagName('ViPRPort')
        if ports is not None and len(ports) > 0:
            port = ports[0].toxml().replace('<ViPRPort>', '')
            port = port.replace('</ViPRPort>', '')
            self.port = int(port)
            LOG.debug(_("ViPR Port: %(port)s") % (locals()))
        if fqdn is None or port is None:
            LOG.debug(_("ViPR server not found."))
            return None

        users = dom.getElementsByTagName('ViPRUserName')
        if users is not None and len(users) > 0:
            user = users[0].toxml().replace('<ViPRUserName>', '')
            user = user.replace('</ViPRUserName>', '')
            self.user = user
            LOG.debug(_("ViPR user name: %(user)s") % (locals()))
        passwords = dom.getElementsByTagName('ViPRPassword')
        if passwords is not None and len(passwords) > 0:
            password = passwords[0].toxml().replace('<ViPRPassword>', '')
            password = password.replace('</ViPRPassword>', '')
            self.password = password
        if user is None or password is None:
            LOG.debug(_("ViPR server user credentials not found."))
            return None

        tenants = dom.getElementsByTagName('ViPRTenant')
        if tenants is not None and len(tenants) > 0:
            tenant = tenants[0].toxml().replace('<ViPRTenant>', '')
            tenant = tenant.replace('</ViPRTenant>', '')
            self.tenant = tenant
            LOG.debug(_("ViPR tenant: %(tenant)s") % (locals()))
        if tenant is None:
            LOG.debug(_("ViPR tenant not found in the config file."))
            return None

        projects = dom.getElementsByTagName('ViPRProject')
        if projects is not None and len(projects) > 0:
            project = projects[0].toxml().replace('<ViPRProject>', '')
            project = project.replace('</ViPRProject>', '')
            self.project = project
            LOG.debug(_("ViPR project: %(project)s") % (locals()))
        if project is None:
            LOG.debug(_("ViPR project not found in the config file."))
            return None

        nhs = dom.getElementsByTagName('ViPRVirtualArray')
        if nhs is not None and len(nhs) > 0:
            nh = nhs[0].toxml().replace('<ViPRVirtualArray>', '')
            nh = nh.replace('</ViPRVirtualArray>', '')
            self.virtualarray = nh
            LOG.debug(_("ViPR VirtualArray: %(nh)s") % (locals()))
        if nh is None:
            LOG.debug(_("ViPR VirtualArray not found in the config file."))
            return None

        viprinfo = {'FQDN': fqdn, 'port': port, 'username': user,
                    'password': password,
                    'tenant': tenant, 'project': project,
                    'virtualarray': nh}

        return viprinfo

    def authenticate_user(self):
        obj = Authentication(self.fqdn, self.port)
        cookiedir = os.getcwd()
        obj.authenticate_user(self.user, self.password, cookiedir, None)

    def create_volume(self, vol):
        self.authenticate_user()
        name = vol['name']
        size = int(vol['size']) * 1073741824
        obj = Volume(self.fqdn, self.port)

        vpool = self.get_vpool(vol)
        self.vpool = vpool['ViPR:VPOOL']

        try:
            sync = True
            count = 1
            res = obj.create(self.tenant + "/" + self.project,
                             name,
                             size,
                             self.virtualarray,
                             self.vpool,
                             None,
                             sync,
                             count,
                             None,
                             None,
                             None,
                             None,
                             None
                             )
            if(sync == False):
                return vipr_utils.format_json_object(res)
        except SOSError as e:
            if(e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Volume " +
                               name + ": Create failed\n" + e.err_text)
            else:
                raise e

    def delete_volume(self, vol):
        self.authenticate_user()
        name = vol['name']
        obj = Volume(self.fqdn, self.port)
        try:
            obj.delete(self.tenant + "/" + self.project + "/" + name)
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Volume " +
                               name + ": Delete failed\n" + e.err_text)
            else:
                raise e

    def list_volume(self):
        obj = Volume(self.fqdn, self.port)
        try:
            uris = obj.list_volumes(self.tenant + "/" + self.project)
            if(len(uris) > 0):
                output = []
                for uri in uris:
                    output.append(obj.show_by_uri(uri))

                if(args.verbose == False):
                    result = []
                    for record in output:
                        result.append(record['name'])
                    return result

                else:
                    return vipr_utils.format_json_object(output)
            else:
                return
        except SOSError as e:
            raise e

    def create_snapshot(self, snapshot):
        self.authenticate_user()
        obj = Snapshot(self.fqdn, self.port)
        try:  
            snapshotname = snapshot['name']
            volumename = snapshot['volume_name']
            resourcepath = self.tenant + "/" + self.project + "/"
            storageresType = 'block'
            storageresTypename = 'volumes'
            filesystem = None
            resourceUri = obj.storageResource_query(storageresType, filesystem, volumename, resourcepath)
            obj.snapshot_create(storageresType, storageresTypename, resourceUri, snapshotname)
            return

        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot: " + snapshotname + ", Create Failed\n" + e.err_text)
            else:
                raise e

    def delete_snapshot(self, snapshot):
        self.authenticate_user()
        obj = Snapshot(self.fqdn, self.port)
        try:
            snapshotname = snapshot['name']
            volumename = snapshot['volume_name']

            storageresType = 'block'
            storageresTypename = 'volumes'
            filesystem = None
            resourcepath = self.tenant + "/" + self.project + "/"
            resourceUri = obj.storageResource_query(storageresType, filesystem, volumename, resourcepath)
            obj.snapshot_delete(storageresType, storageresTypename, resourceUri, snapshotname)
            return
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                raise SOSError(SOSError.SOS_FAILURE_ERR, "Snapshot " + snapshotname + ": Delete Failed\n")
            else:
                raise e

    def initialize_connection(self, volume, 
            protocol, initiatorNode, initiatorPort, hostname):
        try:
            self.authenticate_user()
            volumename = volume['name']            
            obj = ExportGroup(self.fqdn, self.port)

            foundgroupname = None
            tenantproject = self.tenant+ '/' + self.project
            # grouplist = obj.exportgroup_list(tenantproject)
            grouplist = obj.exportgroup_list(self.project, self.tenant)

            for groupid in grouplist:
                #groupdetails = obj.exportgroup_show_uri(groupid)
                groupdetails = obj.exportgroup_show(groupid, self.project, self.tenant)
                initiators = groupdetails['initiators']
                for initiator in initiators:
                    try:
                        # if (initiator['initiator_node'] == initiatorNode and
                        if (initiator['initiator_port'] == initiatorPort):
                            foundgroupname = groupdetails['name']
                            break
                    except KeyError as e:
                        foundgroupname = None 

                    if foundgroupname is not None:
                        break

            if foundgroupname is not None:
                # res = obj.exportgroup_add_volumes(foundgroupname, tenantproject, volumename, None)
                res = obj.exportgroup_add_volumes(foundgroupname, self.project, self.tenant, volumename, None, None)
            else:
                foundgroupname = hostname + 'SG'
                # create a unique name
                foundgroupname = foundgroupname + '-' + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
                # res = obj.exportgroup_create(foundgroupname, tenantproject, self.virtualarray, protocol, initiatorNode, initiatorPort, hostname, volumename)
                res = obj.exportgroup_create(foundgroupname, self.project, self.tenant, self.virtualarray)
                res = obj.exportgroup_add_initiator(foundgroupname, self.project, self.tenant, protocol, initiatorNode, initiatorPort, hostname)
                res = obj.exportgroup_add_volumes(foundgroupname, self.project, self.tenant, volumename, None, None)


            # Wait for LUN to be really attached
            device_info = self.find_device_number(volume)
            try:
                device_number = device_info['hostlunid']
            except KeyError as e:
                device_number = None
            while (device_number is None or device_number == '-1'):
                time.sleep(10)
                device_info = self.find_device_number(volume)
                try:
                    device_number = device_info['hostlunid']
                except KeyError as e:
                    device_number = None

        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Export Group " + foundgroupname + ": Create failed: " + e.err_text)


    def terminate_connection(self, volume, 
            protocol, initiatorNode, initiatorPort, hostname):
        try:
            self.authenticate_user()
            volumename = volume['name']
            volobj = Volume(self.fqdn, self.port)
            tenantproject = self.tenant+ '/' + self.project
            voldetails = volobj.show(tenantproject + '/' + volumename)
            volid = voldetails['id']

            obj = ExportGroup(self.fqdn, self.port)

            foundgroupname = None
            tenantproject = self.tenant+ '/' + self.project
            grouplist = obj.exportgroup_list(self.project, self.tenant)
            for groupid in grouplist:
                #groupdetails = obj.exportgroup_show_uri(groupid)
                groupdetails = obj.exportgroup_show(groupid, self.project, self.tenant)
                initiators = groupdetails['initiators']
                for initiator in initiators:
                    if (initiator['initiator_node'] == initiatorNode and
                        initiator['initiator_port'] == initiatorPort):
                        vols = groupdetails['volumes']
                        for vol in vols:
                            if vol['id'] == volid:
                                foundgroupname = groupdetails['name']
                                break
                        if foundgroupname is not None:
                            break

                if foundgroupname is not None:
                    break

            if foundgroupname is not None:
                res = obj.exportgroup_remove_volumes(foundgroupname, project, tenant, volumename, False)    # no snapshot (snapshot = False)
        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Export Group " + foundgroupname + ": Create failed: " + e.err_text)

    def find_device_number(self, volume):
        try:
            device_info = {} 
            volumename = volume['name']
            obj = ExportGroup(self.fqdn, self.port)
            vol_obj = Volume(self.fqdn, self.port)

            found_device_number = None
            # fullname = self.tenant + '/' + self.project + '/' + volumename
            fullname = self.project + '/' + volumename
            # 0 is a valid number for found_device_number.
            # Only loop if it is None
            while found_device_number is None:
                vol_details = vol_obj.show(fullname)
                """
                tenantproject = self.tenant+ '/' + self.project
                grouplist = obj.exportgroup_list(tenantproject)
                for groupid in grouplist:
                    groupdetails = obj.exportgroup_show_uri(groupid)
                    volumes = groupdetails['volumes']
                    for eachvol in volumes:
                        if (eachvol['id'] == vol_details['id']):
                            # Xing
                            #found_device_number = eachvol['lun']
                            found_device_number = '0'
                            break

                    if found_device_number is not None:
                        break
                """

                uri = vol_details['id']
                (s, h) = vipr_utils.service_json_request(self.fqdn, self.port, 
                                      "GET",
                                      Volume.URI_VOLUME_EXPORTS.format(uri),
                                      None)
                o =  vipr_utils.json_decode(s)
                # o = vol_obj.show_volume_exports_by_uri(uri)
                LOG.debug(_("Volume exports: %s") % o)
                """
                o['itl'][0]

                {'device_wwn': 
                '60:06:01:60:3A:70:32:00:C8:06:BF:10:88:86:E2:11', 
                'hlu': '000022',
                'initiator': 'iqn.1993-08.org.debian:01:56aafff0227d', 
                'target': 'iqn.1992-04.com.emc:cx.apm00123907237.a8'}
                """
                found_device_number = o['itl'][0]['hlu']
                if found_device_number is None:
                    LOG.debug(_("Device Number not found. Retrying..."))
                    time.sleep(10)
                    continue
                else:
                    LOG.debug(_("Found Device Number: %(found_device_number)s")
                        % (locals()))

                endpoint = o['itl'][0]['target']['port']
                ip_address = o['itl'][0]['target']['ip_address']

                device_info['hostlunid'] = str(found_device_number)
                device_info['endpoint'] = endpoint 
                device_info['ip_address'] = ip_address 

        except:
            pass

        return device_info

    def get_vpool(self, volume):
        vpool = {}
        ctxt = context.get_admin_context()
        type_id = volume['volume_type_id']
        if type_id is not None:
            volume_type = volume_types.get_volume_type(ctxt, type_id)
            specs = volume_type.get('extra_specs')
            for key, value in specs.iteritems():
                vpool[key] = value

        return vpool

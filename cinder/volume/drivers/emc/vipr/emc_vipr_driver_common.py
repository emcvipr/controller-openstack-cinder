#!/usr/bin/python

# Copyright (c) 2012-13 EMC Corporation
# All Rights Reserved

# This software contains the intellectual property of EMC Corporation
# or is licensed to EMC Corporation from third parties.  Use of this
# software and the intellectual property contained therein is expressly
# limited to the terms and conditions of the License Agreement under which
# it is provided by or on behalf of EMC.


import os
import socket
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

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

CINDER_EMC_CONFIG_FILE = '/etc/cinder/cinder_emc_config.xml'
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
                raise e        
        except Exception as o:
            raise o
    
        if (retry):        
            return func(*args, **kwargs)
    
    return try_and_retry


AUTHENTICATED = False

class EMCViPRDriverCommon():
    
    OPENSTACK_TAG = 'OpenStack'

    stats = {'driver_version': '1.0',
             'free_capacity_gb': 'unknown',
             'reserved_percentage': '0',
             'storage_protocol': 'iSCSI',
             'total_capacity_gb': 'unknown',
             'vendor_name': 'EMC',
             'volume_backend_name': 'EMCViPRISCSIDriver'}
             
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
        global AUTHENTICATED
        
        # we should check to see if we are already authenticated before blindly doing it again
        if (AUTHENTICATED == False ):
            obj = Authentication(self.fqdn, self.port)
            cookiedir = os.getcwd()
            obj.authenticate_user(self.user, self.password, cookiedir, None)
            AUTHENTICATED = True

    @retry_wrapper
    def create_volume(self, vol):
        self.authenticate_user()
        name = vol['name']
        size = int(vol['size']) * 1073741824
        obj = Volume(self.fqdn, self.port)

        vpool = self._get_vpool(vol)
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
                               name + ": Tag failed\n" + e.err_text)
            else:
                raise e
                
    @retry_wrapper
    def setTags(self, vol):
        self.authenticate_user()
        name = vol['name']
        
        obj = Volume(self.fqdn, self.port)
        
                
        # first, get the current tags that start with the OPENSTACK_TAG eyecatcher
        removeTags=[]
        currentTags = obj.getTags(self.tenant + "/" + self.project + "/" + name)
        for cTag in currentTags:
            if (cTag.startswith(self.OPENSTACK_TAG)):
                removeTags.append(cTag)

        try:
            if (len(removeTags)>0):
                obj.modifyTags(self.tenant + "/" + self.project + "/" + name, None, removeTags)
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
            obj.modifyTags(self.tenant + "/" + self.project + "/" + name, addTags, None)
        except SOSError as e:
            if (e.err_code == SOSError.SOS_FAILURE_ERR):
                LOG.debug("SOSError adding the tag: " + e.err_text)
                
        return obj.getTags(self.tenant + "/" + self.project + "/" + name)    

    @retry_wrapper
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

    @retry_wrapper
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

    @retry_wrapper
    def create_snapshot(self, snapshot):
        self.authenticate_user()
        obj = Snapshot(self.fqdn, self.port)
        try:    
            snapshotname = snapshot['name']
            volumename = snapshot['volume_name']
            projectname = self.project
            tenantname = self.tenant
            storageresType = 'block'
            storageresTypename = 'volumes'
            filesystem = None
            resourceUri = obj.storageResource_query(storageresType, filesystem, volumename, projectname, tenantname)
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
        obj = Snapshot(self.fqdn, self.port)
        try:
            snapshotname = snapshot['name']
            volumename = snapshot['volume_name']
            projectname = self.project
            tenantname = self.tenant
            storageresType = 'block'
            storageresTypename = 'volumes'
            filesystem = None
            resourceUri = obj.storageResource_query(storageresType, filesystem, volumename, projectname, tenantname)
            sync = True
            obj.snapshot_delete(storageresType, storageresTypename, resourceUri, snapshotname, sync)
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
            volumename = volume['name']            
            obj = ExportGroup(self.fqdn, self.port)
            foundgroupname = self._find_exportgroup(obj, initiatorPort)
            if (foundgroupname is None):
                # check if this initiator is contained in any ViPR Host object
                foundhostname= self._find_host(initiatorPort)
                if (foundhostname is None):
                    if (not self._host_exists(hostname)):
                        # create a host so it can be added to the export group
                        host_obj = Host(self.fqdn, self.port)
                        host_obj.host_create(hostname, self.project, self.tenant, socket.getfqdn())
                        LOG.info("Created host " + hostname)
                    # add the initiator to the host
                    host_obj.host_add_initiator(hostname, initiatorPort, protocol, initiatorNode);
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
                res = obj.exportgroup_create(foundgroupname, self.project, self.tenant, self.virtualarray, 'Host', foundhostname);

            res = obj.exportgroup_add_volumes(foundgroupname, self.project, self.tenant, volumename, None, None)

            # Wait for LUN to be really attached
            device_number = None
            while (device_number is None or device_number == '-1'):
                device_info = self.find_device_number(volume)
                try:
                    device_number = device_info['hostlunid']
                except KeyError:
                    device_number = None

                if (device_number is None or device_number == '-1'):
                    time.sleep(10)

        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Attach volume (" + volume['name'] + ") to host (" + hostname + ") initiator (" + initiatorPort + ") failed: " + e.err_text)

    @retry_wrapper
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
            foundgroupname = self._find_exportgroup(obj, initiatorPort)
            if foundgroupname is not None:
                res = obj.exportgroup_remove_volumes(foundgroupname, self.project, self.tenant, volumename, False)    # no snapshot (snapshot = False)
        except SOSError as e:
            raise SOSError(SOSError.SOS_FAILURE_ERR, "Removing volume " + volumename + " from export Group " + foundgroupname + " failed: " + e.err_text)

    @retry_wrapper
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


    '''
    Find the export group to which the given initiator port belong, if exists.
    Question: can an initiator be part of two groups?
    '''
    def _find_exportgroup(self, exportgroup_obj, initiator_port):
        foundgroupname = None
        grouplist = exportgroup_obj.exportgroup_list(self.project, self.tenant)
        for groupid in grouplist:
            groupdetails = exportgroup_obj.exportgroup_show(groupid, self.project, self.tenant)
            initiators = groupdetails['initiators']
            for initiator in initiators:
                if (initiator['initiator_port'] == initiator_port):
                    foundgroupname = groupdetails['name']
                    break

            if foundgroupname is not None:
                break

        return foundgroupname

    
    '''
    Find the host, if exists, to which the given initiator belong.
    '''
    def _find_host(self, initiator_port):
        foundhostname = None
        host_obj = Host(self.fqdn, self.port)
        hosts = host_obj.host_list(self.tenant)
        for host in hosts:
            initiators = host_obj.host_query_initiators(host['id'])
            for initiator in initiators:
                if (initiator_port == initiator['name']):
                    foundhostname = host['name']
                    break

            if foundhostname is not None:
                break

        return foundhostname

    '''
    Check if a Host object with the given hostname already exists in ViPR
    '''
    def _host_exists(self, host_name):
        host_obj = Host(self.fqdn, self.port)
        hosts = host_obj.host_list(self.tenant)
        for host in hosts:
            if (host_name == host['name']):
                return True

        return False


    @retry_wrapper
    def update_volume_stats(self):
        """Retrieve stats info."""
        LOG.debug(_("Updating volume stats"))
        self.authenticate_user()
 
        volume = Volume(self.fqdn, self.port)
        try:
            vols = volume.list_volumes(self.tenant + "/" + self.project)
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
                        (s, h) = vipr_utils.service_json_request(self.fqdn, self.port,
                                      "GET",
                                      URI_VPOOL_VARRAY_CAPACITY.format(vpair[0], vpair[1]),
                                      None)
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

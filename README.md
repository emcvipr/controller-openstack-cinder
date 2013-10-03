Introduction
============

This guide explains how to install, configure, and make use of the EMC ViPR Cinder Driver with the Havana release of OpenStack.


Overview
========

The EMC ViPR Cinder driver contains both an ISCSIDriver as well as a FibreChannelDriver,
with the ability to create/delete and attach/detach volumes and create/delete snapshots, etc.


Requirements
============

EMC ViPR version 1.0, or above, is required. Refer to the EMC ViPR documentation installation and configuration instructions. 



Supported Operations
====================

The following operations are supported:
* Create volume
* Delete volume
* Attach volume
* Detach volume
* Create snapshot
* Delete snapshot
* Get Volume Stats
* Copy image to volume
* Copy volume to image
* Clone volume


Unsupported Operations
======================

The following operations are not supported:
* Create volume from snapshot



Preparation
===========


Configure EMC ViPR
-----------------

The EMC ViPR environment must meet specific configuration requirements to support the OpenStack Cinder Driver:
* ViPR users must be assigned a Tenant Administrator role or a Project Administrator role for the Project being used. ViPR roles are configured by ViPR Security Administrators. Consult the EMC ViPR documentation for details.
* The following configuration must have been done by a ViPR System Administrator, using the ViPR UI, ViPR API, or ViPR CLI:
   - ViPR virtual assets, such as virtual arrays and virtual pools, must have been created.
Note
Multi-volume consistency groups are not supported by the ViPR ViPR Cinder Driver. Please ensure that the Multi-volume consistency option is not enabled on the Virtual Pool with ViPR.
* Each instance of the ViPR Cinder Driver can be used to manage only one one virtual array and one virtual pool within ViPR. 
* The ViPR Cinder Driver requires one Virtual Storage Pool, with the following requirements (non-specified values can be set as desired):
   - Storage Type: Block
   - Provisioning Type: Thin
   - Protocol: iSCSI or Fibre Channel or both
   - Multi-Volume Consistency: DISABLED
   - Maximum Native Snapshots: A value greater than 0 allows the OpenStack user to take Snapshots. 


Download and configure EMC ViPR Cinder driver
----------------------

* Download the EMC ViPR Cinder driver from the following location: https://github.com/emcvipr/controller-openstack-cinder. 

* Copy the vipr subdirectory to the cinder/volume/drivers/emc directory of your OpenStack node(s) where cinder-volume is running.  This directory is where other Cinder drivers are located.

* Modify /etc/cinder/cinder.conf by adding the following lines, substituting values for your environment:

```
volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_iscsi.EMCViPRISCSIDriver
vipr_hostname=lgly7180.lss.emc.com
vipr_port=4443
vipr_username=username
vipr_password=password
vipr_tenant=Provider Tenant 
vipr_project=vprojectname
vipr_varray=varrayname
vipr_cookiedir=/tmp
```

note 1: The value for vipr_cookiedir defaults to /tmp but can be overridden if specified

note 2: to utilize the Fibre Channel Driver, replace the volume_driver line above with:

```
volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_iscsi.EMCViPRFCDriver

```

* Modify the rpc_response_timeout value in /etc/cinder/cinder.conf to at least 5 minutes. if this value does not already exist within the cinder.conf file, please add it

```
rpc_response_timeout=300

```

* Create OpenStack volume types with the cinder command

```
cinder --os-username admin --os-tenant-name admin type-create <typename>
```

* Map the OpenStack volume type to the ViPR Virtual Pool with the cinder command

```
cinder --os-username admin --os-tenant-name admin type-key <typename> set ViPR:VPOOL=<ViPR-poolname>
```


iSCSI Specific Notes
====================

Add your nova compute nodes to ViPR
----------------------

* on the cinder-volume node, cd to the cinder/volume/drivers/emc/vipr/cli directory 

* run the viprcli.py command to add ther compute nodes to the ViPR networks

```
   ./viprcli.py openstack add_host -name <hostname> 
```


Fibre Channel Specific Notes
============================

* The OpenStack compute host must be attached to a VSAN or fabric discovered by ViPR.

* There is no need to perform any SAN zoning operations. EMC ViPR will perform the necessary operations autmoatically as part of the provisioning process


Enable sg_scan to run under rootwrap
----------------------

* within the /etc/cinder/cinder.conf file, add the following line

```
   sg_scan: CommandFilter, sc_scan, root  

```



License
----------------------

```
    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.
```



``Copyright (c) 2013 EMC Corporation.``

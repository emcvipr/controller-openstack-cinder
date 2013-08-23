Introduction
============

This guide explains how to configure and make use of the EMC ViPR Cinder Driver with the Havana release of OpenStack.


Overview
========

The EMC ViPR Cinder driver is based on the existing ISCSIDriver, with the ability to create/delete and attach/detach volumes and create/delete snapshots, etc.


Requirements
============

EMC ViPR version 1.0, or above, is required as well as at least one storage array that support iSCSI volumes. Refer to the EMC ViPR documentation installation and configuration instructions. 



Supported Operations
====================

The following operations are supported:
* Create volume
* Delete volume
* Attach volume
* Detach volume
* Create snapshot
* Delete snapshot
* Create volume from snapshot



Preparation
===========


Configure EMC ViPR
-----------------

Configure at least one Virtual Storage Pool, with the following requirements:
* requirement 1
* requirement 2
* requirement 3


Download and configure EMC ViPR Cinder driver
----------------------

* Download the EMC ViPR Cinder driver from the following location: https://github.com/emcvipr/controller-openstack-cinder. Copy the vipr subdirectory to the cinder/volume/emc directory of your OpenStack node(s) where cinder-volume is running.  This directory is where other Cinder drivers are located.

* Modify /etc/cinder/cinder.conf by adding the following lines, substituting values for your environment:
```
volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_iscsi.EMCViPRISCSIDriver
vipr_hostname=lgly7180.lss.emc.com
vipr_port=4443
vipr_username=username
vipr_password=password
vipr_tenant=Provider Tenant 
vipr_project=proj-iscsi
vipr_varray=va-iscsi

```


* Create OpenStack volume types with the cinder command
```
cinder --os-username admin --os-tenant-name admin type-create <typename>
```

* Map the OpenStack volume type to the ViPR Virtual Pool with the cinder command
```
cinder --os-username admin --os-tenant-name admin type-key <typename> set ViPR:VPOOL=<ViPR-poolname>
```





``Copyright (c) 2013 EMC Corporation.``

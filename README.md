1. Introduction
============

This guide explains how to install, configure, and make use of the EMC ViPR
Cinder Driver. The driver works with Icehouse release of Openstack.



2. Overview
========

The EMC ViPR Cinder driver contains both an ISCSIDriver as well as a
FibreChannelDriver, with the ability to create/delete and attach/detach
volumes and create/delete snapshots, etc.


3. Requirements
============

1. EMC ViPR version 2.1 is required. Refer to the EMC ViPR
   documentation for installation and configuration instructions.
2. EMC ViPR CLI to be installed on the Openstack Cinder node/s.


4. Supported Operations
====================
The following operations are supported:
* Create volume.
* Delete volume.
* Attach volume.
* Detach volume.
* Create snapshot.
* Delete snapshot.
* Get Volume Stats.
* Copy image to volume.
* Copy volume to image.
* Clone volume.
* Extend volume.
* Create volume from snapshot.




5. Preparation
===========

5.1 Install ViPR CLI on Cinder node
-----------------------------------

You can install the ViPR command line interface executable directly from ViPR
appliance onto a supported Linux host.

Before you begin
* You need access to the ViPR appliance host.
* You need root access to the Linux host.

5.1.1 Procedure to install

1. Log in to the Linux server as root.
2. Create a temporary directory to download the CLI installer.
  ```
  mkdir cli/temp
  ```
  ```
  cd cli/temp
  ```
3. Either point your browser to https://<FQDN>:4443/cli or run the wget command
   to retrieve the ViPR CLI installation bundle:
  ```
  wget https://<FQDN>:4443/cli
  ```
   For sites with self-signed certificates or where issues are detected, optionally use
   http://<ViPR_virtual_IP>:9998/cli only when you are inside a trusted
   network. <ViPR_virtual_IP> is the ViPR public virtual IP address, also known as the
   network vip. The CLI installation bundle is downloaded to the current directory.
   
4. Use tar to extract the CLI and its support files from the installation bundle.
  ```
  tar -xvzf <cli_install_bundle>
  ```
5. Run the CLI installation program.
  ```
  python setup.py install
  ```
  Install the ViPR CLI wherever python dist-packages or site-package folder is located at.

  For Example:
  ```
  /usr/local/lib/python2.7/dist-packages
  or
  /usr/lib/python2.6/site-packages
  ```
   
6. Create viprcli.pth in the above folder where CLI is installed with the following contents
   ```
   (if your system has python 2.7):
   ./bin/viprcli-2.1-py2.7.egg	
   ./bin/viprcli-2.1-py2.7.egg/viprcli	
   	
   (if your system has python 2.6):
   ./bin/viprcli-2.1-py2.6.egg 
   ./bin/viprcli-2.1-py2.6.egg/viprcli 
   ```
   
7. Create viprcli.profile in the DIRECTORY where the PARENT DIRECTORY of cinder-volume is located.(You can find that using the command which cinder-volume )
   in devstack.

    For example if the cinder-volume is located in /usr/bin. Then place the viprcli.profile in /usr with the following contents

    ```
    VIPR_CLI_INSTALL_DIR=
    ```

    In the same directory where viprcli.profile is placed, create a folder "cookie" with permissions 777.

8. From the command prompt open python prompt by typing python. Below command should be successful to indicate that the process has been correctly performed. 
   ```
   import viprcli
   ```


5.2 Configure EMC ViPR
----------------------

The EMC ViPR environment must meet specific configuration requirements to support the OpenStack Cinder Driver:
* ViPR users must be assigned a Tenant Administrator role or a Project Administrator role for the Project being used. ViPR roles are configured by ViPR Security Administrators. Consult the EMC ViPR documentation for details.
* The following configuration must have been done by a ViPR System Administrator, using the ViPR UI, ViPR API, or ViPR CLI:
   - ViPR virtual assets, such as virtual arrays and virtual pools, must have been created.
   - Each virtual array designated for use in the OpenStack iSCSI driver must have an IP network created with appropriate IP storage ports.
   Note: Multi-volume consistency groups are not supported by the ViPR Cinder Driver. Please ensure that the Multi-volume consistency option is not enabled on the Virtual Pool with ViPR.
* Each instance of the ViPR Cinder Driver can be used to manage only one virtual array and one virtual pool within ViPR. 
* The ViPR Cinder Driver requires one Virtual Storage Pool, with the following requirements (non-specified values can be set as desired):
   - Storage Type: Block
   - Provisioning Type: Thin
   - Protocol: iSCSI or Fibre Channel or both
   - Multi-Volume Consistency: DISABLED
   - Maximum Native Snapshots: A value greater than 0 allows the OpenStack user to take Snapshots. 


5.3 Download and configure EMC ViPR Cinder driver
-------------------------------------------------

* Download the EMC ViPR Cinder driver from the following location: https://github.com/emcvipr/controller-openstack-cinder. 

* Copy the vipr subdirectory to the cinder/volume/drivers/emc directory of your OpenStack node(s) where cinder-volume is running.  This directory is where other Cinder drivers are located.

* Modify /etc/cinder/cinder.conf by adding the following lines, substituting values for your environment:

  ```
  volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_iscsi.EMCViPRISCSIDriver
  vipr_hostname=<ViPR-Host-Name>
  vipr_port=4443
  vipr_username=<username>
  vipr_password=<password>
  vipr_tenant=<Tenant> 
  vipr_project=<ViPR-Project-Name>
  vipr_varray=<ViPR-Virtual-Array-Name>
  vipr_cookiedir=/tmp
  vipr_storage_vmax=True or False
  ```

  Note 1: The value for vipr_cookiedir defaults to /tmp but can be overridden if specified.

  Note 2: To utilize the Fibre Channel Driver, replace the volume_driver line above with:
  
  Note 3: Please set vipr_storage_vmax to True, if the ViPR vpool has VMAX or VPLEX(with VMAX as backend) as the backing storage.

  ```
  volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_fc.EMCViPRFCDriver

  ```

* Modify the rpc_response_timeout value in /etc/cinder/cinder.conf to at least 5 minutes. if this value does not already exist within the cinder.conf file, please add it

  ```
  rpc_response_timeout=300

  ```
* Now, stop cinder-volume service using following command
  ```
  service openstack-cinder-volume stop
  ```
* Now, restart the cinder-volume service using the following command
  ```
  service openstack-cinder-volume start
  ```
* Create OpenStack volume types with the cinder command

  ```
  cinder --os-username admin --os-tenant-name admin type-create <typename>
  ```

* Map the OpenStack volume type to the ViPR Virtual Pool with the cinder command

  ```
  cinder --os-username admin --os-tenant-name admin type-key <typename> set ViPR:VPOOL=<ViPR-PoolName>
  ```

5.4 Notes to Configure both FC and iSCSI back-end drivers
--------------------------------------------------------

Add/modify the following entries if you are planning to use multiple back-end drivers.
  1.	The "enabled_backends" parameter needs to be set in cinder.conf and other parameters required in each backend need to be placed in individual backend sections (rather than the DEFAULT section).
  2.	 “enabled_backends” will be commented by default, please un-comment and add the multiple back-end names as following. 
    ```
    enabled_backends=viprdriver-iscsi,viprdriver-fc
    ```
  3.	Add the following at the end of the file; please note that each section is named as in #2 above.
    ```
    [viprdriver-iscsi]
    volume_driver=cinder.volume.drivers.emc.vipr.emc_vipr_iscsi.EMCViPRISCSIDriver
    volume_backend_name=EMCViPRISCSIDriver
    vipr_hostname=<ViPR Host Name>
    vipr_port=4443
    vipr_username=<username>
    vipr_password=<password>
    vipr_cli_path=<CLI-Install-Path>
    vipr_tenant=<Tenant>
    vipr_project=<ViPR-Project-Name>
    vipr_varray=<ViPR-Virtual-Array-Name>
    vipr_storage_vmax=True or False
    ```

    ```
    [viprdriver-fc]
    volume_driver=cinder.volume.drivers.emc.vipr.emc_vipr_fc.EMCViPRFCDriver
    volume_backend_name=EMCViPRFCDriver
    vipr_hostname=<ViPR Host Name>
    vipr_port=4443
    vipr_username=<username>
    vipr_password=<password>
    vipr_cli_path=<CLI-Install-Path>
    vipr_tenant=<Tenant>
    vipr_project=<ViPR-Project-Name>
    vipr_varray=<ViPR-Virtual-Array-Name>
    vipr_storage_vmax=True or False
    ```
  4. Stop the cinder-volume.
    ```
    service openstack-cinder-volume stop
    ```
  5. Start the cinder-volume service.
    ```
    service openstack-cinder-volume start
    ```
  6. Setup the volume-types and volume-type to volume-backend association.

    ```
    cinder --os-username admin --os-tenant-name admin type-create "ViPR High Performance"
    cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance" set ViPR:VPOOL="High Performance"
    cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance" set volume_backend_name=EMCViPRISCSIDriver
    cinder --os-username admin --os-tenant-name admin type-create "ViPR High Performance FC"
    cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance FC" set ViPR:VPOOL="High Performance FC"
    cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance FC" set volume_backend_name=EMCViPRFCDriver
    cinder --os-username admin --os-tenant-name admin extra-specs-list
```

  7. iSCSI specific notes
  =======================  
* The openstack compute host must be added to the ViPR along with its iSCSI initiator.
* The iSCSI initiator must be associated with IP network on the ViPR.


  8. Fibre Channel Specific Notes
  ============================
* The OpenStack compute host must be attached to a VSAN or fabric discovered by ViPR.
* There is no need to perform any SAN zoning operations. EMC ViPR will perform the necessary operations automatically as part of the provisioning process.
* If you are running an older version of OpenStack, you may need to add the following line within the /etc/cinder/rootwrap.d/volume.filters file, to enable sg_scan to run under rootwrap.

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



``Copyright (c) 2014 EMC Corporation.``

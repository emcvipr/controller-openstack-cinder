1. Introduction
============

This guide explains how to install, configure, and make use of the EMC ViPR
Cinder Driver. The driver works with following releases of Openstack.
1. Havana
2. Icehouse


2. Overview
========

The EMC ViPR Cinder driver contains both an ISCSIDriver as well as a
FibreChannelDriver, with the ability to create/delete and attach/detach
volumes and create/delete snapshots, etc.


3. Requirements
============

1. EMC ViPR version 1.1 is required. Refer to the EMC ViPR
   documentation for installation and configuration instructions.
2. EMC ViPR CLI to be installed on the Openstack Cinder node/s.



4. Supported Operations
====================

The following operations are supported:
1. Create volume
2. Delete volume
3. Attach volume
4. Detach volume
5. Create snapshot
6. Delete snapshot
7. Get Volume Stats
8. Copy image to volume
9. Copy volume to image
10.Clone volume
11.Create volume from snapshot
12.Extend volume



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
./Installer_viprcli.linux
```
6. Change directory to /opt/vipr/cli or to the directory where the CLI is installed.
7. Note : Perform this step only when you have not provided the correct input in step 5.
   Edit the file viprcli.profile using the vi command and set the VIPR_HOSTNAME to
   the ViPR public virtual IP address and VIPR_PORT=4443 environment variable and
   save the file.
```
# vi viprcli.profile
#!/usr/bin/sh
# Installation directory of ViPR CLI
ViPR_CLI_INSTALL_DIR=/opt/ViPR/cli
# Add the ViPR install directory to the PATH and PYTHONPATH env 
variables
if [ -n $ViPR_CLI_INSTALL_DIR ]
then
export PATH=$ViPR_CLI_INSTALL_DIR/bin:$PATH
export PYTHONPATH=$ViPR_CLI_INSTALL_DIR/bin:$PYTHONPATH
fi
# USER CONFIGURABLE ViPR VARIABLES
# ViPR Host fully qualified domain name
ViPR_HOSTNAME=example.mydomain.com
# ViPR Port Number
ViPR_PORT=4443
:wq
```
8. Run the source command to set the path environment variable for the ViPR
   executable.
```
source ./viprcli.profile
```
9. From the command prompt run: viprcli -h. If the help for viprcli is displayed, then the installation is successful.

5.1.2 Copying ViPR CLI on the non supported platform
 
If ViPR CLI installation is not supported on the operating system where Cinder
is installed, then perform only 4 steps from the section 5.1.1. After extracting 
the contents of the tar file, do the following.

1. cd to folder 'Linux'
2. tar -xvf viprcli.tar.gz
3. Copy "bin" folder to the location of your interest. For e.g /opt/storageos/cli
4. Then perform the steps #6 to #9 from the section 5.1.1.


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
vipr_cli_path=<CLI-Install-Path>
vipr_tenant=<Tenant> 
vipr_project=<ViPR-Project-Name>
vipr_varray=<ViPR-Virtual-Array-Name>
vipr_cookiedir=/tmp
```

Note 1: The value for vipr_cookiedir defaults to /tmp but can be overridden if specified.

Note 2: To utilize the Fibre Channel Driver, replace the volume_driver line above with:

```
volume_driver = cinder.volume.drivers.emc.vipr.emc_vipr_fc.EMCViPRFCDriver

```

* Modify the rpc_response_timeout value in /etc/cinder/cinder.conf to at least 5 minutes. if this value does not already exist within the cinder.conf file, please add it

```
rpc_response_timeout=300

```
* Now, restart the cinder-volume service.

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
2.	 “enabled_backends” will be commented by default, please un-comment and add the multiple back-end names as below. 
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
```
4. Restart the cinder-volume service.
5. Setup the volume-types and volume-type to volume-backend association.

```
cinder --os-username admin --os-tenant-name admin type-create "ViPR High Performance"
cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance" set ViPR:VPOOL="High Performance"
cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance" set volume_backend_name=EMCViPRISCSIDriver
cinder --os-username admin --os-tenant-name admin type-create "ViPR High Performance FC"
cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance FC" set ViPR:VPOOL="High Performance FC"
cinder --os-username admin --os-tenant-name admin type-key "ViPR High Performance FC" set volume_backend_name=EMCViPRFCDriver
cinder --os-username admin --os-tenant-name admin extra-specs-list
```

6. Fibre Channel Specific Notes
============================

* The OpenStack compute host must be attached to a VSAN or fabric discovered by ViPR.

* There is no need to perform any SAN zoning operations. EMC ViPR will perform the necessary operations automatically as part of the provisioning process


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



``Copyright (c) 2013 EMC Corporation.``

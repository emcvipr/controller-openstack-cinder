1. Introduction
============

This guide explains how to install, configure, and make use of the EMC ViPR
Cinder Driver. The driver works with following releases of Openstack.
1. Icehouse
2. Juno


2. Overview
========

The EMC ViPR Cinder driver contains ISCSIDriver, FibreChannelDriver as well as a
ScaleIODriver, with the ability to create/delete and attach/detach
volumes and create/delete snapshots, etc.


3. Requirements
============

1. EMC ViPR version 2.2 is required. Refer to the EMC ViPR
   documentation for installation and configuration instructions.
2. EMC ViPR CLI to be installed on the Openstack Cinder node/s.
3. EMC ViPR 2.2 in combination with Openstack Icehouse supports ScaleIO versions 1.3 
   and 1.31 as the backend.
4. EMC ViPR 2.2 in combination with Openstack Juno supports consistency group and 
   consistency group snap shots.


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
* Create volume from snapshot.
* Extend volume.
* Create consistency group.
* Delete consistency group
* Create consistency group snapshot.
* Delete consistency group snapshot.



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

3. Either point your browser to "https://<FQDN>:4443/cli" or run the wget command
   to retrieve the ViPR CLI installation bundle: 
  ```
  wget https://<FQDN>:4443/cli  --no-check-certificate  --content-disposition
  ```
   For sites with self-signed certificates or where issues are detected, optionally use
   http://<FQDN>:9998/cli only when you are inside a trusted
   network. The CLI installation bundle is downloaded to the current directory. 
   The wget command for the same is below.
  ```
  wget  http://<FQDN>:9998/cli  --content-disposition
  ```   
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

6. Open viprcli.profile file located at the above installation directory.
   The username which we use to run the cinder service should have write permissions
   to the folder path specified by the field VIPR_CLI_INSTALL_DIR. If, the user
   doesnt have the write permissions, then set the value of VIPR_CLI_INSTALL_DIR
   to a path for which the user running cinder has write permissions to.

7. Note : Perform this step only when you have not provided the correct input in step 5.
   Edit the file viprcli.profile using the vi command and set the VIPR_HOSTNAME to
   the ViPR public virtual IP address and VIPR_PORT=4443 environment variable and
   save the file.
  ```
  # vi viprcli.profile
  #!/usr/bin/sh
  # Installation directory of ViPR CLI
  ViPR_CLI_INSTALL_DIR=/home/user1
  # Add the ViPR install directory to the PATH and PYTHONPATH env variables
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

  ```
8. From the command prompt open python prompt by typing python. Below command should be 
   successful to indicate that the process has been correctly performed.

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
* Each instance of the ViPR Cinder Driver can be used to manage only one virtual array and one virtual pool within ViPR. 
* The ViPR Cinder Driver requires one Virtual Storage Pool, with the following requirements (non-specified values can be set as desired):
   - Storage Type: Block
   - Provisioning Type: Thin
   - Protocol: iSCSI, Fibre Channel or both
                        or
                    ScaleIO
   - Multi-Volume Consistency: DISABLED OR ENABLED (Consistency group is supported from Juno release)
   - Maximum Native Snapshots: A value greater than 0 allows the OpenStack user to take Snapshots. 


5.3 Download and configure EMC ViPR Cinder driver
-------------------------------------------------

* Download the EMC ViPR Cinder driver from the following location: https://github.com/emcvipr/controller-openstack-cinder. 

* Copy the vipr subdirectory to the cinder/volume/drivers/emc directory of your OpenStack node(s) where cinder-volume is running.  This directory is where other Cinder drivers are located.

* Modify /etc/cinder/cinder.conf by adding the following lines, substituting values for your environment:

```
volume_driver = cinder.volume.drivers.emc.vipr.iscsi.EMCViPRISCSIDriver
vipr_hostname=<ViPR-Host-Name>
vipr_port=4443
vipr_username=<username>
vipr_password=<password>
vipr_tenant=<Tenant> 
vipr_project=<ViPR-Project-Name>
vipr_varray=<ViPR-Virtual-Array-Name>
vipr_cookiedir=/tmp
vipr_storage_vmax= True or False

Below fields are needed only for ScaleIO backend.

vipr_scaleio_rest_gateway_ip=10.247.78.45
vipr_scaleio_rest_gateway_port=443
vipr_scaleio_rest_server_username=admin
vipr_scaleio_rest_server_password=adminpassword
scaleio_verify_server_certificate=True or False
scaleio_server_certificate_path=<path-of-certificate-for-validation>


```

Note 1: The value for vipr_cookiedir defaults to /tmp but can be overridden if specified.

Note 2: To utilize the Fibre Channel Driver, replace the volume_driver line above with:

```
volume_driver = cinder.volume.drivers.emc.vipr.fc.EMCViPRFCDriver

```
Note 3: To utilize the ScaleIO Driver, replace the volume_driver line above with:

```
volume_driver = cinder.volume.drivers.emc.vipr.scaleio.EMCViPRScaleIODriver

```
Note 4: set vipr_storage_vmax to True, if the ViPR vpool has VMAX or VPLEX(with VMAX as backend) as the backing storage.

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

5.4 Notes to configure FC,iSCSI and ScaleIO back-end drivers(Multiple back-ends)
--------------------------------------------------------------------------------

Add/modify the following entries if you are planning to use multiple back-end drivers.
1.	The "enabled_backends" parameter needs to be set in cinder.conf and other parameters required in each backend need to be placed in individual backend sections (rather than the DEFAULT section).
2.	 enabled_backends will be commented by default, please un-comment and add the multiple back-end names as below. 
 ```
 enabled_backends=viprdriver-iscsi,viprdriver-fc,viprdriver-scaleio
 ```
3.	Add the following at the end of the file; please note that each section is named as in #2 above.
```
[viprdriver-iscsi]
volume_driver=cinder.volume.drivers.emc.vipr.iscsi.EMCViPRISCSIDriver
volume_backend_name=EMCViPRISCSIDriver
vipr_hostname=<ViPR Host Name>
vipr_port=4443
vipr_username=<username>
vipr_password=<password>
vipr_tenant=<Tenant>
vipr_project=<ViPR-Project-Name>
vipr_varray=<ViPR-Virtual-Array-Name>
vipr_cookiedir=/tmp
```

```
[viprdriver-fc]
volume_driver=cinder.volume.drivers.emc.vipr.fc.EMCViPRFCDriver
volume_backend_name=EMCViPRFCDriver
vipr_hostname=<ViPR Host Name>
vipr_port=4443
vipr_username=<username>
vipr_password=<password>
vipr_tenant=<Tenant>
vipr_project=<ViPR-Project-Name>
vipr_varray=<ViPR-Virtual-Array-Name>
vipr_cookiedir=/tmp
```

```
[viprdriver-scaleio]
volume_driver = cinder.volume.drivers.emc.vipr.scaleio.EMCViPRScaleIODriver
volume_backend_name=EMCViPRScaleIODriver
vipr_hostname=<ViPR Host Name>
vipr_port=4443
vipr_username=<username>
vipr_password=<password>
vipr_tenant=<Tenant>
vipr_project=<ViPR-Project-Name>
vipr_varray=<ViPR-Virtual-Array-Name>
vipr_cookiedir=/tmp
vipr_scaleio_rest_gateway_ip=<ScaleIO Rest Gateway>
vipr_scaleio_rest_gateway_port=443
vipr_scaleio_rest_server_username=<rest gateway username>
vipr_scaleio_rest_server_password=<rest gateway password>
scaleio_verify_server_certificate=True or False
scaleio_server_certificate_path=<certificate path>
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
cinder --os-username admin --os-tenant-name admin type-create "ViPR performax SIO"
cinder --os-username admin --os-tenant-name admin type-key "ViPR performax SIO" set ViPR:VPOOL="Scaled Perf"
cinder --os-username admin --os-tenant-name admin type-key "ViPR performax SIO" set volume_backend_name=EMCViPRScaleIODriver
cinder --os-username admin --os-tenant-name admin extra-specs-list
```

6. iSCSI specific notes
=======================

* The openstack compute host must be added to the ViPR along with its iSCSI initiator.
* The iSCSI initiator must be associated with IP network on the ViPR.


7. Fibre Channel Specific Notes
============================

* The OpenStack compute host must be attached to a VSAN or fabric discovered by ViPR.

* There is no need to perform any SAN zoning operations. EMC ViPR will perform the necessary operations automatically as part of the provisioning process


* If you are running an older version of OpenStack, you may need to add the following line within the /etc/cinder/rootwrap.d/volume.filters file, to enable sg_scan to run under rootwrap.

```
   sg_scan: CommandFilter, sc_scan, root  

```

8. ScaleIO notes specific to SDC configuration
==============================================
* Plese install the scaleio SDC on the openstack host.
* The OpenStack compute host must be be added as the SDC the ScaleIO MDS using the below command
  NOTE: The below step has to be repeated when ever the SDC(openstack host in this case) is rebooted.

```
/opt/emc/scaleio/sdc/bin/drv_cfg --add_mdm --ip List of MDM IPs(starting with primary MDM and separated by comma)
Example: /opt/emc/scaleio/sdc/bin/drv_cfg --add_mdm --ip 10.247.78.45,10.247.78.46,10.247.78.47
```

* Verify the above with the following command. It should list the above configuration.
```
/opt/emc/scaleio/sdc/bin/drv_cfg --query_mdms
```

9. Configuring ScaleIO nova driver
====================================
* If the ScaleIO being used is 1.30, then copy the file scaleiodriver.py to the 
nova/virt/libvirt directory.
* If the ScaleIO being used is 1.31, then copy the file scaleiolibvirtdriver to the 
nova/virt/libvirt directory.
* If the ScaleIO being used is 1.30, then use a text editor to edit the libvirt_volume_driver 
key in the Nova configuration file /etc/nova/nova.conf. Add the scaleio key value pair mentioned below
```
libvirt_volume_drivers =
scaleio=nova.virt.libvirt.scaleiodriver.LibvirtScaleIOVolumeDriver
```
* If the ScaleIO being used is 1.31, then use a text editor to edit the libvirt_volume_driver 
key in the Nova configuration file /etc/nova/nova.conf. Add the scaleio key value pair mentioned below
```
libvirt_volume_drivers =
scaleio=nova.virt.libvirt.scaleiolibvirtdriver.LibvirtScaleIOVolumeDriver
```
* Add the same text mentioned in the previous step to the volume_drivers key.
* Create the file scaleio.filters at the locations /etc/nova/rootwarp.d and /etc/cinder/rootwrap.d. Add the
following text to the scaleio.filters file

[Filters]drv_cfg: CommandFilter, /opt/emc/scaleio/sdc/bin/drv_cfg, root

10. Consistency Group specific configuration 
====================================
* Use a text editor to edit the file /etc/cinder/policy.json and change the values
  of the below fields as specified. Upon editing the file, restart the c-api service.

```
    "consistencygroup:create" : "",
    "consistencygroup:delete": "",
    "consistencygroup:get": "",
    "consistencygroup:get_all": "",
```

11. Names of resources in backend storage 
=========================================
* All the resources like Volume, Consistency Group, Snapshot and 
  Consistency Group Snapshot will use the display name in openstack 
  for naming in the backend storage. Previously, we used the
  openstack ID of snapshot for naming the snapshot in the backend.
  
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

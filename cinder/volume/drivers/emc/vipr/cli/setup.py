#!/usr/bin/python

# Copyright (c) 2013 EMC Corporation
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

import distutils.core
import os
import re

distutils.core.setup(
    name='SosCli',
    description='ViPR commands line interface for accessing ViPR appliance',
    classifiers=[
        'Development Status :: Production/Stable',
        'Environment :: Console',
        'Intended Audience :: All Users',
        'License :: EMC license',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    data_files=[('',[	'authentication.py',
			'viprcli.py',
			'common.py',
			'virtualpool.py',
			'exportgroup.py',
			'fileshare.py',
			'virtualarray.py',
			'project.py',
			'snapshot.py',
			'storagepool.py',
			'storageport.py',
			'storagesystem.py',
			'tenant.py',
			'network.py',
			'volume.py',
                        'viprcli.bat',
                        'protectionsystem.py',
            'consistencygroup.py',
            'host.py',
            'hostinitiators.py',
            'hostipinterfaces.py',
            'cluster.py',
            'vcenter.py',
            'vcenterdatacenter.py'

			 
		    ]
		)]
)

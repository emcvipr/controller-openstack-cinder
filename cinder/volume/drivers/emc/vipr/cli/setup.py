#!/usr/bin/env python
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

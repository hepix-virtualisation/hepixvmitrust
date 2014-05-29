from hepixvmitrust.__version__ import version
from sys import version_info
import os

try:
    from setuptools import setup, find_packages
except ImportError:
	try:
            from distutils.core import setup
	except ImportError:
            from ez_setup import use_setuptools
            use_setuptools()
            from setuptools import setup, find_packages

data_files_installdir = "/usr/share/doc/vmilisttool-%s" % (version)
if "VIRTUAL_ENV" in  os.environ:
    data_files_installdir = 'doc'


setup(name='hepixvmitrust',
    version=version,
    description="VM Image list creation and signing tool",
    long_description="""hepixvmitrust is a package that contains a CLI tool, and a minimal
implementation, in its documentation for X509 signing lists of
virtual machine image metadata. The tools are generally reusable
but were developed to satisfy the need to securely exchange virtual
machine images between High Energy Physics sites, in a similar way
to yum and apt repositories provide for rpms, this software provides
for Virtual Maschines.""",
    author="O M Synge",
    author_email="owen.synge@desy.de",
    license='Apache License (2.0)',
    install_requires=[
       "M2Crypto>=0.16",
        ],
    tests_require=[
        'coverage >= 3.0',
        'nose >= 1.1.0',
        'mock',
    ],
    # This is required to make nose tests run under SL6
    setup_requires=[
        'nose',
    ],
    test_suite = 'nose.collector',
    url = 'https://github.com/hepix-virtualisation/hepixvmitrust',
    packages = ['hepixvmitrust'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research'
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        ],

    scripts=['vmilisttool'],
    data_files=[(data_files_installdir ,['README.md','ChangeLog','imagelist.json','minimal.py','LICENSE'])]
    )

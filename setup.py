from hepixvmitrust.__version__ import version
from sys import version_info


try:
	from distutils.core import setup
except:
	try:
        	from setuptools import setup, find_packages
	except ImportError:
        	from ez_setup import use_setuptools
        	use_setuptools()
        	from setuptools import setup, find_packages


setup(name='hepixvmitrust',
    version=version,
    description="VM Image list creationg and signing tool",
    author="O M Synge",
    author_email="owen.synge@desy.de",
    install_requires=[
       "M2Crypto>=0.16",
        ],
    url = 'https://github.com/hepix-virtualisation/hepixvmitrust',
    packages = ['hepixvmitrust'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research'
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache 2.0',
        ],
    
    scripts=['vmilisttool'],
    data_files=[('/usr/share/doc/vmilisttool',['README.md','ChangeLog','imagelist.json','minimal.py','LICENSE'])]
    )

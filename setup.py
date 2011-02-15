from distutils.core import setup
setup(name='desy-grid-vmis',
    version='0.0.1',
    description="Simple straw man signer",
    author="O M Synge",
    author_email="owen.Synge@desy.de",
    url="www-it.desy.de",
    scripts = ["vmilisttool.py"],
    package_dir={'': '.'},
    data_files=[('/usr/bin/', ['vmilisttool.py']),
        ('/usr/share/doc/vmilisttool',['README','env.sh'])]
    )

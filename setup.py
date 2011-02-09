from distutils.core import setup
setup(name='desy-grid-vmis',
    version='0.0.1',
    description="Simple straw man signer",
    author="O M Synge",
    author_email="owen.Synge@desy.de",
    url="www-it.desy.de",
    scripts = ["vmimagesigner"],
    package_dir={'': '.'},
    packages=['vmis'],
    data_files=[('/usr/bin/', ['vmimagesigner']),
        ('/usr/share/doc/vmimagemanager',['README','env.sh'])]
    )

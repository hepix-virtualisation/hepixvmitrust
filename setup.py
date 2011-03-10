from distutils.core import setup
setup(name='desy-grid-vmis',
    version='0.0.5',
    description="Simple straw man signer",
    author="O M Synge",
    author_email="owen.Synge@desy.de",
    url="www-it.desy.de",
    scripts=['vmilisttool.py'],
    data_files=[('/usr/share/doc/vmilisttool',['README','ChangeLog','imagelist.json'])]
    )

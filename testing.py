#!/usr/bin/env python

import codecs
import optparse
import os
import sys
import hashlib
import os.path
# needed to the signing of images.
from M2Crypto import BIO, Rand, SMIME
import uuid
# simplejson is included with Python 2.6 and above
# with the name json
if float(sys.version[:3]) >= 2.6:
    import json
else:
    # python 2.4 or 2.5 can also import simplejson
    # as working alternative to the json included.
    import simplejson as json

import datetime

# we should probably not import everything, ok for now
from hepixvmitrust import *

def test_things():
    image = EndorserModel()
    f = open("endorser", 'w')
    json.dump(image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("endorser", 'r')
    json_stuff = json.load(f)
    print 'dsadasd'
    fred= VMendorserDecoder(json_stuff)
    print 'dsadasd'
    print fred.metadata
    
def test_things2():
    image = ImageModel()
    f = open("fred", 'w')
    json.dump(image, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("fred", 'r')
    json_stuff = json.load(f)
    fred= VMimageDecoder(json_stuff)
    print fred.metadata
    print 'dsadasd'

def test_things3():
    list_mode = ListModel()
    f = open("listmodel", 'w')
    json.dump(list_mode, f, cls=VMimageListEncoder, sort_keys=True, indent=4)
    f.close()
    f = open("listmodel", 'r')
    json_stuff = json.load(f)
    fred= VMimageDecoder(json_stuff)
    print fred.metadata
    print 'dsadasd'
def test_things4():
    view = VMListView()
    loadedlist = view.load_file('imagelist.json')
    
    
    avmlistOutput = json.dumps(loadedlist,cls=VMimageListEncoder)
    print "vmimagelist=%s" % (type(avmlistOutput))
    f = imagemodel(vmi_uid='32455374',
        vmi_url='http://www.yokel.org',
        vmi_hash_sha512='bignum',
        vmi_hypervisor='kvm',
        vmi_description='easy to run vm',
        vmi_os_version='sl6.0201101',
        vmi_os_architecture='i386',
        vmi_disk_size='20e12bytes')
    imageoutput = json.dumps(f,cls=VMimageListEncoder)
    print "xdx%s" % (imageoutput)
    fred = json.loads(imageoutput,object_hook=VMimageDecoder)
    imageoutput = json.dumps(f,cls=VMimageListEncoder)
    print "xdx%s" % (imageoutput)
    avmlist = listmodel(owner_real_name="Owen Synge",
        owner_email='owen.synge@yokel.org',
        vmi_url='www.yokel.org',
        vmic_url='www.yokel.org',
        images=[f])
    avmlistOutput = json.dumps(avmlist,cls=VMimageListEncoder)
    print "vmimagelist=%s" % (avmlistOutput)
    view.save_file(avmlist,'imagelist.json')

def test_things5():
    view = VMListView()
    loadedlist = view.load_file('/tmp/foo2.json')
    print "loadedlist=%s" % (loadedlist)
    print "loadedlist.metadata=%s" % (loadedlist.metadata)
    print "loadedlist.endorser=%s" % (loadedlist.endorser)
    print "loadedlist.images=%s" % (loadedlist.images)
    
    avmlistOutput = json.dumps(loadedlist,cls=VMimageListEncoder, sort_keys=True, indent=4)
    print "vmimagelist=%s" % (avmlistOutput)

def main():
    # TODO: this needs to have the above testing functions
    #       run and tested.
    print "Running Some Tests"

if __name__ == "__main__":
    main()
